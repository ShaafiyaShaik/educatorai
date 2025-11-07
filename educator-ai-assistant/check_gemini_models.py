#!/usr/bin/env python3
"""
Check available Gemini models
"""

import google.generativeai as genai
from app.core.config import settings

# Configure with the project's configured Gemini API key (read from settings/.env)
genai.configure(api_key=getattr(settings, 'GEMINI_API_KEY', None))

print("🔍 Checking available Gemini models...")
try:
    models = genai.list_models()
    for model in models:
        print(f"✅ Model: {model.name}")
        print(f"   Display Name: {model.display_name}")
        print(f"   Supported Methods: {model.supported_generation_methods}")
        print("---")
except Exception as e:
    print(f"❌ Error: {e}")