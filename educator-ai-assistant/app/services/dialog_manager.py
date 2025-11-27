"""Dialog manager enforcing autonomy modes and simple decision rules.

This is a minimal implementation that decides whether an extracted action
should be executed immediately, needs confirmation, or requires a slot
clarification. It reads `AUTONOMY_MODE` from the environment: one of
"manual", "assist", "autonomous". Defaults to "assist".

Rules (simple):
- manual: never auto-execute (always require confirm)
- assist: auto-execute when confidence >= assist_threshold and no missing slots
- autonomous: execute even with lower confidence (but still not for mass actions)

This module is intentionally small — expand thresholds, risk checks and
whitelists as needed.
"""
import os
from typing import List, Optional


class DialogManager:
    def __init__(self):
        self.mode = os.getenv("AUTONOMY_MODE", "assist").lower()
        # Confidence thresholds
        self.assist_threshold = float(os.getenv("ASSIST_CONFIDENCE", "0.8"))
        self.autonomous_threshold = float(os.getenv("AUTONOMY_CONFIDENCE", "0.6"))
        # Max recipients allowed for auto-execute in assist mode
        self.max_auto_recipients = int(os.getenv("MAX_AUTO_RECIPIENTS", "5"))

    def should_execute(self, intent: str, confidence: float, missing_slots: Optional[List[str]] = None, recipient_count: int = 1, force: bool = False) -> bool:
        """Return True if the action should be executed immediately.

        `missing_slots` is a list of required but absent slots.
        """
        if force:
            return True
        if missing_slots:
            return False
        if self.mode == "manual":
            return False
        if self.mode == "assist":
            # Avoid auto-executing mass recipient actions
            if recipient_count > self.max_auto_recipients:
                return False
            return confidence >= self.assist_threshold
        if self.mode == "autonomous":
            return confidence >= self.autonomous_threshold
        # default conservative behavior
        return False
