import React, { useState, useEffect } from 'react';
import { 
  Send, MessageSquare, Clock, CheckCircle, User, Mail, 
  X, Plus, Template, Filter, Search, AlertCircle
} from 'lucide-react';
import axios from 'axios';

const StudentMessaging = () => {
  const [messages, setMessages] = useState([]);
  const [templates, setTemplates] = useState([]);
  const [students, setStudents] = useState([]);
  const [selectedStudent, setSelectedStudent] = useState(null);
  const [showSendModal, setShowSendModal] = useState(false);
  const [showTemplateModal, setShowTemplateModal] = useState(false);
  const [loading, setLoading] = useState(false);
  const [activeTab, setActiveTab] = useState('conversations');
  
  // Message form state
  const [messageForm, setMessageForm] = useState({
    receiver_id: '',
    subject: '',
    message: '',
    message_type: 'general',
    priority: 'normal'
  });

  // Template form state
  const [templateForm, setTemplateForm] = useState({
    template_name: '',
    subject_template: '',
    message_template: '',
    message_type: 'general'
  });

  const [filters, setFilters] = useState({
    search: '',
    message_type: '',
    priority: ''
  });

  useEffect(() => {
    fetchInitialData();
  }, []);

  const fetchInitialData = async () => {
    try {
      const token = localStorage.getItem('token');
      const headers = { 'Authorization': `Bearer ${token}` };

      const [messagesRes, templatesRes, studentsRes] = await Promise.all([
        axios.get('http://localhost:8001/api/v1/messages/sent', { headers }),
        axios.get('http://localhost:8001/api/v1/messages/templates', { headers }),
        axios.get('http://localhost:8003/api/v1/messages/students/summary', { headers })
      ]);

      setMessages(messagesRes.data);
      setTemplates(templatesRes.data);
      setStudents(studentsRes.data);
    } catch (error) {
      console.error('Error fetching data:', error);
    }
  };

  const sendMessage = async () => {
    if (!messageForm.receiver_id || !messageForm.subject || !messageForm.message) {
      alert('Please fill in all required fields');
      return;
    }

    setLoading(true);
    try {
      const token = localStorage.getItem('token');
      const headers = { 'Authorization': `Bearer ${token}` };

      await axios.post('http://localhost:8001/api/v1/messages/send', messageForm, { headers });
      
      alert('Message sent successfully!');
      setMessageForm({
        receiver_id: '',
        subject: '',
        message: '',
        message_type: 'general',
        priority: 'normal'
      });
      setShowSendModal(false);
      fetchInitialData();
    } catch (error) {
      console.error('Error sending message:', error);
      alert('Failed to send message');
    } finally {
      setLoading(false);
    }
  };

  const createTemplate = async () => {
    setLoading(true);
    try {
      const token = localStorage.getItem('token');
      const headers = { 'Authorization': `Bearer ${token}` };

      await axios.post('http://localhost:8001/api/v1/messages/templates', templateForm, { headers });
      
      alert('Template created successfully!');
      setTemplateForm({
        template_name: '',
        subject_template: '',
        message_template: '',
        message_type: 'general'
      });
      setShowTemplateModal(false);
      fetchInitialData();
    } catch (error) {
      console.error('Error creating template:', error);
      alert('Failed to create template');
    } finally {
      setLoading(false);
    }
  };

  const useTemplate = (template) => {
    setMessageForm({
      ...messageForm,
      subject: template.subject_template,
      message: template.message_template,
      message_type: template.message_type
    });
  };

  const openStudentConversation = async (studentId) => {
    try {
      const token = localStorage.getItem('token');
      const headers = { 'Authorization': `Bearer ${token}` };

      const response = await axios.get(`http://localhost:8001/api/v1/messages/student/${studentId}/conversation`, { headers });
      setSelectedStudent({
        id: studentId,
        messages: response.data,
        name: students.find(s => s.student_id === studentId)?.student_name || 'Unknown'
      });
    } catch (error) {
      console.error('Error fetching conversation:', error);
    }
  };

  const filteredMessages = messages.filter(msg => {
    const matchesSearch = !filters.search || 
      msg.subject.toLowerCase().includes(filters.search.toLowerCase()) ||
      msg.receiver_name.toLowerCase().includes(filters.search.toLowerCase());
    
    const matchesType = !filters.message_type || msg.message_type === filters.message_type;
    const matchesPriority = !filters.priority || msg.priority === filters.priority;
    
    return matchesSearch && matchesType && matchesPriority;
  });

  const getPriorityColor = (priority) => {
    switch (priority) {
      case 'urgent': return 'text-red-600 bg-red-100';
      case 'high': return 'text-orange-600 bg-orange-100';
      case 'normal': return 'text-blue-600 bg-blue-100';
      case 'low': return 'text-gray-600 bg-gray-100';
      default: return 'text-blue-600 bg-blue-100';
    }
  };

  const getMessageTypeIcon = (type) => {
    switch (type) {
      case 'academic': return '📚';
      case 'behavioral': return '⚡';
      case 'attendance': return '📅';
      default: return '💬';
    }
  };

  return (
    <div className="min-h-screen bg-gray-50 p-6">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="bg-white rounded-lg shadow p-6 mb-6">
          <div className="flex justify-between items-center">
            <div>
              <h1 className="text-2xl font-bold text-gray-900 flex items-center gap-2">
                <MessageSquare className="w-6 h-6 text-blue-600" />
                Student Messaging
              </h1>
              <p className="text-gray-600 mt-1">Communicate directly with students</p>
            </div>
            
            <div className="flex gap-2">
              <button
                onClick={() => setShowTemplateModal(true)}
                className="flex items-center gap-2 px-4 py-2 bg-gray-600 text-white rounded-lg hover:bg-gray-700 transition-colors"
              >
                <Template className="w-4 h-4" />
                Templates
              </button>
              <button
                onClick={() => setShowSendModal(true)}
                className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
              >
                <Send className="w-4 h-4" />
                New Message
              </button>
            </div>
          </div>
        </div>

        {/* Tab Navigation */}
        <div className="bg-white rounded-lg shadow mb-6">
          <div className="flex border-b">
            {[
              { id: 'conversations', label: 'Conversations', icon: MessageSquare },
              { id: 'sent', label: 'Sent Messages', icon: Mail },
              { id: 'students', label: 'Student List', icon: User }
            ].map(tab => (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`flex items-center gap-2 px-6 py-4 border-b-2 transition-colors ${
                  activeTab === tab.id 
                    ? 'border-blue-500 text-blue-600' 
                    : 'border-transparent text-gray-600 hover:text-gray-800'
                }`}
              >
                <tab.icon className="w-4 h-4" />
                {tab.label}
              </button>
            ))}
          </div>
        </div>

        {/* Filters */}
        <div className="bg-white rounded-lg shadow p-4 mb-6">
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <div className="relative">
              <Search className="w-4 h-4 absolute left-3 top-3 text-gray-400" />
              <input
                type="text"
                placeholder="Search messages..."
                value={filters.search}
                onChange={(e) => setFilters({...filters, search: e.target.value})}
                className="pl-10 w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              />
            </div>
            
            <select
              value={filters.message_type}
              onChange={(e) => setFilters({...filters, message_type: e.target.value})}
              className="px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            >
              <option value="">All Types</option>
              <option value="general">General</option>
              <option value="academic">Academic</option>
              <option value="behavioral">Behavioral</option>
              <option value="attendance">Attendance</option>
            </select>
            
            <select
              value={filters.priority}
              onChange={(e) => setFilters({...filters, priority: e.target.value})}
              className="px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            >
              <option value="">All Priorities</option>
              <option value="low">Low</option>
              <option value="normal">Normal</option>
              <option value="high">High</option>
              <option value="urgent">Urgent</option>
            </select>
            
            <button
              onClick={() => setFilters({ search: '', message_type: '', priority: '' })}
              className="px-4 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 transition-colors"
            >
              Clear Filters
            </button>
          </div>
        </div>

        {/* Content */}
        {activeTab === 'conversations' && (
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            {/* Student List */}
            <div className="bg-white rounded-lg shadow">
              <div className="p-4 border-b">
                <h3 className="font-semibold text-gray-900">Students</h3>
              </div>
              <div className="max-h-96 overflow-y-auto">
                {students.map(student => (
                  <div
                    key={student.student_id}
                    className="p-4 border-b hover:bg-gray-50 cursor-pointer"
                    onClick={() => openStudentConversation(student.student_id)}
                  >
                    <div className="flex items-center justify-between">
                      <div>
                        <p className="font-medium text-gray-900">{student.student_name}</p>
                        {student.last_message_preview && (
                          <p className="text-sm text-gray-500 truncate">{student.last_message_preview}</p>
                        )}
                      </div>
                      {student.unread_count > 0 && (
                        <span className="bg-blue-500 text-white text-xs px-2 py-1 rounded-full">
                          {student.unread_count}
                        </span>
                      )}
                    </div>
                    {student.last_message_date && (
                      <p className="text-xs text-gray-400 mt-1">
                        {new Date(student.last_message_date).toLocaleDateString()}
                      </p>
                    )}
                  </div>
                ))}
              </div>
            </div>

            {/* Conversation View */}
            <div className="lg:col-span-2 bg-white rounded-lg shadow">
              {selectedStudent ? (
                <div>
                  <div className="p-4 border-b flex items-center justify-between">
                    <h3 className="font-semibold text-gray-900">
                      Conversation with {selectedStudent.name}
                    </h3>
                    <button
                      onClick={() => {
                        setMessageForm({...messageForm, receiver_id: selectedStudent.id});
                        setShowSendModal(true);
                      }}
                      className="px-3 py-1 bg-blue-600 text-white rounded text-sm hover:bg-blue-700"
                    >
                      Send Message
                    </button>
                  </div>
                  <div className="max-h-96 overflow-y-auto p-4 space-y-4">
                    {selectedStudent.messages.map(message => (
                      <div key={message.id} className="border rounded-lg p-4">
                        <div className="flex items-center justify-between mb-2">
                          <div className="flex items-center gap-2">
                            <span className="text-sm">{getMessageTypeIcon(message.message_type)}</span>
                            <span className="font-medium text-gray-900">{message.subject}</span>
                            <span className={`px-2 py-1 rounded text-xs ${getPriorityColor(message.priority)}`}>
                              {message.priority}
                            </span>
                          </div>
                          <span className="text-xs text-gray-500">
                            {new Date(message.created_at).toLocaleString()}
                          </span>
                        </div>
                        <p className="text-gray-700">{message.message}</p>
                        <div className="mt-2 flex items-center gap-2">
                          {message.is_read ? (
                            <CheckCircle className="w-4 h-4 text-green-500" />
                          ) : (
                            <Clock className="w-4 h-4 text-gray-400" />
                          )}
                          <span className="text-xs text-gray-500">
                            {message.is_read ? 'Read' : 'Unread'}
                          </span>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              ) : (
                <div className="p-8 text-center text-gray-500">
                  <MessageSquare className="w-12 h-12 mx-auto mb-4 text-gray-300" />
                  <p>Select a student to view conversation</p>
                </div>
              )}
            </div>
          </div>
        )}

        {activeTab === 'sent' && (
          <div className="bg-white rounded-lg shadow">
            <div className="p-4 border-b">
              <h3 className="font-semibold text-gray-900">Sent Messages</h3>
            </div>
            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-gray-200">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Student</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Subject</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Type</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Priority</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Status</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Date</th>
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-200">
                  {filteredMessages.map(message => (
                    <tr key={message.id} className="hover:bg-gray-50">
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="text-sm font-medium text-gray-900">{message.receiver_name}</div>
                      </td>
                      <td className="px-6 py-4">
                        <div className="text-sm text-gray-900">{message.subject}</div>
                        <div className="text-sm text-gray-500 truncate max-w-xs">{message.message}</div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="flex items-center gap-1">
                          <span>{getMessageTypeIcon(message.message_type)}</span>
                          <span className="text-sm text-gray-700 capitalize">{message.message_type}</span>
                        </div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <span className={`px-2 py-1 rounded text-xs ${getPriorityColor(message.priority)}`}>
                          {message.priority}
                        </span>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="flex items-center gap-1">
                          {message.is_read ? (
                            <CheckCircle className="w-4 h-4 text-green-500" />
                          ) : (
                            <Clock className="w-4 h-4 text-gray-400" />
                          )}
                          <span className="text-sm text-gray-600">
                            {message.is_read ? 'Read' : 'Unread'}
                          </span>
                        </div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                        {new Date(message.created_at).toLocaleDateString()}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}

        {activeTab === 'students' && (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {students.map(student => (
              <div key={student.student_id} className="bg-white rounded-lg shadow p-6">
                <div className="flex items-center justify-between mb-4">
                  <div className="flex items-center gap-3">
                    <div className="w-10 h-10 bg-blue-100 rounded-full flex items-center justify-center">
                      <User className="w-5 h-5 text-blue-600" />
                    </div>
                    <div>
                      <h3 className="font-semibold text-gray-900">{student.student_name}</h3>
                      <p className="text-sm text-gray-500">Student ID: {student.student_id}</p>
                    </div>
                  </div>
                  {student.unread_count > 0 && (
                    <span className="bg-red-500 text-white text-xs px-2 py-1 rounded-full">
                      {student.unread_count} unread
                    </span>
                  )}
                </div>
                
                {student.last_message_preview && (
                  <div className="mb-4">
                    <p className="text-sm text-gray-600">Last message:</p>
                    <p className="text-sm text-gray-800 bg-gray-50 p-2 rounded mt-1">
                      {student.last_message_preview}
                    </p>
                    <p className="text-xs text-gray-500 mt-1">
                      {new Date(student.last_message_date).toLocaleDateString()}
                    </p>
                  </div>
                )}
                
                <div className="flex gap-2">
                  <button
                    onClick={() => {
                      setMessageForm({...messageForm, receiver_id: student.student_id});
                      setShowSendModal(true);
                    }}
                    className="flex-1 bg-blue-600 text-white px-3 py-2 rounded text-sm hover:bg-blue-700 transition-colors"
                  >
                    Send Message
                  </button>
                  <button
                    onClick={() => openStudentConversation(student.student_id)}
                    className="flex-1 bg-gray-100 text-gray-700 px-3 py-2 rounded text-sm hover:bg-gray-200 transition-colors"
                  >
                    View History
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}

        {/* Send Message Modal */}
        {showSendModal && (
          <div className="fixed inset-0 bg-gray-600 bg-opacity-50 flex items-center justify-center z-50">
            <div className="bg-white rounded-lg shadow-xl max-w-2xl w-full mx-4 max-h-[90vh] overflow-y-auto">
              <div className="px-6 py-4 border-b border-gray-200 flex items-center justify-between">
                <h2 className="text-xl font-semibold text-gray-900">Send Message</h2>
                <button
                  onClick={() => setShowSendModal(false)}
                  className="text-gray-400 hover:text-gray-600"
                >
                  <X className="w-5 h-5" />
                </button>
              </div>
              
              <div className="p-6 space-y-4">
                {/* Student Selection */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Student</label>
                  <select
                    value={messageForm.receiver_id}
                    onChange={(e) => setMessageForm({...messageForm, receiver_id: e.target.value})}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                    required
                  >
                    <option value="">Select a student</option>
                    {students.map(student => (
                      <option key={student.student_id} value={student.student_id}>
                        {student.student_name}
                      </option>
                    ))}
                  </select>
                </div>

                {/* Message Type and Priority */}
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">Type</label>
                    <select
                      value={messageForm.message_type}
                      onChange={(e) => setMessageForm({...messageForm, message_type: e.target.value})}
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                    >
                      <option value="general">General</option>
                      <option value="academic">Academic</option>
                      <option value="behavioral">Behavioral</option>
                      <option value="attendance">Attendance</option>
                    </select>
                  </div>
                  
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">Priority</label>
                    <select
                      value={messageForm.priority}
                      onChange={(e) => setMessageForm({...messageForm, priority: e.target.value})}
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                    >
                      <option value="low">Low</option>
                      <option value="normal">Normal</option>
                      <option value="high">High</option>
                      <option value="urgent">Urgent</option>
                    </select>
                  </div>
                </div>

                {/* Templates */}
                {templates.length > 0 && (
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">Use Template</label>
                    <select
                      onChange={(e) => {
                        if (e.target.value) {
                          const template = templates.find(t => t.id === parseInt(e.target.value));
                          if (template) useTemplate(template);
                        }
                      }}
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                    >
                      <option value="">Select a template (optional)</option>
                      {templates.map(template => (
                        <option key={template.id} value={template.id}>
                          {template.template_name}
                        </option>
                      ))}
                    </select>
                  </div>
                )}

                {/* Subject */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Subject</label>
                  <input
                    type="text"
                    value={messageForm.subject}
                    onChange={(e) => setMessageForm({...messageForm, subject: e.target.value})}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                    placeholder="Enter message subject"
                    required
                  />
                </div>

                {/* Message */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Message</label>
                  <textarea
                    value={messageForm.message}
                    onChange={(e) => setMessageForm({...messageForm, message: e.target.value})}
                    rows={6}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                    placeholder="Enter your message"
                    required
                  />
                </div>
              </div>

              <div className="px-6 py-4 border-t border-gray-200 flex justify-end gap-2">
                <button
                  onClick={() => setShowSendModal(false)}
                  className="px-4 py-2 text-gray-700 bg-gray-100 rounded-lg hover:bg-gray-200 transition-colors"
                >
                  Cancel
                </button>
                <button
                  onClick={sendMessage}
                  disabled={loading}
                  className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors disabled:opacity-50"
                >
                  {loading ? 'Sending...' : 'Send Message'}
                </button>
              </div>
            </div>
          </div>
        )}

        {/* Template Modal */}
        {showTemplateModal && (
          <div className="fixed inset-0 bg-gray-600 bg-opacity-50 flex items-center justify-center z-50">
            <div className="bg-white rounded-lg shadow-xl max-w-2xl w-full mx-4">
              <div className="px-6 py-4 border-b border-gray-200 flex items-center justify-between">
                <h2 className="text-xl font-semibold text-gray-900">Create Message Template</h2>
                <button
                  onClick={() => setShowTemplateModal(false)}
                  className="text-gray-400 hover:text-gray-600"
                >
                  <X className="w-5 h-5" />
                </button>
              </div>
              
              <div className="p-6 space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Template Name</label>
                  <input
                    type="text"
                    value={templateForm.template_name}
                    onChange={(e) => setTemplateForm({...templateForm, template_name: e.target.value})}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                    placeholder="e.g., Assignment Reminder"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Message Type</label>
                  <select
                    value={templateForm.message_type}
                    onChange={(e) => setTemplateForm({...templateForm, message_type: e.target.value})}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  >
                    <option value="general">General</option>
                    <option value="academic">Academic</option>
                    <option value="behavioral">Behavioral</option>
                    <option value="attendance">Attendance</option>
                  </select>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Subject Template</label>
                  <input
                    type="text"
                    value={templateForm.subject_template}
                    onChange={(e) => setTemplateForm({...templateForm, subject_template: e.target.value})}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                    placeholder="e.g., Assignment Due: [Subject]"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Message Template</label>
                  <textarea
                    value={templateForm.message_template}
                    onChange={(e) => setTemplateForm({...templateForm, message_template: e.target.value})}
                    rows={6}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                    placeholder="Enter your message template..."
                  />
                </div>
              </div>

              <div className="px-6 py-4 border-t border-gray-200 flex justify-end gap-2">
                <button
                  onClick={() => setShowTemplateModal(false)}
                  className="px-4 py-2 text-gray-700 bg-gray-100 rounded-lg hover:bg-gray-200 transition-colors"
                >
                  Cancel
                </button>
                <button
                  onClick={createTemplate}
                  disabled={loading}
                  className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors disabled:opacity-50"
                >
                  {loading ? 'Creating...' : 'Create Template'}
                </button>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default StudentMessaging;