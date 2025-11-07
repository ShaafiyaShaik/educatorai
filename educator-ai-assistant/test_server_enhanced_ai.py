#!/usr/bin/env python3
"""
Simple server test for enhanced AI assistant
"""

import sys
sys.path.append('.')

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from app.core.config import settings
from app.core.database import init_db
from app.api.enhanced_ai_assistant import router as enhanced_ai_router

# Simple FastAPI app for testing
app = FastAPI(title="Enhanced AI Test Server")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include our enhanced AI router
app.include_router(enhanced_ai_router, prefix="/api/v1/gemini-assistant", tags=["enhanced-ai"])

@app.get("/")
async def root():
    return {"message": "Enhanced AI Test Server", "status": "running"}

@app.get("/health")
async def health():
    return {"status": "healthy"}

if __name__ == "__main__":
    print("🚀 Starting Enhanced AI Test Server...")
    print("📡 Server will run on http://localhost:8003")
    print("🤖 Enhanced AI available at /api/v1/gemini-assistant/enhanced-chat")
    
    # Initialize database
    init_db()
    
    # Run server
    uvicorn.run(app, host="0.0.0.0", port=8003)