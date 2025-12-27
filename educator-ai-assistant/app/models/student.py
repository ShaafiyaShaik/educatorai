"""
Student models for the administrative assistant system
"""

from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text, ForeignKey, Float
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from datetime import datetime
from app.core.database import Base

class Section(Base):
    __tablename__ = "sections"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)  # e.g., "Section A", "Section B"
    educator_id = Column(Integer, ForeignKey("educators.id"), nullable=False)
    academic_year = Column(String(20), default="2024-2025")
    semester = Column(String(20), default="Fall")
    
    # Relationships
    educator = relationship("Educator", back_populates="sections")
    students = relationship("Student", back_populates="section")
    subjects = relationship("Subject", back_populates="section")
    section_reports = relationship("SentReport", back_populates="section")
    meetings = relationship("Meeting", back_populates="section")
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    def __repr__(self):
        return f"<Section(id={self.id}, name='{self.name}', educator_id={self.educator_id})>"

class Student(Base):
    __tablename__ = "students"
    
    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(String(50), unique=True, index=True, nullable=False)  # e.g., "STU001"
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    email = Column(String(255), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)  # For student authentication
    roll_number = Column(Integer, nullable=False)  # Roll number within section
    section_id = Column(Integer, ForeignKey("sections.id"), nullable=False)
    
    # Additional student info
    phone = Column(String(20))
    date_of_birth = Column(DateTime)
    address = Column(Text)
    guardian_email = Column(String(255))  # For sending notifications to parents
    is_active = Column(Boolean, default=True)
    
    # Relationships
    section = relationship("Section", back_populates="students")
    grades = relationship("Grade", back_populates="student")
    notifications = relationship("Notification", back_populates="student")
    received_reports = relationship("SentReport", back_populates="student")
    attendance_records = relationship("Attendance", back_populates="student")
    performance_summaries = relationship("StudentPerformanceSummary", back_populates="student")
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"
    
    def __repr__(self):
        return f"<Student(id={self.id}, student_id='{self.student_id}', name='{self.full_name}')>"

class Subject(Base):
    __tablename__ = "subjects"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)  # e.g., "Mathematics", "Physics", "Chemistry"
    code = Column(String(20), nullable=False)   # e.g., "MATH101", "PHYS201"
    section_id = Column(Integer, ForeignKey("sections.id"), nullable=False)
    credits = Column(Integer, default=3)
    passing_grade = Column(Float, default=60.0)  # Minimum grade to pass
    
    # Relationships
    section = relationship("Section", back_populates="subjects")
    grades = relationship("Grade", back_populates="subject")
    attendance_records = relationship("Attendance", back_populates="subject")
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    def __repr__(self):
        return f"<Subject(id={self.id}, code='{self.code}', name='{self.name}')>"

class Grade(Base):
    __tablename__ = "grades"
    
    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("students.id"), nullable=False)
    subject_id = Column(Integer, ForeignKey("subjects.id"), nullable=False)
    
    # Grade information
    marks_obtained = Column(Float, nullable=False)
    total_marks = Column(Float, default=100.0)
    percentage = Column(Float)  # Calculated field
    grade_letter = Column(String(5))  # A+, A, B+, B, C, D, F
    is_passed = Column(Boolean)  # Calculated based on passing_grade
    
    # Assessment details
    assessment_type = Column(String(50), default="Final Exam")  # Midterm, Final, Assignment, etc.
    assessment_date = Column(DateTime)
    remarks = Column(Text)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    student = relationship("Student", back_populates="grades")
    subject = relationship("Subject", back_populates="grades")
    
    def calculate_percentage(self):
        """Calculate percentage from marks"""
        if self.total_marks > 0:
            self.percentage = (self.marks_obtained / self.total_marks) * 100
        return self.percentage
    
    def calculate_grade_letter(self):
        """Calculate letter grade from percentage"""
        if self.percentage is None:
            self.calculate_percentage()
        
        if self.percentage >= 95:
            self.grade_letter = "A+"
        elif self.percentage >= 90:
            self.grade_letter = "A"
        elif self.percentage >= 85:
            self.grade_letter = "B+"
        elif self.percentage >= 80:
            self.grade_letter = "B"
        elif self.percentage >= 75:
            self.grade_letter = "C+"
        elif self.percentage >= 70:
            self.grade_letter = "C"
        elif self.percentage >= 65:
            self.grade_letter = "D+"
        elif self.percentage >= 60:
            self.grade_letter = "D"
        else:
            self.grade_letter = "F"
        
        return self.grade_letter
    
    def __repr__(self):
        return f"<Grade(student_id={self.student_id}, subject_id={self.subject_id}, marks={self.marks_obtained}/{self.total_marks})>"