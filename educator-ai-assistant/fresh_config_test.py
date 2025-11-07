#!/usr/bin/env python3
"""
Fresh config test with explicit reload
"""
import sys
import os
import importlib

# Clear any cached modules
modules_to_remove = [key for key in sys.modules.keys() if key.startswith('app.')]
for module in modules_to_remove:
    del sys.modules[module]

sys.path.insert(0, os.path.dirname(__file__))

# Fresh import
from app.core.config import Settings

# Create new settings instance
fresh_settings = Settings()

print("🔧 Fresh Config Test:")
print(f"DATABASE_URL: {fresh_settings.DATABASE_URL}")

# Also test by reading the file directly
with open("app/core/config.py", "r") as f:
    content = f.read()
    if "educator_db.sqlite" in content:
        print("✅ File contains educator_db.sqlite")
    else:
        print("❌ File does not contain educator_db.sqlite")
        
# Look for the actual line
lines = content.split('\n')
for i, line in enumerate(lines):
    if 'DATABASE_URL' in line and 'str' in line:
        print(f"Line {i+1}: {line.strip()}")