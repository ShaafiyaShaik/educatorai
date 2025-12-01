import React, { useState, useEffect, useRef } from 'react';
import { 
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
  PieChart, Pie, Cell, LineChart, Line, Legend
} from 'recharts';
import { 
  Users, TrendingUp, Award, AlertTriangle, Download, Filter,
  BookOpen, GraduationCap, Target, BarChart3, Send, Wifi, WifiOff
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

  // Real-time WebSocket state
  const [wsConnected, setWsConnected] = useState(false);
  const [lastUpdate, setLastUpdate] = useState(null);
  const wsRef = useRef(null);
  const educatorIdRef = useRef(null);

  useEffect(() => {
    fetchInitialData();
    return () => {
      // Cleanup WebSocket on component unmount
      if (wsRef.current) {
        wsRef.current.close();
      }
    };
  }, []);

  useEffect(() => {
    if (activeView) {
      fetchPerformanceData();
    }
  }, [activeView, filters]);

  // Initialize WebSocket connection for real-time updates
  useEffect(() => {
    const token = localStorage.getItem('token');
    if (!token || !educatorIdRef.current) return;

    const connectWebSocket = () => {
      try {
        // Use wss if the API base is https
        const wsBase = API_BASE_URL.replace(/^http/, 'ws');
        const wsUrl = `${wsBase}/ws/performance/${educatorIdRef.current}`;
        wsRef.current = new WebSocket(wsUrl);

        wsRef.current.onopen = () => {
          console.log('WebSocket connected for real-time performance updates');
          setWsConnected(true);
        };

        wsRef.current.onmessage = (event) => {
          try {
            const updatedData = JSON.parse(event.data);
            console.log('Received real-time performance update:', updatedData);
            setPerformanceData(updatedData);
            setLastUpdate(new Date().toLocaleTimeString());
          } catch (error) {
            console.error('Error parsing WebSocket message:', error);
          }
        };

        wsRef.current.onclose = () => {
          console.log('WebSocket disconnected');
          setWsConnected(false);
          // Attempt to reconnect after 5 seconds
          setTimeout(connectWebSocket, 5000);
        };

        wsRef.current.onerror = (error) => {
          console.error('WebSocket error:', error);
          setWsConnected(false);
        };
      } catch (error) {
        console.error('Failed to establish WebSocket connection:', error);
        setWsConnected(false);
      }
    };

    connectWebSocket();

    return () => {
      if (wsRef.current) {
        wsRef.current.close();
      }
    };
  }, [educatorIdRef.current]);

  const fetchInitialData = async () => {
    try {
      const token = localStorage.getItem('token');
      const headers = { 'Authorization': `Bearer ${token}` };

      // Fetch sections and subjects for filters, and current educator info for WebSocket
      const [sectionsRes, dashboardRes] = await Promise.all([
        axios.get(`${API_BASE_URL}/api/v1/students/sections`, { headers }),
        axios.get(`${API_BASE_URL}/api/v1/dashboard/dashboard`, { headers })
      ]);

      setSections(sectionsRes.data.sections || []);
      
      // Store educator ID for WebSocket connection
      if (dashboardRes.data && dashboardRes.data.educator_id) {
        educatorIdRef.current = dashboardRes.data.educator_id;
      }
      
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
          endpoint = `${API_BASE_URL}/api/v1/performance/overview`;
          break;
        case 'filtered':
          endpoint = `${API_BASE_URL}/api/v1/performance/filtered`;
          break;
        default:
          endpoint = `${API_BASE_URL}/api/v1/performance/overview`;
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

  const fetchSentReports = async () => {
    try {
      const token = localStorage.getItem('token');
      const headers = { 'Authorization': `Bearer ${token}` };
      
      const response = await axios.get(`${API_BASE_URL}/api/v1/performance/sent-reports`, { headers });
      setSentReports(response.data);
    } catch (error) {
      console.error('Error fetching sent reports:', error);
    }
  };

  const handleSendReport = async (reportData) => {
    try {
      const token = localStorage.getItem('token');
      const headers = { 'Authorization': `Bearer ${token}` };
      
      const response = await axios.post(`${API_BASE_URL}/api/v1/performance/send-report`, reportData, { headers });
      
      if (response.data.success) {
        alert(`Report sent successfully! Generated ${response.data.report_count} reports.`);
        setShowSendReportModal(false);
        fetchSentReports(); // Refresh sent reports
      }
    } catch (error) {
      console.error('Error sending report:', error);
      alert('Error sending report. Please try again.');
    }
  };

  const fetchStudentDetails = async (studentId) => {
    try {
      const token = localStorage.getItem('token');
      const headers = { 'Authorization': `Bearer ${token}` };
      
      const response = await axios.get(`${API_BASE_URL}/api/v1/performance/student/${studentId}`, { headers });
      setSelectedStudent(response.data);
    } catch (error) {
      console.error('Error fetching student details:', error);
    }
  };

  const downloadReport = async (format) => {
    if (!performanceData) return;

    try {
      const token = localStorage.getItem('token');
      const headers = { 'Authorization': `Bearer ${token}` };

      const endpoint = activeView === 'filtered' 
        ? `${API_BASE_URL}/api/v1/performance/filtered-download`
        : `${API_BASE_URL}/api/v1/performance/overview-download`;

      let response;
      if (activeView === 'filtered') {
        response = await axios.post(endpoint, 
          { ...filters, format }, 
          { headers, responseType: 'blob' }
        );
      } else {
        response = await axios.get(`${endpoint}?format=${format}`, 
          { headers, responseType: 'blob' }
        );
      }

      const contentType = response.headers['content-type'];
      const fileExtension = format === 'pdf' ? 'pdf' : 'xlsx';
      
      const blob = new Blob([response.data], { type: contentType });
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `performance_${activeView}_${new Date().toISOString().split('T')[0]}.${fileExtension}`);
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(url);
    } catch (error) {
      console.error('Error downloading report:', error);
      alert('Error downloading report. Please try again.');
    }
  };

  const updateFilters = (newFilters) => {
    setFilters(prev => ({ ...prev, ...newFilters }));
  };

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-7xl mx-auto py-6 px-4">
        {/* Header */}
        <div className="bg-white rounded-lg shadow p-6 mb-6">
          <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
            <div>
              <h1 className="text-2xl font-bold text-gray-900 flex items-center gap-2">
                <BarChart3 className="w-6 h-6 text-blue-600" />
                Enhanced Performance Analytics
                {/* Real-time status indicator */}
                <div className={`ml-2 flex items-center gap-1 px-2 py-1 rounded-full text-xs ${
                  wsConnected ? 'bg-green-100 text-green-700' : 'bg-gray-100 text-gray-500'
                }`}>
                  {wsConnected ? <Wifi className="w-3 h-3" /> : <WifiOff className="w-3 h-3" />}
                  {wsConnected ? 'Live' : 'Offline'}
                </div>
              </h1>
              <p className="text-gray-600 mt-1">
                Comprehensive student performance analysis and reporting
                {lastUpdate && (
                  <span className="ml-2 text-sm text-green-600">
                    • Last updated: {lastUpdate}
                  </span>
                )}
              </p>
            </div>
            
            <div className="flex flex-wrap gap-2">
              <button
                onClick={() => setShowSendReportModal(true)}
                className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
              >
                <Send className="w-4 h-4" />
                Send Report
              </button>
              
              <button
                onClick={() => {
                  fetchSentReports();
                  setShowReportsHistory(!showReportsHistory);
                }}
                className="flex items-center gap-2 px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 transition-colors"
              >
                <BookOpen className="w-4 h-4" />
                Report History
              </button>
              
              <button
                onClick={() => downloadReport('pdf')}
                className="flex items-center gap-2 px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors"
                disabled={loading || !performanceData}
              >
                <Download className="w-4 h-4" />
                PDF
              </button>
              
              <button
                onClick={() => downloadReport('excel')}
                className="flex items-center gap-2 px-4 py-2 bg-orange-600 text-white rounded-lg hover:bg-orange-700 transition-colors"
                disabled={loading || !performanceData}
              >
                <Download className="w-4 h-4" />
                Excel
              </button>
            </div>
          </div>
        </div>

        {/* View Selector */}
        <div className="bg-white rounded-lg shadow p-6 mb-6">
          <div className="flex space-x-1 bg-gray-100 p-1 rounded-lg">
            {[
              { id: 'overall', label: 'Overall Performance', icon: Target },
              { id: 'filtered', label: 'Filtered Analysis', icon: Filter }
            ].map(view => (
              <button
                key={view.id}
                onClick={() => setActiveView(view.id)}
                className={`flex-1 flex items-center justify-center gap-2 px-4 py-2 rounded-md transition-all ${
                  activeView === view.id 
                    ? 'bg-blue-600 text-white shadow-sm' 
                    : 'text-gray-600 hover:text-gray-800'
                }`}
              >
                <view.icon className="w-4 h-4" />
                {view.label}
              </button>
            ))}
          </div>
        </div>

        {/* Filters - Only show for filtered view */}
        {activeView === 'filtered' && (
          <FilterPanel 
            filters={filters}
            sections={sections}
            subjects={subjects}
            onFiltersChange={updateFilters}
          />
        )}

        {/* Loading State */}
        {loading && (
          <div className="flex items-center justify-center py-12">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500"></div>
          </div>
        )}

        {/* Performance Data Display */}
        {!loading && performanceData && (
          <div className="space-y-6">
            <PerformanceOverview data={performanceData} />
            <ChartsSection data={performanceData} />
            <StudentsList 
              students={performanceData.students || []} 
              onStudentClick={fetchStudentDetails}
            />
          </div>
        )}

        {/* Student Detail Modal */}
        {selectedStudent && (
          <StudentDetailModal 
            student={selectedStudent} 
            onClose={() => setSelectedStudent(null)} 
          />
        )}

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

// Performance Overview Component
const PerformanceOverview = ({ data }) => {
  const stats = [
    {
      title: 'Total Students',
      value: data.total_students || 0,
      icon: Users,
      color: 'blue'
    },
    {
      title: 'Class Average',
      value: `${(data.overall_average || 0).toFixed(1)}%`,
      icon: Target,
      color: 'green'
    },
    {
      title: 'Top Performers',
      value: data.top_performers?.length || 0,
      icon: Award,
      color: 'yellow'
    },
    {
      title: 'Need Attention',
      value: data.low_performers?.length || 0,
      icon: AlertTriangle,
      color: 'red'
    }
  ];

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
      {stats.map((stat, index) => (
        <StatCard key={index} {...stat} />
      ))}
    </div>
  );
};

// Charts Section Component
const ChartsSection = ({ data }) => {
  // Transform grade_distribution object to array format for charts
  const gradeDistributionArray = Object.entries(data.grade_distribution || {}).map(([grade, count]) => ({
    grade,
    count: parseInt(count)
  }));

  return (
    <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
      {/* Grade Distribution Chart */}
      <div className="bg-white p-6 rounded-lg shadow">
        <h3 className="text-lg font-semibold mb-4">Grade Distribution</h3>
        <ResponsiveContainer width="100%" height={300}>
          <BarChart data={gradeDistributionArray}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="grade" />
            <YAxis />
            <Tooltip />
            <Bar dataKey="count" fill="#3B82F6" />
          </BarChart>
        </ResponsiveContainer>
        {gradeDistributionArray.length === 0 && (
          <div className="text-center text-gray-500 mt-4">No grade distribution data available</div>
        )}
      </div>

      {/* Subject Performance Chart */}
      <div className="bg-white p-6 rounded-lg shadow">
        <h3 className="text-lg font-semibold mb-4">Subject Performance</h3>
        <ResponsiveContainer width="100%" height={300}>
          <BarChart data={data.subject_performance_chart || []}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="subject_name" />
            <YAxis />
            <Tooltip />
            <Bar dataKey="average_score" fill="#10B981" name="Average Score %" />
            <Bar dataKey="pass_rate" fill="#F59E0B" name="Pass Rate %" />
          </BarChart>
        </ResponsiveContainer>
        {(!data.subject_performance_chart || data.subject_performance_chart.length === 0) && (
          <div className="text-center text-gray-500 mt-4">No subject performance data available</div>
        )}
      </div>

      {/* Section Performance Chart */}
      <div className="bg-white p-6 rounded-lg shadow">
        <h3 className="text-lg font-semibold mb-4">Section Performance Comparison</h3>
        <ResponsiveContainer width="100%" height={300}>
          <BarChart data={data.sections_performance_chart || []}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="section_name" />
            <YAxis />
            <Tooltip />
            <Legend />
            <Bar dataKey="average_score" fill="#3B82F6" name="Average Score %" />
            <Bar dataKey="pass_rate" fill="#10B981" name="Pass Rate %" />
          </BarChart>
        </ResponsiveContainer>
        {(!data.sections_performance_chart || data.sections_performance_chart.length === 0) && (
          <div className="text-center text-gray-500 mt-4">No section performance data available</div>
        )}
      </div>

      {/* Monthly Trends Chart */}
      {data.monthly_trends && data.monthly_trends.length > 0 && (
        <div className="bg-white p-6 rounded-lg shadow">
          <h3 className="text-lg font-semibold mb-4">Monthly Performance Trends</h3>
          <ResponsiveContainer width="100%" height={300}>
            <LineChart data={data.monthly_trends}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="month" />
              <YAxis />
              <Tooltip />
              <Legend />
              <Line type="monotone" dataKey="average_score" stroke="#3B82F6" strokeWidth={2} name="Average Score %" />
              <Line type="monotone" dataKey="pass_rate" stroke="#10B981" strokeWidth={2} name="Pass Rate %" />
            </LineChart>
          </ResponsiveContainer>
        </div>
      )}

      {/* Attendance Statistics */}
      {data.attendance_stats && Object.keys(data.attendance_stats).length > 0 && (
        <div className="bg-white p-6 rounded-lg shadow">
          <h3 className="text-lg font-semibold mb-4">Attendance Statistics</h3>
          <div className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <div className="text-center">
                <p className="text-2xl font-bold text-green-600">{data.attendance_stats.average_attendance?.toFixed(1) || 0}%</p>
                <p className="text-sm text-gray-600">Average Attendance</p>
              </div>
              <div className="text-center">
                <p className="text-2xl font-bold text-blue-600">{data.attendance_stats.total_classes || 0}</p>
                <p className="text-sm text-gray-600">Total Classes</p>
              </div>
            </div>
            <div className="grid grid-cols-3 gap-2 text-sm">
              <div className="text-center p-2 bg-green-50 rounded">
                <p className="font-semibold text-green-800">{data.attendance_stats.excellent_attendance || 0}</p>
                <p className="text-green-600">Excellent (90%+)</p>
              </div>
              <div className="text-center p-2 bg-yellow-50 rounded">
                <p className="font-semibold text-yellow-800">{data.attendance_stats.good_attendance || 0}</p>
                <p className="text-yellow-600">Good (75-89%)</p>
              </div>
              <div className="text-center p-2 bg-red-50 rounded">
                <p className="font-semibold text-red-800">{data.attendance_stats.poor_attendance || 0}</p>
                <p className="text-red-600">Poor (&lt;75%)</p>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

// Filter Panel Component
const FilterPanel = ({ filters, sections, subjects, onFiltersChange }) => {
  return (
    <div className="bg-white rounded-lg shadow p-6 mb-6">
      <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
        <Filter className="w-5 h-5" />
        Performance Filters
      </h3>
      
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {/* Sort By */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">Sort By</label>
          <select
            value={filters.sort_by}
            onChange={(e) => onFiltersChange({ sort_by: e.target.value })}
            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
          >
            <option value="average">Average Score</option>
            <option value="total">Total Marks</option>
            <option value="name">Name</option>
          </select>
        </div>

        {/* Sort Order */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">Order</label>
          <select
            value={filters.sort_order}
            onChange={(e) => onFiltersChange({ sort_order: e.target.value })}
            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
          >
            <option value="desc">Descending</option>
            <option value="asc">Ascending</option>
          </select>
        </div>

        {/* Performance Threshold */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">Min Score (%)</label>
          <input
            type="number"
            min="0"
            max="100"
            value={filters.performance_threshold || ''}
            onChange={(e) => onFiltersChange({ 
              performance_threshold: e.target.value ? parseInt(e.target.value) : null 
            })}
            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            placeholder="e.g., 75"
          />
        </div>
      </div>

      {/* Performer Counts */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mt-4">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">Top Performers Count</label>
          <input
            type="number"
            min="1"
            max="50"
            value={filters.top_count}
            onChange={(e) => onFiltersChange({ top_count: parseInt(e.target.value) || 5 })}
            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">Low Performers Count</label>
          <input
            type="number"
            min="1"
            max="50"
            value={filters.low_count}
            onChange={(e) => onFiltersChange({ low_count: parseInt(e.target.value) || 5 })}
            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
          />
        </div>
      </div>
    </div>
  );
};

// Students List Component
const StudentsList = ({ students, onStudentClick }) => {
  if (!students || students.length === 0) {
    return (
      <div className="bg-white rounded-lg shadow p-6 text-center">
        <Users className="w-12 h-12 mx-auto text-gray-400 mb-4" />
        <p className="text-gray-600">No students found</p>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-lg shadow">
      <div className="px-6 py-4 border-b border-gray-200">
        <h3 className="text-lg font-semibold text-gray-900">Student Performance Details</h3>
      </div>
      
      <div className="overflow-x-auto">
        <table className="min-w-full divide-y divide-gray-200">
          <thead className="bg-gray-50">
            <tr>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Student
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Section
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Average
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Grade
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Status
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Actions
              </th>
            </tr>
          </thead>
          <tbody className="bg-white divide-y divide-gray-200">
            {students.map((student, index) => (
              <tr key={student.student_id || index} className="hover:bg-gray-50">
                <td className="px-6 py-4 whitespace-nowrap">
                  <div className="flex items-center">
                    <div className="flex-shrink-0 h-8 w-8">
                      <div className="h-8 w-8 rounded-full bg-gray-300 flex items-center justify-center">
                        <span className="text-sm font-medium text-gray-700">
                          {student.name?.charAt(0) || 'S'}
                        </span>
                      </div>
                    </div>
                    <div className="ml-4">
                      <div className="text-sm font-medium text-gray-900">{student.name}</div>
                      <div className="text-sm text-gray-500">{student.student_id}</div>
                    </div>
                  </div>
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                  {student.section_name}
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                  {student.average_percentage?.toFixed(1)}%
                </td>
                <td className="px-6 py-4 whitespace-nowrap">
                  <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${
                    student.overall_grade === 'A' ? 'bg-green-100 text-green-800' :
                    student.overall_grade === 'B' ? 'bg-blue-100 text-blue-800' :
                    student.overall_grade === 'C' ? 'bg-yellow-100 text-yellow-800' :
                    'bg-red-100 text-red-800'
                  }`}>
                    {student.overall_grade}
                  </span>
                </td>
                <td className="px-6 py-4 whitespace-nowrap">
                  <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${
                    student.is_passed ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'
                  }`}>
                    {student.is_passed ? 'Pass' : 'Fail'}
                  </span>
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
                  <button
                    onClick={() => onStudentClick(student.student_id)}
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
                <p><span className="font-medium">Overall Average:</span> {student.average_percentage?.toFixed(1)}%</p>
                <p><span className="font-medium">Overall Grade:</span> {student.overall_grade}</p>
              </div>
            </div>
            
            <div>
              <h3 className="text-lg font-medium text-gray-900 mb-2">Performance Summary</h3>
              <div className="space-y-2">
                <p><span className="font-medium">Total Marks:</span> {student.total_marks_obtained}/{student.total_marks_possible}</p>
                <p><span className="font-medium">Subjects:</span> {student.subject_grades?.length || 0}</p>
                <p><span className="font-medium">Status:</span> 
                  <span className={`ml-2 inline-flex px-2 py-1 text-xs font-semibold rounded-full ${
                    student.is_passed ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'
                  }`}>
                    {student.is_passed ? 'Pass' : 'Fail'}
                  </span>
                </p>
              </div>
            </div>
          </div>

          <div>
            <h3 className="text-lg font-medium text-gray-900 mb-4">Subject-wise Performance</h3>
            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-gray-200">
                <thead className="bg-gray-50">
                  <tr>
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
            onClick={onClose}
            className="px-4 py-2 bg-gray-300 text-gray-700 rounded-lg hover:bg-gray-400 transition-colors"
          >
            Close
          </button>
        </div>
      </div>
    </div>
  );
};

export default EnhancedPerformanceViews;