"""Lightweight Hugging Face executor for action extraction.

This module provides a simple prompt-based extractor using a Hugging Face
text-to-text model (e.g., Flan-T5 family). It's intentionally lightweight —
it does not train a model here, but offers a place to call a fine-tuned
model or the Hugging Face Inference API later.

Functions:
- parse_action_with_hf(message, history, model_name) -> Optional[dict]

Notes:
- Requires `transformers` and `torch` (already in requirements.txt).
- For production, prefer a small fine-tuned model that reliably outputs
  structured JSON. This function currently uses a prompting approach.
"""
from typing import Any, Dict, List, Optional
import logging
import json

try:
    from transformers import pipeline
except Exception:
    pipeline = None

logger = logging.getLogger(__name__)


def parse_action_with_hf(message: str, history: Optional[List[Dict[str, str]]] = None, model_name: str = None) -> Optional[Dict[str, Any]]:
    """Use a HF text2text model to extract an action JSON from the message.

    Returns a dict like { action: 'send_message', recipient: 'Jennifer', content: '...' }
    or None if parsing failed.
    """
    if pipeline is None:
        logger.warning("transformers.pipeline unavailable — cannot call HF model")
        return None

    model_name = model_name or "google/flan-t5-small"

    prompt_parts = [
        "Extract intent and slots from the user message. Respond ONLY with a JSON object with keys: action (send_message|schedule_meeting|none), recipient, content, datetime. If no action, return {\"action\": \"none\"}.",
        f"Message: {message}",
    ]
    if history:
        prompt_parts.append("History:\n" + "\n".join(h.get("content", "") for h in history))

    prompt = "\n\n".join(prompt_parts)

    try:
        gen = pipeline("text2text-generation", model=model_name, device=0 if False else -1)
        out = gen(prompt, max_length=256, do_sample=False)
        text = out[0]["generated_text"] if isinstance(out, list) and out else str(out)
        # Try to find JSON substring
        start = text.find("{")
        end = text.rfind("}")
        if start == -1 or end == -1:
            # maybe the whole text is JSON
            text = text.strip()
            try:
                return json.loads(text)
            except Exception:
                logger.debug("HF output not JSON: %s", text)
                return None
        json_str = text[start : end + 1]
        try:
            return json.loads(json_str)
        except Exception as e:
            logger.exception("Failed to parse JSON from HF output: %s", e)
            return None
    except Exception as e:
        logger.exception("HF model call failed: %s", e)
        return None
