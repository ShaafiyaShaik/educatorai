"""Lightweight local NLU for fast intent and slot extraction.

This module implements a very small rule-based parser as a fast first-pass
before calling Gemini. It returns an intent, slots dict, and a confidence
score (0..1). The intent names align with the system intents used elsewhere.
"""
from typing import Dict, Any, Optional, Tuple
import re


def parse_fast(text: str) -> Tuple[Optional[str], Dict[str, Any], float]:
    """Attempt to quickly extract an intent and slots with simple heuristics.

    Returns (intent_name or None, slots dict, confidence float).
    """
    if not text:
        return None, {}, 0.0

    txt = text.strip()
    low = txt.lower()

    # send_message patterns
    m = re.search(r"send (?:a )?message to ([\w\s'\-\.]+?)[:\-\s]+([\s\S]+)$", txt, re.IGNORECASE)
    if m:
        recipient = m.group(1).strip()
        content = m.group(2).strip()
        return "send_message", {"recipient": recipient, "content": content}, 0.95

    m2 = re.search(r"(?:message|msg) to ([\w\s'\-\.]+?)(?: about |: | to )?(.*)$", txt, re.IGNORECASE)
    if m2:
        recipient = m2.group(1).strip()
        content = m2.group(2).strip() or None
        return "send_message", {"recipient": recipient, "content": content}, 0.9

    # schedule_meeting patterns
    ms = re.search(r"schedule (?:a )?meeting (?:with )?([\w\s'\-\.]+?) (?:on |at |for )?([\w\s,:-]+)$", txt, re.IGNORECASE)
    if ms:
        recipient = ms.group(1).strip()
        datetime = ms.group(2).strip()
        return "schedule_meeting", {"recipient": recipient, "datetime": datetime}, 0.9

    # quick schedule query
    if any(k in low for k in ("my schedule", "what is my schedule", "my calendar", "schedule this week")):
        return "get_schedule", {}, 0.9

    # grades query
    if any(k in low for k in ("grade", "grades", "marks", "scores")):
        # try to capture name
        m3 = re.search(r"([A-Za-z][A-Za-z'\-\.\s]{0,60}?)'s\s+(?:grades|marks|scores)", low)
        if m3:
            name = m3.group(1).strip()
            name_cap = " ".join([p.capitalize() for p in name.split()])
            return "get_grades", {"recipient": name_cap}, 0.85
        return "get_grades", {}, 0.6

    # fallback: if the text looks like a name (two capitalized words)
    nm = re.match(r"^[A-Z][a-z]+\s+[A-Z][a-z]+$", txt)
    if nm:
        return "query_student", {"name": txt.strip()}, 0.9

    return None, {}, 0.0


def format_slots(intent: Optional[str], slots: Dict[str, Any]) -> Dict[str, Any]:
    # Normalize slot keys used across the system
    out = {}
    if not intent:
        return out
    if intent == "send_message":
        out["recipient"] = slots.get("recipient")
        out["content"] = slots.get("content")
    if intent == "schedule_meeting":
        out["recipient"] = slots.get("recipient")
        out["datetime"] = slots.get("datetime")
    if intent == "get_grades":
        out["recipient"] = slots.get("recipient")
    if intent == "query_student":
        out["name"] = slots.get("name")
    return out
