"""
Enhanced performance tracking models
"""

from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text, ForeignKey, Float, Date, Index, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base

class Exam(Base):
    __tablename__ = "exams"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), nullable=False)  # e.g., "Midterm Exam", "Final Exam"
    code = Column(String(50), nullable=False)   # e.g., "MT2025", "FE2025"
    exam_date = Column(Date, nullable=False)
    term = Column(String(50), nullable=False)   # e.g., "Fall 2025", "Spring 2025"
    academic_year = Column(String(20), nullable=False)  # e.g., "2024-2025"
    
    # Exam configuration
    total_marks = Column(Float, default=100.0)
    passing_marks = Column(Float, default=60.0)
    duration_minutes = Column(Integer, default=180)  # Exam duration
    
    # Relationships
    grades = relationship("Grade", back_populates="exam")
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    def __repr__(self):
        return f"<Exam(id={self.id}, name='{self.name}', date='{self.exam_date}')>"

class Attendance(Base):
    __tablename__ = "attendance"
    
    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("students.id"), nullable=False)
    date = Column(Date, nullable=False)
    present = Column(Boolean, default=False)
    
    # Additional attendance details
    subject_id = Column(Integer, ForeignKey("subjects.id"))  # Optional: subject-specific attendance
    period = Column(Integer)  # Period number (1, 2, 3, etc.)
    remarks = Column(Text)    # Late, Excused, etc.
    
    # Relationships
    student = relationship("Student", back_populates="attendance_records")
    subject = relationship("Subject", back_populates="attendance_records")
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Indexes for performance
    __table_args__ = (
        Index('idx_student_date', 'student_id', 'date'),
        Index('idx_subject_date', 'subject_id', 'date'),
    )
    
    def __repr__(self):
        return f"<Attendance(student_id={self.student_id}, date='{self.date}', present={self.present})>"

class PerformanceCache(Base):
    __tablename__ = "performance_cache"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Scope identifiers
    section_id = Column(Integer, ForeignKey("sections.id"))
    subject_id = Column(Integer, ForeignKey("subjects.id"))
    exam_id = Column(Integer, ForeignKey("exams.id"))
    term = Column(String(50))
    academic_year = Column(String(20))
    
    # Cached metrics
    total_students = Column(Integer, default=0)
    average_score = Column(Float)
    median_score = Column(Float)
    highest_score = Column(Float)
    lowest_score = Column(Float)
    standard_deviation = Column(Float)
    
    # Pass/Fail statistics
    pass_count = Column(Integer, default=0)
    fail_count = Column(Integer, default=0)
    pass_percentage = Column(Float)
    
    # Attendance statistics (if applicable)
    average_attendance = Column(Float)
    
    # Additional metadata
    metadata_json = Column(JSON)  # For storing additional calculated metrics
    
    # Relationships
    section = relationship("Section")
    subject = relationship("Subject")
    exam = relationship("Exam")
    
    # Timestamps
    calculated_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Indexes for performance
    __table_args__ = (
        Index('idx_section_subject_term', 'section_id', 'subject_id', 'term'),
        Index('idx_section_exam', 'section_id', 'exam_id'),
    )
    
    def __repr__(self):
        return f"<PerformanceCache(section_id={self.section_id}, subject_id={self.subject_id}, avg={self.average_score})>"

class StudentPerformanceSummary(Base):
    __tablename__ = "student_performance_summary"
    
    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("students.id"), nullable=False)
    
    # Academic period
    term = Column(String(50), nullable=False)
    academic_year = Column(String(20), nullable=False)
    
    # Overall performance metrics
    overall_average = Column(Float)
    overall_grade = Column(String(5))  # A+, A, B+, etc.
    total_credits = Column(Integer)
    earned_credits = Column(Integer)
    
    # Subject-wise averages (JSON for flexibility)
    subject_averages = Column(JSON)  # {"Mathematics": 85.5, "Science": 92.0}
    
    # Attendance summary
    total_days = Column(Integer, default=0)
    present_days = Column(Integer, default=0)
    attendance_percentage = Column(Float)
    
    # Status flags
    is_promoted = Column(Boolean, default=False)
    needs_attention = Column(Boolean, default=False)  # Low performance flag
    
    # Relationships
    student = relationship("Student", back_populates="performance_summaries")
    
    # Timestamps
    calculated_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Unique constraint
    __table_args__ = (
        Index('idx_student_term_year', 'student_id', 'term', 'academic_year', unique=True),
    )
    
    def __repr__(self):
        return f"<StudentPerformanceSummary(student_id={self.student_id}, term='{self.term}', avg={self.overall_average})>"