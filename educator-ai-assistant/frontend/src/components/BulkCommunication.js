import React, { useState, useEffect, useRef } from 'react';
import { 
  Send, AlertCircle, CheckCircle, X,
  MessageSquare, FileText, Calendar, Settings, Target
} from 'lucide-react';
import toast from 'react-hot-toast';
import { bulkCommunication } from '../services/api';

const BulkCommunication = ({ initialSelectedStudents = [], onSelectedStudentsChange = () => {} }) => {
  // State Management
  const [activeMode, setActiveMode] = useState('compose'); // compose, history, templates
  const [sections, setSections] = useState([]);
  const [students, setStudents] = useState([]);
  const [emailTemplates, setEmailTemplates] = useState([]);
  const [sentHistory, setSentHistory] = useState([]);
  const [loading, setLoading] = useState(false);

  // Form State
  const [bulkEmailForm, setBulkEmailForm] = useState({
    target_type: 'section', // section, individual, selected_students
    sections: [],
    student_emails: [],
    student_ids: [],
    message_template: '',
    subject: '',
    send_email: true,
    create_notifications: true,
    selected_template: ''
  });

  const [selectedStudents, setSelectedStudents] = useState([]);
  const [previewMode, setPreviewMode] = useState(false);
  const [previewData, setPreviewData] = useState(null);
  // Debug refs and flags
  const subjectRef = useRef(null);
  const messageRef = useRef(null);
  const DEBUG_AUTO_REFOCUS = true; // set true temporarily to auto-refocus inputs after updates

  // Load initial data
  useEffect(() => {
    loadSections();
    loadEmailTemplates();
    loadSentHistory();
  }, []);

  // If parent supplied initial selected students (from dashboard preselection), apply them
  useEffect(() => {
    if (Array.isArray(initialSelectedStudents) && initialSelectedStudents.length > 0) {
      // Initialize local selected students and switch to the selected_students target type
      setSelectedStudents(initialSelectedStudents);
      setBulkEmailForm(prev => ({ ...prev, target_type: 'selected_students', student_ids: initialSelectedStudents.map(s => s.id) }));
      // Ensure we have students loaded so the checkboxes render correctly
      loadStudents();
      // Inform parent about applied selection
      try {
        onSelectedStudentsChange(initialSelectedStudents);
      } catch (e) {
        // ignore
      }
    }
  }, [initialSelectedStudents, onSelectedStudentsChange]);

  // Keep parent in sync whenever selectedStudents changes locally
  useEffect(() => {
    try {
      onSelectedStudentsChange(selectedStudents);
    } catch (e) {
      // ignore
    }
    // Also keep the form student_ids in sync
    setBulkEmailForm(prev => ({ ...prev, student_ids: selectedStudents.map(s => s.id) }));
  }, [selectedStudents, onSelectedStudentsChange]);

  const loadSections = async () => {
    try {
      const response = await bulkCommunication.getSections();
      setSections(response.data.sections);
    } catch (error) {
      console.error('Failed to load sections:', error);
      toast.error('Failed to load sections');
    }
  };

  const loadStudents = async (sectionId = null) => {
    try {
      const params = sectionId ? { section_id: sectionId } : {};
      const response = await bulkCommunication.getStudents(params);
      setStudents(response.data.students);
    } catch (error) {
      console.error('Failed to load students:', error);
      toast.error('Failed to load students');
    }
  };

  const loadEmailTemplates = async () => {
    try {
      const response = await bulkCommunication.getEmailTemplates();
      setEmailTemplates(response.data.templates);
    } catch (error) {
      console.error('Failed to load email templates:', error);
      toast.error('Failed to load email templates');
    }
  };

  const loadSentHistory = async () => {
    try {
      const response = await bulkCommunication.getSentHistory();
      setSentHistory(response.data.communications);
    } catch (error) {
      console.error('Failed to load sent history:', error);
      toast.error('Failed to load sent history');
    }
  };

  // Attach debug event listeners once to help find focus stealing
  useEffect(() => {
    const events = ['keydown','keyup','keypress','blur','focus','mousedown'];
    const handler = (ev) => {
      try {
        // log event type and target along with active element
        // keep logs concise
        console.debug('[FocusDebug]', ev.type, 'target=', ev.target && ev.target.tagName, 'active=', document.activeElement && document.activeElement.tagName);
      } catch (e) {
        // ignore
      }
    };

    events.forEach((e) => window.addEventListener(e, handler, { capture: true }));

    return () => {
      events.forEach((e) => window.removeEventListener(e, handler, { capture: true }));
    };
  }, []);

  const handleSectionChange = (sectionNames) => {
    setBulkEmailForm(prev => ({
      ...prev,
      sections: sectionNames
    }));
    
    // Load students for selected sections
    if (sectionNames.length > 0) {
      const selectedSectionIds = sections
        .filter(s => sectionNames.includes(s.name))
        .map(s => s.id);
      
      // Load all students for selected sections
      Promise.all(selectedSectionIds.map(id => loadStudents(id)))
        .then(() => {
          // Combine students from all sections
          loadStudents(); // Load all students and we'll filter on frontend
        });
    }
  };

  const handleTemplateSelect = (template) => {
    setBulkEmailForm(prev => ({
      ...prev,
      subject: template.subject,
      message_template: template.template,
      selected_template: template.id
    }));
  };

  // Handle subject input change
  const handleSubjectChange = (e) => {
    const value = e.target.value;
    console.log('[FocusDebug] handleSubjectChange called with:', value);
    setBulkEmailForm(prev => ({ ...prev, subject: value }));
    
    // Optional auto-refocus workaround
    if (DEBUG_AUTO_REFOCUS) {
      setTimeout(() => {
        if (subjectRef.current && document.activeElement !== subjectRef.current) {
          console.log('[FocusDebug] Auto-refocusing subject input');
          subjectRef.current.focus();
        }
      }, 0);
    }
  };

  // Handle message template change
  const handleMessageChange = (e) => {
    const value = e.target.value;
    console.log('[FocusDebug] handleMessageChange called with:', value);
    setBulkEmailForm(prev => ({ ...prev, message_template: value }));
    
    // Optional auto-refocus workaround
    if (DEBUG_AUTO_REFOCUS) {
      setTimeout(() => {
        if (messageRef.current && document.activeElement !== messageRef.current) {
          console.log('[FocusDebug] Auto-refocusing message input');
          messageRef.current.focus();
        }
      }, 0);
    }
  };

  const handleSendBulkEmail = async () => {
    if (!bulkEmailForm.message_template || !bulkEmailForm.subject) {
      toast.error('Please provide both subject and message template');
      return;
    }

    if (bulkEmailForm.target_type === 'section' && bulkEmailForm.sections.length === 0) {
      toast.error('Please select at least one section');
      return;
    }

    if (bulkEmailForm.target_type === 'selected_students' && selectedStudents.length === 0) {
      toast.error('Please select at least one student');
      return;
    }

    setLoading(true);
    try {
      const requestData = { ...bulkEmailForm };
      
      if (bulkEmailForm.target_type === 'selected_students') {
        requestData.student_ids = selectedStudents.map(s => s.id);
      }

      const response = await bulkCommunication.sendBulkEmail(requestData);
      
      if (response.data.success) {
        toast.success(response.data.message);
        setPreviewData(response.data);
        setPreviewMode(true);
        loadSentHistory(); // Refresh history
      } else {
        toast.error('Failed to send bulk emails');
      }
    } catch (error) {
      console.error('Error sending bulk emails:', error);
      toast.error('Failed to send bulk emails: ' + (error.response?.data?.detail || error.message));
    } finally {
      setLoading(false);
    }
  };

  const ComposeEmailSection = () => (
    <div className="space-y-6">
      {/* Target Selection */}
      <div className="bg-white rounded-lg shadow-md p-6">
        <h3 className="text-lg font-semibold mb-4 flex items-center">
          <Target className="w-5 h-5 mr-2 text-blue-600" />
          Select Recipients
        </h3>

        <div className="space-y-4">
          {/* Target Type Selection */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Target Type
            </label>
            <select
              value={bulkEmailForm.target_type}
              onChange={(e) => setBulkEmailForm(prev => ({ ...prev, target_type: e.target.value }))}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="section">Entire Section(s)</option>
              <option value="selected_students">Select Individual Students</option>
            </select>
          </div>

          {/* Section Selection */}
          {bulkEmailForm.target_type === 'section' && (
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Select Sections
              </label>
              <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
                {sections.map((section) => (
                  <label key={section.id} className="flex items-center space-x-2 p-3 border rounded-lg hover:bg-gray-50">
                    <input
                      type="checkbox"
                      checked={bulkEmailForm.sections.includes(section.name)}
                      onChange={(e) => {
                        const newSections = e.target.checked
                          ? [...bulkEmailForm.sections, section.name]
                          : bulkEmailForm.sections.filter(s => s !== section.name);
                        handleSectionChange(newSections);
                      }}
                      className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                    />
                    <div>
                      <div className="font-medium">{section.name}</div>
                      <div className="text-sm text-gray-500">{section.student_count} students</div>
                    </div>
                  </label>
                ))}
              </div>
            </div>
          )}

          {/* Student Selection */}
          {bulkEmailForm.target_type === 'selected_students' && (
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Select Students
              </label>
              <button
                onClick={() => loadStudents()}
                className="mb-3 px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700"
              >
                Load All Students
              </button>
              <div className="max-h-60 overflow-y-auto border rounded-lg">
                {students.map((student) => (
                  <label key={student.id} className="flex items-center space-x-3 p-3 border-b hover:bg-gray-50">
                    <input
                      type="checkbox"
                      checked={selectedStudents.some(s => s.id === student.id)}
                      onChange={(e) => {
                        if (e.target.checked) {
                          setSelectedStudents(prev => [...prev, student]);
                        } else {
                          setSelectedStudents(prev => prev.filter(s => s.id !== student.id));
                        }
                      }}
                      className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                    />
                    <div>
                      <div className="font-medium">{student.name}</div>
                      <div className="text-sm text-gray-500">{student.email} • {student.section_name}</div>
                    </div>
                  </label>
                ))}
              </div>
              {selectedStudents.length > 0 && (
                <div className="mt-2 text-sm text-blue-600">
                  {selectedStudents.length} student(s) selected
                </div>
              )}
            </div>
          )}
        </div>
      </div>

      {/* Email Template Selection */}
      <div className="bg-white rounded-lg shadow-md p-6">
        <h3 className="text-lg font-semibold mb-4 flex items-center">
          <FileText className="w-5 h-5 mr-2 text-green-600" />
          Email Template
        </h3>

        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Choose Template
            </label>
            <div className="grid gap-3">
              {emailTemplates.map((template) => (
                <div
                  key={template.id}
                  className="p-4 border rounded-lg cursor-pointer hover:bg-blue-50 hover:border-blue-300"
                  onClick={() => handleTemplateSelect(template)}
                >
                  <div className="font-medium text-blue-600">{template.name}</div>
                  <div className="text-sm text-gray-600 mt-1">{template.subject}</div>
                  <div className="text-xs text-gray-500 mt-2 line-clamp-2">
                    {template.template.substring(0, 100)}...
                  </div>
                </div>
              ))}
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Email Subject
            </label>
            <input
              ref={subjectRef}
              type="text"
              value={bulkEmailForm.subject}
              onChange={handleSubjectChange}
              onFocus={() => console.debug('[FocusDebug] subject onFocus active=', document.activeElement && document.activeElement.tagName)}
              onBlur={() => console.debug('[FocusDebug] subject onBlur active=', document.activeElement && document.activeElement.tagName)}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              placeholder="Enter email subject..."
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Message Template
            </label>
            <textarea
              ref={messageRef}
              value={bulkEmailForm.message_template}
              onChange={handleMessageChange}
              onFocus={() => console.debug('[FocusDebug] message onFocus active=', document.activeElement && document.activeElement.tagName)}
              onBlur={() => console.debug('[FocusDebug] message onBlur active=', document.activeElement && document.activeElement.tagName)}
              rows={10}
              dir="ltr"
              style={{ direction: 'ltr', textAlign: 'left' }}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              placeholder="Enter your message template. You can use variables like {student_name}, {math_marks}, {science_marks}, {english_marks}, {average_score}, {status}, etc."
            />
          </div>

          <div className="text-sm text-gray-600 bg-gray-50 p-3 rounded-md">
            <strong>Available Variables:</strong> {'{student_name}'}, {'{math_marks}'}, {'{science_marks}'}, 
            {'{english_marks}'}, {'{average_score}'}, {'{status}'}, {'{grade_letter}'}, {'{section}'}, {'{roll_no}'}
          </div>
        </div>
      </div>

      {/* Send Options */}
      <div className="bg-white rounded-lg shadow-md p-6">
        <h3 className="text-lg font-semibold mb-4 flex items-center">
          <Settings className="w-5 h-5 mr-2 text-purple-600" />
          Delivery Options
        </h3>

        <div className="space-y-3">
          <label className="flex items-center space-x-3">
            <input
              type="checkbox"
              checked={bulkEmailForm.send_email}
              onChange={(e) => setBulkEmailForm(prev => ({ ...prev, send_email: e.target.checked }))}
              className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
            />
            <span className="text-sm font-medium">Send actual emails to students</span>
          </label>

          <label className="flex items-center space-x-3">
            <input
              type="checkbox"
              checked={bulkEmailForm.create_notifications}
              onChange={(e) => setBulkEmailForm(prev => ({ ...prev, create_notifications: e.target.checked }))}
              className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
            />
            <span className="text-sm font-medium">Create portal notifications for students</span>
          </label>
        </div>

        <button
          onClick={handleSendBulkEmail}
          disabled={loading}
          className="mt-6 w-full bg-blue-600 text-white py-3 px-4 rounded-md hover:bg-blue-700 disabled:opacity-50 flex items-center justify-center"
        >
          {loading ? (
            <>
              <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
              Sending...
            </>
          ) : (
            <>
              <Send className="w-4 h-4 mr-2" />
              Send Bulk Report
            </>
          )}
        </button>
      </div>
    </div>
  );

  const HistorySection = () => (
    <div className="bg-white rounded-lg shadow-md p-6">
      <div className="flex justify-between items-center mb-6">
        <h3 className="text-lg font-semibold flex items-center">
          <Calendar className="w-5 h-5 mr-2 text-blue-600" />
          Sent Communication History
        </h3>
        <button
          onClick={loadSentHistory}
          className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700"
        >
          Refresh
        </button>
      </div>

      <div className="space-y-3">
        {sentHistory.map((comm) => (
          <div key={comm.id} className="border rounded-lg p-4 hover:bg-gray-50">
            <div className="flex justify-between items-start">
              <div>
                <div className="font-medium">{comm.subject}</div>
                <div className="text-sm text-gray-600">To: {comm.recipient_email}</div>
                <div className="text-sm text-gray-500 mt-1">
                  Sent: {new Date(comm.sent_at).toLocaleString()}
                </div>
              </div>
              <div className="flex items-center space-x-2">
                {comm.is_sent ? (
                  <CheckCircle className="w-5 h-5 text-green-500" />
                ) : (
                  <AlertCircle className="w-5 h-5 text-red-500" />
                )}
                <span className="text-sm font-medium">
                  {comm.is_sent ? 'Delivered' : 'Failed'}
                </span>
              </div>
            </div>
            <div className="mt-2 text-sm text-gray-600 bg-gray-50 p-2 rounded">
              {comm.message_preview}
            </div>
          </div>
        ))}
        
        {sentHistory.length === 0 && (
          <div className="text-center py-8 text-gray-500">
            No communication history found.
          </div>
        )}
      </div>
    </div>
  );

  const PreviewResultsModal = () => {
    if (!previewMode || !previewData) return null;

    return (
      <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
        <div className="bg-white rounded-lg shadow-xl max-w-4xl max-h-90vh overflow-y-auto m-4">
          <div className="p-6">
            <div className="flex justify-between items-center mb-4">
              <h2 className="text-xl font-bold text-green-600">
                Bulk Communication Results
              </h2>
              <button
                onClick={() => setPreviewMode(false)}
                className="text-gray-500 hover:text-gray-700"
              >
                <X className="w-6 h-6" />
              </button>
            </div>

            {/* Summary Stats */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
              <div className="bg-green-50 p-4 rounded-lg">
                <div className="text-2xl font-bold text-green-600">{previewData.emails_sent}</div>
                <div className="text-sm text-green-700">Emails Sent</div>
              </div>
              <div className="bg-red-50 p-4 rounded-lg">
                <div className="text-2xl font-bold text-red-600">{previewData.emails_failed}</div>
                <div className="text-sm text-red-700">Failed</div>
              </div>
              <div className="bg-blue-50 p-4 rounded-lg">
                <div className="text-2xl font-bold text-blue-600">{previewData.notifications_created}</div>
                <div className="text-sm text-blue-700">Portal Notifications</div>
              </div>
            </div>

            {/* Email Results */}
            <div className="space-y-4">
              <h3 className="font-semibold">Email Delivery Results:</h3>
              <div className="max-h-60 overflow-y-auto">
                {previewData.email_results?.map((result, index) => (
                  <div key={index} className="flex items-center justify-between p-3 border rounded">
                    <div>
                      <div className="font-medium">{result.student_name}</div>
                      <div className="text-sm text-gray-600">{result.student_email}</div>
                    </div>
                    <div className="flex items-center space-x-2">
                      {result.success ? (
                        <CheckCircle className="w-5 h-5 text-green-500" />
                      ) : (
                        <AlertCircle className="w-5 h-5 text-red-500" />
                      )}
                      <span className="text-sm">{result.message}</span>
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* Performance Data Preview */}
            <div className="mt-6">
              <h3 className="font-semibold mb-3">Student Performance Data:</h3>
              <div className="max-h-60 overflow-y-auto">
                {previewData.performance_data?.slice(0, 5).map((student, index) => (
                  <div key={index} className="p-3 border rounded mb-2">
                    <div className="font-medium">{student.student_name} ({student.section})</div>
                    <div className="text-sm text-gray-600">
                      Math: {student.math_marks}% | Science: {student.science_marks}% | English: {student.english_marks}%
                    </div>
                    <div className="text-sm font-medium">
                      Average: {student.average_score}% | Grade: {student.grade_letter} | Status: {student.status}
                    </div>
                  </div>
                ))}
                {previewData.performance_data?.length > 5 && (
                  <div className="text-sm text-gray-500 text-center">
                    ... and {previewData.performance_data.length - 5} more students
                  </div>
                )}
              </div>
            </div>

            <div className="mt-6 flex justify-end">
              <button
                onClick={() => setPreviewMode(false)}
                className="px-6 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700"
              >
                Close
              </button>
            </div>
          </div>
        </div>
      </div>
    );
  };

  return (
    <div className="p-6">
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-gray-900 mb-2">Bulk Communication</h1>
        <p className="text-gray-600">Send personalized performance reports to students via email and portal notifications</p>
      </div>

      {/* Navigation Tabs */}
      <div className="mb-6">
        <nav className="flex space-x-4">
          <button
            onClick={() => setActiveMode('compose')}
            className={`px-4 py-2 rounded-md font-medium ${
              activeMode === 'compose'
                ? 'bg-blue-600 text-white'
                : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
            }`}
          >
            <MessageSquare className="w-4 h-4 inline mr-2" />
            Compose & Send
          </button>
          <button
            onClick={() => setActiveMode('history')}
            className={`px-4 py-2 rounded-md font-medium ${
              activeMode === 'history'
                ? 'bg-blue-600 text-white'
                : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
            }`}
          >
            <Calendar className="w-4 h-4 inline mr-2" />
            History
          </button>
        </nav>
      </div>

      {/* Content */}
      {activeMode === 'compose' && <ComposeEmailSection />}
      {activeMode === 'history' && <HistorySection />}

      {/* Preview Results Modal */}
      <PreviewResultsModal />
    </div>
  );
};

export default BulkCommunication;