#!/usr/bin/env python3
"""
Simple server starter
"""
import os
import sys
import subprocess

# Set the PYTHONPATH to include the current directory
current_dir = os.getcwd()
os.environ['PYTHONPATH'] = current_dir

# Start the server
cmd = [sys.executable, "-m", "uvicorn", "app.main:app", "--host", "127.0.0.1", "--port", "8003"]
print(f"Starting server with command: {' '.join(cmd)}")
print(f"Current directory: {current_dir}")
print(f"PYTHONPATH: {os.environ.get('PYTHONPATH')}")

subprocess.run(cmd)