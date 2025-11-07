import React, { useState, useEffect, useRef } from 'react';
import { 
  LogOut, 
  Send, 
  Calendar, 
  FileText, 
  BarChart3, 
  Mail, 
  Bot, 
  User, 
  Plus,
  Clock,
  CheckCircle,
  AlertCircle,
  Settings
} from 'lucide-react';
import toast from 'react-hot-toast';
import api from '../services/api';

const Dashboard = ({ setIsAuthenticated }) => {
  const [user, setUser] = useState(null);
  const [activeTab, setActiveTab] = useState('chat');
  const [messages, setMessages] = useState([]);
  const [inputMessage, setInputMessage] = useState('');
  const [loading, setLoading] = useState(false);
  const [typing, setTyping] = useState(false);
  const [stats, setStats] = useState({
    upcomingEvents: 0,
    pendingEmails: 0,
    activeRecords: 0,
    completedTasks: 0
  });
  const messagesEndRef = useRef(null);

  useEffect(() => {
    fetchUserProfile();
    fetchRealStats();
    // Add welcome message
    setMessages([
      {
        id: 1,
        type: 'assistant',
        content: 'Hello! I\'m your AI administrative assistant. I can help you with real scheduling, record keeping, compliance reports, and communications. What would you like me to help you with today?',
        timestamp: new Date()
      }
    ]);
  }, []);

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  // Helper functions for extracting information from natural language
  const extractScheduleTitle = (message) => {
    const titlePatterns = [
      /schedule (a )?(.+?) (for|on|at)/i,
      /meeting (about|for) (.+?)(?:\s|$)/i,
      /(.*?) meeting/i
    ];
    
    for (const pattern of titlePatterns) {
      const match = message.match(pattern);
      if (match && match[2]) return match[2].trim();
    }
    return null;
  };

  const extractDateTime = (message) => {
    const now = new Date();
    
    if (message.includes('tomorrow')) {
      const tomorrow = new Date(now);
      tomorrow.setDate(tomorrow.getDate() + 1);
      tomorrow.setHours(14, 0, 0, 0); // Default 2 PM
      return tomorrow.toISOString();
    }
    
    if (message.includes('next week')) {
      const nextWeek = new Date(now);
      nextWeek.setDate(nextWeek.getDate() + 7);
      nextWeek.setHours(14, 0, 0, 0);
      return nextWeek.toISOString();
    }
    
    // Add more sophisticated date parsing here
    return null;
  };

  const extractLocation = (message) => {
    const locationPatterns = [
      /(?:at|in) (room \d+|conference room|office)/i,
      /location:? (.+?)(?:\s|$)/i
    ];
    
    for (const pattern of locationPatterns) {
      const match = message.match(pattern);
      if (match && match[1]) return match[1].trim();
    }
    return null;
  };

  const extractAttendees = (message) => {
    const emailPattern = /[\w.-]+@[\w.-]+\.\w+/g;
    const emails = message.match(emailPattern);
    return emails || [];
  };

  const extractEmail = (message) => {
    const emailPattern = /[\w.-]+@[\w.-]+\.\w+/;
    const match = message.match(emailPattern);
    return match ? match[0] : null;
  };

  const extractSubject = (message) => {
    const subjectPatterns = [
      /subject:? (.+?)(?:\n|$)/i,
      /about (.+?)(?:\s|$)/i,
      /regarding (.+?)(?:\s|$)/i
    ];
    
    for (const pattern of subjectPatterns) {
      const match = message.match(pattern);
      if (match && match[1]) return match[1].trim();
    }
    return null;
  };

  const extractStudentName = (message) => {
    const namePatterns = [
      /student (?:named? )?([A-Z][a-z]+ [A-Z][a-z]+)/i,
      /for ([A-Z][a-z]+ [A-Z][a-z]+)/i
    ];
    
    for (const pattern of namePatterns) {
      const match = message.match(pattern);
      if (match && match[1]) return match[1].trim();
    }
    return null;
  };

  const extractRecordType = (message) => {
    if (message.includes('grade')) return 'grades';
    if (message.includes('attendance')) return 'attendance';
    if (message.includes('assignment')) return 'assignments';
    if (message.includes('behavior')) return 'behavioral';
    return 'general';
  };

  const extractReportType = (message) => {
    if (message.includes('attendance')) return 'attendance_report';
    if (message.includes('grade')) return 'grade_report';
    if (message.includes('compliance')) return 'compliance_report';
    if (message.includes('activity')) return 'activity_report';
    return 'general_report';
  };

  const extractReportTitle = (message) => {
    const titlePatterns = [
      /generate (.+?) report/i,
      /report (?:on|about) (.+?)(?:\s|$)/i
    ];
    
    for (const pattern of titlePatterns) {
      const match = message.match(pattern);
      if (match && match[1]) return match[1].trim() + ' Report';
    }
    return null;
  };

  const fetchUserProfile = async () => {
    try {
      const response = await api.get('/api/v1/educators/me');
      setUser(response.data);
    } catch (error) {
      console.error('Failed to fetch user profile:', error);
    }
  };

  const fetchRealStats = async () => {
    try {
      // Fetch actual data from the database
      const [schedulesRes, recordsRes, complianceRes] = await Promise.all([
        api.get('/api/v1/scheduling/'),
        api.get('/api/v1/records'),
        api.get('/api/v1/compliance/')
      ]);

      const now = new Date();
      const scheduleData = Array.isArray(schedulesRes.data) ? schedulesRes.data : [];
      const recordData = Array.isArray(recordsRes.data) ? recordsRes.data : [];
      const complianceData = Array.isArray(complianceRes.data) ? complianceRes.data : [];
      
      const upcomingEvents = scheduleData.filter(event => 
        event?.start_datetime && new Date(event.start_datetime) > now
      ).length;

      setStats({
        upcomingEvents: upcomingEvents || 0,
        pendingEmails: 0, // Will be implemented with real email queue
        activeRecords: recordData.length || 0,
        completedTasks: complianceData.length || 0
      });
    } catch (error) {
      console.error('Failed to fetch stats:', error);
      // Reset to default values if there's an error
      setStats({
        upcomingEvents: 0,
        pendingEmails: 0,
        activeRecords: 0,
        completedTasks: 0
      });
    }
  };

  const handleLogout = () => {
    localStorage.removeItem('token');
    setIsAuthenticated(false);
    toast.success('Logged out successfully');
  };

  const sendMessage = async () => {
    if (!inputMessage.trim()) return;

    const userMessage = {
      id: Date.now(),
      type: 'user',
      content: inputMessage,
      timestamp: new Date()
    };

    setMessages(prev => [...prev, userMessage]);
    setInputMessage('');
    setTyping(true);

    try {
      // Simulate AI processing different types of requests
      const response = await processAIRequest(inputMessage);
      
      setTimeout(() => {
        const assistantMessage = {
          id: Date.now() + 1,
          type: 'assistant',
          content: response,
          timestamp: new Date()
        };
        setMessages(prev => [...prev, assistantMessage]);
        setTyping(false);
      }, 1500);

    } catch (error) {
      setTyping(false);
      toast.error('Failed to process request');
    }
  };

  const processAIRequest = async (message) => {
    const lowerMessage = message.toLowerCase();
    
    try {
      if (lowerMessage.includes('schedule') || lowerMessage.includes('meeting') || lowerMessage.includes('calendar')) {
        // Create actual schedule entry
        const scheduleData = {
          title: extractScheduleTitle(message) || 'New Meeting',
          description: message,
          event_type: 'meeting',
          start_datetime: extractDateTime(message) || new Date(Date.now() + 24*60*60*1000).toISOString(), // Default to tomorrow
          end_datetime: new Date(Date.now() + 25*60*60*1000).toISOString(), // Default 1 hour duration
          location: extractLocation(message) || 'TBD',
          is_recurring: false
        };
        
        const response = await api.post('/api/v1/scheduling/', scheduleData);
        await fetchRealStats(); // Update stats
        return `📅 Meeting scheduled successfully! Event created: "${scheduleData.title}" for ${new Date(scheduleData.start_datetime).toLocaleDateString()}. Event ID: ${response.data.id}`;
      }
      
      if (lowerMessage.includes('email') || lowerMessage.includes('send') || lowerMessage.includes('notification')) {
        // Prepare real email (you'll need to configure SMTP)
        const emailData = {
          recipient_email: extractEmail(message) || user?.email || 'admin@university.edu',
          subject: extractSubject(message) || 'Administrative Notification',
          content: message,
          email_type: 'notification'
        };
        
        const response = await api.post('/api/v1/communications/send-email', emailData);
        return `📧 Email prepared and queued for sending to ${emailData.recipient_email}. Subject: "${emailData.subject}". ${response.data.message || 'Email processing initiated.'}`;
      }
      
      if (lowerMessage.includes('record') || lowerMessage.includes('student') || lowerMessage.includes('grade')) {
        // Create actual record
        const recordData = {
          student_name: extractStudentName(message) || 'Student Record',
          record_type: extractRecordType(message) || 'general',
          content: message,
          metadata: { created_via: 'ai_assistant' }
        };
        
        const response = await api.post('/api/v1/records', recordData);
        await fetchRealStats(); // Update stats
        return `📋 Student record created successfully! Record ID: ${response.data.id} for ${recordData.student_name}. Type: ${recordData.record_type}`;
      }
      
      if (lowerMessage.includes('compliance') || lowerMessage.includes('report')) {
        // Generate actual compliance report
        const reportData = {
          report_type: extractReportType(message) || 'general_compliance',
          title: extractReportTitle(message) || 'Compliance Report',
          content: `Generated based on request: ${message}`,
          metadata: { 
            generated_via: 'ai_assistant',
            request_timestamp: new Date().toISOString()
          }
        };
        
        const response = await api.post('/api/v1/compliance/reports', reportData);
        await fetchRealStats(); // Update stats
        return `📊 Compliance report generated successfully! Report: "${reportData.title}" (ID: ${response.data.id}). The report covers ${reportData.report_type} and has been saved to the system.`;
      }

      // Default AI response for general conversation
      return `I'm here to help with your administrative tasks! I can:
      
🗓️ **Schedule real meetings** - Just tell me when and what for
📧 **Send actual emails** - Specify recipient and content  
� **Create student records** - Provide student name and details
� **Generate compliance reports** - Specify what type of report needed

What specific task would you like me to help you with?`;
      
    } catch (error) {
      console.error('AI Request processing error:', error);
      return `I encountered an error while processing your request: ${error.response?.data?.detail || error.message}. Please try again or be more specific about what you need.`;
    }
  };

  const quickActions = [
    { icon: Calendar, label: 'Schedule Meeting', action: () => setInputMessage('Schedule a meeting for tomorrow') },
    { icon: Mail, label: 'Send Email', action: () => setInputMessage('Help me send an email notification') },
    { icon: BarChart3, label: 'Generate Report', action: () => setInputMessage('Generate a compliance report') },
    { icon: FileText, label: 'Manage Records', action: () => setInputMessage('Help me with student records') }
  ];

  const statsDisplay = [
    { icon: Calendar, label: 'Upcoming Events', value: (stats.upcomingEvents || 0).toString(), color: 'text-blue-600' },
    { icon: Mail, label: 'Pending Emails', value: (stats.pendingEmails || 0).toString(), color: 'text-green-600' },
    { icon: FileText, label: 'Active Records', value: (stats.activeRecords || 0).toString(), color: 'text-purple-600' },
    { icon: CheckCircle, label: 'Completed Tasks', value: (stats.completedTasks || 0).toString(), color: 'text-emerald-600' }
  ];

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white shadow-sm border-b">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-16">
            <div className="flex items-center">
              <div className="bg-gradient-to-r from-blue-500 to-purple-600 rounded-lg p-2 mr-3">
                <Bot className="h-6 w-6 text-white" />
              </div>
              <div>
                <h1 className="text-xl font-bold text-gray-900">Educator AI</h1>
                <p className="text-sm text-gray-500">Administrative Assistant</p>
              </div>
            </div>
            
            <div className="flex items-center space-x-4">
              <div className="text-right">
                <p className="text-sm font-medium text-gray-900">
                  {user?.full_name || 'Loading...'}
                </p>
                <p className="text-xs text-gray-500">{user?.department}</p>
              </div>
              <button
                onClick={handleLogout}
                className="flex items-center space-x-2 text-gray-500 hover:text-gray-700 transition"
              >
                <LogOut className="h-5 w-5" />
                <span>Logout</span>
              </button>
            </div>
          </div>
        </div>
      </header>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="grid grid-cols-1 lg:grid-cols-4 gap-8">
          {/* Sidebar */}
          <div className="lg:col-span-1">
            <div className="bg-white rounded-xl shadow-sm p-6 mb-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">Quick Stats</h3>
              <div className="space-y-4">
                {statsDisplay.map((stat, index) => (
                  <div key={index} className="flex items-center space-x-3">
                    <div className={`p-2 rounded-lg bg-gray-100`}>
                      <stat.icon className={`h-5 w-5 ${stat.color}`} />
                    </div>
                    <div>
                      <p className="text-2xl font-bold text-gray-900">{stat.value}</p>
                      <p className="text-sm text-gray-500">{stat.label}</p>
                    </div>
                  </div>
                ))}
              </div>
            </div>

            <div className="bg-white rounded-xl shadow-sm p-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">Quick Actions</h3>
              <div className="space-y-2">
                {quickActions.map((action, index) => (
                  <button
                    key={index}
                    onClick={action.action}
                    className="w-full flex items-center space-x-3 p-3 text-left hover:bg-gray-50 rounded-lg transition"
                  >
                    <action.icon className="h-5 w-5 text-blue-600" />
                    <span className="text-sm font-medium text-gray-700">{action.label}</span>
                  </button>
                ))}
              </div>
            </div>
          </div>

          {/* Main Content */}
          <div className="lg:col-span-3">
            <div className="bg-white rounded-xl shadow-sm h-[calc(100vh-12rem)]">
              {/* Chat Header */}
              <div className="border-b px-6 py-4">
                <div className="flex items-center space-x-3">
                  <div className="bg-gradient-to-r from-blue-500 to-purple-600 rounded-full p-2">
                    <Bot className="h-5 w-5 text-white" />
                  </div>
                  <div>
                    <h2 className="text-lg font-semibold text-gray-900">AI Assistant</h2>
                    <p className="text-sm text-gray-500">Ready to help with your administrative tasks</p>
                  </div>
                </div>
              </div>

              {/* Chat Messages */}
              <div className="flex-1 overflow-y-auto p-6 h-[calc(100%-8rem)]">
                <div className="space-y-4">
                  {messages.map((message) => (
                    <div
                      key={message.id}
                      className={`flex items-start space-x-3 ${
                        message.type === 'user' ? 'flex-row-reverse space-x-reverse' : ''
                      }`}
                    >
                      <div className={`flex-shrink-0 w-8 h-8 rounded-full flex items-center justify-center ${
                        message.type === 'user' 
                          ? 'bg-blue-600' 
                          : 'bg-gradient-to-r from-purple-500 to-pink-500'
                      }`}>
                        {message.type === 'user' ? (
                          <User className="h-4 w-4 text-white" />
                        ) : (
                          <Bot className="h-4 w-4 text-white" />
                        )}
                      </div>
                      <div className={`max-w-xs lg:max-w-md xl:max-w-lg ${
                        message.type === 'user' ? 'text-right' : ''
                      }`}>
                        <div className={`inline-block p-4 rounded-2xl ${
                          message.type === 'user'
                            ? 'bg-blue-600 text-white'
                            : 'bg-gray-100 text-gray-900'
                        }`}>
                          <p className="text-sm whitespace-pre-wrap">{message.content || ''}</p>
                        </div>
                        <p className="text-xs text-gray-500 mt-1">
                          {message.timestamp ? message.timestamp.toLocaleTimeString() : 'Now'}
                        </p>
                      </div>
                    </div>
                  ))}
                  
                  {typing && (
                    <div className="flex items-start space-x-3">
                      <div className="flex-shrink-0 w-8 h-8 rounded-full bg-gradient-to-r from-purple-500 to-pink-500 flex items-center justify-center">
                        <Bot className="h-4 w-4 text-white" />
                      </div>
                      <div className="bg-gray-100 rounded-2xl p-4">
                        <div className="flex space-x-1">
                          <div className="typing-indicator"></div>
                          <div className="typing-indicator"></div>
                          <div className="typing-indicator"></div>
                        </div>
                      </div>
                    </div>
                  )}
                </div>
                <div ref={messagesEndRef} />
              </div>

              {/* Chat Input */}
              <div className="border-t p-4">
                <div className="flex space-x-4">
                  <input
                    type="text"
                    value={inputMessage}
                    onChange={(e) => setInputMessage(e.target.value)}
                    onKeyPress={(e) => e.key === 'Enter' && sendMessage()}
                    placeholder="Ask me anything about administrative tasks..."
                    className="flex-1 px-4 py-3 border border-gray-300 rounded-full focus:ring-2 focus:ring-blue-500 focus:border-transparent transition"
                    disabled={loading || typing}
                  />
                  <button
                    onClick={sendMessage}
                    disabled={loading || typing || !inputMessage.trim()}
                    className="bg-gradient-to-r from-blue-500 to-purple-600 text-white rounded-full p-3 hover:from-blue-600 hover:to-purple-700 transition disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    <Send className="h-5 w-5" />
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Dashboard;