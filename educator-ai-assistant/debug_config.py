#!/usr/bin/env python3
"""
Debug config loading
"""
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from app.core.config import settings

print("🔧 Config Debug:")
print(f"DATABASE_URL: {settings.DATABASE_URL}")
print(f"Settings object: {settings}")
print(f"All settings:")
for field_name in settings.model_fields:
    value = getattr(settings, field_name)
    print(f"  {field_name}: {value}")