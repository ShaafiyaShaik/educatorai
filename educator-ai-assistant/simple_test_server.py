#!/usr/bin/env python3

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

print("🚀 Starting simple test server...")

try:
    from fastapi import FastAPI, HTTPException
    from fastapi.middleware.cors import CORSMiddleware
    from app.core.database import SessionLocal
    from app.models.educator import Educator
    from app.models.student import Student
    from app.core.auth import verify_password
    import uvicorn
    
    app = FastAPI(title="Quick Test Server")
    
    # Add CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:3000"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    @app.get("/test")
    def test_endpoint():
        return {"message": "Server is working!"}
    
    @app.post("/test-educator-login")
    def test_educator_login(email: str, password: str):
        try:
            db = SessionLocal()
            educator = db.query(Educator).filter(Educator.email == email).first()
            
            if not educator:
                return {"success": False, "message": "Educator not found"}
            
            password_valid = verify_password(password, educator.hashed_password)
            db.close()
            
            return {
                "success": password_valid,
                "message": "Login successful" if password_valid else "Invalid password",
                "educator": educator.full_name if password_valid else None
            }
        except Exception as e:
            return {"success": False, "message": f"Error: {str(e)}"}
    
    @app.post("/test-student-login")
    def test_student_login(email: str, password: str):
        try:
            db = SessionLocal()
            student = db.query(Student).filter(Student.email == email).first()
            
            if not student:
                return {"success": False, "message": "Student not found"}
            
            password_valid = verify_password(password, student.password_hash)
            db.close()
            
            return {
                "success": password_valid,
                "message": "Login successful" if password_valid else "Invalid password",
                "student": student.full_name if password_valid else None
            }
        except Exception as e:
            return {"success": False, "message": f"Error: {str(e)}"}
    
    if __name__ == "__main__":
        print("✅ Simple test server starting on port 8004...")
        uvicorn.run(app, host="0.0.0.0", port=8004)
        
except Exception as e:
    print(f"❌ Failed to start server: {str(e)}")
    import traceback
    traceback.print_exc()