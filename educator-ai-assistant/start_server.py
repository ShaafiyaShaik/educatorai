#!/usr/bin/env python3
"""
Professional FastAPI server launcher for Educator AI Assistant
"""
import os
import sys
import subprocess
import time

def check_dependencies():
    """Check if required dependencies are installed"""
    required_packages = [
        'fastapi', 'uvicorn', 'sqlalchemy', 'pydantic', 'bcrypt',
        'reportlab', 'pandas', 'openpyxl'
    ]
    
    missing = []
    for package in required_packages:
        try:
            __import__(package.replace('-', '_'))
        except ImportError:
            missing.append(package)
    
    if missing:
        print(f"Missing dependencies: {', '.join(missing)}")
        print("Installing missing packages...")
        for package in missing:
            subprocess.check_call([sys.executable, '-m', 'pip', 'install', package])
    
    return True

def start_server():
    """Start the FastAPI server"""
    print("🚀 Starting Educator AI Assistant Server...")
    
    # Add current directory to Python path
    current_dir = os.path.dirname(os.path.abspath(__file__))
    if current_dir not in sys.path:
        sys.path.insert(0, current_dir)
    
    # Check dependencies
    check_dependencies()
    
    try:
        from app.main import app
        import uvicorn
        
        print("✅ Application loaded successfully")
        print("🔧 Server Configuration:")
        print("   • Host: localhost")
        print("   • Port: 8003") 
        print("   • Environment: Development")
        print("   • Auto-reload: Enabled")
        print("   • CORS: Enabled for all origins")
        print("")
        print("📊 Database Status:")
        
        # Quick database check
        from app.core.database import get_db
        from app.models.student import Student, Section, Grade
        from app.models.educator import Educator
        
        db = next(get_db())
        educator_count = db.query(Educator).count()
        student_count = db.query(Student).count()
        section_count = db.query(Section).count()
        grade_count = db.query(Grade).count()
        
        print(f"   • Educators: {educator_count}")
        print(f"   • Students: {student_count}")
        print(f"   • Sections: {section_count}")
        print(f"   • Grades: {grade_count}")
        
        # Check shaaf's data
        shaaf = db.query(Educator).filter(Educator.email == "shaaf@gmail.com").first()
        if shaaf:
            shaaf_sections = db.query(Section).filter(Section.educator_id == shaaf.id).count()
            print(f"   • Shaaf's Sections: {shaaf_sections}")
        
        db.close()
        
        print("")
        print("🌐 API Endpoints Available:")
        print("   • Performance Analytics: /api/v1/performance/")
        print("   • Student Management: /api/v1/students/")
        print("   • Authentication: /api/v1/educators/login")
        print("")
        print("📱 Frontend URLs:")
        print("   • React App: http://localhost:3000")
        print("   • API Docs: http://localhost:8003/docs")
        print("   • API Redoc: http://localhost:8003/redoc")
        print("")
        print("🔑 Login Credentials:")
        print("   • Email: shaaf@gmail.com")
        print("   • Password: password123")
        print("")
        print("=" * 60)
        
        # Start the server
        uvicorn.run(
            "app.main:app", 
            host="localhost", 
            port=8003, 
            log_level="info",
            reload=True,
            reload_dirs=[current_dir]
        )
        
    except ImportError as e:
        print(f"❌ Import Error: {e}")
        print("💡 Make sure you're in the correct directory and dependencies are installed")
        return False
    except Exception as e:
        print(f"❌ Server Error: {e}")
        return False

if __name__ == "__main__":
    success = start_server()
    if not success:
        print("Server failed to start. Check the error messages above.")
        sys.exit(1)