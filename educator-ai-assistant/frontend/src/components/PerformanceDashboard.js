import React, { useState, useEffect, useRef } from 'react';
import axios from 'axios';

const PerformanceDashboard = () => {
  const [activeTab, setActiveTab] = useState('overview');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  
  // WebSocket for real-time updates
  const [isConnected, setIsConnected] = useState(false);
  const [lastUpdate, setLastUpdate] = useState(null);
  const wsRef = useRef(null);
  
  // Data states
  const [teacherSummary, setTeacherSummary] = useState(null);
  const [sectionData, setSectionData] = useState([]);
  const [selectedSection, setSelectedSection] = useState(null);
  const [sectionPerformance, setSectionPerformance] = useState(null);
  const [subjectAnalytics, setSubjectAnalytics] = useState(null);
  const [selectedStudent, setSelectedStudent] = useState(null);
  const [studentDetail, setStudentDetail] = useState(null);
  
  // Filter states
  const [filters, setFilters] = useState({
    term: '',
    subject: '',
    passFailFilter: 'all',
    attendanceThreshold: '',
    sortBy: 'roll_number',
    sortOrder: 'asc'
  });

  useEffect(() => {
    loadTeacherSummary();
    
    // WebSocket connection for real-time updates
    const connectWebSocket = () => {
    try {
      const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
      const wsUrl = `${protocol}//${window.location.host}/api/v1/performance/ws/performance/1`; // Educator ID 1 for testing
      
      wsRef.current = new WebSocket(wsUrl);
      
      wsRef.current.onopen = () => {
        console.log('WebSocket connected for real-time performance updates');
        setIsConnected(true);
      };
      
      wsRef.current.onmessage = (event) => {
        try {
          const update = JSON.parse(event.data);
          console.log('Received real-time update:', update);
          setLastUpdate(new Date().toLocaleTimeString());
          
          // Handle different types of updates
          if (update.type === 'performance_update') {
            // Update overview data with new performance metrics
            if (update.data) {
              setTeacherSummary(prevSummary => ({
                ...prevSummary,
                total_students: update.data.total_students,
                overall_average: update.data.overall_average,
                overall_pass_rate: update.data.overall_pass_rate,
                grade_distribution: update.data.grade_distribution,
                subject_performance_chart: update.data.subject_performance_chart,
                sections_performance_chart: update.data.sections_performance_chart
              }));
            }
          } else if (update.type === 'grade_update') {
            // Show notification for new grade
            console.log(`New grade: ${update.grade_data?.student_name} - ${update.grade_data?.score}/${update.grade_data?.total_marks}`);
            // Update performance data
            if (update.performance_data) {
              setTeacherSummary(prevSummary => ({
                ...prevSummary,
                ...update.performance_data
              }));
            }
          } else if (update.type === 'attendance_update') {
            // Show notification for attendance change
            console.log(`Attendance updated: ${update.attendance_data?.student_name} - ${update.attendance_data?.status}`);
          } else if (update.type === 'exam_created') {
            // Show notification for new exam
            console.log(`New exam created: ${update.exam_data?.exam_name} for ${update.exam_data?.subject_name}`);
          }
        } catch (error) {
          console.error('Error parsing WebSocket message:', error);
        }
      };
      
      wsRef.current.onclose = () => {
        console.log('WebSocket disconnected');
        setIsConnected(false);
        // Attempt to reconnect after 5 seconds
        setTimeout(connectWebSocket, 5000);
      };
      
      wsRef.current.onerror = (error) => {
        console.error('WebSocket error:', error);
        setIsConnected(false);
      };
      
    } catch (error) {
      console.error('Failed to connect WebSocket:', error);
    }
  };

    connectWebSocket();
    
    // Cleanup on component unmount
    return () => {
      if (wsRef.current) {
        wsRef.current.close();
      }
    };
  }, []);

  const loadTeacherSummary = async () => {
    setLoading(true);
    try {
      const token = localStorage.getItem('token');
      if (!token) {
        setError('Authentication required. Please login.');
        setLoading(false);
        return;
      }
      
      const headers = { Authorization: `Bearer ${token}` };
      const response = await axios.get(`/api/v1/performance/overview`, { headers });
      setTeacherSummary(response.data);
      setSectionData(response.data.sections_summary);
    } catch (error) {
      setError('Failed to load teacher summary');
      console.error(error);
    } finally {
      setLoading(false);
    }
  };

  const loadSectionPerformance = async (sectionId) => {
    setLoading(true);
    try {
      const token = localStorage.getItem('token');
      if (!token) {
        setError('Authentication required. Please login.');
        setLoading(false);
        return;
      }
      
      const headers = { Authorization: `Bearer ${token}` };
      const params = new URLSearchParams(filters);
      const response = await axios.get(`/api/v1/performance/section/${sectionId}?${params}`, { headers });
      setSectionPerformance(response.data);
      setSelectedSection(sectionId);
    } catch (error) {
      setError('Failed to load section performance');
      console.error(error);
    } finally {
      setLoading(false);
    }
  };

  const loadStudentDetail = async (studentId) => {
    setLoading(true);
    try {
      const token = localStorage.getItem('token');
      if (!token) {
        setError('Authentication required. Please login.');
        return;
      }
      
      const headers = { Authorization: `Bearer ${token}` };
      const response = await axios.get(`/api/v1/performance/student/${studentId}`, { headers });
      setStudentDetail(response.data);
      setSelectedStudent(studentId);
    } catch (error) {
      setError('Failed to load student details');
      console.error(error);
    } finally {
      setLoading(false);
    }
  };

  const handleFilterChange = (key, value) => {
    setFilters(prev => ({ ...prev, [key]: value }));
  };

  const applyFilters = () => {
    if (selectedSection) {
      loadSectionPerformance(selectedSection);
    }
  };

  const exportData = async (format) => {
    try {
      const response = await axios.post('/api/v1/performance/export', {
        scope: 'section',
        section_id: selectedSection,
        filters: filters,
        format: format
      }, { responseType: 'blob' });
      
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `performance_report.${format}`);
      document.body.appendChild(link);
      link.click();
      link.remove();
    } catch (error) {
      setError('Failed to export data');
      console.error(error);
    }
  };

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-white shadow">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="py-6">
            <div className="flex items-center justify-between">
              <h1 className="text-3xl font-bold text-gray-900">Performance Dashboard</h1>
              <div className="flex items-center space-x-4">
                <div className={`flex items-center space-x-2 px-3 py-1 rounded-full text-sm ${isConnected ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'}`}>
                  <div className={`w-2 h-2 rounded-full ${isConnected ? 'bg-green-500' : 'bg-red-500'}`}></div>
                  <span>{isConnected ? 'Live Data' : 'Offline'}</span>
                </div>
                {lastUpdate && (
                  <span className="text-sm text-gray-500">Last update: {lastUpdate}</span>
                )}
              </div>
            </div>
            <p className="mt-2 text-sm text-gray-600">Comprehensive student performance analytics and insights</p>
          </div>
        </div>
      </div>

      {/* Navigation Tabs */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="border-b border-gray-200">
          <nav className="-mb-px flex space-x-8">
            {[
              { id: 'overview', label: 'Overview', icon: '📊' },
              { id: 'sections', label: 'Section View', icon: '🏫' },
              { id: 'subjects', label: 'Subject Analytics', icon: '📚' },
              { id: 'students', label: 'Student Details', icon: '👥' }
            ].map((tab) => (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`py-4 px-1 border-b-2 font-medium text-sm ${
                  activeTab === tab.id
                    ? 'border-blue-500 text-blue-600'
                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                }`}
              >
                <span className="mr-2">{tab.icon}</span>
                {tab.label}
              </button>
            ))}
          </nav>
        </div>
      </div>

      {/* Main Content */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {error && (
          <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded mb-6">
            {error}
          </div>
        )}

        {loading && (
          <div className="text-center py-8">
            <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
            <p className="mt-2 text-gray-600">Loading...</p>
          </div>
        )}

        {/* Overview Tab */}
        {activeTab === 'overview' && teacherSummary && (
          <div className="space-y-6">
            {/* Summary Cards */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
              <div className="bg-white rounded-lg shadow p-6">
                <div className="flex items-center">
                  <div className="flex-shrink-0">
                    <div className="w-8 h-8 bg-blue-100 rounded-full flex items-center justify-center">
                      <span className="text-blue-600 text-sm font-medium">👥</span>
                    </div>
                  </div>
                  <div className="ml-4">
                    <p className="text-sm font-medium text-gray-500">Total Students</p>
                    <p className="text-2xl font-semibold text-gray-900">{teacherSummary.total_students}</p>
                  </div>
                </div>
              </div>

              <div className="bg-white rounded-lg shadow p-6">
                <div className="flex items-center">
                  <div className="flex-shrink-0">
                    <div className="w-8 h-8 bg-green-100 rounded-full flex items-center justify-center">
                      <span className="text-green-600 text-sm font-medium">📈</span>
                    </div>
                  </div>
                  <div className="ml-4">
                    <p className="text-sm font-medium text-gray-500">Overall Average</p>
                    <p className="text-2xl font-semibold text-gray-900">
                      {teacherSummary.overall_average?.toFixed(1) || 'N/A'}%
                    </p>
                  </div>
                </div>
              </div>

              <div className="bg-white rounded-lg shadow p-6">
                <div className="flex items-center">
                  <div className="flex-shrink-0">
                    <div className="w-8 h-8 bg-green-100 rounded-full flex items-center justify-center">
                      <span className="text-green-600 text-sm font-medium">✅</span>
                    </div>
                  </div>
                  <div className="ml-4">
                    <p className="text-sm font-medium text-gray-500">Pass Rate</p>
                    <p className="text-2xl font-semibold text-gray-900">
                      {teacherSummary.overall_pass_rate?.toFixed(1) || 0}%
                    </p>
                  </div>
                </div>
              </div>

              <div className="bg-white rounded-lg shadow p-6">
                <div className="flex items-center">
                  <div className="flex-shrink-0">
                    <div className="w-8 h-8 bg-orange-100 rounded-full flex items-center justify-center">
                      <span className="text-orange-600 text-sm font-medium">⚠️</span>
                    </div>
                  </div>
                  <div className="ml-4">
                    <p className="text-sm font-medium text-gray-500">Alerts</p>
                    <p className="text-2xl font-semibold text-gray-900">{teacherSummary.alerts.length}</p>
                  </div>
                </div>
              </div>
            </div>

            {/* Sections Overview */}
            <div className="bg-white rounded-lg shadow">
              <div className="px-6 py-4 border-b border-gray-200">
                <h2 className="text-lg font-semibold text-gray-900">Sections Overview</h2>
              </div>
              <div className="p-6">
                <div className="overflow-x-auto">
                  <table className="min-w-full divide-y divide-gray-200">
                    <thead>
                      <tr>
                        <th className="px-6 py-3 bg-gray-50 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Section</th>
                        <th className="px-6 py-3 bg-gray-50 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Students</th>
                        <th className="px-6 py-3 bg-gray-50 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Average</th>
                        <th className="px-6 py-3 bg-gray-50 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Pass Rate</th>
                        <th className="px-6 py-3 bg-gray-50 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Actions</th>
                      </tr>
                    </thead>
                    <tbody className="bg-white divide-y divide-gray-200">
                      {sectionData.map((section) => (
                        <tr key={section.section_id} className="hover:bg-gray-50">
                          <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                            {section.section_name}
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                            {section.total_students}
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                            {section.average_score?.toFixed(1) || 'N/A'}%
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap">
                            <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${
                              section.pass_rate >= 80 
                                ? 'bg-green-100 text-green-800'
                                : section.pass_rate >= 60
                                ? 'bg-yellow-100 text-yellow-800'
                                : 'bg-red-100 text-red-800'
                            }`}>
                              {section.pass_rate?.toFixed(1) || 0}%
                            </span>
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
                            <button
                              onClick={() => {
                                setActiveTab('sections');
                                loadSectionPerformance(section.section_id);
                              }}
                              className="text-blue-600 hover:text-blue-900"
                            >
                              View Details
                            </button>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            </div>

            {/* Alerts */}
            {teacherSummary.alerts.length > 0 && (
              <div className="bg-white rounded-lg shadow">
                <div className="px-6 py-4 border-b border-gray-200">
                  <h2 className="text-lg font-semibold text-gray-900">Performance Alerts</h2>
                </div>
                <div className="p-6">
                  <div className="space-y-4">
                    {teacherSummary.alerts.map((alert, index) => (
                      <div key={index} className={`p-4 rounded-lg ${
                        alert.severity === 'high' 
                          ? 'bg-red-50 border border-red-200'
                          : 'bg-yellow-50 border border-yellow-200'
                      }`}>
                        <div className="flex">
                          <div className="flex-shrink-0">
                            <span className="text-lg">{alert.severity === 'high' ? '🚨' : '⚠️'}</span>
                          </div>
                          <div className="ml-3">
                            <p className={`text-sm font-medium ${
                              alert.severity === 'high' ? 'text-red-800' : 'text-yellow-800'
                            }`}>
                              {alert.message}
                            </p>
                            <p className="text-xs text-gray-600 mt-1">Alert Type: {alert.type}</p>
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            )}
          </div>
        )}

        {/* Section View Tab */}
        {activeTab === 'sections' && (
          <div className="space-y-6">
            {/* Filters */}
            <div className="bg-white rounded-lg shadow p-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">Filters & Controls</h3>
              <div className="grid grid-cols-1 md:grid-cols-3 lg:grid-cols-6 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700">Section</label>
                  <select 
                    className="mt-1 block w-full rounded-md border-gray-300 shadow-sm"
                    onChange={(e) => {
                      const sectionId = parseInt(e.target.value);
                      if (sectionId) loadSectionPerformance(sectionId);
                    }}
                    value={selectedSection || ''}
                  >
                    <option value="">Select Section</option>
                    {sectionData.map(section => (
                      <option key={section.section_id} value={section.section_id}>
                        {section.section_name}
                      </option>
                    ))}
                  </select>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700">Subject</label>
                  <select 
                    className="mt-1 block w-full rounded-md border-gray-300 shadow-sm"
                    value={filters.subject}
                    onChange={(e) => handleFilterChange('subject', e.target.value)}
                  >
                    <option value="">All Subjects</option>
                    <option value="Mathematics">Mathematics</option>
                    <option value="Science">Science</option>
                    <option value="English">English</option>
                  </select>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700">Status</label>
                  <select 
                    className="mt-1 block w-full rounded-md border-gray-300 shadow-sm"
                    value={filters.passFailFilter}
                    onChange={(e) => handleFilterChange('passFailFilter', e.target.value)}
                  >
                    <option value="all">All Students</option>
                    <option value="pass">Pass Only</option>
                    <option value="fail">Fail Only</option>
                  </select>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700">Sort By</label>
                  <select 
                    className="mt-1 block w-full rounded-md border-gray-300 shadow-sm"
                    value={filters.sortBy}
                    onChange={(e) => handleFilterChange('sortBy', e.target.value)}
                  >
                    <option value="roll_number">Roll Number</option>
                    <option value="name">Name</option>
                    <option value="average">Average Score</option>
                    <option value="attendance">Attendance</option>
                  </select>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700">Order</label>
                  <select 
                    className="mt-1 block w-full rounded-md border-gray-300 shadow-sm"
                    value={filters.sortOrder}
                    onChange={(e) => handleFilterChange('sortOrder', e.target.value)}
                  >
                    <option value="asc">Ascending</option>
                    <option value="desc">Descending</option>
                  </select>
                </div>

                <div className="flex items-end">
                  <button
                    onClick={applyFilters}
                    className="w-full bg-blue-600 text-white px-4 py-2 rounded-md hover:bg-blue-700"
                  >
                    Apply Filters
                  </button>
                </div>
              </div>

              {selectedSection && (
                <div className="mt-4 flex space-x-2">
                  <button
                    onClick={() => exportData('csv')}
                    className="bg-green-600 text-white px-4 py-2 rounded-md hover:bg-green-700 text-sm"
                  >
                    📊 Export CSV
                  </button>
                  <button
                    onClick={() => exportData('pdf')}
                    className="bg-red-600 text-white px-4 py-2 rounded-md hover:bg-red-700 text-sm"
                  >
                    📄 Export PDF
                  </button>
                </div>
              )}
            </div>

            {/* Section Performance Data */}
            {sectionPerformance && (
              <div className="space-y-6">
                {/* Section Summary */}
                <div className="bg-white rounded-lg shadow p-6">
                  <h3 className="text-lg font-semibold text-gray-900 mb-4">
                    {sectionPerformance.section_info.name} - Performance Summary
                  </h3>
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                    <div className="text-center">
                      <p className="text-2xl font-bold text-blue-600">{sectionPerformance.summary_stats.total_students}</p>
                      <p className="text-sm text-gray-600">Total Students</p>
                    </div>
                    <div className="text-center">
                      <p className="text-2xl font-bold text-green-600">
                        {sectionPerformance.summary_stats.section_average?.toFixed(1) || 'N/A'}%
                      </p>
                      <p className="text-sm text-gray-600">Section Average</p>
                    </div>
                    <div className="text-center">
                      <p className="text-2xl font-bold text-green-600">{sectionPerformance.summary_stats.pass_count}</p>
                      <p className="text-sm text-gray-600">Students Passed</p>
                    </div>
                    <div className="text-center">
                      <p className="text-2xl font-bold text-red-600">{sectionPerformance.summary_stats.fail_count}</p>
                      <p className="text-sm text-gray-600">Students Failed</p>
                    </div>
                  </div>
                </div>

                {/* Student Performance Table */}
                <div className="bg-white rounded-lg shadow">
                  <div className="px-6 py-4 border-b border-gray-200">
                    <h3 className="text-lg font-semibold text-gray-900">Student Performance</h3>
                  </div>
                  <div className="overflow-x-auto">
                    <table className="min-w-full divide-y divide-gray-200">
                      <thead>
                        <tr>
                          <th className="px-6 py-3 bg-gray-50 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Roll</th>
                          <th className="px-6 py-3 bg-gray-50 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Name</th>
                          <th className="px-6 py-3 bg-gray-50 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Email</th>
                          <th className="px-6 py-3 bg-gray-50 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Math</th>
                          <th className="px-6 py-3 bg-gray-50 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Science</th>
                          <th className="px-6 py-3 bg-gray-50 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">English</th>
                          <th className="px-6 py-3 bg-gray-50 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Average</th>
                          <th className="px-6 py-3 bg-gray-50 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Attendance</th>
                          <th className="px-6 py-3 bg-gray-50 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Status</th>
                          <th className="px-6 py-3 bg-gray-50 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Actions</th>
                        </tr>
                      </thead>
                      <tbody className="bg-white divide-y divide-gray-200">
                        {sectionPerformance.students.map((student) => (
                          <tr key={student.student_id} className="hover:bg-gray-50">
                            <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                              {student.roll_number}
                            </td>
                            <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                              {student.student_name}
                            </td>
                            <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                              {student.email}
                            </td>
                            <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                              {student.math_marks?.toFixed(1) || 'N/A'}
                            </td>
                            <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                              {student.science_marks?.toFixed(1) || 'N/A'}
                            </td>
                            <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                              {student.english_marks?.toFixed(1) || 'N/A'}
                            </td>
                            <td className="px-6 py-4 whitespace-nowrap text-sm font-semibold text-gray-900">
                              {student.overall_average?.toFixed(1) || 'N/A'}%
                            </td>
                            <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                              {student.attendance_percentage?.toFixed(1) || 'N/A'}%
                            </td>
                            <td className="px-6 py-4 whitespace-nowrap">
                              <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${
                                student.status === 'Pass' 
                                  ? 'bg-green-100 text-green-800'
                                  : student.status === 'Fail'
                                  ? 'bg-red-100 text-red-800'
                                  : 'bg-gray-100 text-gray-800'
                              }`}>
                                {student.status}
                              </span>
                            </td>
                            <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
                              <button
                                onClick={() => loadStudentDetail(student.student_id)}
                                className="text-blue-600 hover:text-blue-900 mr-2"
                              >
                                View Profile
                              </button>
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
              </div>
            )}
          </div>
        )}

        {/* Subjects Tab */}
        {activeTab === 'subjects' && teacherSummary && (
          <div className="space-y-6">
            {/* Subjects Overview Cards */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              <div className="bg-white rounded-lg shadow p-6">
                <div className="text-center">
                  <p className="text-2xl font-bold text-blue-600">{teacherSummary.total_subjects}</p>
                  <p className="text-sm text-gray-600">Total Subjects</p>
                </div>
              </div>
              <div className="bg-white rounded-lg shadow p-6">
                <div className="text-center">
                  <p className="text-2xl font-bold text-green-600">
                    {teacherSummary.subjects_summary?.reduce((acc, subject) => acc + subject.average_score, 0) / (teacherSummary.subjects_summary?.length || 1) || 0}%
                  </p>
                  <p className="text-sm text-gray-600">Avg Subject Performance</p>
                </div>
              </div>
              <div className="bg-white rounded-lg shadow p-6">
                <div className="text-center">
                  <p className="text-2xl font-bold text-purple-600">
                    {teacherSummary.subjects_summary?.reduce((acc, subject) => acc + subject.pass_rate, 0) / (teacherSummary.subjects_summary?.length || 1) || 0}%
                  </p>
                  <p className="text-sm text-gray-600">Avg Subject Pass Rate</p>
                </div>
              </div>
            </div>

            {/* Subject Performance Table */}
            <div className="bg-white rounded-lg shadow">
              <div className="px-6 py-4 border-b border-gray-200 flex justify-between items-center">
                <h3 className="text-lg font-semibold text-gray-900">Subject Performance Analytics</h3>
                <button 
                  onClick={() => exportData('subjects', 'csv')}
                  className="bg-green-600 text-white px-4 py-2 rounded-md hover:bg-green-700"
                >
                  📊 Export CSV
                </button>
              </div>
              <div className="overflow-x-auto">
                <table className="min-w-full divide-y divide-gray-200">
                  <thead>
                    <tr>
                      <th className="px-6 py-3 bg-gray-50 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Subject</th>
                      <th className="px-6 py-3 bg-gray-50 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Code</th>
                      <th className="px-6 py-3 bg-gray-50 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Students</th>
                      <th className="px-6 py-3 bg-gray-50 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Average Score</th>
                      <th className="px-6 py-3 bg-gray-50 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Pass Rate</th>
                      <th className="px-6 py-3 bg-gray-50 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Highest</th>
                      <th className="px-6 py-3 bg-gray-50 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Lowest</th>
                      <th className="px-6 py-3 bg-gray-50 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Actions</th>
                    </tr>
                  </thead>
                  <tbody className="bg-white divide-y divide-gray-200">
                    {(teacherSummary.subjects_summary || []).map((subject) => (
                      <tr key={subject.subject_id} className="hover:bg-gray-50">
                        <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                          {subject.subject_name}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                          {subject.subject_code}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                          {subject.total_students}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                          {subject.average_score?.toFixed(1) || 'N/A'}%
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap">
                          <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${
                            subject.pass_rate >= 80 
                              ? 'bg-green-100 text-green-800'
                              : subject.pass_rate >= 60
                              ? 'bg-yellow-100 text-yellow-800'
                              : 'bg-red-100 text-red-800'
                          }`}>
                            {subject.pass_rate?.toFixed(1) || 0}%
                          </span>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                          {subject.highest_score?.toFixed(1) || 'N/A'}%
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                          {subject.lowest_score?.toFixed(1) || 'N/A'}%
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
                          <button className="text-blue-600 hover:text-blue-900 mr-2">
                            View Details
                          </button>
                          <button className="text-green-600 hover:text-green-900">
                            📊 Analytics
                          </button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>

            {/* Grade Distribution Chart */}
            {teacherSummary.grade_distribution && Object.keys(teacherSummary.grade_distribution).length > 0 && (
              <div className="bg-white rounded-lg shadow p-6">
                <h3 className="text-lg font-semibold text-gray-900 mb-4">Overall Grade Distribution</h3>
                <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-6 gap-4">
                  {Object.entries(teacherSummary.grade_distribution).map(([grade, count]) => (
                    <div key={grade} className="text-center p-3 bg-gray-50 rounded-lg">
                      <p className="text-2xl font-bold text-blue-600">{count}</p>
                      <p className="text-sm text-gray-600">Grade {grade}</p>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}

        {/* Student Details Modal */}
        {selectedStudent && studentDetail && (
          <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
            <div className="bg-white rounded-lg shadow-xl max-w-4xl w-full max-h-screen overflow-y-auto">
              <div className="sticky top-0 bg-white border-b border-gray-200 px-6 py-4 flex justify-between items-center">
                <h3 className="text-lg font-semibold text-gray-900">
                  Student Profile: {studentDetail.student_info.name}
                </h3>
                <button
                  onClick={() => {
                    setSelectedStudent(null);
                    setStudentDetail(null);
                  }}
                  className="text-gray-400 hover:text-gray-600 text-xl font-semibold"
                >
                  ×
                </button>
              </div>
              
              <div className="p-6 space-y-6">
                {/* Student Info */}
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <p className="text-sm font-medium text-gray-500">Name</p>
                    <p className="text-lg font-semibold">{studentDetail.student_info.name}</p>
                  </div>
                  <div>
                    <p className="text-sm font-medium text-gray-500">Roll Number</p>
                    <p className="text-lg font-semibold">{studentDetail.student_info.roll_number}</p>
                  </div>
                  <div>
                    <p className="text-sm font-medium text-gray-500">Email</p>
                    <p className="text-lg">{studentDetail.student_info.email}</p>
                  </div>
                  <div>
                    <p className="text-sm font-medium text-gray-500">Section</p>
                    <p className="text-lg">{studentDetail.student_info.section}</p>
                  </div>
                </div>

                {/* Current Performance */}
                <div className="bg-blue-50 rounded-lg p-4">
                  <h4 className="text-lg font-semibold text-blue-900 mb-3">Current Performance</h4>
                  <div className="grid grid-cols-3 gap-4">
                    <div className="text-center">
                      <p className="text-2xl font-bold text-blue-600">
                        {studentDetail.current_performance.overall_average?.toFixed(1) || 'N/A'}%
                      </p>
                      <p className="text-sm text-blue-800">Overall Average</p>
                    </div>
                    <div className="text-center">
                      <p className="text-2xl font-bold text-blue-600">
                        {studentDetail.current_performance.grade_letter || 'N/A'}
                      </p>
                      <p className="text-sm text-blue-800">Grade</p>
                    </div>
                    <div className="text-center">
                      <p className="text-2xl font-bold text-blue-600">
                        {studentDetail.current_performance.attendance_percentage?.toFixed(1) || 'N/A'}%
                      </p>
                      <p className="text-sm text-blue-800">Attendance</p>
                    </div>
                  </div>
                </div>

                {/* Grade History */}
                <div>
                  <h4 className="text-lg font-semibold text-gray-900 mb-3">Grade History</h4>
                  <div className="overflow-x-auto">
                    <table className="min-w-full divide-y divide-gray-200">
                      <thead>
                        <tr>
                          <th className="px-4 py-2 bg-gray-50 text-left text-xs font-medium text-gray-500 uppercase">Subject</th>
                          <th className="px-4 py-2 bg-gray-50 text-left text-xs font-medium text-gray-500 uppercase">Exam</th>
                          <th className="px-4 py-2 bg-gray-50 text-left text-xs font-medium text-gray-500 uppercase">Marks</th>
                          <th className="px-4 py-2 bg-gray-50 text-left text-xs font-medium text-gray-500 uppercase">Percentage</th>
                          <th className="px-4 py-2 bg-gray-50 text-left text-xs font-medium text-gray-500 uppercase">Grade</th>
                          <th className="px-4 py-2 bg-gray-50 text-left text-xs font-medium text-gray-500 uppercase">Date</th>
                        </tr>
                      </thead>
                      <tbody className="bg-white divide-y divide-gray-200">
                        {studentDetail.grade_history.slice(0, 10).map((grade) => (
                          <tr key={grade.id}>
                            <td className="px-4 py-2 text-sm text-gray-900">{grade.subject}</td>
                            <td className="px-4 py-2 text-sm text-gray-500">{grade.exam}</td>
                            <td className="px-4 py-2 text-sm text-gray-500">
                              {grade.marks_obtained}/{grade.total_marks}
                            </td>
                            <td className="px-4 py-2 text-sm font-semibold text-gray-900">
                              {grade.percentage?.toFixed(1) || 'N/A'}%
                            </td>
                            <td className="px-4 py-2 text-sm text-gray-500">{grade.grade_letter}</td>
                            <td className="px-4 py-2 text-sm text-gray-500">
                              {new Date(grade.assessment_date || grade.created_at).toLocaleDateString()}
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>

                {/* Actions */}
                <div className="flex space-x-4">
                  <button className="bg-blue-600 text-white px-4 py-2 rounded-md hover:bg-blue-700">
                    📧 Send Message
                  </button>
                  <button className="bg-green-600 text-white px-4 py-2 rounded-md hover:bg-green-700">
                    📊 Send Performance Report
                  </button>
                  <button className="bg-purple-600 text-white px-4 py-2 rounded-md hover:bg-purple-700">
                    📅 Schedule Meeting
                  </button>
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default PerformanceDashboard;