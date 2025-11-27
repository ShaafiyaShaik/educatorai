"""Intent router service

This module provides a small pipeline that uses the installed SimpleGeminiChatbot
for intent detection (without letting Gemini try to access internal data), and
then performs server-side slot resolution and execution using internal APIs.

Design goals:
- Use Gemini only for intent detection / extraction of structured action JSON.
- Resolve student names / ids and execute actions via internal endpoints on the
  backend (so the model doesn't need direct access to private data).
- Respect a "do not ask" directive (e.g. "don't ask me any more questions") to
  force execution even when some slots are missing.
"""
from typing import Any, Dict, List, Optional
import logging
import difflib
import re

import httpx

from app.agents.simple_gemini_chatbot import simple_chatbot
from app.services.action_executor import send_message as executor_send_message, schedule_meeting as executor_schedule_meeting, fetch_grades as executor_fetch_grades, fetch_schedule as executor_fetch_schedule
from app.services.nlu import parse_fast, format_slots
from app.services.conversation_state import get_state, update_state
from app.services.dialog_manager import DialogManager

logger = logging.getLogger(__name__)


def _normalize_name(s: Optional[str]) -> str:
    """Normalize a name for comparison: lower, remove punctuation, collapse spaces."""
    if not s:
        return ""
    # remove common punctuation, keep letters and spaces
    cleaned = re.sub(r"[^0-9A-Za-z\s]", "", s)
    cleaned = re.sub(r"\s+", " ", cleaned).strip().lower()
    return cleaned


def _name_matches(query: str, candidate: str, fuzzy_cutoff: float = 0.78) -> bool:
    """Return True if query and candidate likely refer to the same name.

    - exact normalized equality
    - substring containment
    - difflib similarity above cutoff
    """
    nq = _normalize_name(query)
    nc = _normalize_name(candidate)
    if not nq or not nc:
        return False
    if nq == nc:
        return True
    if nq in nc or nc in nq:
        return True
    # fuzzy match
    try:
        ratio = difflib.SequenceMatcher(None, nq, nc).ratio()
        if ratio >= fuzzy_cutoff:
            return True
        # Additional heuristic: if last names are very similar, accept even
        # if whole-name ratio is lower (handles misspelled first names).
        q_parts = nq.split()
        c_parts = nc.split()
        if len(q_parts) >= 1 and len(c_parts) >= 1:
            q_last = q_parts[-1]
            c_last = c_parts[-1]
            if q_last and c_last:
                last_ratio = difflib.SequenceMatcher(None, q_last, c_last).ratio()
                if last_ratio >= 0.85:
                    return True
    except Exception:
        pass
    return False


def _strip_action_block(text: Optional[str]) -> str:
    """Remove any <ACTION_JSON>...</ACTION_JSON> blocks from model reply for user-facing text."""
    if not text:
        return ""
    try:
        return re.sub(r"<ACTION_JSON>.*?</ACTION_JSON>", "", text, flags=re.DOTALL).strip()
    except Exception:
        return text or ""


def _find_last_mentioned_student(history: Optional[List[Dict[str, str]]]) -> Optional[str]:
    """Scan conversation history (assistant messages) for the last explicitly mentioned student name.

    Looks for patterns like "found X student(s) matching '...': Name (Section: ...)" or
    capitalized two-word names in assistant messages.
    """
    if not history:
        return None
    # search assistant messages in reverse
    name_pattern = re.compile(r"([A-Z][a-z]+\s+[A-Z][a-z]+)")
    found = None
    for h in reversed(history):
        role = h.get("role")
        content = h.get("content", "")
        if role and role.lower() == "assistant":
            # try the explicit 'found' pattern first
            m = re.search(r"found \d+ student\(s\) matching '\s*([^']+?)\s*':\s*([^\(\n]+)", content, re.IGNORECASE)
            if m:
                # group 2 may contain comma-separated names; pick first
                candidate = m.group(2).split(",")[0].strip()
                # normalize whitespace
                candidate = re.sub(r"\s+", " ", candidate)
                return candidate
            # fallback: look for capitalized name tokens
            m2 = name_pattern.search(content)
            if m2:
                return m2.group(1)
    return None


def _should_force_execute(message: str) -> bool:
    text = (message or "").lower()
    phrases = ["don't ask", "do not ask", "dont ask", "don't ask me", "no questions"]
    return any(p in text for p in phrases)


async def _resolve_student_by_name(client: httpx.AsyncClient, name: str, headers: Dict[str, str]) -> Dict[str, Any]:
    """Try to resolve a student name to an ID. Returns dict:
    { id: Optional[int], name: Optional[str], suggestions: List[str] }
    """
    result = {"id": None, "name": None, "suggestions": []}
    if not name:
        return result
    try:
        # Combine both student endpoints to build a candidate list
        candidates = []
        resp = await client.get("/api/v1/bulk-communication/students", headers=headers)
        if resp.status_code == 200:
            students = resp.json().get("students", [])
            for s in students:
                if s.get("name"):
                    candidates.append({"id": s.get("id"), "name": s.get("name")})

        resp2 = await client.get("/api/v1/students", headers=headers)
        if resp2.status_code == 200:
            data = resp2.json()
            students2 = data.get("students") if isinstance(data, dict) else data
            if students2:
                for s in students2:
                    if s.get("name"):
                        # avoid duplicates by name
                        if not any(c["name"] == s.get("name") for c in candidates):
                            candidates.append({"id": s.get("id"), "name": s.get("name")})

        lname = name.lower().strip()
        # Exact match first
        for c in candidates:
            if c.get("name") and c.get("name").lower().strip() == lname:
                result["id"] = c.get("id")
                result["name"] = c.get("name")
                return result

        # Partial substring match
        for c in candidates:
            if c.get("name") and lname in c.get("name").lower():
                result["id"] = c.get("id")
                result["name"] = c.get("name")
                return result

        # Fuzzy match using difflib; return top 3 suggestions
        names = [c.get("name") for c in candidates if c.get("name")]
        close = difflib.get_close_matches(name, names, n=3, cutoff=0.6)
        result["suggestions"] = close
        # Map suggestion to id if exact string matches
        if close:
            best = close[0]
            for c in candidates:
                if c.get("name") == best:
                    result["id"] = c.get("id")
                    result["name"] = c.get("name")
                    break
    except Exception as e:
        logger.exception("Error resolving student name '%s': %s", name, e)
    return result


async def detect_and_execute(
    message: str,
    history: Optional[List[Dict[str, str]]] = None,
    language: str = "auto",
    auto_execute: bool = True,
    auth_header: Optional[str] = None,
    educator_id: Optional[int] = None,
) -> Dict[str, Any]:
    """Detect intent using the SimpleGeminiChatbot and execute the action.

    Returns a dict: { reply, action, executed }
    """
    # 1) Quick server-side heuristics BEFORE calling the LLM to avoid
    # depending on Gemini for simple lookups or action parsing.
    # Try a lightweight regex on the raw user message first (fast, local).
    action = None
    try:
        action = simple_chatbot._simple_regex_action(message)
    except Exception:
        action = None

    # conversation memory: last resolved student (from state or history)
    last_student_name = None
    if educator_id:
        try:
            st = get_state(educator_id)
            last_student_name = st.get("last_resolved_student")
        except Exception:
            last_student_name = None
    # fall back to scanning assistant history for an explicit name
    if not last_student_name:
        last_student_name = _find_last_mentioned_student(history)

    # If there is a pending clarification stored in conversation state,
    # check whether the current user message is a selection for that
    # clarification (e.g., '1' or the full name). If so, resolve and
    # continue with the pending action.
    if educator_id:
        try:
            st = get_state(educator_id)
            pending = st.get("pending_clarify")
        except Exception:
            pending = None
    else:
        pending = None

    def _parse_selection(msg: str, suggestions: List[str]) -> Optional[str]:
        if not msg:
            return None
        t = msg.strip()
        # numeric selection
        if re.fullmatch(r"\d+", t):
            idx = int(t) - 1
            if 0 <= idx < len(suggestions):
                return suggestions[idx]
            return None
        # direct name match (case-insensitive) or fuzzy match
        for s in suggestions:
            if s.lower().strip() == t.lower().strip():
                return s
        # fuzzy contains
        for s in suggestions:
            if _name_matches(t, s):
                return s
        return None

    if pending and isinstance(pending, dict):
        user_choice = _parse_selection(message, pending.get("suggestions", []))
        if user_choice:
            # clear pending state and transform the stored action
            try:
                stored_action = pending.get("action")
                update_state(educator_id, pending_clarify=None)
            except Exception:
                stored_action = None
            if stored_action:
                # set chosen recipient and continue processing as if user had provided it
                stored_action["recipient"] = user_choice
                action = stored_action
                # fall through to normal execution below

    # Helper: replace pronouns that refer to a previously-resolved student
    def _replace_pronouns_with_name(text: str, name: Optional[str]) -> str:
        if not text or not name:
            return text
        # common pronouns/phrases teachers use to refer to the previously found student
        patterns = [r"\bthat student\b", r"\bthat one\b", r"\bthem\b", r"\bthem\b", r"\bher\b", r"\bhim\b", r"\bthat pupil\b"]
        out = text
        for p in patterns:
            out = re.sub(p, name, out, flags=re.IGNORECASE)
        return out

    # 2) Detect direct student-existence queries before hitting the model
    def _is_student_query_text(text: str) -> Optional[str]:
        if not text:
            return None
        t = text.lower()
        import re
        # Try multiple tolerant patterns including common misspellings like 'studnet'
        patterns = [
            r"(?:is there|do i have|do i|have i)\s+(?:any\s+)?([a-zA-Z][\w\s]{0,60}?)\s*(?:as|in|in my|a|is)?\s*(?:student|studnet|class|section|enrolled)?\??$",
            r"(?:is)\s+([a-zA-Z][\w\s]{0,60}?)\s+(?:a student|enrolled|present)\??$",
            r"(?:who is |is there a student named )([a-zA-Z][\w\s]{0,60})"
        ]
        for p in patterns:
            m = re.search(p, t)
            if m:
                name = m.group(1).strip()
                # remove words like 'any' or 'the' at start
                name = re.sub(r'^(any|the)\s+', '', name)
                return name
        return None

    def _is_schedule_query_text(text: str) -> bool:
        if not text:
            return False
        t = text.lower()
        patterns = [
            "my schedule",
            "schedule this week",
            "what is my schedule",
            "what's my schedule",
            "my calendar",
            "what do i have this week",
        ]
        return any(p in t for p in patterns)


    def _parse_schedule_request(text: str) -> Optional[Dict[str, str]]:
        """Parse schedule requests for explicit ranges like 'this month', 'this week', 'next week', or custom date ranges.

        Returns dict with keys: start_date (ISO), end_date (ISO), label (friendly label)
        or None if the text isn't a schedule request we can handle here.
        """
        if not text:
            return None
        t = text.lower()
        import datetime

        # Normalize some common phrasings
        if "this month" in t or "whole this month" in t or "whole this month's" in t or "this month's" in t:
            today = datetime.date.today()
            start = today.replace(day=1)
            # compute last day of month
            if start.month == 12:
                last = datetime.date(start.year, 12, 31)
            else:
                next_month = datetime.date(start.year, start.month + 1, 1)
                last = next_month - datetime.timedelta(days=1)
            label = start.strftime("%B %Y")
            return {"start_date": start.isoformat(), "end_date": last.isoformat(), "label": label}

        # Explicit 'this week' remains supported
        if "this week" in t:
            today = datetime.date.today()
            start = today - datetime.timedelta(days=today.weekday())
            end = start + datetime.timedelta(days=6)
            label = f"Week of {start.isoformat()}"
            return {"start_date": start.isoformat(), "end_date": end.isoformat(), "label": label}

        # Allow 'next week' and 'last week'
        if "next week" in t:
            today = datetime.date.today()
            start = today - datetime.timedelta(days=today.weekday()) + datetime.timedelta(days=7)
            end = start + datetime.timedelta(days=6)
            label = f"Week of {start.isoformat()}"
            return {"start_date": start.isoformat(), "end_date": end.isoformat(), "label": label}
        if "last week" in t or "previous week" in t:
            today = datetime.date.today()
            start = today - datetime.timedelta(days=today.weekday()) - datetime.timedelta(days=7)
            end = start + datetime.timedelta(days=6)
            label = f"Week of {start.isoformat()}"
            return {"start_date": start.isoformat(), "end_date": end.isoformat(), "label": label}

        # If user asked generically "my schedule" without range, default to this week
        if "my schedule" in t or "my calendar" in t or "what is my schedule" in t:
            today = datetime.date.today()
            start = today - datetime.timedelta(days=today.weekday())
            end = start + datetime.timedelta(days=6)
            label = f"Week of {start.isoformat()}"
            return {"start_date": start.isoformat(), "end_date": end.isoformat(), "label": label}

        return None


    def _is_grades_query_text(text: str) -> Optional[Dict[str, str]]:
        """Detect grade/score queries and try to extract a student name and optional section.

        Returns dict {'name': str, 'section': Optional[str]} or None.
        Examples matched:
        - "check Steven's grades"
        - "what are Nicole's marks from section A"
        - "show me John Doe's grades"
        """
        if not text:
            return None
        t = text.strip()
        low = t.lower()
        # Quick guard: only run heavy regex if grade-related keywords exist
        if not any(k in low for k in ("grade", "grades", "marks", "scores", "score")):
            return None
        # Try to capture patterns like "check <name>'s grades" or "show me <name> grades"
        # name may be one or two words, optionally followed by "from section X"
        m = re.search(r"(?:check|show|what are|what's|what is|display|give me|tell me)\s+([A-Za-z][A-Za-z\'\-\.\s]{0,60}?)\s*(?:'s|s)?\s*(?:grades|marks|scores)?(?:\s*(?:from|in)\s*(?:section\s*)?([A-Za-z0-9\-]+))?", low)
        if m:
            name = m.group(1).strip()
            section = m.group(2).strip() if m.group(2) else None
            # avoid matching generic phrases like "what are my grades" here (handled elsewhere)
            if name and name not in ("my", "the"):
                # Capitalize name heuristically for downstream resolution
                name_cap = " ".join([p.capitalize() for p in name.split()])
                return {"name": name_cap, "section": section}

        # Fallback: possessive patterns like "Steven's grades"
        m2 = re.search(r"([A-Za-z][A-Za-z\'\-\.\s]{0,60}?)'s\s+(?:grades|marks|scores)", low)
        if m2:
            name = m2.group(1).strip()
            name_cap = " ".join([p.capitalize() for p in name.split()])
            return {"name": name_cap, "section": None}

        return None

    student_query_name = None
    if action is None:
        student_query_name = _is_student_query_text(message)
    # Detect grade/score queries early
    grades_query = None
    if action is None:
        grades_query = _is_grades_query_text(message)

    # If the user message looks like a plain name (e.g. "Nichole Smith", "NS",
    # or just two words), treat it as a direct student-existence query. This
    # helps when users type a name instead of a full question.
    def _looks_like_name(text: str) -> Optional[str]:
        if not text:
            return None
        t = text.strip()
        # Reject overly long inputs
        if len(t) > 60:
            return None
        # Reject obvious greetings and very short tokens ("hi", "ok")
        greetings = {"hi", "hello", "hey", "ok", "okay", "thanks", "thank you", "bye"}
        if t.lower() in greetings:
            return None
        # If it is just initials (e.g. 'NS'), try to expand as initials if possible
        if re.fullmatch(r"[A-Z]{2,4}", t):
            return None
        # Accept one or two word names (allow hyphens, apostrophes)
        if len(t.split()) == 1 and len(t) < 3:
            return None
        if re.fullmatch(r"[A-Za-z][A-Za-z\-\'\.]+(?:\s+[A-Za-z][A-Za-z\-\'\.]+)?", t):
            return t
        return None
    if action is None and student_query_name is None:
        # Fast local NLU first (low latency). If it doesn't produce an intent,
        # fall back to Gemini.
        try:
            intent, slots, conf = parse_fast(message or canonical_message or "")
        except Exception:
            intent, slots, conf = (None, {}, 0.0)

        if intent:
            slots_norm = format_slots(intent, slots)
            # build an action dict compatible with Gemini output
            action = {"action": intent, **slots_norm, "confidence": conf}
            reply = None
        else:
            # We disable auto_execute in the model so it doesn't try to act on its own.
            model_result = simple_chatbot.chat(message=canonical_message, history=history, language=language, auto_execute=False)
            reply = model_result.get("reply")
            action = model_result.get("action")
            # If the model didn't extract an action, try a lightweight regex fallback
            if action is None:
                try:
                    action = simple_chatbot._simple_regex_action(reply or canonical_message or message)
                except Exception:
                    action = None
    else:
        # If we had a pre-detected action, set a simple reply placeholder (will be overwritten after execution)
        reply = None

    # Post-process extracted action: if recipient is a pronoun, replace it with
    # the last resolved student name so downstream resolution can succeed.
    if action and isinstance(action, dict):
        rec = action.get("recipient")
        if rec and isinstance(rec, str):
            low = rec.lower()
            if any(p in low for p in ("that student", "that one", "them", "her", "him", "that pupil")) and last_student_name:
                action["recipient"] = last_student_name

    # If still no action, and we didn't detect a student query earlier, try
    # to see if the LLM's reply is a student-existence question; otherwise,
    # use the pre-extracted student_query_name.
    if student_query_name is None and action is None:
        # attempt to parse the model reply as a student query as a last resort
        def _is_student_query_from_text(text: str) -> Optional[str]:
            if not text:
                return None
            import re
            m = re.search(r"([A-Za-z][\w\s]{0,60})\s*(?:is a student|a student|enrolled|in my class|in my section)", text.lower())
            if m:
                return m.group(1).strip()
            return None
        student_query_name = _is_student_query_from_text(reply) if reply else None
    if student_query_name:
        headers = {}
        if auth_header:
            headers["Authorization"] = auth_header
        base_url = "http://127.0.0.1:8003"
        matches = []
        async with httpx.AsyncClient(base_url=base_url) as client:
            try:
                resp = await client.get("/api/v1/bulk-communication/students", headers=headers)
                logger.debug("Student bulk endpoint response status=%s", getattr(resp, 'status_code', None))
                if resp.status_code == 200:
                    data_students = resp.json().get("students", [])
                    logger.debug("bulk students count=%s sample=%s", len(data_students), [s.get('name') for s in data_students[:5]])
                    for s in data_students:
                        # Try multiple likely name fields to be robust
                        candidate_names = []
                        for f in ("name", "full_name", "student_name"):
                            v = s.get(f)
                            if v:
                                candidate_names.append(v)
                        # Also try first/last
                        if s.get("first_name") or s.get("last_name"):
                            fq = "".join([s.get("first_name") or "", " ", s.get("last_name") or ""]).strip()
                            if fq:
                                candidate_names.append(fq)
                        # Normalize and compare
                        for cand in candidate_names:
                            if _name_matches(student_query_name, cand):
                                matches.append({"id": s.get("id"), "name": cand, "section": s.get("section_name")})

                resp2 = await client.get("/api/v1/students", headers=headers)
                logger.debug("Students endpoint response status=%s", getattr(resp2, 'status_code', None))
                if resp2.status_code == 200:
                    data = resp2.json()
                    students2 = data.get("students") if isinstance(data, dict) else data
                    if students2:
                        logger.debug("students endpoint count=%s sample=%s", len(students2), [s.get('name') for s in students2[:5]])
                        for s in students2:
                            candidate_names = []
                            for f in ("name", "full_name", "student_name"):
                                v = s.get(f)
                                if v:
                                    candidate_names.append(v)
                            if s.get("first_name") or s.get("last_name"):
                                fq = "".join([s.get("first_name") or "", " ", s.get("last_name") or ""]).strip()
                                if fq:
                                    candidate_names.append(fq)
                            for cand in candidate_names:
                                if _name_matches(student_query_name, cand):
                                    if not any(m.get("id") == s.get("id") for m in matches):
                                        matches.append({"id": s.get("id"), "name": cand, "section": s.get("section_name")})
            except Exception as e:
                logger.exception("Error querying students for existence check: %s", e)

        if matches:
            # Build a concise reply listing matches (limit to 5)
            parts = []
            for m in matches[:5]:
                sec = m.get("section") or "Unknown section"
                parts.append(f"{m.get('name')} (Section: {sec})")
            reply_text = f"Yes — found {len(matches)} student(s) matching '{student_query_name}': " + ", ".join(parts)
            return {"reply": reply_text, "action": None, "executed": None}
        else:
            return {"reply": f"No students named '{student_query_name}' were found in your roster.", "action": None, "executed": None}

    executed = None

    if action and auto_execute:
        # Prepare headers passed through from the frontend so internal endpoints
        # can authorize the action on behalf of the educator.
        headers = {}
        if auth_header:
            headers["Authorization"] = auth_header

        # Use a local async client that targets the internal API server. The
        # running backend in dev typically listens on 127.0.0.1:8003 in this
        # project; keep that as default but allow environment to override later.
        base_url = "http://127.0.0.1:8003"

        force_execute = _should_force_execute(message)
        # Dialog manager: decide whether to execute automatically based on mode/confidence
        dm = DialogManager()

        async with httpx.AsyncClient(base_url=base_url) as client:
            act = action.get("action")
            try:
                # Determine confidence and missing slots for this intent
                confidence = action.get("confidence") if isinstance(action, dict) else None
                confidence = float(confidence) if confidence is not None else 0.85
                missing = []
                recipient = action.get("recipient") if isinstance(action, dict) else None
                if act == "send_message":
                    if not recipient:
                        missing.append("recipient")
                if act in ("schedule_meeting", "create_meeting"):
                    if not recipient:
                        missing.append("recipient")
                    if not action.get("datetime"):
                        missing.append("datetime")
                if act in ("get_grades", "fetch_grades"):
                    if not recipient:
                        missing.append("recipient")

                recipient_count = 1
                # consult dialog manager whether to proceed
                should_exec = dm.should_execute(act, confidence, missing_slots=missing, recipient_count=recipient_count, force=force_execute)
                if not should_exec and not force_execute:
                    # If missing slots, prompt for them; otherwise require confirmation
                    if missing:
                        executed = {"status": "needs_more_info", "missing": missing}
                        return {"reply": "I need more information to complete that action.", "action": action, "executed": executed}
                    else:
                        executed = {"status": "needs_confirmation"}
                        return {"reply": "I can do that — would you like me to proceed?", "action": action, "executed": executed}
                if act == "send_message":
                    recipient = action.get("recipient")
                    content = action.get("content") or message

                    # Resolve recipient
                    student_id = None
                    resolved_name = None
                    suggestions = []
                    try:
                        maybe_id = int(recipient)
                        student_id = maybe_id
                    except Exception:
                        info = await _resolve_student_by_name(client, recipient, headers)
                        student_id = info.get("id")
                        resolved_name = info.get("name")
                        suggestions = info.get("suggestions", [])

                    if student_id is None:
                        if suggestions:
                            if force_execute:
                                chosen = suggestions[0]
                                info2 = await _resolve_student_by_name(client, chosen, headers)
                                student_id = info2.get("id")
                                resolved_name = info2.get("name")
                            else:
                                # Store pending clarification in conversation state so
                                # the next user message may select among suggestions.
                                executed = {"status": "needs_clarification", "missing": ["recipient"], "suggestions": suggestions}
                                try:
                                    if educator_id:
                                        update_state(educator_id, pending_clarify={"action": action, "suggestions": suggestions})
                                except Exception:
                                    logger.exception("Failed to store pending clarification in conversation state")
                                # Build a short user-facing disambiguation prompt
                                opt_lines = [f"{i+1}) {s}" for i, s in enumerate(suggestions[:6])]
                                prompt = (
                                    "I found multiple matches for that name. Which one did you mean? "
                                    + "Reply with the number or the full name: " + " | ".join(opt_lines)
                                )
                                return {"reply": prompt, "action": action, "executed": executed}
                        else:
                            if force_execute:
                                executed = {"status": "error", "detail": "Recipient not found (force_execute)"}
                            else:
                                executed = {"status": "needs_more_info", "missing": ["recipient"]}

                    if student_id:
                        res = await executor_send_message(client, headers, student_id, content, actor_id=educator_id)
                        if res.get("status") == "ok":
                            executed = {"status": "ok", "detail": f"Message sent to {resolved_name or recipient}", "response": res.get("response")}
                            # update conversation memory with the last resolved student
                            try:
                                if educator_id and resolved_name:
                                    update_state(educator_id, last_resolved_student=resolved_name)
                            except Exception:
                                logger.exception("Failed to update conversation state after send_message")
                        else:
                            executed = {"status": "error", "detail": res.get("detail"), "response": res.get("response")}

                elif act in ("schedule_meeting", "create_meeting"):
                    recipient = action.get("recipient")
                    dt = action.get("datetime")

                    info = await _resolve_student_by_name(client, recipient, headers)
                    student_id = info.get("id")
                    resolved_name = info.get("name")
                    suggestions = info.get("suggestions", [])

                    if student_id is None:
                        if suggestions:
                            if force_execute:
                                chosen = suggestions[0]
                                info2 = await _resolve_student_by_name(client, chosen, headers)
                                student_id = info2.get("id")
                                resolved_name = info2.get("name")
                            else:
                                executed = {"status": "needs_more_info", "missing": ["recipient"], "suggestions": suggestions}
                        else:
                            if force_execute:
                                executed = {"status": "error", "detail": "Recipient not found (force_execute)"}
                            else:
                                executed = {"status": "needs_more_info", "missing": ["recipient"]}
                    else:
                        if not dt and not force_execute:
                            executed = {"status": "needs_more_info", "missing": ["datetime"]}
                        else:
                            title = action.get("title") or f"Meeting with {resolved_name or recipient}"
                            res = await executor_schedule_meeting(client, headers, [student_id], title, dt, actor_id=educator_id)
                            if res.get("status") == "ok":
                                executed = {"status": "ok", "detail": f"Meeting scheduled with {resolved_name or recipient}", "response": res.get("response")}
                                try:
                                    if educator_id and resolved_name:
                                        update_state(educator_id, last_resolved_student=resolved_name)
                                except Exception:
                                    logger.exception("Failed to update conversation state after schedule_meeting")
                            else:
                                executed = {"status": "error", "detail": res.get("detail"), "response": res.get("response")}

                elif act in ("get_grades", "fetch_grades"):
                    recipient = action.get("recipient")
                    try:
                        maybe_id = int(recipient)
                        student_id = maybe_id
                    except Exception:
                        info = await _resolve_student_by_name(client, recipient, headers)
                        student_id = info.get("id")
                        resolved_name = info.get("name")

                    if not student_id:
                        executed = {"status": "error", "detail": "Recipient not found"}
                    else:
                        res = await executor_fetch_grades(client, headers, student_id, actor_id=educator_id)
                        if res.get("status") == "ok":
                            executed = {"status": "ok", "detail": "fetched_grades", "response": res.get("response")}
                        else:
                            executed = {"status": "error", "detail": res.get("detail"), "response": res.get("response")}

                else:
                    executed = {"status": "error", "detail": "Unknown action"}
            except Exception as e:
                logger.exception("Error executing action %s: %s", act, e)
                executed = {"status": "error", "detail": str(e)}

    # Normalize executed into a user-friendly reply so the frontend can show
    # a simple confirmation instead of raw JSON.
    user_reply = reply or ""
    if executed is not None:
        try:
            status = executed.get("status")
        except Exception:
            status = None

        if status == "ok":
            # Prefer the executed.detail if available, otherwise a generic message
            detail = executed.get("detail") or "Action completed successfully."
            user_reply = f"{detail}"
        elif status == "needs_more_info":
            missing = executed.get("missing", [])
            user_reply = (
                f"I need more information to complete that action. Missing: {', '.join(missing)}"
            )
        elif status == "error":
            detail = executed.get("detail") or "An error occurred while executing the action."
            # Surface HTTP response text if available for debugging
            resp_text = executed.get("response")
            if resp_text:
                user_reply = f"Failed to perform action: {detail} (info: {resp_text})"
            else:
                user_reply = f"Failed to perform action: {detail}"

    return {"reply": user_reply, "action": action, "executed": executed}
