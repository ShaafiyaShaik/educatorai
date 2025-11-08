import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';

const StudentManagement = () => {
  const [sections, setSections] = useState([]);
  const [selectedSection, setSelectedSection] = useState(null);
  const [students, setStudents] = useState([]);
  const [filteredStudents, setFilteredStudents] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [filters, setFilters] = useState({
    search: '',
    passStatus: '',
    subjectFilter: ''
  });
  const [showStudentModal, setShowStudentModal] = useState(false);
  const [selectedStudent, setSelectedStudent] = useState(null);
  const navigate = useNavigate();

  useEffect(() => {
    fetchSections();
  }, []);

  useEffect(() => {
    if (selectedSection) {
      fetchStudents();
    }
  }, [selectedSection, filters]);

  const fetchSections = async () => {
    try {
      const token = localStorage.getItem('token');
      console.log('Fetching sections with token:', token ? 'Present' : 'Missing');
      
      if (!token) {
        setError('No authentication token found. Please log in again.');
        navigate('/login');
        return;
      }
      
      // Try both ports
      const baseUrls = ['http://localhost:8003', 'http://localhost:8001', 'http://localhost:8002'];
      let response = null;
      
      for (const baseUrl of baseUrls) {
        try {
          response = await axios.get(`${baseUrl}/api/v1/students/sections`, {
            headers: { 'Authorization': `Bearer ${token}` }
          });
          console.log(`Successfully connected to ${baseUrl}`);
          // Store the working base URL for future requests
          window.API_BASE_URL = baseUrl;
          break;
        } catch (err) {
          console.log(`Failed to connect to ${baseUrl}:`, err.message);
          continue;
        }
      }
      
      if (!response) {
        throw new Error('Could not connect to any API server');
      }
      
      console.log('Sections response:', response.data);
      setSections(response.data);
      
      if (response.data.length > 0) {
        setSelectedSection(response.data[0]);
      } else {
        setError('No sections found');
      }
    } catch (error) {
      console.error('Error fetching sections:', error);
      if (error.response?.status === 401) {
        setError('Authentication failed. Please log in again.');
        localStorage.removeItem('token');
        navigate('/login');
      } else {
        setError('Failed to load sections: ' + (error.response?.data?.detail || error.message));
      }
    }
  };

  const fetchStudents = async () => {
    if (!selectedSection) return;
    
    setLoading(true);
    try {
      const token = localStorage.getItem('token');
      console.log('Fetching students for section:', selectedSection, 'with token:', token ? 'Present' : 'Missing');
      
      if (!token) {
        setError('No authentication token found. Please log in again.');
        navigate('/login');
        return;
      }
      
      const params = new URLSearchParams();
      
      if (filters.search) params.append('search', filters.search);
      if (filters.passStatus) params.append('pass_status', filters.passStatus);
      if (filters.subjectFilter) params.append('subject_filter', filters.subjectFilter);
      
      // Use the base URL that worked for sections, or try both
      const baseUrl = window.API_BASE_URL || 'http://localhost:8003';
      const url = `${baseUrl}/api/v1/students/sections/${selectedSection.id}/students/filtered?${params}`;
      console.log('Fetching students from URL:', url);
      
      const response = await axios.get(url, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      
      console.log('Students response:', response.data);
      setStudents(response.data);
      setFilteredStudents(response.data);
      setError(null);
    } catch (error) {
      console.error('Error fetching students:', error);
      if (error.response?.status === 401) {
        setError('Authentication failed. Please log in again.');
        localStorage.removeItem('token');
        navigate('/login');
      } else {
        setError('Failed to load students: ' + (error.response?.data?.detail || error.message));
      }
      setStudents([]);
      setFilteredStudents([]);
    } finally {
      setLoading(false);
    }
  };

  const handleFilterChange = (filterType, value) => {
    setFilters(prev => ({
      ...prev,
      [filterType]: value
    }));
  };

  const viewStudentProfile = async (student) => {
    try {
      const token = localStorage.getItem('token');
      const response = await axios.get(
        `http://localhost:8003/api/v1/students/students/${student.id}/profile`,
        { headers: { 'Authorization': `Bearer ${token}` } }
      );
      setSelectedStudent(response.data);
      setShowStudentModal(true);
    } catch (error) {
      console.error('Error fetching student profile:', error);
      setError('Failed to load student profile');
    }
  };

  const sendMessage = (student) => {
    // Open Bulk Notification modal with this student preselected
    try {
      const pre = [{ id: student.id, name: student.full_name || `${student.first_name} ${student.last_name}`, first_name: student.first_name, last_name: student.last_name, email: student.email }];
      localStorage.setItem('preselectedUsers', JSON.stringify(pre));
      window.location.reload();
    } catch (e) {
      console.error('Failed to open bulk notifications with preselected student', e);
      alert('Failed to open bulk notifications');
    }
  };

  const getGradeColor = (percentage) => {
    if (percentage >= 85) return 'text-green-600';
    if (percentage >= 70) return 'text-blue-600';
    if (percentage >= 60) return 'text-yellow-600';
    return 'text-red-600';
  };

  const getPassStatusBadge = (isPassed) => {
    return isPassed ? (
      <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-800">
        Passed
      </span>
    ) : (
      <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-red-100 text-red-800">
        Failed
      </span>
    );
  };

  return (
    <div className="max-w-7xl mx-auto p-6">
      <div className="mb-6">
        <h1 className="text-3xl font-bold text-gray-900">Student Management</h1>
        <p className="text-gray-600 mt-2">Manage students across your sections</p>
      </div>

      {/* Section Selection */}
      <div className="mb-6">
        <label className="block text-sm font-medium text-gray-700 mb-2">
          Select Section
        </label>
        <select
          value={selectedSection?.id || ''}
          onChange={(e) => {
            const section = sections.find(s => s.id === parseInt(e.target.value));
            setSelectedSection(section);
          }}
          className="block w-full md:w-64 px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
        >
          {sections.map(section => (
            <option key={section.id} value={section.id}>
              {section.name} ({section.student_count} students)
            </option>
          ))}
        </select>
      </div>

      {/* Filters */}
      <div className="bg-white p-4 rounded-lg shadow mb-6">
        <h3 className="text-lg font-medium text-gray-900 mb-4">Filters</h3>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {/* Search */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Search by Name
            </label>
            <input
              type="text"
              value={filters.search}
              onChange={(e) => handleFilterChange('search', e.target.value)}
              placeholder="Enter student name..."
              className="block w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-blue-500 focus:border-blue-500"
            />
          </div>

          {/* Pass/Fail Status */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Pass Status
            </label>
            <select
              value={filters.passStatus}
              onChange={(e) => handleFilterChange('passStatus', e.target.value)}
              className="block w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-blue-500 focus:border-blue-500"
            >
              <option value="">All Students</option>
              <option value="passed">Passed</option>
              <option value="failed">Failed</option>
            </select>
          </div>

          {/* Subject Performance */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Subject Performance
            </label>
            <select
              value={filters.subjectFilter}
              onChange={(e) => handleFilterChange('subjectFilter', e.target.value)}
              className="block w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-blue-500 focus:border-blue-500"
            >
              <option value="">All</option>
              <option value="Math<40">Math &lt; 40%</option>
              <option value="Science<40">Science &lt; 40%</option>
              <option value="English<40">English &lt; 40%</option>
              <option value="Math>=80">Math ≥ 80%</option>
              <option value="Science>=80">Science ≥ 80%</option>
              <option value="English>=80">English ≥ 80%</option>
            </select>
          </div>
        </div>
      </div>

      {/* Students List */}
      {loading ? (
        <div className="text-center py-8">
          <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
          <p className="mt-2 text-gray-600">Loading students...</p>
        </div>
      ) : error ? (
        <div className="bg-red-50 border border-red-200 rounded-md p-4">
          <p className="text-red-600">{error}</p>
          <button
            onClick={fetchStudents}
            className="mt-2 text-sm text-red-600 hover:text-red-800 underline"
          >
            Try again
          </button>
        </div>
      ) : (
        <div className="bg-white shadow rounded-lg overflow-hidden">
          <div className="px-4 py-5 sm:p-6">
            <h3 className="text-lg font-medium text-gray-900 mb-4">
              Students in {selectedSection?.name} ({filteredStudents.length} students)
            </h3>
            
            {filteredStudents.length === 0 ? (
              <p className="text-gray-500 text-center py-8">No students found matching the current filters</p>
            ) : (
              <div className="overflow-x-auto">
                <table className="min-w-full divide-y divide-gray-200">
                  <thead className="bg-gray-50">
                    <tr>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Student
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Overall Average
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
                    {filteredStudents.map((student) => (
                      <tr key={student.id} className="hover:bg-gray-50">
                        <td className="px-6 py-4 whitespace-nowrap">
                          <div className="flex items-center">
                            <div className="flex-shrink-0 h-10 w-10">
                              <div className="h-10 w-10 rounded-full bg-blue-100 flex items-center justify-center">
                                <span className="text-sm font-medium text-blue-600">
                                  {student.first_name[0]}{student.last_name[0]}
                                </span>
                              </div>
                            </div>
                            <div className="ml-4">
                              <div className="text-sm font-medium text-gray-900">
                                {student.full_name}
                              </div>
                              <div className="text-sm text-gray-500">
                                {student.student_id}
                              </div>
                            </div>
                          </div>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap">
                          <span className={`text-sm font-medium ${getGradeColor(student.overall_average)}`}>
                            {student.overall_average}%
                          </span>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap">
                          {getPassStatusBadge(student.is_overall_passed)}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                          {student.passed_subjects}/{student.total_subjects} passed
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
                          <div className="flex space-x-2">
                            <button
                              onClick={() => viewStudentProfile(student)}
                              className="text-blue-600 hover:text-blue-900"
                            >
                              View Profile
                            </button>
                            <button
                              onClick={() => sendMessage(student)}
                              className="text-green-600 hover:text-green-900"
                            >
                              Message
                            </button>
                          </div>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Student Profile Modal */}
      {showStudentModal && selectedStudent && (
        <StudentProfileModal
          student={selectedStudent}
          onClose={() => {
            setShowStudentModal(false);
            setSelectedStudent(null);
          }}
        />
      )}
    </div>
  );
};

// Student Profile Modal Component
const StudentProfileModal = ({ student, onClose }) => {
  return (
    <div className="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full z-50">
      <div className="relative top-20 mx-auto p-5 border w-11/12 md:w-3/4 lg:w-1/2 shadow-lg rounded-md bg-white">
        <div className="mt-3">
          {/* Header */}
          <div className="flex justify-between items-center mb-4">
            <h3 className="text-lg font-medium text-gray-900">
              Student Profile: {student.student.full_name}
            </h3>
            <button
              onClick={onClose}
              className="text-gray-400 hover:text-gray-600"
            >
              <svg className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>

          {/* Student Info */}
          <div className="mb-6">
            <div className="bg-gray-50 p-4 rounded-lg">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <p className="text-sm font-medium text-gray-500">Student ID</p>
                  <p className="text-sm text-gray-900">{student.student.student_id}</p>
                </div>
                <div>
                  <p className="text-sm font-medium text-gray-500">Email</p>
                  <p className="text-sm text-gray-900">{student.student.email}</p>
                </div>
                <div>
                  <p className="text-sm font-medium text-gray-500">Overall Average</p>
                  <p className="text-sm text-gray-900">{student.student.overall_average}%</p>
                </div>
                <div>
                  <p className="text-sm font-medium text-gray-500">Status</p>
                  <p className="text-sm text-gray-900">
                    {student.student.is_overall_passed ? 'Passed' : 'Failed'}
                  </p>
                </div>
              </div>
            </div>
          </div>

          {/* Academic Performance */}
          <div className="mb-6">
            <h4 className="text-md font-medium text-gray-900 mb-3">Academic Performance</h4>
            <div className="space-y-2">
              {student.student.grades.map((grade) => (
                <div key={grade.id} className="flex justify-between items-center p-2 bg-gray-50 rounded">
                  <span className="text-sm font-medium">{grade.subject_name}</span>
                  <div className="text-right">
                    <span className={`text-sm font-medium ${grade.percentage >= 70 ? 'text-green-600' : 'text-red-600'}`}>
                      {grade.percentage}% ({grade.grade_letter})
                    </span>
                    <div className="text-xs text-gray-500">
                      {grade.marks_obtained}/{grade.total_marks}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Attendance Summary */}
          <div className="mb-6">
            <h4 className="text-md font-medium text-gray-900 mb-3">Attendance Summary</h4>
            <div className="bg-gray-50 p-4 rounded-lg">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <p className="text-sm font-medium text-gray-500">Total Classes</p>
                  <p className="text-sm text-gray-900">{student.attendance_summary.total_classes}</p>
                </div>
                <div>
                  <p className="text-sm font-medium text-gray-500">Attendance Rate</p>
                  <p className="text-sm text-gray-900">{student.attendance_summary.attendance_percentage}%</p>
                </div>
              </div>
            </div>
          </div>

          {/* Recent Notifications */}
          <div className="mb-6">
            <h4 className="text-md font-medium text-gray-900 mb-3">Recent Notifications</h4>
            <div className="space-y-2">
              {student.notifications.map((notification) => (
                <div key={notification.id} className="p-3 bg-blue-50 rounded-lg">
                  <div className="flex justify-between items-start">
                    <div>
                      <p className="text-sm font-medium text-gray-900">{notification.title}</p>
                      <p className="text-sm text-gray-600">{notification.message}</p>
                    </div>
                    <span className={`text-xs px-2 py-1 rounded-full ${notification.is_read ? 'bg-gray-200 text-gray-600' : 'bg-blue-200 text-blue-800'}`}>
                      {notification.is_read ? 'Read' : 'Unread'}
                    </span>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Actions */}
          <div className="flex justify-end space-x-3">
            <button
              onClick={onClose}
              className="px-4 py-2 text-sm font-medium text-gray-700 bg-gray-200 rounded-md hover:bg-gray-300"
            >
              Close
            </button>
            <button
              onClick={() => {
                const s = student.student; // modal receives an object with `.student`
                const pre = [{ id: s.id, name: s.full_name || `${s.first_name} ${s.last_name}`, first_name: s.first_name, last_name: s.last_name, email: s.email }];
                localStorage.setItem('preselectedUsers', JSON.stringify(pre));
                window.location.reload();
              }}
              className="px-4 py-2 text-sm font-medium text-white bg-blue-600 rounded-md hover:bg-blue-700"
            >
              Send Message
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default StudentManagement;