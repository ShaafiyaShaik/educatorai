import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';

const TeacherDashboard = () => {
  const [dashboardData, setDashboardData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const navigate = useNavigate();

  useEffect(() => {
    fetchDashboardData();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const fetchDashboardData = async () => {
    try {
      const token = localStorage.getItem('token');
      if (!token) {
        navigate('/login');
        return;
      }

      const response = await axios.get('http://localhost:8001/api/v1/dashboard/dashboard', {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });

      setDashboardData(response.data);
      setLoading(false);
    } catch (error) {
      console.error('Error fetching dashboard data:', error);
      setError('Failed to load dashboard data');
      setLoading(false);
      
      if (error.response?.status === 401) {
        localStorage.removeItem('token');
        navigate('/login');
      }
    }
  };

  const handleSectionClick = (sectionId, sectionName) => {
    // Navigate to section detail page (to be implemented)
    navigate(`/section/${sectionId}`, { state: { sectionName } });
  };

  const handleLogout = () => {
    localStorage.removeItem('token');
    navigate('/login');
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
          <p className="mt-4 text-gray-600">Loading dashboard...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="text-red-600 text-xl mb-4">❌ {error}</div>
          <button 
            onClick={() => window.location.reload()} 
            className="bg-blue-600 text-white px-4 py-2 rounded hover:bg-blue-700"
          >
            Retry
          </button>
        </div>
      </div>
    );
  }

  const { teacher_name, teacher_email, overall_stats, sections } = dashboardData;

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-white shadow-sm border-b">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center py-4">
            <div>
              <h1 className="text-2xl font-bold text-gray-900">Teacher Dashboard</h1>
              <p className="text-gray-600">Welcome back, {teacher_name}</p>
            </div>
            <div className="flex items-center space-x-4">
              <span className="text-sm text-gray-500">{teacher_email}</span>
              <button
                onClick={handleLogout}
                className="bg-red-600 text-white px-4 py-2 rounded hover:bg-red-700 transition-colors"
              >
                Logout
              </button>
            </div>
          </div>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Overall Statistics */}
        <div className="bg-white rounded-lg shadow-md p-6 mb-8">
          <h2 className="text-xl font-semibold text-gray-800 mb-6 flex items-center">
            📊 Overall Statistics
          </h2>
          
          <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
            <div className="bg-blue-50 rounded-lg p-4 text-center">
              <div className="text-3xl font-bold text-blue-600">{overall_stats.total_students}</div>
              <div className="text-sm text-gray-600 mt-1">Total Students</div>
            </div>
            
            <div className="bg-green-50 rounded-lg p-4 text-center">
              <div className="text-3xl font-bold text-green-600">{overall_stats.total_passed}</div>
              <div className="text-sm text-gray-600 mt-1">Passed</div>
            </div>
            
            <div className="bg-red-50 rounded-lg p-4 text-center">
              <div className="text-3xl font-bold text-red-600">{overall_stats.total_failed}</div>
              <div className="text-sm text-gray-600 mt-1">Failed</div>
            </div>
            
            <div className="bg-purple-50 rounded-lg p-4 text-center">
              <div className="text-3xl font-bold text-purple-600">{overall_stats.overall_pass_rate}%</div>
              <div className="text-sm text-gray-600 mt-1">Pass Rate</div>
            </div>
          </div>

          <div className="mt-4 text-center">
            <div className="text-lg text-gray-700">
              Overall Average: <span className="font-semibold text-gray-900">{overall_stats.overall_average}</span>
            </div>
          </div>
        </div>

        {/* Sections */}
        <div className="bg-white rounded-lg shadow-md p-6">
          <h2 className="text-xl font-semibold text-gray-800 mb-6 flex items-center">
            📚 Your Sections
          </h2>
          
          <div className="grid gap-4">
            {sections.map((section) => (
              <div 
                key={section.section_id}
                onClick={() => handleSectionClick(section.section_id, section.section_name)}
                className="border rounded-lg p-4 hover:bg-gray-50 cursor-pointer transition-colors border-gray-200 hover:border-blue-300"
              >
                <div className="flex justify-between items-start">
                  <div className="flex-1">
                    <div className="flex items-center justify-between mb-3">
                      <h3 className="text-lg font-medium text-gray-900">{section.section_name}</h3>
                      <span className="text-sm text-gray-500">Click to view details →</span>
                    </div>
                    
                    <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
                      <div>
                        <span className="text-gray-600">Total Students:</span>
                        <div className="font-semibold text-blue-600">{section.total_students}</div>
                      </div>
                      
                      <div>
                        <span className="text-gray-600">Passed:</span>
                        <div className="font-semibold text-green-600">{section.passed_students}</div>
                      </div>
                      
                      <div>
                        <span className="text-gray-600">Failed:</span>
                        <div className="font-semibold text-red-600">{section.failed_students}</div>
                      </div>
                      
                      <div>
                        <span className="text-gray-600">Average:</span>
                        <div className="font-semibold text-purple-600">{section.section_average}</div>
                      </div>
                    </div>

                    {/* Subject Averages */}
                    <div className="mt-3 pt-3 border-t border-gray-100">
                      <div className="text-xs text-gray-500 mb-1">Subject Averages:</div>
                      <div className="flex space-x-4 text-sm">
                        {Object.entries(section.subjects_average).map(([subject, average]) => (
                          <span key={subject} className="text-gray-700">
                            {subject}: <span className="font-medium">{average}</span>
                          </span>
                        ))}
                      </div>
                    </div>

                    {/* Pass Rate Bar */}
                    <div className="mt-3">
                      <div className="flex justify-between text-xs text-gray-600 mb-1">
                        <span>Pass Rate</span>
                        <span>{section.pass_rate}%</span>
                      </div>
                      <div className="w-full bg-gray-200 rounded-full h-2">
                        <div 
                          className="bg-green-500 h-2 rounded-full transition-all duration-300"
                          style={{ width: `${section.pass_rate}%` }}
                        ></div>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            ))}
          </div>

          {sections.length === 0 && (
            <div className="text-center py-8 text-gray-500">
              <p>No sections found. Please contact your administrator.</p>
            </div>
          )}
        </div>

        {/* Quick Actions */}
        <div className="mt-8 bg-white rounded-lg shadow-md p-6">
          <h2 className="text-xl font-semibold text-gray-800 mb-4">Quick Actions</h2>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <button className="bg-blue-600 text-white p-4 rounded-lg hover:bg-blue-700 transition-colors">
              📧 Send Bulk Communication
            </button>
            <button className="bg-green-600 text-white p-4 rounded-lg hover:bg-green-700 transition-colors">
              📊 Generate Reports
            </button>
            <button className="bg-purple-600 text-white p-4 rounded-lg hover:bg-purple-700 transition-colors">
              🤖 AI Assistant
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default TeacherDashboard;