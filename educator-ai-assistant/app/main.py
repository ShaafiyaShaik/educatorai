"""
Educator AI Administrative Assistant
Main FastAPI application for automating routine communications and administrative tasks.
"""
import sys
from pathlib import Path

# Ensure project root is on sys.path so `import app` works when uvicorn spawns
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import uvicorn
from app.core.config import settings
from app.core.database import init_db
from app.api import (
    educators, dashboard, communications,
    users, students, students_auth, student_dashboard,
    bulk_communication, performance_views, student_messaging,
    scheduling, records, compliance, meeting_requests,
    meeting_scheduler
)

# Initialize FastAPI app
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    init_db()
    yield
    # Shutdown
    pass

app = FastAPI(
    title="Educator AI Administrative Assistant",
    description="An AI-powered administrative assistant to reduce non-teaching tasks for educators",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware - Allow both local development and production
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",  # Local development
        "http://localhost:8003",  # Local backend
        "https://educatorai-frontend.onrender.com",  # Production frontend (update with your actual URL)
        "*"  # Temporary - remove after testing
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routers
app.include_router(educators.router, prefix="/api/v1/educators", tags=["educators"])
app.include_router(dashboard.router, prefix="/api/v1/dashboard", tags=["dashboard"])
app.include_router(communications.router, prefix="/api/v1/communications", tags=["communications"])
app.include_router(users.router, prefix="/api/v1/users", tags=["users"])
app.include_router(students.router, prefix="/api/v1/students", tags=["students"])
app.include_router(students_auth.router, prefix="/api/v1/student-auth", tags=["student-auth"])
app.include_router(student_dashboard.router, prefix="/api/v1/student-dashboard", tags=["student-dashboard"])
app.include_router(bulk_communication.router, prefix="/api/v1/bulk-communication", tags=["bulk-communication"])
app.include_router(performance_views.router, prefix="/api/v1/performance", tags=["performance-views"])
app.include_router(student_messaging.router, prefix="/api/v1/messages", tags=["student-messaging"])
app.include_router(scheduling.router, prefix="/api/v1/scheduling", tags=["scheduling"])
app.include_router(records.router, prefix="/api/v1/records", tags=["records"])
app.include_router(compliance.router, prefix="/api/v1/compliance", tags=["compliance"])
app.include_router(meeting_requests.router, prefix="/api/v1/meeting-requests", tags=["meeting-requests"])
app.include_router(meeting_scheduler.router, prefix="/api/v1/meetings", tags=["meeting-scheduler"])
# Chatbot/assistant modules removed by user request

# Register the new isolated simple chatbot router (keeps all logic separate
# from any previous assistant implementations).
from app.api import simple_chatbot
app.include_router(simple_chatbot.router, prefix="/api/v1/simple-chatbot", tags=["simple-chatbot"])

@app.get("/")
async def root():
    """Root endpoint with API information"""
    return {
        "message": "Educator AI Administrative Assistant API",
        "version": "1.0.0",
        "status": "active",
        "features": [
            "Automated scheduling",
            "Record keeping",
            "Compliance reporting",
            "Communication automation"
        ]
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "timestamp": "2025-09-20"}

if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG
    )