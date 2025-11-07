import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import StudentLogin from './StudentLogin';
import StudentDashboard from './StudentDashboard';

const StudentApp = () => {
  const [isLoggedIn, setIsLoggedIn] = useState(false);
  const [studentData, setStudentData] = useState(null);
  const navigate = useNavigate();

  useEffect(() => {
    // Check if student is already logged in
    const token = localStorage.getItem('studentToken');
    const storedStudentData = localStorage.getItem('studentData');
    
    if (token && storedStudentData) {
      try {
        const parsedStudentData = JSON.parse(storedStudentData);
        setStudentData(parsedStudentData);
        setIsLoggedIn(true);
      } catch (error) {
        console.error('Error parsing stored student data:', error);
        // Clear invalid data
        localStorage.removeItem('studentToken');
        localStorage.removeItem('studentData');
      }
    }
  }, []);

  const handleLogin = (student) => {
    setStudentData(student);
    setIsLoggedIn(true);
  };

  const handleLogout = () => {
    // Clear student data and token
    localStorage.removeItem('studentToken');
    localStorage.removeItem('studentData');
    
    setStudentData(null);
    setIsLoggedIn(false);
    
    // Redirect to login page
    navigate('/login');
  };

  if (isLoggedIn && studentData) {
    return <StudentDashboard studentData={studentData} onLogout={handleLogout} />;
  }

  return <StudentLogin onLogin={handleLogin} />;
};

export default StudentApp;