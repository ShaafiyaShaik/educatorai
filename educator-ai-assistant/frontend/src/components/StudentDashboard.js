import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { StudentReportsView, ParentModeToggle } from './StudentDashboardReports';

const StudentDashboard = ({ studentData, onLogout }) => {
  const [activeTab, setActiveTab] = useState('profile');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [isParentMode, setIsParentMode] = useState(false);
  
  // Dashboard data states
  const [profile, setProfile] = useState(null);
  const [marks, setMarks] = useState(null);
  const [notifications, setNotifications] = useState([]);
  const [scheduledEvents, setScheduledEvents] = useState([]);
  const [contactForm, setContactForm] = useState({
    subject: '',
    message: '',
    recipient_educator_id: 1 // Default to first educator for now
  });

  // Report modal state
  const [showReportModal, setShowReportModal] = useState(false);
  const [selectedReport, setSelectedReport] = useState(null);

  // loadTabData is defined below; we intentionally omit it from deps to
  // avoid re-running when the function identity changes. ESLint would
  // normally warn here. This effect only needs to run when `activeTab`
  // changes.
  useEffect(() => {
    // Inline tab-loading logic to satisfy eslint hook dependency checks.
    const fetchForTab = async (tab) => {
      setLoading(true);
      setError('');

      try {
        // Set up axios defaults for student authentication
        const token = localStorage.getItem('studentToken');
        if (token) {
          axios.defaults.headers.common['Authorization'] = `Bearer ${token}`;
        }

        switch (tab) {
          case 'profile': {
            const response = await axios.get('http://localhost:8003/api/v1/student-dashboard/profile');
            setProfile(response.data);
            break;
          }
          case 'marks': {
            const response = await axios.get('http://localhost:8003/api/v1/student-dashboard/marks');
            setMarks(response.data);
            break;
          }
          case 'notifications': {
            const response = await axios.get('http://localhost:8003/api/v1/student-dashboard/notifications');
            setNotifications(response.data);
            break;
          }
          case 'schedule': {
            const response = await axios.get('http://localhost:8003/api/v1/student-dashboard/scheduled-events');
            setScheduledEvents(response.data);
            break;
          }
          default:
            break;
        }
      } catch (err) {
        console.error(`Error loading ${tab} data:`, err);
        setError(`Failed to load ${tab} data`);
      } finally {
        setLoading(false);
      }
    };

    fetchForTab(activeTab);
  }, [activeTab]);

  // Previously loadTabData was a separate function. Logic is now inlined
  // inside the useEffect above to avoid hook dependency warnings.

  // Specific loaders were previously defined separately. Their logic
  // is now handled inline in the useEffect above.

  const handleContactSubmit = async (e) => {
    e.preventDefault();
    try {
      await axios.post('http://localhost:8003/api/v1/student-dashboard/contact-teacher', contactForm);
      alert('Message sent successfully!');
      setContactForm({
        subject: '',
        message: '',
        recipient_educator_id: 1
      });
    } catch (error) {
      console.error('Error sending message:', error);
      alert('Failed to send message');
    }
  };

  const handleViewReport = (notification) => {
    try {
      if (notification.report_data) {
        // report_data is already parsed by the backend
        setSelectedReport(notification.report_data);
        setShowReportModal(true);
      } else {
        alert('No structured report data available for this notification.');
      }
    } catch (error) {
      console.error('Error displaying report data:', error);
      alert('Error displaying report data.');
    }
  };

  const closeReportModal = () => {
    setShowReportModal(false);
    setSelectedReport(null);
  };

  const handleLogout = () => {
    localStorage.removeItem('studentToken');
    localStorage.removeItem('studentData');
    delete axios.defaults.headers.common['Authorization'];
    onLogout();
  };

  const getGradeColor = (grade) => {
    const gradeColors = {
      'A+': 'text-green-600 bg-green-100',
      'A': 'text-green-600 bg-green-100',
      'B+': 'text-blue-600 bg-blue-100',
      'B': 'text-blue-600 bg-blue-100',
      'C+': 'text-yellow-600 bg-yellow-100',
      'C': 'text-yellow-600 bg-yellow-100',
      'D+': 'text-orange-600 bg-orange-100',
      'D': 'text-orange-600 bg-orange-100',
      'F': 'text-red-600 bg-red-100'
    };
    return gradeColors[grade] || 'text-gray-600 bg-gray-100';
  };

  const formatDateTime = (dateTime) => {
    return new Date(dateTime).toLocaleString();
  };

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white shadow-sm border-b">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center py-4">
            <div className="flex items-center">
              <h1 className="text-2xl font-bold text-gray-900">Student Dashboard</h1>
              <span className="ml-4 px-3 py-1 bg-blue-100 text-blue-800 rounded-full text-sm">
                {studentData?.first_name} {studentData?.last_name}
              </span>
            </div>
            <button
              onClick={handleLogout}
              className="bg-red-500 hover:bg-red-600 text-white px-4 py-2 rounded-md text-sm font-medium transition-colors"
            >
              Logout
            </button>
          </div>
        </div>
      </header>

      {/* Navigation Tabs */}
      <nav className="bg-white border-b">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex space-x-8">
            {[
              { id: 'profile', label: 'Profile', icon: '👤' },
              { id: 'marks', label: 'Marks', icon: '📊' },
              { id: 'reports', label: 'Reports', icon: '📋' },
              { id: 'notifications', label: 'Notifications', icon: '🔔' },
              { id: 'schedule', label: 'Schedule', icon: '📅' },
              { id: 'contact', label: 'Contact Teacher', icon: '💬' }
            ].map((tab) => (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`py-4 px-2 border-b-2 font-medium text-sm ${
                  activeTab === tab.id
                    ? 'border-blue-500 text-blue-600'
                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                }`}
              >
                <span className="mr-2">{tab.icon}</span>
                {tab.label}
              </button>
            ))}
          </div>
        </div>
      </nav>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto py-6 sm:px-6 lg:px-8">
        <div className="px-4 py-6 sm:px-0">
          {error && (
            <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded mb-4">
              {error}
            </div>
          )}

          {loading && (
            <div className="text-center py-4">
              <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
              <p className="mt-2 text-gray-600">Loading...</p>
            </div>
          )}

          {/* Profile Tab */}
          {activeTab === 'profile' && profile && (
            <div className="bg-white shadow rounded-lg p-6">
              <h2 className="text-xl font-semibold mb-4">Student Profile</h2>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div>
                  <h3 className="font-medium text-gray-900 mb-3">Personal Information</h3>
                  <div className="space-y-2">
                    <p><span className="font-medium">Name:</span> {profile.name}</p>
                    <p><span className="font-medium">Student ID:</span> {profile.student_id}</p>
                    <p><span className="font-medium">Email:</span> {profile.email}</p>
                    <p><span className="font-medium">Roll Number:</span> {profile.roll_number}</p>
                    <p><span className="font-medium">Phone:</span> {profile.contact.phone || 'Not provided'}</p>
                  </div>
                </div>
                <div>
                  <h3 className="font-medium text-gray-900 mb-3">Academic Information</h3>
                  <div className="space-y-2">
                    <p><span className="font-medium">Section:</span> {profile.section.name}</p>
                    <p><span className="font-medium">Academic Year:</span> {profile.section.academic_year}</p>
                    <p><span className="font-medium">Semester:</span> {profile.section.semester}</p>
                    <p><span className="font-medium">Status:</span> 
                      <span className={`ml-2 px-2 py-1 rounded-full text-xs ${
                        profile.status === 'Active' ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'
                      }`}>
                        {profile.status}
                      </span>
                    </p>
                    <p><span className="font-medium">Guardian Email:</span> {profile.contact.guardian_email || 'Not provided'}</p>
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* Marks Tab */}
          {activeTab === 'marks' && marks && (
            <div className="bg-white shadow rounded-lg p-6">
              <h2 className="text-xl font-semibold mb-4">Academic Performance</h2>
              
              {/* Overall Statistics */}
              <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
                <div className="bg-blue-50 p-4 rounded-lg">
                  <h3 className="font-medium text-blue-900">Overall Average</h3>
                  <p className="text-2xl font-bold text-blue-600">{marks.overall_average}%</p>
                </div>
                <div className="bg-green-50 p-4 rounded-lg">
                  <h3 className="font-medium text-green-900">Passed Subjects</h3>
                  <p className="text-2xl font-bold text-green-600">{marks.passed_subjects}</p>
                </div>
                <div className="bg-red-50 p-4 rounded-lg">
                  <h3 className="font-medium text-red-900">Failed Subjects</h3>
                  <p className="text-2xl font-bold text-red-600">{marks.failed_subjects}</p>
                </div>
                <div className="bg-purple-50 p-4 rounded-lg">
                  <h3 className="font-medium text-purple-900">Overall Status</h3>
                  <p className={`text-2xl font-bold ${
                    marks.overall_status === 'Pass' ? 'text-green-600' : 'text-red-600'
                  }`}>
                    {marks.overall_status}
                  </p>
                </div>
              </div>

              {/* Subject-wise Grades */}
              <div className="overflow-x-auto">
                <table className="min-w-full divide-y divide-gray-200">
                  <thead className="bg-gray-50">
                    <tr>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Subject</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Marks</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Percentage</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Grade</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Status</th>
                    </tr>
                  </thead>
                  <tbody className="bg-white divide-y divide-gray-200">
                    {marks.grades.map((grade, index) => (
                      <tr key={index}>
                        <td className="px-6 py-4 whitespace-nowrap">
                          <div>
                            <div className="text-sm font-medium text-gray-900">{grade.subject_name}</div>
                            <div className="text-sm text-gray-500">{grade.subject_code}</div>
                          </div>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                          {grade.marks_obtained}/{grade.total_marks}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                          {grade.percentage}%
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap">
                          <span className={`px-2 inline-flex text-xs leading-5 font-semibold rounded-full ${getGradeColor(grade.grade_letter)}`}>
                            {grade.grade_letter}
                          </span>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap">
                          <span className={`px-2 inline-flex text-xs leading-5 font-semibold rounded-full ${
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
          )}

          {/* Reports Tab */}
          {activeTab === 'reports' && (
            <div className="space-y-6">
              <ParentModeToggle 
                isParentMode={isParentMode}
                onToggle={() => setIsParentMode(!isParentMode)}
              />
              <StudentReportsView isParentMode={isParentMode} />
            </div>
          )}

          {/* Notifications Tab */}
          {activeTab === 'notifications' && (
            <div className="bg-white shadow rounded-lg p-6">
              <h2 className="text-xl font-semibold mb-4">Notifications</h2>
              {notifications.length === 0 ? (
                <p className="text-gray-500 text-center py-8">No notifications available</p>
              ) : (
                <div className="space-y-4">
                  {notifications.map((notification) => (
                    <div key={notification.id} className="border border-gray-200 rounded-lg p-4">
                      <div className="flex justify-between items-start">
                        <div className="flex-1">
                          <h3 className="font-medium text-gray-900">{notification.title}</h3>
                          <p className="text-sm text-gray-600 mt-1">{notification.message}</p>
                          <div className="flex items-center mt-2 text-xs text-gray-500">
                            <span>From: {notification.from_educator}</span>
                            <span className="mx-2">•</span>
                            <span>{formatDateTime(notification.sent_at)}</span>
                          </div>
                          {/* View Report Button for Grade Reports */}
                          {(notification.message_type === 'GRADE_REPORT' || notification.message_type === 'grade_report') && notification.report_data && (
                            <div className="mt-3">
                              <button
                                onClick={() => handleViewReport(notification)}
                                className="inline-flex items-center px-3 py-1.5 border border-blue-300 text-xs font-medium rounded-md text-blue-700 bg-blue-50 hover:bg-blue-100 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 transition-colors"
                              >
                                📋 View Report
                              </button>
                            </div>
                          )}
                        </div>
                        <span className={`px-2 py-1 rounded-full text-xs ${
                          notification.message_type === 'important' ? 'bg-red-100 text-red-800' : 'bg-blue-100 text-blue-800'
                        }`}>
                          {notification.message_type}
                        </span>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}

          {/* Schedule Tab */}
          {activeTab === 'schedule' && (
            <div className="bg-white shadow rounded-lg p-6">
              <h2 className="text-xl font-semibold mb-4">Scheduled Events</h2>
              {scheduledEvents.length === 0 ? (
                <p className="text-gray-500 text-center py-8">No scheduled events</p>
              ) : (
                <div className="space-y-4">
                  {scheduledEvents.map((event) => (
                    <div key={event.id} className="border border-gray-200 rounded-lg p-4">
                      <div className="flex justify-between items-start">
                        <div className="flex-1">
                          <div className="flex items-center gap-2 mb-1">
                            <h3 className="font-medium text-gray-900">{event.title}</h3>
                            <span className={`px-2 py-0.5 rounded text-xs font-medium ${
                              event.event_type === 'meeting' 
                                ? 'bg-blue-100 text-blue-700' 
                                : 'bg-green-100 text-green-700'
                            }`}>
                              {event.event_type === 'meeting' ? '📅 Meeting' : '📋 Task'}
                            </span>
                          </div>
                          <p className="text-sm text-gray-600 mt-1">{event.description}</p>
                          <div className="flex items-center mt-2 text-xs text-gray-500">
                            <span>📅 {formatDateTime(event.start_datetime)}</span>
                            {event.location && (
                              <>
                                <span className="mx-2">•</span>
                                <span>📍 {event.location}</span>
                              </>
                            )}
                            <span className="mx-2">•</span>
                            <span>👨‍🏫 {event.educator_name}</span>
                            {event.event_type === 'meeting' && event.virtual_meeting_link && (
                              <>
                                <span className="mx-2">•</span>
                                <a href={event.virtual_meeting_link} target="_blank" rel="noopener noreferrer" 
                                   className="text-blue-600 hover:text-blue-800">
                                  🔗 Join Meeting
                                </a>
                              </>
                            )}
                            {event.event_type === 'meeting' && event.requires_rsvp && (
                              <>
                                <span className="mx-2">•</span>
                                <span className={`font-medium ${
                                  event.rsvp_status === 'accepted' ? 'text-green-600' : 
                                  event.rsvp_status === 'declined' ? 'text-red-600' : 'text-yellow-600'
                                }`}>
                                  RSVP: {event.rsvp_status || 'pending'}
                                </span>
                              </>
                            )}
                          </div>
                        </div>
                        <span className={`px-2 py-1 rounded-full text-xs ${
                          event.status === 'scheduled' ? 'bg-green-100 text-green-800' : 'bg-yellow-100 text-yellow-800'
                        }`}>
                          {event.status}
                        </span>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}

          {/* Contact Teacher Tab */}
          {activeTab === 'contact' && (
            <div className="bg-white shadow rounded-lg p-6">
              <h2 className="text-xl font-semibold mb-4">Contact Teacher</h2>
              <form onSubmit={handleContactSubmit} className="space-y-4">
                <div>
                  <label htmlFor="subject" className="block text-sm font-medium text-gray-700">Subject</label>
                  <input
                    type="text"
                    id="subject"
                    value={contactForm.subject}
                    onChange={(e) => setContactForm({...contactForm, subject: e.target.value})}
                    className="mt-1 block w-full border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500"
                    placeholder="Enter message subject"
                    required
                  />
                </div>
                <div>
                  <label htmlFor="message" className="block text-sm font-medium text-gray-700">Message</label>
                  <textarea
                    id="message"
                    rows={6}
                    value={contactForm.message}
                    onChange={(e) => setContactForm({...contactForm, message: e.target.value})}
                    className="mt-1 block w-full border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500"
                    placeholder="Type your message here..."
                    required
                  ></textarea>
                </div>
                <button
                  type="submit"
                  className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-md font-medium"
                >
                  Send Message
                </button>
              </form>
            </div>
          )}
        </div>
      </main>

      {/* Report Modal */}
      {showReportModal && selectedReport && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
          <div className="bg-white rounded-lg shadow-xl max-w-2xl w-full max-h-screen overflow-y-auto">
            <div className="sticky top-0 bg-white border-b border-gray-200 px-6 py-4 flex justify-between items-center">
              <h3 className="text-lg font-semibold text-gray-900">Academic Performance Report</h3>
              <button
                onClick={closeReportModal}
                className="text-gray-400 hover:text-gray-600 text-xl font-semibold"
              >
                ×
              </button>
            </div>
            
            <div className="p-6">
              {selectedReport ? (
                <>
                  {/* Report Header */}
                  <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 mb-6">
                    <h4 className="text-lg font-semibold text-blue-900 mb-2">Student Information</h4>
                    <div className="grid grid-cols-2 gap-4 text-sm">
                      <div>
                        <span className="font-medium text-blue-800">Student Name:</span>
                        <div className="text-blue-900">{selectedReport.student_name || '—'}</div>
                      </div>
                      <div>
                        <span className="font-medium text-blue-800">Roll Number:</span>
                        <div className="text-blue-900">{selectedReport.roll_no || '—'}</div>
                      </div>
                      <div>
                        <span className="font-medium text-blue-800">Section:</span>
                        <div className="text-blue-900">{selectedReport.section || '—'}</div>
                      </div>
                      <div>
                        <span className="font-medium text-blue-800">Report Date:</span>
                        <div className="text-blue-900">{selectedReport.report_date || '—'}</div>
                      </div>
                    </div>
                  </div>

                  {/* Subject-wise Performance */}
                  {selectedReport.subjects ? (
                    <div className="mb-6">
                      <h4 className="text-lg font-semibold text-gray-900 mb-3">📊 Subject-wise Performance</h4>
                      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                        {Object.entries(selectedReport.subjects).map(([subject, marks]) => (
                          <div key={subject} className="bg-gray-50 border border-gray-200 rounded-lg p-4">
                            <div className="text-center">
                              <h5 className="font-medium text-gray-900 mb-2">{subject}</h5>
                              <div className="text-2xl font-bold text-blue-600 mb-1">{marks}%</div>
                              <div className={`text-xs px-2 py-1 rounded-full ${
                                marks >= 85 ? 'bg-green-100 text-green-800' :
                                marks >= 70 ? 'bg-yellow-100 text-yellow-800' :
                                marks >= 50 ? 'bg-orange-100 text-orange-800' :
                                'bg-red-100 text-red-800'
                              }`}>
                                {marks >= 85 ? 'Excellent' :
                                 marks >= 70 ? 'Good' :
                                 marks >= 50 ? 'Average' : 'Needs Improvement'}
                              </div>
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>
                  ) : (
                    <div className="mb-6 text-sm text-gray-600">No structured subject data available for this report.</div>
                  )}

                  {/* Overall Performance */}
                  <div className="bg-green-50 border border-green-200 rounded-lg p-4">
                    <h4 className="text-lg font-semibold text-green-900 mb-3">📈 Overall Assessment</h4>
                    <div className="grid grid-cols-3 gap-4 text-center">
                      <div>
                        <span className="block text-sm font-medium text-green-800">Average Score</span>
                        <span className="text-2xl font-bold text-green-900">{(selectedReport.overall && selectedReport.overall.average) ? `${selectedReport.overall.average}%` : '—'}</span>
                      </div>
                      <div>
                        <span className="block text-sm font-medium text-green-800">Grade</span>
                        <span className="text-2xl font-bold text-green-900">{(selectedReport.overall && selectedReport.overall.grade) || '—'}</span>
                      </div>
                      <div>
                        <span className="block text-sm font-medium text-green-800">Status</span>
                        <span className={`inline-block px-3 py-1 rounded-full text-sm font-medium ${
                          (selectedReport.overall && selectedReport.overall.status === 'Pass') ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'
                        }`}>
                          {(selectedReport.overall && selectedReport.overall.status) || '—'}
                        </span>
                      </div>
                    </div>
                  </div>
                </>
              ) : (
                <div className="text-center py-8 text-gray-600">No structured report data available for this notification.</div>
              )}

              {/* Footer */}
              <div className="mt-6 pt-4 border-t border-gray-200 text-center text-sm text-gray-600">
                <p>Report prepared by: <span className="font-medium">{selectedReport.educator_name}</span></p>
                <p className="mt-1">Generated on: {selectedReport.report_date}</p>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default StudentDashboard;