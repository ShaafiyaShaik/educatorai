import React, { useState } from 'react';
import { Send, X, MessageSquare } from 'lucide-react';
import axios from 'axios';

const SendMessageButton = ({ student, onMessageSent }) => {
  const [showModal, setShowModal] = useState(false);
  const [loading, setLoading] = useState(false);
  const [messageForm, setMessageForm] = useState({
    subject: '',
    message: '',
    message_type: 'general',
    priority: 'normal',
    receiver_type: 'student',
    is_report: false
  });

  const quickMessages = {
    academic: [
      "Great improvement in recent assignments!",
      "Please see me after class to discuss your progress.",
      "Assignment due date reminder",
      "Excellent work on the recent project!"
    ],
    behavioral: [
      "Thank you for your positive attitude in class.",
      "Please remember to follow classroom guidelines.",
      "Your participation has been outstanding!",
      "Let's work together to improve classroom behavior."
    ],
    attendance: [
      "Please ensure regular attendance for better learning.",
      "Missed assignments due to absence - please catch up.",
      "Your attendance has been excellent this month!",
      "Please contact me regarding recent absences."
    ],
    general: [
      "Keep up the good work!",
      "Please remember to bring your materials to class.",
      "Great to see your enthusiasm for learning!",
      "Please see me during office hours."
    ]
  };

  const sendMessage = async () => {
    if (!messageForm.subject || !messageForm.message) {
      alert('Please fill in subject and message');
      return;
    }

    setLoading(true);
    try {
      const token = localStorage.getItem('token');
      const headers = { 'Authorization': `Bearer ${token}` };

      const messageData = {
        receiver_id: student.id,
        receiver_type: messageForm.receiver_type || 'student',
        subject: messageForm.subject,
        message: messageForm.message,
        message_type: messageForm.message_type,
        priority: messageForm.priority,
        is_report: !!messageForm.is_report
      };

      // Use relative URL so frontend works regardless of backend host/port in dev/prod
      const url = '/api/v1/messages/send';

      const resp = await axios.post(url, messageData, { headers });
      // If backend returned a message object, optionally pass it to onMessageSent
      const created = resp && resp.data ? resp.data : null;

      // Inform the user of success
      alert('Message sent successfully!');
      setMessageForm({
        subject: '',
        message: '',
        message_type: 'general',
        priority: 'normal',
        receiver_type: 'student',
        is_report: false
      });
      setShowModal(false);
      
      if (onMessageSent) {
        try {
          // pass created message if available so parent can update UI immediately
          onMessageSent(created);
        } catch (e) {
          // fallback: call without args
          onMessageSent();
        }
      }
    } catch (error) {
      console.error('Error sending message:', error);
      // Show backend-provided error message when available
      const backendMsg = error?.response?.data?.detail || error?.response?.data || error?.message;
      alert(`Failed to send message: ${backendMsg}`);
    } finally {
      setLoading(false);
    }
  };

  const handleQuickMessage = (message) => {
    setMessageForm(prev => ({
      ...prev,
      message: message,
      subject: prev.subject || `Quick message - ${prev.message_type}`
    }));
  };

  const goToBulkNotification = () => {
    try {
      const pre = [{ id: student.id, name: `${student.first_name} ${student.last_name}`, first_name: student.first_name, last_name: student.last_name, email: student.email }];
      localStorage.setItem('preselectedUsers', JSON.stringify(pre));
      // Reload the dashboard so it picks up the preselected user and opens the bulk notification modal
      window.location.reload();
    } catch (e) {
      console.error('Failed to open bulk notifications with preselected student', e);
      alert('Failed to open bulk notifications');
    }
  };

  return (
    <>
      <button
        onClick={goToBulkNotification}
        className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
      >
        <MessageSquare className="w-4 h-4" />
        Send Message
      </button>

      {showModal && (
        <div className="fixed inset-0 bg-gray-600 bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg shadow-xl max-w-2xl w-full mx-4 max-h-[90vh] overflow-y-auto">
            <div className="px-6 py-4 border-b border-gray-200 flex items-center justify-between">
              <h2 className="text-xl font-semibold text-gray-900">
                Send Message to {student.first_name} {student.last_name}
              </h2>
              <button
                onClick={() => setShowModal(false)}
                className="text-gray-400 hover:text-gray-600"
              >
                <X className="w-5 h-5" />
              </button>
            </div>
            
            <div className="p-6 space-y-4">
              {/* Student Info */}
              <div className="bg-gray-50 p-3 rounded-lg">
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 bg-blue-100 rounded-full flex items-center justify-center">
                    <span className="text-blue-600 font-semibold">
                      {student.first_name?.[0]}{student.last_name?.[0]}
                    </span>
                  </div>
                  <div>
                    <p className="font-medium text-gray-900">
                      {student.first_name} {student.last_name}
                    </p>
                    <p className="text-sm text-gray-500">
                      Student ID: {student.student_id} | Section: {student.section_name}
                    </p>
                  </div>
                </div>
              </div>

              {/* Message Type and Priority */}
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Message Type</label>
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
                  <label className="block text-sm font-medium text-gray-700 mb-1">Send To</label>
                  <select
                    value={messageForm.receiver_type}
                    onChange={(e) => setMessageForm({...messageForm, receiver_type: e.target.value})}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  >
                    <option value="student">Student</option>
                    <option value="parent">Parent</option>
                    <option value="both">Both</option>
                  </select>
                </div>
              </div>

              <div className="flex items-center gap-4">
                <label className="flex items-center gap-2">
                  <input
                    type="checkbox"
                    checked={messageForm.is_report}
                    onChange={(e) => setMessageForm({...messageForm, is_report: e.target.checked})}
                    className="form-checkbox"
                  />
                  <span className="text-sm">Send as report</span>
                </label>
                <p className="text-xs text-gray-500">Toggle to send a formal report (will create a SentReport)</p>
              </div>

              {/* Quick Messages */}
              {quickMessages[messageForm.message_type] && (
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">Quick Messages</label>
                  <div className="grid grid-cols-1 gap-2">
                    {quickMessages[messageForm.message_type].map((msg, index) => (
                      <button
                        key={index}
                        onClick={() => handleQuickMessage(msg)}
                        className="text-left p-2 text-sm bg-gray-100 hover:bg-gray-200 rounded border transition-colors"
                      >
                        {msg}
                      </button>
                    ))}
                  </div>
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
                <p className="text-xs text-gray-500 mt-1">
                  {messageForm.message.length}/500 characters
                </p>
              </div>
            </div>

            <div className="px-6 py-4 border-t border-gray-200 flex justify-end gap-2">
              <button
                onClick={() => setShowModal(false)}
                className="px-4 py-2 text-gray-700 bg-gray-100 rounded-lg hover:bg-gray-200 transition-colors"
              >
                Cancel
              </button>
              <button
                onClick={sendMessage}
                disabled={loading || !messageForm.subject || !messageForm.message}
                className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors disabled:opacity-50 flex items-center gap-2"
              >
                <Send className="w-4 h-4" />
                {loading ? 'Sending...' : 'Send Message'}
              </button>
            </div>
          </div>
        </div>
      )}
    </>
  );
};

export default SendMessageButton;