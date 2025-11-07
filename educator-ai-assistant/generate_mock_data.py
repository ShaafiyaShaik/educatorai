"""
Mock Data Generator for Teacher Portal
Creates realistic student data for testing the teacher portal functionality.
"""

import json
import random
from datetime import datetime
from typing import Dict, List, Any

# List of common first names
FIRST_NAMES = [
    "Aarav", "Vivaan", "Aditya", "Vihaan", "Arjun", "Sai", "Reyansh", "Ayaan", "Krishna", "Ishaan",
    "Shaurya", "Atharv", "Advait", "Aadhya", "Ananya", "Diya", "Aarohi", "Anika", "Navya", "Sara",
    "Myra", "Priya", "Kavya", "Riya", "Avni", "Kiara", "Tara", "Saanvi", "Alisha", "Anaya",
    "Raj", "Dev", "Ved", "Om", "Kian", "Arnav", "Kabir", "Rudra", "Aryan", "Yash",
    "Sia", "Ira", "Eva", "Zara", "Nisha", "Aditi", "Shreya", "Pooja", "Simran", "Ritu",
    "Amit", "Rohit", "Suresh", "Rakesh", "Mahesh", "Dinesh", "Ramesh", "Umesh", "Yogesh", "Hitesh",
    "Neha", "Sonia", "Meera", "Geeta", "Seeta", "Rita", "Lata", "Mala", "Kala", "Usha",
    "Arjun", "Karan", "Varun", "Tarun", "Arun", "Shaun", "Rohan", "Sohan", "Mohan", "Gopal",
    "Maya", "Sita", "Gita", "Rita", "Nita", "Mita", "Lila", "Tina", "Nina", "Dina",
    "Rahul", "Sahil", "Nikhil", "Akhil", "Sunil", "Anil", "Kapil", "Nakul", "Vipul", "Nipun"
]

# List of common last names
LAST_NAMES = [
    "Sharma", "Verma", "Gupta", "Agarwal", "Tiwari", "Mishra", "Joshi", "Shukla", "Pandey", "Yadav",
    "Singh", "Kumar", "Patel", "Shah", "Modi", "Jain", "Soni", "Goel", "Bansal", "Jindal",
    "Chopra", "Malhotra", "Kapoor", "Arora", "Bhatia", "Sethi", "Khanna", "Tandon", "Garg", "Sood",
    "Reddy", "Rao", "Nair", "Pillai", "Menon", "Iyer", "Krishnan", "Naidu", "Chandra", "Varma",
    "Das", "Sen", "Roy", "Ghosh", "Mukherjee", "Chatterjee", "Banerjee", "Bose", "Dutta", "Saha",
    "Khan", "Ali", "Ahmed", "Hussain", "Rahman", "Ansari", "Qureshi", "Siddiqui", "Shaikh", "Malik",
    "D'Souza", "Fernandes", "Pereira", "Rodrigues", "Gomes", "Lobo", "Dias", "Xavier", "Costa", "Silva",
    "Kaur", "Kaul", "Mehta", "Thakur", "Bhatt", "Dixit", "Saxena", "Srivastava", "Dwivedi", "Tripathi"
]

# Subject configuration
SUBJECTS = ["Math", "Science", "English"]
PASSING_AVERAGE = 40

def generate_random_name() -> str:
    """Generate a random full name"""
    first_name = random.choice(FIRST_NAMES)
    last_name = random.choice(LAST_NAMES)
    return f"{first_name} {last_name}"

def generate_student_email(name: str, section: str, roll_no: str) -> str:
    """Generate a unique email for the student"""
    # Clean name for email
    clean_name = name.lower().replace(" ", "")
    section_code = section.replace("Section ", "").lower()
    return f"{clean_name}.{section_code}.{roll_no.lower()}@student.edu"

def generate_marks() -> Dict[str, int]:
    """Generate random marks for all subjects"""
    marks = {}
    for subject in SUBJECTS:
        # Generate realistic marks with some distribution
        # 70% chance of decent marks (40-90), 20% chance of high marks (80-100), 10% chance of low marks (0-40)
        rand = random.random()
        if rand < 0.1:  # Low marks
            marks[subject] = random.randint(0, 40)
        elif rand < 0.8:  # Decent marks
            marks[subject] = random.randint(40, 90)
        else:  # High marks
            marks[subject] = random.randint(80, 100)
    return marks

def calculate_average(marks: Dict[str, int]) -> float:
    """Calculate average marks"""
    total = sum(marks.values())
    return round(total / len(marks), 2)

def determine_status(average: float) -> str:
    """Determine pass/fail status based on average"""
    return "Pass" if average >= PASSING_AVERAGE else "Fail"

def generate_student_data(section_name: str, student_count: int = 50) -> List[Dict[str, Any]]:
    """Generate student data for a section"""
    students = []
    section_code = section_name.split()[-1]  # Get 'A', 'B', 'C' from 'Section A'
    
    for i in range(1, student_count + 1):
        # Generate roll number
        roll_no = f"{section_code}{i:03d}"  # A001, A002, etc.
        
        # Generate student details
        name = generate_random_name()
        email = generate_student_email(name, section_name, roll_no)
        marks = generate_marks()
        average = calculate_average(marks)
        status = determine_status(average)
        
        student = {
            "roll_no": roll_no,
            "name": name,
            "email": email,
            "marks": marks,
            "average": average,
            "status": status
        }
        students.append(student)
    
    return students

def calculate_section_statistics(students: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Calculate statistics for a section"""
    total_students = len(students)
    passed_students = len([s for s in students if s["status"] == "Pass"])
    failed_students = total_students - passed_students
    
    # Calculate subject-wise statistics
    subject_stats = {}
    for subject in SUBJECTS:
        subject_marks = [s["marks"][subject] for s in students]
        subject_passed = len([mark for mark in subject_marks if mark >= PASSING_AVERAGE])
        subject_failed = total_students - subject_passed
        subject_average = round(sum(subject_marks) / len(subject_marks), 2)
        
        subject_stats[subject] = {
            "average": subject_average,
            "passed": subject_passed,
            "failed": subject_failed,
            "highest": max(subject_marks),
            "lowest": min(subject_marks)
        }
    
    # Calculate overall average
    all_averages = [s["average"] for s in students]
    overall_average = round(sum(all_averages) / len(all_averages), 2)
    
    return {
        "total_students": total_students,
        "passed_students": passed_students,
        "failed_students": failed_students,
        "pass_percentage": round((passed_students / total_students) * 100, 2),
        "overall_average": overall_average,
        "subject_statistics": subject_stats
    }

def generate_teacher_data(teacher_email: str) -> Dict[str, Any]:
    """Generate complete data for a teacher"""
    sections_data = {}
    section_names = ["Section A", "Section B", "Section C"]
    
    for section_name in section_names:
        students = generate_student_data(section_name)
        statistics = calculate_section_statistics(students)
        
        sections_data[section_name] = {
            "students": students,
            "statistics": statistics
        }
    
    # Calculate teacher-level statistics
    total_students = sum(data["statistics"]["total_students"] for data in sections_data.values())
    total_passed = sum(data["statistics"]["passed_students"] for data in sections_data.values())
    total_failed = total_students - total_passed
    
    # Calculate overall teacher average
    all_averages = []
    for section_data in sections_data.values():
        all_averages.extend([s["average"] for s in section_data["students"]])
    
    teacher_overall_average = round(sum(all_averages) / len(all_averages), 2)
    
    teacher_stats = {
        "total_students": total_students,
        "total_passed": total_passed,
        "total_failed": total_failed,
        "overall_pass_percentage": round((total_passed / total_students) * 100, 2),
        "overall_average": teacher_overall_average,
        "total_sections": len(section_names)
    }
    
    return {
        "teacher_email": teacher_email,
        "sections": sections_data,
        "teacher_statistics": teacher_stats,
        "generated_at": datetime.now().isoformat()
    }

def generate_mock_data_for_teachers(teacher_emails: List[str]) -> Dict[str, Any]:
    """Generate mock data for multiple teachers"""
    mock_data = {}
    
    for teacher_email in teacher_emails:
        print(f"Generating data for {teacher_email}...")
        mock_data[teacher_email] = generate_teacher_data(teacher_email)
    
    return mock_data

def save_mock_data(data: Dict[str, Any], filename: str = "mock_student_data.json"):
    """Save mock data to JSON file"""
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    print(f"Mock data saved to {filename}")

def print_summary(data: Dict[str, Any]):
    """Print a summary of generated data"""
    print("\n" + "="*60)
    print("MOCK DATA GENERATION SUMMARY")
    print("="*60)
    
    for teacher_email, teacher_data in data.items():
        print(f"\nTeacher: {teacher_email}")
        print("-" * 40)
        stats = teacher_data["teacher_statistics"]
        print(f"Total Students: {stats['total_students']}")
        print(f"Total Sections: {stats['total_sections']}")
        print(f"Passed: {stats['total_passed']} ({stats['overall_pass_percentage']}%)")
        print(f"Failed: {stats['total_failed']}")
        print(f"Overall Average: {stats['overall_average']}")
        
        print("\nSection Breakdown:")
        for section_name, section_data in teacher_data["sections"].items():
            section_stats = section_data["statistics"]
            print(f"  {section_name}: {section_stats['passed_students']}/{section_stats['total_students']} passed "
                  f"({section_stats['pass_percentage']}%) - Avg: {section_stats['overall_average']}")

if __name__ == "__main__":
    # Example teacher emails (you can modify this list)
    teachers = [
        "teacher1@example.com",
        "teacher2@example.com", 
        "shaaf@gmail.com",  # Your existing teacher account
        "demo.teacher@edu.com"
    ]
    
    print("Starting mock data generation...")
    print(f"Generating data for {len(teachers)} teachers")
    print(f"Each teacher will have 3 sections with 50 students each")
    print(f"Total students to generate: {len(teachers) * 3 * 50}")
    
    # Generate the mock data
    mock_data = generate_mock_data_for_teachers(teachers)
    
    # Save to file
    save_mock_data(mock_data)
    
    # Print summary
    print_summary(mock_data)
    
    print(f"\nMock data generation completed!")
    print(f"Data saved to 'mock_student_data.json'")
    print(f"You can now use this data to populate your database or test your application.")