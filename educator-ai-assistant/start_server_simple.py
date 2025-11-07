#!/usr/bin/env python3
"""
Simple server starter script
"""
import os
import sys

# Add the current directory to Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

try:
    from app.main import app
    import uvicorn
    
    print("Starting FastAPI server on http://localhost:8001")
    uvicorn.run(app, host="localhost", port=8001, log_level="info")
except ImportError as e:
    print(f"Import error: {e}")
    print("Current working directory:", os.getcwd())
    print("Python path:", sys.path)
except Exception as e:
    print(f"Server error: {e}")