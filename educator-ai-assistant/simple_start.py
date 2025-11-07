#!/usr/bin/env python3
"""
Simple server start and test
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import uvicorn
from app.main import app

if __name__ == "__main__":
    print("🚀 Starting Educator AI Assistant Server")
    print("📍 Server will run on: http://localhost:8003")
    print("🎯 Test educator login at: http://localhost:8003/docs")
    print("=" * 60)
    
    uvicorn.run(app, host="0.0.0.0", port=8003)