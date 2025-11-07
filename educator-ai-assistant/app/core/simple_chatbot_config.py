"""
Simple chatbot configuration. This file contains a default Gemini API key and
model settings for the newly added isolated chatbot. The API key is allowed
to be overridden by the SIMPLE_GEMINI_API_KEY environment variable.

NOTE: Storing API keys in source is not recommended for production. The key
is seeded here per the user's request but it is preferred to put secrets in
environment variables or secret stores.
"""
from os import getenv

# Default API key provided by the user. Can be overridden via env var.
DEFAULT_GEMINI_API_KEY = "AIzaSyBWqTxhCsIWUhzORyCDlTqeg9sS6lPfXzU"

SIMPLE_GEMINI_API_KEY = getenv("SIMPLE_GEMINI_API_KEY", DEFAULT_GEMINI_API_KEY)

# Model selection and generation parameters
# Use a stable model known to be supported for generate_content in this repo.
SIMPLE_GEMINI_MODEL = getenv("SIMPLE_GEMINI_MODEL", "gemini-2.0-flash")
SIMPLE_GEMINI_MAX_TOKENS = int(getenv("SIMPLE_GEMINI_MAX_TOKENS", "512"))
SIMPLE_GEMINI_TEMPERATURE = float(getenv("SIMPLE_GEMINI_TEMPERATURE", "0.2"))
# When true, the simple chatbot will return a deterministic developer fallback
# response instead of calling the Gemini API when quota/errors occur. Useful
# for local development when API credentials or quota aren't available.
SIMPLE_GEMINI_DEV_FALLBACK = getenv("SIMPLE_GEMINI_DEV_FALLBACK", "false").lower() in ("1", "true", "yes")
