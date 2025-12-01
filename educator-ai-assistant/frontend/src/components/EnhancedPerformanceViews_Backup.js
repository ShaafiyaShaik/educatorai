import React, { useState, useEffect } from 'react';
import { 
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
  PieChart, Pie, Cell, LineChart, Line, Legend
} from 'recharts';
import { 
  Users, TrendingUp, Award, AlertTriangle, Download, Filter,
  BookOpen, GraduationCap, Target, BarChart3, Send
} from 'lucide-react';
import axios from 'axios';
import { API_BASE_URL } from '../services/api';
import { SendReportModal, SentReportsHistory } from './SendReports';

const COLORS = ['#0088FE', '#00C49F', '#FFBB28', '#FF8042', '#8884D8'];

const EnhancedPerformanceViews = () => {
  const [activeView, setActiveView] = useState('overall');
  const [performanceData, setPerformanceData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [filters, setFilters] = useState({
    view_type: 'overall',
    sort_by: 'average',
    sort_order: 'desc',
    performance_threshold: null,
    section_ids: null,
    subject_ids: null,
    include_top_performers: true,
    include_low_performers: true,
    top_count: 5,
    low_count: 5
  });
  const [sections, setSections] = useState([]);
  const [subjects, setSubjects] = useState([]);
  const [selectedStudent, setSelectedStudent] = useState(null);
  
  // Report sending state
  const [showSendReportModal, setShowSendReportModal] = useState(false);
  const [showReportsHistory, setShowReportsHistory] = useState(false);
  const [sentReports, setSentReports] = useState([]);

  useEffect(() => {
    fetchInitialData();
  }, []);

  useEffect(() => {
    if (activeView) {
      fetchPerformanceData();
    }
  }, [activeView, filters]);

  const fetchInitialData = async () => {
    try {
      const token = localStorage.getItem('token');
      const headers = { 'Authorization': `Bearer ${token}` };

      // Fetch sections and subjects for filters
      const [sectionsRes, dashboardRes] = await Promise.all([
        axios.get(`${API_BASE_URL}/api/v1/students/sections`, { headers }),
        axios.get(`${API_BASE_URL}/api/v1/dashboard/dashboard`, { headers })
      ]);

      setSections(sectionsRes.data.sections || []);
      
      // Extract subjects from sections
      const allSubjects = [];
      if (sectionsRes.data.sections) {
        sectionsRes.data.sections.forEach(section => {
          if (section.subjects) {
            allSubjects.push(...section.subjects);
          }
        });
      }
      setSubjects(allSubjects);

    } catch (error) {
      console.error('Error fetching initial data:', error);
    }
  };

  const fetchPerformanceData = async () => {
    setLoading(true);
    try {
      const token = localStorage.getItem('token');
      const headers = { 'Authorization': `Bearer ${token}` };

      let endpoint = '';
      switch (activeView) {
        case 'overall':
          endpoint = `${API_BASE_URL}/api/v1/performance/performance/overview`;
          break;
        case 'filtered':
          endpoint = `${API_BASE_URL}/api/v1/performance/performance/filtered`;
          break;
        default:
          endpoint = `${API_BASE_URL}/api/v1/performance/performance/overview`;
      }

      let response;
      if (activeView === 'filtered') {
        response = await axios.post(endpoint, filters, { headers });
      } else {
        response = await axios.get(endpoint, { headers });
      }

      setPerformanceData(response.data);
    } catch (error) {
      console.error('Error fetching performance data:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleFilterChange = (key, value) => {
    setFilters(prev => ({
      ...prev,
      [key]: value
    }));
  };

  const handleViewChange = (view) => {
    setActiveView(view);
    setFilters(prev => ({
      ...prev,
      view_type: view
    }));
  };

  const downloadReport = async (format) => {
    try {
      const token = localStorage.getItem('token');
      
      // Map active view to API view types
      const viewTypeMap = {
        'overall': 'overall',
        'sections': 'section', 
        'subjects': 'subject',
        'filtered': 'overall' // Default to overall for filtered view
      };
      
      const apiViewType = viewTypeMap[activeView] || 'overall';
      
      const params = new URLSearchParams({
        format,
        view_type: apiViewType
      });

      // Add specific IDs based on current selections
      if (activeView === 'sections' && filters.section_ids && filters.section_ids.length > 0) {
        params.append('section_id', filters.section_ids[0]);
      }
      
      if (activeView === 'subjects' && filters.subject_ids && filters.subject_ids.length > 0) {
        params.append('subject_id', filters.subject_ids[0]);
      }

      const response = await axios.get(
        `${API_BASE_URL}/api/v1/performance/performance/reports/download?${params}`,
        {
          headers: { 'Authorization': `Bearer ${token}` },
          responseType: 'blob'
        }
      );

      // Create descriptive filename based on view type
      const reportNames = {
        'overall': 'Overall_Performance_Report',
        'sections': 'Section_Analysis_Report',
        'subjects': 'Subject_Analysis_Report',
        'filtered': 'Custom_Performance_Report'
      };
      
      const timestamp = new Date().toISOString().slice(0, 19).replace(/[:-]/g, '');
      const filename = `${reportNames[activeView]}_${timestamp}.${format}`;

      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', filename);
      document.body.appendChild(link);
      link.click();
      link.remove();
      
      // Show success message
      console.log(`${format.toUpperCase()} report downloaded: ${filename}`);
    } catch (error) {
      console.error('Error downloading report:', error);
      // You could add a toast notification here
    }
  };

  const openStudentDetail = async (studentId) => {
    try {
      const token = localStorage.getItem('token');
      const response = await axios.get(
        `http://localhost:8001/api/v1/performance/performance/student/${studentId}`,
        { headers: { 'Authorization': `Bearer ${token}` } }
      );
      setSelectedStudent(response.data);
    } catch (error) {
      console.error('Error fetching student details:', error);
    }
  };

  const getReportTitle = () => {
    const titles = {
      'overall': 'Overall Performance Analysis',
      'sections': 'Section Analysis Report',
      'subjects': 'Subject Analysis Report',
      'filtered': 'Custom Performance Report'
    };
    return titles[activeView] || 'Performance Report';
  };

  // Report sending functions
  const fetchSentReports = async () => {
    try {
      const token = localStorage.getItem('token');
      const response = await axios.get(
        'http://localhost:8001/api/v1/performance/sent-reports',
        { headers: { 'Authorization': `Bearer ${token}` } }
      );
      setSentReports(response.data);
    } catch (error) {
      console.error('Error fetching sent reports:', error);
    }
  };

  const handleSendReport = async (reportData) => {
    try {
      const token = localStorage.getItem('token');
      await axios.post(
        'http://localhost:8001/api/v1/performance/send-report',
        reportData,
        { headers: { 'Authorization': `Bearer ${token}` } }
      );
      
      // Show success message
      alert('Report sent successfully!');
      
      // Refresh sent reports if history is visible
      if (showReportsHistory) {
        fetchSentReports();
      }
    } catch (error) {
      console.error('Error sending report:', error);
      alert('Failed to send report. Please try again.');
    }
  };

  // Load sent reports when history is shown
  useEffect(() => {
    if (showReportsHistory) {
      fetchSentReports();
    }
  }, [showReportsHistory]);

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="animate-spin rounded-full h-32 w-32 border-b-2 border-blue-500"></div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 p-6">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900 mb-2">
            Enhanced Performance Analytics
          </h1>
          <p className="text-gray-600">
            Comprehensive performance insights with advanced filtering and reporting
          </p>
        </div>

        {/* Navigation Tabs */}
        <div className="mb-6">
          <div className="border-b border-gray-200">
            <nav className="-mb-px flex space-x-8">
              {[
                { id: 'overall', name: 'Overall Performance', icon: BarChart3 },
                { id: 'sections', name: 'Section Analysis', icon: Users },
                { id: 'subjects', name: 'Subject Analysis', icon: BookOpen },
                { id: 'filtered', name: 'Custom Filters', icon: Filter }
              ].map((tab) => (
                <button
                  key={tab.id}
                  onClick={() => handleViewChange(tab.id)}
                  className={`${
                    activeView === tab.id
                      ? 'border-blue-500 text-blue-600'
                      : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                  } whitespace-nowrap py-2 px-1 border-b-2 font-medium text-sm flex items-center gap-2`}
                >
                  <tab.icon className="w-4 h-4" />
                  {tab.name}
                </button>
              ))}
            </nav>
          </div>
        </div>

        {/* Action Bar */}
        <div className="mb-6 flex justify-between items-center">
          <div className="flex gap-2">
            <button
              onClick={() => downloadReport('pdf')}
              className="flex items-center gap-2 px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 transition-colors"
              title={`Download ${getReportTitle()} as PDF`}
            >
              <Download className="w-4 h-4" />
              Download PDF
            </button>
            <button
              onClick={() => downloadReport('excel')}
              className="flex items-center gap-2 px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors"
              title={`Download ${getReportTitle()} as Excel`}
            >
              <Download className="w-4 h-4" />
              Download Excel
            </button>
          </div>
          
          {/* Report Type Indicator */}
          <div className="hidden md:flex items-center gap-2 px-3 py-2 bg-blue-50 text-blue-700 rounded-lg border border-blue-200">
            <BarChart3 className="w-4 h-4" />
            <span className="text-sm font-medium">Report: {getReportTitle()}</span>
          </div>

          {activeView === 'filtered' && (
            <div className="flex gap-4">
              <select
                value={filters.sort_by}
                onChange={(e) => handleFilterChange('sort_by', e.target.value)}
                className="px-3 py-2 border border-gray-300 rounded-lg"
              >
                <option value="average">Sort by Average</option>
                <option value="name">Sort by Name</option>
                <option value="attendance">Sort by Attendance</option>
              </select>
              <select
                value={filters.sort_order}
                onChange={(e) => handleFilterChange('sort_order', e.target.value)}
                className="px-3 py-2 border border-gray-300 rounded-lg"
              >
                <option value="desc">Descending</option>
                <option value="asc">Ascending</option>
              </select>
            </div>
          )}
        </div>

        {/* Performance Content */}
        {performanceData && (
          <div className="space-y-6">
            {/* Overall Statistics Cards */}
            {(activeView === 'overall' || activeView === 'filtered') && (
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
                <StatCard
                  title="Total Students"
                  value={performanceData.total_students || performanceData.total_count || 0}
                  icon={Users}
                  color="blue"
                />
                <StatCard
                  title="Pass Rate"
                  value={`${performanceData.overall_pass_rate || 0}%`}
                  icon={Target}
                  color="green"
                />
                <StatCard
                  title="Average Score"
                  value={`${performanceData.overall_average || 0}%`}
                  icon={TrendingUp}
                  color="yellow"
                />
                <StatCard
                  title="Total Sections"
                  value={performanceData.total_sections || 0}
                  icon={GraduationCap}
                  color="purple"
                />
              </div>
            )}

            {/* Main Content Area */}
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
              {/* Performance Charts */}
              <div className="lg:col-span-2 space-y-6">
                {/* Section Performance Chart */}
                {performanceData.sections_summary && (
                  <div className="bg-white p-6 rounded-lg shadow">
                    <h3 className="text-lg font-semibold mb-4">Section Performance Comparison</h3>
                    <ResponsiveContainer width="100%" height={300}>
                      <BarChart data={performanceData.sections_summary}>
                        <CartesianGrid strokeDasharray="3 3" />
                        <XAxis dataKey="section_name" />
                        <YAxis />
                        <Tooltip />
                        <Legend />
                        <Bar dataKey="average_score" fill="#3B82F6" name="Average Score %" />
                        <Bar dataKey="pass_rate" fill="#10B981" name="Pass Rate %" />
                      </BarChart>
                    </ResponsiveContainer>
                  </div>
                )}

                {/* Subject Performance Chart */}
                {performanceData.subjects_summary && (
                  <div className="bg-white p-6 rounded-lg shadow">
                    <h3 className="text-lg font-semibold mb-4">Subject Performance Analysis</h3>
                    <ResponsiveContainer width="100%" height={300}>
                      <LineChart data={performanceData.subjects_summary}>
                        <CartesianGrid strokeDasharray="3 3" />
                        <XAxis dataKey="subject_name" />
                        <YAxis />
                        <Tooltip />
                        <Legend />
                        <Line type="monotone" dataKey="average_score" stroke="#8884d8" name="Average Score %" />
                        <Line type="monotone" dataKey="pass_rate" stroke="#82ca9d" name="Pass Rate %" />
                      </LineChart>
                    </ResponsiveContainer>
                  </div>
                )}

                {/* Grade Distribution */}
                {performanceData.grade_level_stats && (
                  <div className="bg-white p-6 rounded-lg shadow">
                    <h3 className="text-lg font-semibold mb-4">Grade Distribution</h3>
                    <ResponsiveContainer width="100%" height={300}>
                      <PieChart>
                        <Pie
                          data={[
                            { name: 'Excellent (90%+)', value: performanceData.grade_level_stats.excellent, color: '#10B981' },
                            { name: 'Good (75-89%)', value: performanceData.grade_level_stats.good, color: '#3B82F6' },
                            { name: 'Average (60-74%)', value: performanceData.grade_level_stats.average, color: '#F59E0B' },
                            { name: 'Below Average (<60%)', value: performanceData.grade_level_stats.below_average, color: '#EF4444' }
                          ]}
                          cx="50%"
                          cy="50%"
                          labelLine={false}
                          outerRadius={80}
                          fill="#8884d8"
                          dataKey="value"
                        >
                          {performanceData.grade_level_stats && 
                            Object.values(performanceData.grade_level_stats).map((entry, index) => (
                              <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                            ))
                          }
                        </Pie>
                        <Tooltip />
                        <Legend />
                      </PieChart>
                    </ResponsiveContainer>
                  </div>
                )}
              </div>

              {/* Side Panel */}
              <div className="space-y-6">
                {/* Top Performers */}
                {(performanceData.top_performers || (performanceData.sections_summary && performanceData.sections_summary[0]?.top_performers)) && (
                  <div className="bg-white p-6 rounded-lg shadow">
                    <div className="flex items-center gap-2 mb-4">
                      <Award className="w-5 h-5 text-yellow-500" />
                      <h3 className="text-lg font-semibold">Top Performers</h3>
                    </div>
                    <div className="space-y-3">
                      {(performanceData.top_performers || performanceData.sections_summary?.[0]?.top_performers || []).slice(0, 5).map((student) => (
                        <div
                          key={student.id}
                          className="flex items-center justify-between p-3 bg-green-50 rounded-lg cursor-pointer hover:bg-green-100 transition-colors"
                          onClick={() => openStudentDetail(student.id)}
                        >
                          <div>
                            <p className="font-medium text-green-800">{student.name}</p>
                            <p className="text-sm text-green-600">{student.section_name}</p>
                          </div>
                          <div className="text-right">
                            <p className="font-bold text-green-800">{student.average_score}%</p>
                            <p className="text-sm text-green-600">{student.status}</p>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {/* Low Performers - Need Attention */}
                {(performanceData.low_performers || (performanceData.sections_summary && performanceData.sections_summary[0]?.low_performers)) && (
                  <div className="bg-white p-6 rounded-lg shadow">
                    <div className="flex items-center gap-2 mb-4">
                      <AlertTriangle className="w-5 h-5 text-red-500" />
                      <h3 className="text-lg font-semibold">Need Attention</h3>
                    </div>
                    <div className="space-y-3">
                      {(performanceData.low_performers || performanceData.sections_summary?.[0]?.low_performers || []).slice(0, 5).map((student) => (
                        <div
                          key={student.id}
                          className="flex items-center justify-between p-3 bg-red-50 rounded-lg cursor-pointer hover:bg-red-100 transition-colors"
                          onClick={() => openStudentDetail(student.id)}
                        >
                          <div>
                            <p className="font-medium text-red-800">{student.name}</p>
                            <p className="text-sm text-red-600">{student.section_name}</p>
                          </div>
                          <div className="text-right">
                            <p className="font-bold text-red-800">{student.average_score}%</p>
                            <p className="text-sm text-red-600">{student.status}</p>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {/* Quick Filters (for filtered view) */}
                {activeView === 'filtered' && (
                  <div className="bg-white p-6 rounded-lg shadow">
                    <h3 className="text-lg font-semibold mb-4">Quick Filters</h3>
                    <div className="space-y-4">
                      <div>
                        <label className="block text-sm font-medium text-gray-700 mb-1">
                          Minimum Score Threshold
                        </label>
                        <input
                          type="number"
                          min="0"
                          max="100"
                          value={filters.performance_threshold || ''}
                          onChange={(e) => handleFilterChange('performance_threshold', e.target.value ? parseFloat(e.target.value) : null)}
                          className="w-full px-3 py-2 border border-gray-300 rounded-lg"
                          placeholder="e.g., 75"
                        />
                      </div>
                      
                      <div>
                        <label className="block text-sm font-medium text-gray-700 mb-1">
                          Select Sections
                        </label>
                        <select
                          multiple
                          value={filters.section_ids || []}
                          onChange={(e) => {
                            const values = Array.from(e.target.selectedOptions, option => parseInt(option.value));
                            handleFilterChange('section_ids', values.length > 0 ? values : null);
                          }}
                          className="w-full px-3 py-2 border border-gray-300 rounded-lg"
                        >
                          {sections.map(section => (
                            <option key={section.id} value={section.id}>
                              {section.name}
                            </option>
                          ))}
                        </select>
                      </div>
                    </div>
                  </div>
                )}
              </div>
            </div>

            {/* Students Table (for filtered view) */}
            {activeView === 'filtered' && performanceData.students && (
              <div className="bg-white p-6 rounded-lg shadow">
                <h3 className="text-lg font-semibold mb-4">
                  Student Performance ({performanceData.total_count} students)
                </h3>
                <div className="overflow-x-auto">
                  <table className="min-w-full table-auto">
                    <thead>
                      <tr className="bg-gray-50">
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                          Student
                        </th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                          Section
                        </th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                          Average Score
                        </th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                          Status
                        </th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                          Subjects
                        </th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                          Actions
                        </th>
                      </tr>
                    </thead>
                    <tbody className="bg-white divide-y divide-gray-200">
                      {performanceData.students.map((student) => (
                        <tr key={student.id} className="hover:bg-gray-50">
                          <td className="px-6 py-4 whitespace-nowrap">
                            <div>
                              <div className="text-sm font-medium text-gray-900">{student.name}</div>
                              <div className="text-sm text-gray-500">{student.student_id}</div>
                            </div>
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                            {student.section_name}
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap">
                            <div className="flex items-center">
                              <span className={`text-sm font-medium ${
                                student.average_score >= 90 ? 'text-green-600' :
                                student.average_score >= 75 ? 'text-blue-600' :
                                student.average_score >= 60 ? 'text-yellow-600' : 'text-red-600'
                              }`}>
                                {student.average_score}%
                              </span>
                            </div>
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap">
                            <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${
                              student.status === 'Pass' 
                                ? 'bg-green-100 text-green-800' 
                                : 'bg-red-100 text-red-800'
                            }`}>
                              {student.status}
                            </span>
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                            {student.passed_subjects}/{student.total_subjects}
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
                            <button
                              onClick={() => openStudentDetail(student.id)}
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
            )}
          </div>
        )}
      </div>

      {/* Student Detail Modal */}
      {selectedStudent && (
        <StudentDetailModal 
          student={selectedStudent} 
          onClose={() => setSelectedStudent(null)} 
        />
      )}
    </div>
  );
};

// Stat Card Component
const StatCard = ({ title, value, icon: Icon, color }) => {
  const colorClasses = {
    blue: 'bg-blue-500 text-white',
    green: 'bg-green-500 text-white',
    yellow: 'bg-yellow-500 text-white',
    purple: 'bg-purple-500 text-white',
    red: 'bg-red-500 text-white'
  };

  return (
    <div className="bg-white p-6 rounded-lg shadow">
      <div className="flex items-center">
        <div className={`p-3 rounded-lg ${colorClasses[color]} mr-4`}>
          <Icon className="w-6 h-6" />
        </div>
        <div>
          <p className="text-sm text-gray-600">{title}</p>
          <p className="text-2xl font-bold text-gray-900">{value}</p>
        </div>
      </div>
    </div>
  );
};

// Student Detail Modal Component
const StudentDetailModal = ({ student, onClose }) => {
  return (
    <div className="fixed inset-0 bg-gray-600 bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg shadow-xl max-w-4xl w-full mx-4 max-h-[90vh] overflow-y-auto">
        <div className="px-6 py-4 border-b border-gray-200 flex items-center justify-between">
          <h2 className="text-xl font-semibold text-gray-900">
            Student Performance Details
          </h2>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600"
          >
            <span className="sr-only">Close</span>
            ✕
          </button>
        </div>
        
        <div className="px-6 py-4">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-6">
            <div>
              <h3 className="text-lg font-medium text-gray-900 mb-2">Student Information</h3>
              <div className="space-y-2">
                <p><span className="font-medium">Name:</span> {student.name}</p>
                <p><span className="font-medium">Student ID:</span> {student.student_id}</p>
                <p><span className="font-medium">Section:</span> {student.section_name}</p>
                <p><span className="font-medium">Email:</span> {student.email}</p>
              </div>
            </div>
            
            <div>
              <h3 className="text-lg font-medium text-gray-900 mb-2">Performance Summary</h3>
              <div className="space-y-2">
                <p><span className="font-medium">Average Score:</span> {student.average_score}%</p>
                <p><span className="font-medium">Status:</span> 
                  <span className={`ml-1 px-2 py-1 text-xs font-semibold rounded-full ${
                    student.status === 'Pass' 
                      ? 'bg-green-100 text-green-800' 
                      : 'bg-red-100 text-red-800'
                  }`}>
                    {student.status}
                  </span>
                </p>
                <p><span className="font-medium">Total Subjects:</span> {student.total_subjects}</p>
                <p><span className="font-medium">Passed:</span> {student.passed_subjects}</p>
                <p><span className="font-medium">Failed:</span> {student.failed_subjects}</p>
              </div>
            </div>
          </div>
          
          <div>
            <h3 className="text-lg font-medium text-gray-900 mb-4">Subject-wise Performance</h3>
            <div className="overflow-x-auto">
              <table className="min-w-full table-auto">
                <thead>
                  <tr className="bg-gray-50">
                    <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase">Subject</th>
                    <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase">Code</th>
                    <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase">Marks</th>
                    <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase">Percentage</th>
                    <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase">Grade</th>
                    <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase">Status</th>
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-200">
                  {student.subject_grades?.map((grade, index) => (
                    <tr key={index}>
                      <td className="px-4 py-2 text-sm text-gray-900">{grade.subject_name}</td>
                      <td className="px-4 py-2 text-sm text-gray-900">{grade.subject_code}</td>
                      <td className="px-4 py-2 text-sm text-gray-900">
                        {grade.marks_obtained}/{grade.total_marks}
                      </td>
                      <td className="px-4 py-2 text-sm text-gray-900">{grade.percentage?.toFixed(1)}%</td>
                      <td className="px-4 py-2 text-sm text-gray-900">{grade.grade_letter}</td>
                      <td className="px-4 py-2">
                        <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${
                          grade.is_passed ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'
                        }`}>
                          {grade.is_passed ? 'Pass' : 'Fail'}
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>
        
        <div className="px-6 py-4 border-t border-gray-200 flex justify-end">
          <button
            onClick={() => setSelectedStudent(null)}
            className="px-4 py-2 bg-gray-300 text-gray-700 rounded-lg hover:bg-gray-400 transition-colors"
          >
            Close
          </button>
        </div>
      </div>
    </div>
  ) : null}

      {/* Reports History Section */}
      {showReportsHistory && (
        <div className="mt-8">
          <SentReportsHistory 
            sentReports={sentReports}
            onRefresh={fetchSentReports}
          />
        </div>
      )}

      {/* Send Report Modal */}
      <SendReportModal
        isOpen={showSendReportModal}
        onClose={() => setShowSendReportModal(false)}
        onSendReport={handleSendReport}
      />
      
      </div>
    </div>
  );
};

export default EnhancedPerformanceViews;