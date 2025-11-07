import React, { useState, useEffect } from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate, useParams } from 'react-router-dom';
import { Toaster } from 'react-hot-toast';
import Login from './components/Login';
import Register from './components/Register';
import ComprehensiveDashboard from './components/ComprehensiveDashboard';
import StudentApp from './components/StudentApp';
import PortalSelection from './components/PortalSelection';
import './App.css';

// Component to handle section redirects
function SectionRedirect() {
  const { sectionId } = useParams();
  
  // Store the section ID in localStorage so the dashboard can use it
  useEffect(() => {
    if (sectionId) {
      localStorage.setItem('selectedSectionId', sectionId);
    }
  }, [sectionId]);
  
  return <Navigate to="/dashboard" />;
}

function App() {
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // Check if user is already logged in
    const token = localStorage.getItem('token');
    console.log('App.js checking authentication, token:', token ? 'exists' : 'none');
    if (token) {
      setIsAuthenticated(true);
      console.log('Setting authenticated to true');
    }
    setLoading(false);
  }, []);

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center gradient-bg">
        <div className="animate-spin rounded-full h-32 w-32 border-b-2 border-white"></div>
      </div>
    );
  }

  return (
    <Router 
      future={{
        v7_startTransition: true,
        v7_relativeSplatPath: true
      }}
    >
      <div className="App">
        <Toaster position="top-right" />
        <Routes>
          <Route 
            path="/portals" 
            element={<PortalSelection />} 
          />
          <Route 
            path="/login" 
            element={<Login setIsAuthenticated={setIsAuthenticated} />} 
          />
          <Route 
            path="/register" 
            element={
              !isAuthenticated ? 
                <Register setIsAuthenticated={setIsAuthenticated} /> : 
                <Navigate to="/dashboard" />
            } 
          />
          <Route 
            path="/dashboard" 
            element={
              isAuthenticated ? 
                <ComprehensiveDashboard setIsAuthenticated={setIsAuthenticated} /> : 
                <Navigate to="/login" />
            } 
          />
          <Route 
            path="/student" 
            element={<StudentApp />} 
          />
          <Route 
            path="/section/:sectionId" 
            element={
              isAuthenticated ? 
                <SectionRedirect /> : 
                <Navigate to="/login" />
            } 
          />
          <Route 
            path="/" 
            element={<PortalSelection />} 
          />
        </Routes>
      </div>
    </Router>
  );
}

export default App;