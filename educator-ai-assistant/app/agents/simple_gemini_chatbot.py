"""
SimpleGeminiChatbot

This module implements a minimal, isolated chatbot that forwards conversation
inputs to the Google Gemini (Generative AI) API using the provided API key.

Design decisions:
- Isolated from any existing assistant code; no imports from previous assistant
  modules so it won't interfere with them.
- Accepts conversation history from the frontend so chat state is preserved.
- Attempts lightweight action extraction for two actions: send_message and
  schedule_meeting. Execution is simulated/stubbed here (logged and returned)
  because project-specific integrations (mail/SMS/calendar) vary per install.
"""
from typing import Any, Dict, List, Optional
import json
import re
import logging

import google.generativeai as genai

from app.core.simple_chatbot_config import (
    SIMPLE_GEMINI_API_KEY,
    SIMPLE_GEMINI_MODEL,
    SIMPLE_GEMINI_MAX_TOKENS,
    SIMPLE_GEMINI_TEMPERATURE,
    SIMPLE_GEMINI_DEV_FALLBACK,
    SIMPLE_GEMINI_ALT_API_KEYS,
)

logger = logging.getLogger(__name__)

# Initialize the Gemni client with the provided key. This initialization is
# isolated to this module and will not affect other modules in the project.
# Configure the Gemini client for this module using the provided API key.
genai.configure(api_key=SIMPLE_GEMINI_API_KEY)


class SimpleGeminiChatbot:
    """A minimal wrapper around Gemini chat for the teacher chatbot.

    Public method:
    - chat(message, history, language, auto_execute)
      -> returns dict: { reply: str, action: Optional[dict], executed: Optional[dict] }
    """

    def __init__(self) -> None:
        self.model = SIMPLE_GEMINI_MODEL
        self.max_tokens = SIMPLE_GEMINI_MAX_TOKENS
        self.temperature = SIMPLE_GEMINI_TEMPERATURE
        self.dev_fallback = SIMPLE_GEMINI_DEV_FALLBACK
        # Track configured API key and alternates so we can rotate on quota
        # errors without requiring a process restart.
        self.api_key = SIMPLE_GEMINI_API_KEY
        self.alt_keys = SIMPLE_GEMINI_ALT_API_KEYS if 'SIMPLE_GEMINI_ALT_API_KEYS' in globals() else []
        try:
            genai.configure(api_key=self.api_key)
        except Exception:
            # Non-fatal: configuration may fail in some dev environments; we'll
            # surface errors on calls instead.
            logger.debug("Failed to configure genai client with initial key")

    def _generate_with_retries(self, prompt: str, max_retries: int = 3):
        """Attempt model.generate_content with exponential backoff on quota errors.
        On non-quota errors, attempt one fallback-model try (list_models) before failing.
        Raises the final exception if all attempts fail.
        """
        import time
        import random

        try:
            # optional import for precise exception detection
            from google.api_core.exceptions import ResourceExhausted
        except Exception:
            ResourceExhausted = None

        attempt = 0
        last_exc = None
        while attempt <= max_retries:
            try:
                model = genai.GenerativeModel(self.model)
                resp = model.generate_content(prompt)
                return resp
            except Exception as e:
                last_exc = e
                # Detect quota/resource-exhausted patterns if we can't import the class
                is_quota = False
                if ResourceExhausted and isinstance(e, ResourceExhausted):
                    is_quota = True
                else:
                    msg = str(e).lower()
                    if "quota" in msg or "429" in msg or "resourceexhausted" in msg:
                        is_quota = True

                if is_quota:
                    # Try rotating through alternate API keys (if provided) before
                    # falling back to exponential backoff retry. Build a candidate
                    # list starting with the current key.
                    keys_to_try = [getattr(self, 'api_key', SIMPLE_GEMINI_API_KEY)]
                    try:
                        for k in getattr(self, 'alt_keys', []):
                            if k and k not in keys_to_try:
                                keys_to_try.append(k)
                    except Exception:
                        # alt_keys may not exist in some dev setups
                        pass

                    logger.warning("Gemini quota hit for current key; attempting key rotation through %d keys", len(keys_to_try))
                    rotated = False
                    for k in keys_to_try:
                        try:
                            logger.info("Trying Gemini API key rotation with a different key (partial masked)")
                            genai.configure(api_key=k)
                            # update the configured key on success
                            self.api_key = k
                            model = genai.GenerativeModel(self.model)
                            resp = model.generate_content(prompt)
                            rotated = True
                            return resp
                        except Exception as e2:
                            # If the error for this key is a quota error, continue to next
                            msg2 = str(e2).lower()
                            if "quota" in msg2 or "429" in msg2 or "resourceexhausted" in msg2:
                                logger.warning("Key rotation attempt hit quota for this key; trying next key")
                                continue
                            else:
                                # Non-quota error for this key — log and try next key
                                logger.exception("Key rotation attempt failed with non-quota error: %s", e2)
                                continue

                    # If rotation didn't succeed, fallback to exponential backoff
                    attempt += 1
                    if attempt > max_retries:
                        break
                    sleep = (2 ** attempt) + random.uniform(0, 1)
                    logger.warning("Gemini quota hit; no keys available or all exhausted. Retrying in %.1fs (attempt %d/%d)", sleep, attempt, max_retries)
                    time.sleep(sleep)
                    continue

                # Non-quota error: try a fallback model once
                try:
                    models = genai.list_models()
                    fallback_name = None
                    for m in models:
                        name = getattr(m, 'name', None) or getattr(m, 'model', None)
                        if name and ("flash" in name or "pro" in name or "2.0" in name):
                            fallback_name = name
                            break
                    if fallback_name:
                        logger.info("Retrying with fallback model %s due to error: %s", fallback_name, e)
                        model = genai.GenerativeModel(fallback_name)
                        resp = model.generate_content(prompt)
                        return resp
                except Exception as e2:
                    logger.exception("Fallback attempt failed: %s", e2)

                # Not a quota error or fallback failed — break and surface the last exception
                break

        # If we get here, all attempts failed
        raise last_exc

    def _build_messages(self, message: str, history: Optional[List[Dict[str, str]]], language: str) -> List[Dict[str, str]]:
        # System prompt encourages the model to preserve language (including Telugu)
        system = (
            "You are a helpful administrative assistant for educators. Reply in the user's language. "
            "If the user requests actions like sending a message or scheduling a meeting,"
            " output a JSON object inside delimiters <ACTION_JSON>{...}</ACTION_JSON> with keys:"
            " action (send_message | schedule_meeting), recipient, content, datetime (optional)."
            " If no action is required, do not output the ACTION_JSON block and only reply normally."
        )

        # We will return a single prompt string compatible with the installed
        # google.generativeai client. The client in this project uses
        # genai.GenerativeModel(...).generate_content(prompt) style calls.
        parts = [system, "\n\nConversation:\n"]
        if history:
            for h in history:
                role = h.get("role", "user")
                content = h.get("content", "")
                if role == 'user':
                    parts.append(f"User: {content}\n")
                else:
                    parts.append(f"Assistant: {content}\n")

        # Append current user message
        parts.append(f"User: {message}\nAssistant:")
        return "".join(parts)

    def _extract_action_block(self, text: str) -> Optional[Dict[str, Any]]:
        # Look for the explicit JSON block the system prompt requested
        m = re.search(r"<ACTION_JSON>(.*?)</ACTION_JSON>", text, re.DOTALL)
        if not m:
            return None
        try:
            payload = m.group(1).strip()
            # Some models may include markdown or backticks; try to find first { ... }
            json_start = payload.find("{")
            json_end = payload.rfind("}")
            if json_start == -1 or json_end == -1:
                return None
            json_str = payload[json_start:json_end+1]
            action = json.loads(json_str)
            return action
        except Exception as e:
            logger.exception("Failed to parse action JSON: %s", e)
            return None

    def _simple_regex_action(self, text: str) -> Optional[Dict[str, Any]]:
        # Very light-weight regex fallback to catch common patterns like
        # "send message to Jennifer: ..." or "schedule meeting with John tomorrow at 10am"
        send_match = re.search(r"send (?:a )?message to ([\w\s]+)[:\-\s]*([\s\S]+)$", text, re.IGNORECASE)
        if send_match:
            recipient = send_match.group(1).strip()
            content = send_match.group(2).strip()
            return {"action": "send_message", "recipient": recipient, "content": content}
        sched_match = re.search(r"schedule (?:a )?meeting with ([\w\s]+) (?:on |at |for )?([\w\s:,]+)$", text, re.IGNORECASE)
        if sched_match:
            recipient = sched_match.group(1).strip()
            datetime = sched_match.group(2).strip()
            return {"action": "schedule_meeting", "recipient": recipient, "datetime": datetime}
        return None

    def _execute_action(self, action: Dict[str, Any]) -> Dict[str, Any]:
        # Lightweight simulated execution. In production you would wire this
        # into your existing communication / calendar systems. We return a
        # structured status so the frontend can show success/failure.
        try:
            act = action.get("action")
            if act == "send_message":
                recipient = action.get("recipient")
                content = action.get("content")
                # TODO: integrate with actual messaging system. For now simulate.
                logger.info("Simulated sending message to %s: %s", recipient, content)
                return {"status": "ok", "detail": f"Message sent to {recipient}"}
            if act == "schedule_meeting":
                recipient = action.get("recipient")
                dt = action.get("datetime")
                logger.info("Simulated scheduling meeting with %s at %s", recipient, dt)
                return {"status": "ok", "detail": f"Meeting scheduled with {recipient} at {dt}"}
            return {"status": "error", "detail": "Unknown action"}
        except Exception as e:
            logger.exception("Error executing action: %s", e)
            return {"status": "error", "detail": str(e)}

    def chat(self, message: str, history: Optional[List[Dict[str, str]]] = None, language: str = "auto", auto_execute: bool = True) -> Dict[str, Any]:
        """Send a message to Gemini and optionally execute actions.

        Args:
            message: user message
            history: conversation history (list of {role, content})
            language: language hint (unused by the model directly beyond system prompt)
            auto_execute: if True, perform simple simulated execution for recognized actions

        Returns:
            { reply: str, action: Optional[dict], executed: Optional[dict] }
        """
        prompt = self._build_messages(message, history, language)

        try:
            resp = self._generate_with_retries(prompt)
            reply_text = resp.text if hasattr(resp, 'text') else str(resp)
        except Exception as e:
            # If dev fallback is enabled, return a deterministic mocked reply so
            # local development can continue without Gemini quota/credentials.
            logger.exception("Gemini API call failed for model %s: %s", self.model, e)
            if self.dev_fallback:
                logger.info("SIMPLE_GEMINI_DEV_FALLBACK enabled — returning deterministic dev response")
                # Provide a simple, parseable reply that the rest of the code can
                # attempt to extract actions from (or the frontend can display).
                dev_reply = (
                    "[DEV FALLBACK] Gemini API unavailable or quota exceeded. "
                    "This is a simulated assistant reply for development."
                )
                # Attempt to include a no-op action example if the user asked for an action
                # (keeps downstream parsing stable)
                return {"reply": dev_reply, "action": None, "executed": None}
            else:
                return {"reply": "Error contacting Gemini API.", "action": None, "executed": None}

        # Try to extract an explicit action block
        action = self._extract_action_block(reply_text)
        if action is None:
            # Try a lightweight regex-based extraction
            action = self._simple_regex_action(reply_text)

        executed = None
        if action and auto_execute:
            executed = self._execute_action(action)

        return {"reply": reply_text, "action": action, "executed": executed}


# Expose a single module-level instance to be imported by the API router.
simple_chatbot = SimpleGeminiChatbot()
