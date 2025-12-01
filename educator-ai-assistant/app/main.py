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
from os import getenv
from app.api import (
    educators, dashboard, communications,
    users, students, students_auth, student_dashboard,
    bulk_communication, performance_views, student_messaging,
    scheduling, records, compliance, meeting_requests,
    meeting_scheduler
)
from app.api import admin as admin_api

# Initialize FastAPI app
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    init_db()
    # Optionally seed demo users if environment explicitly requests it
    if getenv("SEED_DEMO_USERS", "false").lower() in ("1", "true", "yes"):
        try:
            from app.scripts.seed_demo_users import seed_demo_educators
            seed_demo_educators()
        except Exception:
            # Avoid crashing startup if seeding fails; log can be checked in deployment
            import logging
            logging.exception("Failed to seed demo users")
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
        "https://educatorai-frontend.onrender.com",  # Production frontend
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
app.include_router(__import__("app.api.actions", fromlist=["router"]).router, prefix="/api/v1/actions", tags=["actions"])
app.include_router(admin_api.router, prefix="/api/v1/admin", tags=["admin"])
# Debug admin endpoints (temporary) to report runtime DB path and quick checks
from app.api import debug_db
app.include_router(debug_db.router, prefix="/api/v1/admin", tags=["admin-debug"])
# Chatbot/assistant modules removed by user request

# Register the new isolated simple chatbot router (keeps all logic separate
# from any previous assistant implementations).
from app.api import simple_chatbot
app.include_router(simple_chatbot.router, prefix="/api/v1/simple-chatbot", tags=["simple-chatbot"])
# Action engine: internal routes the chatbot can call to perform actions
from app.api import action_engine
app.include_router(action_engine.router, prefix="/api/v1/action-engine", tags=["action-engine"])

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