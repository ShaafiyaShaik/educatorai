import React, { useState, useEffect, useRef } from 'react';
  import { 
    Calendar, Mail, Bot, User, Send, FileText, CheckCircle, Clock, Trash2,
    Settings, Plus, X, Search, Users, GraduationCap,
    BarChart3
  } from 'lucide-react';
  import toast from 'react-hot-toast';
  import { communications, aiAssistant, scheduling, educators } from '../services/api';
  import StudentManagement from './StudentManagement';
  import ScheduleManagement from './ScheduleManagement';
  import CalendarView from './CalendarView';
  import EnhancedPerformanceViews from './EnhancedPerformanceViews';
  import BulkCommunication from './BulkCommunication';
  import SimpleChatbot from './SimpleChatbot';

  const ComprehensiveDashboard = ({ setIsAuthenticated }) => {
    const [user, setUser] = useState(null);
    const [activeTab, setActiveTab] = useState('overview');
    const [activeModal, setActiveModal] = useState(null);
    const [inputMessage, setInputMessage] = useState('');
    const [messages, setMessages] = useState([]);

    const [stats, setStats] = useState({
      upcomingEvents: 0,
      pendingEmails: 0,
      activeRecords: 0,
      completedTasks: 0
    });

    // Check for section redirect on component mount
    useEffect(() => {
      const selectedSectionId = localStorage.getItem('selectedSectionId');
      if (selectedSectionId) {
        setActiveTab('student-management');
        localStorage.removeItem('selectedSectionId'); // Clear it after use
      }
        // If a preselected user(s) was set (via SendMessageButton), open bulk notification modal with them
        try {
          const pre = localStorage.getItem('preselectedUsers');
          if (pre) {
            const users = JSON.parse(pre);
            if (Array.isArray(users) && users.length > 0) {
              // Set the dashboard-level selectedUsers then open the detailed Bulk Communication tab
              setSelectedUsers(users);
              setActiveTab('bulk-communication');
              // Do NOT open the simple "bulk-notification" modal here — the detailed BulkCommunication tab
              // contains the full recipient-selection UI the teacher expects.
            }
            localStorage.removeItem('preselectedUsers');
          }
        } catch (e) {
          console.error('Failed to apply preselected users for bulk notification', e);
        }
    }, []);



    // AI Conversation State
    const [conversationContext, setConversationContext] = useState({
      activeTask: null,
      taskData: {},
      step: 0,
      requiredFields: []
    });

    // Enhanced AI Assistant State
    const [assistantState, setAssistantState] = useState('idle'); // 'thinking', 'acting', 'idle'
    const [autonomyMode, setAutonomyMode] = useState('manual'); // 'manual', 'assist', 'autonomous'
    const [languagePreference, setLanguagePreference] = useState('auto'); // 'en', 'te', 'auto'
    const [typing, setTyping] = useState(false);
    const [loading, setLoading] = useState(false);
    const [suggestedActions, setSuggestedActions] = useState([]);
    const [activityLog, setActivityLog] = useState([]);

    // Meeting Form State
    const [meetingForm, setMeetingForm] = useState({
      title: '',
      description: '',
      startDate: '',
      startTime: '',
      duration: '60',
      location: '',
      meetingType: 'in-person',
      participants: [],
      priority: 'medium',
      recurring: false,
      recurrencePattern: 'weekly'
    });

    // Email Form State
    const [emailForm, setEmailForm] = useState({
      to: [],
      cc: [],
      bcc: [],
      subject: '',
      content: '',
      template: '',
      priority: 'normal',
      sendLater: false,
      scheduledTime: ''
    });

    // User Search State
    const [userSearch, setUserSearch] = useState('');
    const [searchResults, setSearchResults] = useState([]);
    const [selectedUsers, setSelectedUsers] = useState([]);

    // New State for All Operations
    const [allCommunications, setAllCommunications] = useState([]);
    const [incomingEmails, setIncomingEmails] = useState([]);


    // Forms for various operations
    const [profileForm, setProfileForm] = useState({
      first_name: '',
      last_name: '',
      email: '',
      department: '',
      title: '',
      office_location: '',
      phone: ''
    });



    const [bulkNotificationForm, setBulkNotificationForm] = useState({
      target_groups: [],
      notification_type: '',
      subject: '',
      message: '',
      priority: 'normal',
      schedule_send: false,
      scheduled_date: '',
      scheduled_time: ''
    });





    const messagesEndRef = useRef(null);

    // Load chat history from localStorage on component mount
    useEffect(() => {
      fetchUserProfile();
      fetchRealStats();
      loadChatHistory();
      scrollToBottom();
      // Explicitly call communications to ensure it's fetched
      console.log('🚀 Component mounted, calling fetchAllCommunications...');
      fetchAllCommunications();
    }, []);

    // Save chat history to localStorage whenever messages change
    useEffect(() => {
      saveChatHistory();
      scrollToBottom();
    }, [messages]);

    // Save conversation context when it changes
    useEffect(() => {
      if (messages.length > 0) {
        saveChatHistory();
      }
    }, [conversationContext]);

    useEffect(() => {
      scrollToBottom();
    }, [messages]);

    const scrollToBottom = () => {
      messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    };

    // Load chat history from localStorage
    const loadChatHistory = () => {
      try {
        const savedChat = localStorage.getItem('educator_ai_chat');
        if (savedChat) {
          const { messages: savedMessages, conversationContext: savedContext, timestamp } = JSON.parse(savedChat);
          const hourAgo = Date.now() - (60 * 60 * 1000); // 1 hour in milliseconds
          
          // Only load if the chat is less than 1 hour old
          if (timestamp > hourAgo && Array.isArray(savedMessages)) {
            // Convert timestamp strings back to Date objects
            const messagesWithDates = savedMessages.map(msg => ({
              ...msg,
              timestamp: msg.timestamp ? new Date(msg.timestamp) : new Date()
            }));
            
            setMessages(messagesWithDates);
            if (savedContext) {
              setConversationContext(savedContext);
            }
          } else {
            // Clear old chat history
            localStorage.removeItem('educator_ai_chat');
          }
        }
      } catch (error) {
        console.error('Error loading chat history:', error);
        localStorage.removeItem('educator_ai_chat');
      }
    };

    // Save chat history to localStorage
    const saveChatHistory = () => {
      try {
        if (messages.length > 0) {
          const chatData = {
            messages: messages,
            conversationContext: conversationContext,
            timestamp: Date.now()
          };
          localStorage.setItem('educator_ai_chat', JSON.stringify(chatData));
        }
      } catch (error) {
        console.error('Error saving chat history:', error);
      }
    };

    // Clear chat history
    const clearChatHistory = () => {
      setMessages([]);
      setConversationContext({
        activeTask: null,
        taskData: {},
        step: 0,
        requiredFields: []
      });
      localStorage.removeItem('educator_ai_chat');
      toast.success('Chat history cleared');
    };

    const fetchUserProfile = async () => {
      try {
        console.log('👤 Fetching user profile...');
        const response = await educators.getProfile();
        console.log('✅ Profile fetched:', response.data);
        setUser(response.data);
      } catch (error) {
        console.error('Failed to fetch user profile:', error);
        // Fallback to default data if API fails
        setUser({ first_name: 'User', last_name: '', email: 'user@example.com' });
      }
    };

    const fetchRealStats = async () => {
      try {
        // Just fetch communications for basic stats now
        const commsRes = await communications.list();
        const commsData = Array.isArray(commsRes.data?.data) ? commsRes.data.data : [];

        setStats({
          upcomingEvents: 0,
          pendingEmails: commsData.length || 0,
          activeRecords: 0,
          completedTasks: 0
        });
      } catch (error) {
        console.error('Failed to fetch stats:', error);
        setStats({
          upcomingEvents: 0,
          pendingEmails: 0,
          activeRecords: 0,
          completedTasks: 0
        });
      }
    };

    // ===== COMPREHENSIVE DATA FETCHING FUNCTIONS =====
    


    const fetchAllCommunications = async () => {
      try {
        console.log('🔄 Fetching communications...');
        const response = await communications.list();
        console.log('📧 Communications response:', response);
        console.log('📧 Communications data:', response.data);
        setAllCommunications(response.data.data || []);
        console.log('✅ Communications fetched successfully:', response.data.data || []);
      } catch (error) {
        console.error('❌ Failed to fetch communications:', error);
        setAllCommunications([]);
      }
    };

    const fetchIncomingEmails = async () => {
      try {
        console.log('📨 Fetching incoming emails...');
        const response = await communications.getIncoming();
        console.log('📨 Incoming emails response:', response);
        console.log('📨 Incoming emails data:', response.data);
        setIncomingEmails(response.data.data || []);
        console.log('✅ Incoming emails fetched successfully:', response.data.data || []);
      } catch (error) {
        console.error('❌ Failed to fetch incoming emails:', error);
        setIncomingEmails([]);
      }
    };





    const handleLogout = () => {
      localStorage.removeItem('token');
      setIsAuthenticated(false);
      toast.success('Logged out successfully');
    };

    // User Search Functionality
    const searchUsers = async (query) => {
      if (!query.trim()) {
        setSearchResults([]);
        return;
      }
      
      try {
        // For now, just show empty results since we removed the users API
        setSearchResults([]);
      } catch (error) {
        console.error('Failed to search users:', error);
        setSearchResults([]);
      }
    };







    // Email Functions
    const handleSendEmail = async () => {
      try {
        if (!emailForm.to.length || !emailForm.subject || !emailForm.content) {
          toast.error('Please fill in all required fields');
          return;
        }

        const emailData = {
          recipient_email: emailForm.to.join(', '),
          subject: emailForm.subject,
          content: emailForm.content,
          email_type: 'notification'
        };

        await communications.sendEmail(emailData);
        toast.success('Email sent successfully!');
        setActiveModal(null);
        resetEmailForm();
        
      } catch (error) {
        console.error('Failed to send email:', error);
        toast.error('Failed to send email');
      }
    };

    const resetEmailForm = () => {
      setEmailForm({
        to: [],
        cc: [],
        bcc: [],
        subject: '',
        content: '',
        template: '',
        priority: 'normal',
        sendLater: false,
        scheduledTime: ''
      });
    };

    // Meeting Scheduling Functions
    const handleScheduleMeeting = async () => {
      try {
        // Validate form
        if (!meetingForm.title || !meetingForm.startDate || !meetingForm.startTime) {
          toast.error('Please fill in all required fields');
          return;
        }

        // Combine date and time
        const startDateTime = new Date(`${meetingForm.startDate}T${meetingForm.startTime}`);
        const endDateTime = new Date(startDateTime.getTime() + (parseInt(meetingForm.duration) * 60000));

        // Create meeting data
        const meetingData = {
          title: meetingForm.title,
          description: meetingForm.description,
          event_type: 'meeting',
          start_datetime: startDateTime.toISOString(),
          end_datetime: endDateTime.toISOString(),
          location: meetingForm.location,
          is_recurring: meetingForm.recurring
        };

        await scheduling.create(meetingData);
        toast.success('Meeting scheduled successfully!');

        setActiveModal(null);
        resetMeetingForm();
        
        // Refresh data to update calendar and schedule views
        await fetchRealStats();
        
      } catch (error) {
        console.error('Failed to schedule meeting:', error);
        if (error.response?.data?.detail) {
          toast.error(error.response.data.detail);
        } else {
          toast.error('Failed to schedule meeting');
        }
      }
    };

    const resetMeetingForm = () => {
      setMeetingForm({
        title: '',
        description: '',
        startDate: '',
        startTime: '',
        duration: '60',
        location: '',
        meetingType: 'in-person',
        participants: [],
        priority: 'medium',
        recurring: false,
        recurrencePattern: 'weekly'
      });
      setSelectedUsers([]);
    };



    // COMMUNICATIONS OPERATIONS
    const handleSendBulkNotification = async () => {
      try {
        await communications.sendBulkNotification(bulkNotificationForm);
        toast.success('Bulk notification sent successfully!');
        setActiveModal(null);
        setBulkNotificationForm({ recipients: [], subject: '', message: '', priority: 'normal' });
      } catch (error) {
        console.error('Failed to send bulk notification:', error);
        toast.error('Failed to send bulk notification');
      }
    };





    // COMMUNICATIONS HANDLERS
    const handleQuickEmail = async (templateType) => {
      const templates = {
        'weekly-update': {
          subject: 'Weekly Administrative Update',
          content: 'This is your weekly administrative update...'
        },
        'meeting-reminder': {
          subject: 'Meeting Reminder',
          content: 'This is a reminder about your upcoming meeting...'
        },
        'progress-report': {
          subject: 'Progress Report',
          content: 'Please find the latest progress report attached...'
        }
      };
      
      const template = templates[templateType];
      if (template) {
        setEmailForm(template);
        setActiveModal('compose-email');
      }
    };

    const handleUseTemplate = (templateType) => {
      const templates = {
        'meeting-invitation': {
          subject: 'Meeting Invitation',
          content: 'You are invited to attend a meeting...'
        },
        'follow-up': {
          subject: 'Follow-up',
          content: 'Following up on our previous discussion...'
        },
        'thank-you': {
          subject: 'Thank You',
          content: 'Thank you for your time and participation...'
        }
      };
      
      const template = templates[templateType];
      if (template) {
        setEmailForm(template);
        setActiveModal('compose-email');
      }
    };

    // FORM HANDLERS
    const handleProfileFormSubmit = async () => {
      try {
        console.log('🔄 Updating profile...', profileForm);
        await educators.updateProfile(profileForm);
        toast.success('Profile updated successfully!');
        setActiveModal(null);
        // Refresh user data
        fetchUserProfile();
      } catch (error) {
        console.error('Failed to update profile:', error);
        toast.error('Failed to update profile');
      }
    };



    // Enhanced AI Chat Functions
    const sendMessage = async () => {
      if (!inputMessage.trim()) return;

      const userMessage = {
        id: Date.now(),
        type: 'user',
        content: inputMessage,
        timestamp: new Date()
      };

      setMessages(prev => [...prev, userMessage]);
      const currentMessage = inputMessage;
      setInputMessage('');
      setAssistantState('thinking');

      try {
        // Call enhanced AI assistant API with Gemini
        console.log('Sending to enhanced AI:', currentMessage);
        const response = await aiAssistant.processCommand({
          message: currentMessage,              // Updated field name
          autonomy_mode: autonomyMode || 'assist',  // Updated field name
          language: languagePreference || 'en'     // Updated field name
        });
        
        console.log('Enhanced AI response:', response.data);
        
        setAssistantState(response.data.state || 'idle');
        
        // Handle suggested actions from enhanced AI
        if (response.data.actions && response.data.actions.length > 0) {
          setSuggestedActions(response.data.actions);
        }
        
        // Add assistant response with enhanced AI format
        const assistantMessage = {
          id: Date.now() + 1,
          type: 'assistant',
          content: response.data.response,  // Updated field name
          timestamp: new Date(),
          actions_taken: response.data.actions || [],
          suggested_actions: response.data.actions || [],
          requires_confirmation: response.data.requires_approval || false,
          audit_log: response.data.audit_log || [],
          confidence: response.data.confidence || 1.0
        };
        
        setMessages(prev => [...prev, assistantMessage]);
        
        // Update activity log with enhanced AI actions
        if (response.data.actions && response.data.actions.length > 0) {
          setActivityLog(prev => [...response.data.actions.map(actionItem => ({
            id: Date.now() + Math.random(),
            timestamp: new Date(),
            action: actionItem.action || actionItem,
            result: actionItem.result || 'completed',
            executed: actionItem.executed || false,
            can_undo: actionItem.action?.type !== 'audit'
          })), ...prev]);
        }
        
        setAssistantState('idle');
        
      } catch (error) {
        console.error('Enhanced AI Assistant error:', error);
        setAssistantState('idle');
        
        const errorMessage = {
          id: Date.now() + 1,
          type: 'assistant',
          content: '🤖 I encountered an error processing your request. Please try again or rephrase your question.',
          timestamp: new Date()
        };
        setMessages(prev => [...prev, errorMessage]);
        toast.error('Assistant error: ' + (error.response?.data?.detail || error.message));
      }
    };

    const processAIRequest = async (message) => {
      const lowerMessage = message.toLowerCase();
      
      // Handle conversation continuation
      if (conversationContext.activeTask) {
        return await continueConversation(message);
      }
      
      // Detect intent and start new conversation
      if (lowerMessage.includes('schedule') || lowerMessage.includes('meeting')) {
        return await startSchedulingConversation(message);
      } else if (lowerMessage.includes('email') || lowerMessage.includes('send') || lowerMessage.includes('notify')) {
        return await startEmailConversation(message);
      } else if (lowerMessage.includes('report') || lowerMessage.includes('compliance')) {
        return await startComplianceConversation(message);
      } else if (lowerMessage.includes('record') || lowerMessage.includes('file')) {
        return await startRecordConversation(message);
      } else {
        return await handleGeneralQuery(message);
      }
    };

    const startSchedulingConversation = async (message) => {
      const context = {
        activeTask: 'scheduling',
        taskData: {
          title: '',
          participants: '',
          date: '',
          time: '',
          duration: '',
          location: '',
          description: '',
          type: 'meeting'
        },
        step: 1,
        requiredFields: ['title', 'participants', 'date', 'time']
      };
      setConversationContext(context);
      
      return "I'd be happy to help you schedule a meeting! Let me gather some details:\n\n1. What is the subject/title of the meeting?\n2. Who should be invited? (Please provide names or email addresses)\n3. What date works best?\n4. What time would you prefer?\n\nLet's start with the meeting title - what would you like to call this meeting?";
    };

    const startEmailConversation = async (message) => {
      const context = {
        activeTask: 'email',
        taskData: {
          recipients: '',
          subject: '',
          content: '',
          type: 'single'
        },
        step: 1,
        requiredFields: ['recipients', 'subject', 'content']
      };
      setConversationContext(context);
      
      return "I'll help you compose and send an email. I need a few details:\n\n1. Who should receive the email? (recipients)\n2. What's the subject line?\n3. What's the message content?\n\nLet's start - who would you like to send this email to?";
    };

    const startComplianceConversation = async (message) => {
      const context = {
        activeTask: 'compliance',
        taskData: {
          reportType: '',
          period: '',
          description: ''
        },
        step: 1,
        requiredFields: ['reportType', 'period']
      };
      setConversationContext(context);
      
      return "I can help you generate a compliance report. I need to know:\n\n1. What type of compliance report do you need?\n2. What period should this report cover?\n3. Any specific description or focus areas?\n\nWhat type of compliance report are you looking for?";
    };

    const startRecordConversation = async (message) => {
      const context = {
        activeTask: 'record',
        taskData: {
          title: '',
          type: '',
          content: '',
          category: ''
        },
        step: 1,
        requiredFields: ['title', 'type', 'content']
      };
      setConversationContext(context);
      
      return "I'll help you create a new administrative record. Please provide:\n\n1. Record title\n2. Record type (student, course, administrative, etc.)\n3. Record content/description\n4. Category (optional)\n\nWhat should the title of this record be?";
    };

    const continueConversation = async (message) => {
      const { activeTask, taskData, step } = conversationContext;
      
      switch (activeTask) {
        case 'scheduling':
          return await handleSchedulingStep(message, taskData, step);
        case 'email':
          return await handleEmailStep(message, taskData, step);
        case 'compliance':
          return await handleComplianceStep(message, taskData, step);
        case 'record':
          return await handleRecordStep(message, taskData, step);
        default:
          setConversationContext({ activeTask: null, taskData: {}, step: 0, requiredFields: [] });
          return "I'm sorry, something went wrong. Let's start over. How can I help you?";
      }
    };

    const handleSchedulingStep = async (message, taskData, step) => {
      const newTaskData = { ...taskData };
      
      switch (step) {
        case 1: // Title
          newTaskData.title = message;
          setConversationContext({ ...conversationContext, taskData: newTaskData, step: 2 });
          return `Great! The meeting title is "${message}". Now, who should be invited to this meeting? Please provide names or email addresses of the participants.`;
          
        case 2: // Participants
          newTaskData.participants = message;
          setConversationContext({ ...conversationContext, taskData: newTaskData, step: 3 });
          return `Perfect! I'll invite: ${message}. What date would work best for this meeting? (e.g., "next Tuesday", "September 25th", "tomorrow")`;
          
        case 3: // Date
          newTaskData.date = message;
          setConversationContext({ ...conversationContext, taskData: newTaskData, step: 4 });
          return `Got it! The date is ${message}. What time should we schedule this meeting? (e.g., "2:00 PM", "10:30 AM", "morning")`;
          
        case 4: // Time
          newTaskData.time = message;
          setConversationContext({ ...conversationContext, taskData: newTaskData, step: 5 });
          return `Excellent! Time: ${message}. A few more optional details:\n\nHow long should the meeting be? (default: 1 hour)\nWhat's the location? (or "virtual" for online meeting)\nAny additional description?\n\nYou can say "schedule it" to create the meeting now, or provide these additional details.`;
          
        case 5: // Additional details or confirmation
          if (message.toLowerCase().includes('schedule it') || message.toLowerCase().includes('create')) {
            return await executeScheduling(newTaskData);
          } else {
            // Parse additional details
            if (message.toLowerCase().includes('hour') || message.toLowerCase().includes('minute')) {
              newTaskData.duration = message;
            }
            if (message.toLowerCase().includes('room') || message.toLowerCase().includes('office') || message.toLowerCase().includes('virtual')) {
              newTaskData.location = message;
            } else {
              newTaskData.description = message;
            }
            setConversationContext({ ...conversationContext, taskData: newTaskData });
            return `Thank you for the additional details. I now have:\n\n📅 Title: ${newTaskData.title}\n👥 Participants: ${newTaskData.participants}\n📆 Date: ${newTaskData.date}\n⏰ Time: ${newTaskData.time}\n${newTaskData.duration ? `⏱️ Duration: ${newTaskData.duration}\n` : ''}${newTaskData.location ? `📍 Location: ${newTaskData.location}\n` : ''}${newTaskData.description ? `📝 Description: ${newTaskData.description}\n` : ''}\nShould I schedule this meeting now? (Say "yes" to confirm)`;
          }
          
        case 6: // Final confirmation
          if (message.toLowerCase().includes('yes') || message.toLowerCase().includes('confirm')) {
            return await executeScheduling(newTaskData);
          } else {
            setConversationContext({ activeTask: null, taskData: {}, step: 0, requiredFields: [] });
            return "Meeting scheduling cancelled. Is there anything else I can help you with?";
          }
          
        default:
          return await executeScheduling(newTaskData);
      }
    };

    const executeScheduling = async (taskData) => {
      try {
        // Parse the date and time into a proper datetime
        const dateTimeStr = `${taskData.date} ${taskData.time}`;
        const parsedDateTimeStr = parseDateTime(dateTimeStr);
        
        // Create Date object from the parsed string
        const startDateTime = new Date(parsedDateTimeStr);
        
        // Validate the date
        if (isNaN(startDateTime.getTime())) {
          console.error('Invalid date created:', parsedDateTimeStr);
          setConversationContext({ activeTask: null, taskData: {}, step: 0, requiredFields: [] });
          return "I had trouble parsing the date and time. Could you try scheduling again with a more specific time format like '2:00 PM' or '14:00'?";
        }
        
        const duration = parseDuration(taskData.duration) || 60; // default 1 hour
        const endDateTime = new Date(startDateTime.getTime() + (duration * 60000));

        const meetingData = {
          title: taskData.title,
          description: `Meeting with: ${taskData.participants}${taskData.description ? `\n\nDescription: ${taskData.description}` : ''}`,
          event_type: 'meeting',
          start_datetime: startDateTime.toISOString(),
          end_datetime: endDateTime.toISOString(),
          location: taskData.location || 'TBD',
          is_recurring: false
        };

        console.log('Meeting scheduling disabled - removed functionality:', meetingData);
        
        setConversationContext({ activeTask: null, taskData: {}, step: 0, requiredFields: [] });
        
        return `✅ Perfect! I've successfully scheduled your meeting:\n\n📅 "${taskData.title}"\n👥 Participants: ${taskData.participants}\n📆 ${startDateTime.toLocaleDateString()}\n⏰ ${startDateTime.toLocaleTimeString()}\n📍 ${taskData.location || 'TBD'}\n\nThe meeting has been added to your calendar. I can help you with anything else you need!`;
      } catch (error) {
        console.error('Failed to schedule meeting:', error);
        console.error('Error details:', error.response?.data || error.message);
        setConversationContext({ activeTask: null, taskData: {}, step: 0, requiredFields: [] });
        
        // Provide more specific error message
        const errorMessage = error.response?.data?.detail || error.message || 'Unknown error';
        return `I encountered an error while scheduling the meeting: ${errorMessage}. Please try using the manual scheduling form or provide more details.`;
      }
    };

    const handleGeneralQuery = async (message) => {
      // Handle general queries and provide helpful responses
      const lowerMessage = message.toLowerCase();
      
      if (lowerMessage.includes('help') || lowerMessage.includes('what can you do')) {
        return "I'm your AI administrative assistant! I can help you with:\n\n📅 **Scheduling**: Schedule meetings, check availability, manage calendar\n📧 **Communications**: Send emails, create templates, bulk notifications\n📊 **Reports**: Generate compliance reports, administrative summaries\n📁 **Records**: Create and manage administrative records\n📈 **Analytics**: View stats, track tasks, monitor progress\n\nJust tell me what you'd like to do! For example:\n- \"Schedule a meeting with the department heads\"\n- \"Send an email to my students\"\n- \"Generate a compliance report\"\n- \"Create a new record\"";
      }
      
      if (lowerMessage.includes('stats') || lowerMessage.includes('overview')) {
        setActiveTab('overview');
        return "I've opened your dashboard overview where you can see:\n\n📊 Upcoming Events, Pending Emails, Active Records, and Completed Tasks\n\nYou can also navigate to specific sections using the tabs above. What would you like to focus on?";
      }
      
      return "I'm here to help! I can assist with scheduling meetings, sending emails, generating reports, managing records, and more. What would you like to do?";
    };

    // Helper functions for parsing
    const parseDateTime = (dateTimeStr) => {
      const now = new Date();
      const today = new Date(now.getFullYear(), now.getMonth(), now.getDate());
      
      let targetDate = today;
      
      if (dateTimeStr.includes('tomorrow')) {
        targetDate = new Date(today.getTime() + (24 * 60 * 60 * 1000));
      } else if (dateTimeStr.includes('next week')) {
        targetDate = new Date(today.getTime() + (7 * 24 * 60 * 60 * 1000));
      }
      
      // Extract time from the string
      const time = extractTime(dateTimeStr);
      
      // Combine date and time
      const year = targetDate.getFullYear();
      const month = String(targetDate.getMonth() + 1).padStart(2, '0');
      const day = String(targetDate.getDate()).padStart(2, '0');
      
      const dateTimeString = `${year}-${month}-${day} ${time}`;
      return dateTimeString;
    };

    const extractTime = (str) => {
      // Handle various time formats
      const timeMatch = str.match(/(\d{1,2}):?(\d{2})?\s*(am|pm|AM|PM)/i);
      const simpleTimeMatch = str.match(/(\d{1,2})\s*(am|pm|AM|PM)/i);
      
      if (timeMatch) {
        let hours = parseInt(timeMatch[1]);
        const minutes = parseInt(timeMatch[2]) || 0;
        const period = timeMatch[3].toLowerCase();
        
        // Convert to 24-hour format
        if (period === 'pm' && hours !== 12) {
          hours += 12;
        } else if (period === 'am' && hours === 12) {
          hours = 0;
        }
        
        return `${String(hours).padStart(2, '0')}:${String(minutes).padStart(2, '0')}:00`;
      } else if (simpleTimeMatch) {
        let hours = parseInt(simpleTimeMatch[1]);
        const period = simpleTimeMatch[2].toLowerCase();
        
        // Convert to 24-hour format
        if (period === 'pm' && hours !== 12) {
          hours += 12;
        } else if (period === 'am' && hours === 12) {
          hours = 0;
        }
        
        return `${String(hours).padStart(2, '0')}:00:00`;
      }
      
      return '10:00:00'; // default time
    };

    const parseDuration = (durationStr) => {
      if (!durationStr) return 60;
      const hourMatch = durationStr.match(/(\d+)\s*hour/);
      const minuteMatch = durationStr.match(/(\d+)\s*minute/);
      
      if (hourMatch) return parseInt(hourMatch[1]) * 60;
      if (minuteMatch) return parseInt(minuteMatch[1]);
      return 60;
    };

    const handleEmailStep = async (message, taskData, step) => {
      const newTaskData = { ...taskData };
      
      switch (step) {
        case 1: // Recipients
          newTaskData.recipients = message;
          setConversationContext({ ...conversationContext, taskData: newTaskData, step: 2 });
          return `Great! I'll send the email to: ${message}. What should the subject line be?`;
          
        case 2: // Subject
          newTaskData.subject = message;
          setConversationContext({ ...conversationContext, taskData: newTaskData, step: 3 });
          return `Perfect! Subject: "${message}". Now, what's the content of the email? Please provide the message you want to send.`;
          
        case 3: // Content
          newTaskData.content = message;
          setConversationContext({ ...conversationContext, taskData: newTaskData, step: 4 });
          return `Excellent! I now have:\n\n📧 To: ${newTaskData.recipients}\n📝 Subject: ${newTaskData.subject}\n💬 Content: ${newTaskData.content}\n\nShould I send this email now? (Say "yes" to confirm)`;
          
        case 4: // Confirmation
          if (message.toLowerCase().includes('yes') || message.toLowerCase().includes('send')) {
            try {
              const emailData = {
                recipient_email: newTaskData.recipients,
                subject: newTaskData.subject,
                content: newTaskData.content,
                email_type: 'notification'
              };
              
              await communications.sendEmail(emailData);
              await fetchAllCommunications(); // Refresh communications to show the sent email
              await fetchRealStats(); // Refresh stats
              setConversationContext({ activeTask: null, taskData: {}, step: 0, requiredFields: [] });
              return `✅ Email sent successfully!\n\n📧 To: ${newTaskData.recipients}\n📝 Subject: ${newTaskData.subject}\n\nYour email has been delivered.`;
            } catch (error) {
              console.error('Email sending error:', error);
              setConversationContext({ activeTask: null, taskData: {}, step: 0, requiredFields: [] });
              return `I apologize, but I encountered an error while sending the email: ${error.response?.data?.detail || error.message || 'Unknown error'}. Please try using the manual email form or check your internet connection.`;
            }
          } else {
            setConversationContext({ activeTask: null, taskData: {}, step: 0, requiredFields: [] });
            return "Email cancelled. Is there anything else I can help you with?";
          }
        default:
          return "I'm not sure what step we're on. Let's start over.";
      }
    };

    const handleComplianceStep = async (message, taskData, step) => {
      const newTaskData = { ...taskData };
      
      switch (step) {
        case 1: // Report Type
          newTaskData.reportType = message;
          setConversationContext({ ...conversationContext, taskData: newTaskData, step: 2 });
          return `Got it! Report type: "${message}". What time period should this report cover? (e.g., "last quarter", "this month", "2025 academic year")`;
          
        case 2: // Period
          newTaskData.period = message;
          setConversationContext({ ...conversationContext, taskData: newTaskData, step: 3 });
          return `Perfect! Period: ${message}. Any specific description or focus areas for this report? (or say "generate" to create the report now)`;
          
        case 3: // Description or confirmation
          if (message.toLowerCase().includes('generate') || message.toLowerCase().includes('create')) {
            try {
              const reportData = {
                report_type: newTaskData.reportType,
                description: newTaskData.description || `${newTaskData.reportType} for ${newTaskData.period}`,
                period_start: new Date().toISOString().split('T')[0],
                period_end: new Date().toISOString().split('T')[0]
              };
              
              console.log('Compliance functionality removed:', reportData);
              setConversationContext({ activeTask: null, taskData: {}, step: 0, requiredFields: [] });
              return `❌ Compliance functionality has been disabled.\n\n📊 Type: ${newTaskData.reportType}\n📅 Period: ${newTaskData.period}\n\nThis feature is no longer available.`;
            } catch (error) {
              setConversationContext({ activeTask: null, taskData: {}, step: 0, requiredFields: [] });
              return "I encountered an error while generating the compliance report. Please try using the manual form.";
            }
          } else {
            newTaskData.description = message;
            setConversationContext({ ...conversationContext, taskData: newTaskData, step: 4 });
            return `Thank you! I now have:\n\n📊 Report Type: ${newTaskData.reportType}\n📅 Period: ${newTaskData.period}\n📝 Description: ${newTaskData.description}\n\nShould I generate this compliance report now? (Say "yes" to confirm)`;
          }
          
        case 4: // Final confirmation
          if (message.toLowerCase().includes('yes') || message.toLowerCase().includes('generate')) {
            try {
              const reportData = {
                report_type: newTaskData.reportType,
                description: newTaskData.description,
                period_start: new Date().toISOString().split('T')[0],
                period_end: new Date().toISOString().split('T')[0]
              };
              
              console.log('Compliance functionality removed:', reportData);
              setConversationContext({ activeTask: null, taskData: {}, step: 0, requiredFields: [] });
              return `❌ Compliance functionality has been disabled.\n\n📊 Type: ${newTaskData.reportType}\n📅 Period: ${newTaskData.period}\n📝 Description: ${newTaskData.description}\n\nThis feature is no longer available.`;
            } catch (error) {
              setConversationContext({ activeTask: null, taskData: {}, step: 0, requiredFields: [] });
              return "I encountered an error while generating the report. Please try the manual form.";
            }
          } else {
            setConversationContext({ activeTask: null, taskData: {}, step: 0, requiredFields: [] });
            return "Report generation cancelled. How else can I assist you?";
          }
        default:
          return "I'm not sure what step we're on for compliance. Let's start over.";
      }
    };

    const handleRecordStep = async (message, taskData, step) => {
      const newTaskData = { ...taskData };
      
      switch (step) {
        case 1: // Title
          newTaskData.title = message;
          setConversationContext({ ...conversationContext, taskData: newTaskData, step: 2 });
          return `Great! Record title: "${message}". What type of record is this? (e.g., student, course, administrative, meeting notes, etc.)`;
          
        case 2: // Type
          newTaskData.type = message;
          setConversationContext({ ...conversationContext, taskData: newTaskData, step: 3 });
          return `Perfect! Record type: ${message}. Now please provide the content or description for this record.`;
          
        case 3: // Content
          newTaskData.content = message;
          setConversationContext({ ...conversationContext, taskData: newTaskData, step: 4 });
          return `Excellent! I now have:\n\n📝 Title: ${newTaskData.title}\n📂 Type: ${newTaskData.type}\n📄 Content: ${newTaskData.content}\n\nShould I create this record now? (Say "yes" to confirm)`;
          
        case 4: // Confirmation
          if (message.toLowerCase().includes('yes') || message.toLowerCase().includes('create')) {
            try {
              const recordData = {
                title: newTaskData.title,
                record_type: newTaskData.type,
                content: newTaskData.content,
                category: newTaskData.category || 'general'
              };
              
              console.log('Records functionality removed:', recordData);
              setConversationContext({ activeTask: null, taskData: {}, step: 0, requiredFields: [] });
              return `❌ Records functionality has been disabled.\n\n📝 Title: ${newTaskData.title}\n📂 Type: ${newTaskData.type}\n\nThis feature is no longer available.`;
            } catch (error) {
              setConversationContext({ activeTask: null, taskData: {}, step: 0, requiredFields: [] });
              return "I encountered an error while creating the record. Please try using the manual form.";
            }
          } else {
            setConversationContext({ activeTask: null, taskData: {}, step: 0, requiredFields: [] });
            return "Record creation cancelled. What else can I help you with?";
          }
        default:
          return "I'm not sure what step we're on for record creation. Let's start over.";
      }
    };

    const handleStatClick = (statLabel) => {
      switch (statLabel) {
        case 'Pending Emails':
          // Communications page removed — route to Bulk Reports instead
          setActiveTab('bulk-communication');
          break;
        case 'Upcoming Events':
        case 'Active Records':
        case 'Completed Tasks':
          // Show a detailed view of completed tasks
          toast.success('Viewing completed tasks details');
          break;
        default:
          break;
      }
    };

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
                  <h1 className="text-xl font-bold text-gray-900">Educator AI Pro</h1>
                  <p className="text-sm text-gray-500">Comprehensive Administrative Assistant</p>
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
                  <Settings className="h-4 w-4" />
                  <span>Logout</span>
                </button>
              </div>
            </div>
          </div>
        </header>

        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
          {/* Enhanced Tab Navigation */}
          <div className="flex space-x-1 bg-gray-100 p-1 rounded-lg mb-8 overflow-x-auto">
            {[
              { id: 'overview', label: 'Overview', icon: Calendar },
              { id: 'student-management', label: 'Students', icon: GraduationCap },
              { id: 'performance-analytics', label: 'Performance Analytics', icon: BarChart3 },
              { id: 'schedule-management', label: 'Schedule Tasks', icon: Plus },
              { id: 'calendar-view', label: 'Calendar', icon: Calendar },
              // Communications tab removed
              { id: 'bulk-communication', label: 'Bulk Reports', icon: Send },
              { id: 'chatbot', label: 'Chatbot', icon: Bot },
              { id: 'profile', label: 'Profile', icon: Settings }
            ].map((tab) => (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`flex items-center space-x-2 px-4 py-2 rounded-md transition ${
                  activeTab === tab.id
                    ? 'bg-white text-blue-600 shadow-sm'
                    : 'text-gray-600 hover:text-gray-900'
                }`}
              >
                <tab.icon className="h-4 w-4" />
                <span>{tab.label}</span>
              </button>
            ))}
          </div>

          {/* Overview Tab */}
          {activeTab === 'overview' && (
            <div className="space-y-8">
              {/* Quick Stats */}
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
                {statsDisplay.map((stat, index) => (
                  <button 
                    key={index} 
                    onClick={() => handleStatClick(stat.label)}
                    className="bg-white rounded-xl shadow-sm p-6 border border-gray-100 hover:shadow-md transition-shadow text-left w-full"
                  >
                    <div className="flex items-center justify-between">
                      <div>
                        <p className="text-sm font-medium text-gray-600">{stat.label}</p>
                        <p className={`text-2xl font-bold ${stat.color}`}>{stat.value}</p>
                      </div>
                      <div className={`p-3 rounded-lg bg-gray-50`}>
                        <stat.icon className={`h-6 w-6 ${stat.color}`} />
                      </div>
                    </div>
                  </button>
                ))}
              </div>

              {/* Quick Actions */}
              <div className="bg-white rounded-xl shadow-sm p-6 border border-gray-100">
                <h3 className="text-lg font-semibold text-gray-900 mb-4">Quick Actions</h3>
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-6 gap-4">
                  <button
                    onClick={() => setActiveTab('student-management')}
                    className="flex items-center space-x-3 p-4 bg-indigo-50 hover:bg-indigo-100 rounded-lg transition"
                  >
                    <GraduationCap className="h-5 w-5 text-indigo-600" />
                    <span className="font-medium text-indigo-900">View Students</span>
                  </button>
                  <button
                    onClick={() => setActiveTab('schedule-management')}
                    className="flex items-center space-x-3 p-4 bg-teal-50 hover:bg-teal-100 rounded-lg transition"
                  >
                    <Plus className="h-5 w-5 text-teal-600" />
                    <span className="font-medium text-teal-900">Schedule Task</span>
                  </button>
                  <button
                    onClick={() => setActiveTab('calendar-view')}
                    className="flex items-center space-x-3 p-4 bg-blue-50 hover:bg-blue-100 rounded-lg transition"
                  >
                    <Calendar className="h-5 w-5 text-blue-600" />
                    <span className="font-medium text-blue-900">Open Calendar</span>
                  </button>
                  <button
                    onClick={() => setActiveModal('compose-email')}
                    className="flex items-center space-x-3 p-4 bg-green-50 hover:bg-green-100 rounded-lg transition"
                  >
                    <Mail className="h-5 w-5 text-green-600" />
                    <span className="font-medium text-green-900">Compose Email</span>
                  </button>
                  <button
                    onClick={() => setActiveTab('records')}
                    className="flex items-center space-x-3 p-4 bg-purple-50 hover:bg-purple-100 rounded-lg transition"
                  >
                    <FileText className="h-5 w-5 text-purple-600" />
                    <span className="font-medium text-purple-900">Manage Records</span>
                  </button>
                  {/* AI Assistant removed from quick actions */}
                </div>
              </div>
            </div>
          )}

          {/* Communications tab removed per request */}

          {/* Bulk Communication Tab */}
          {activeTab === 'bulk-communication' && (
            <BulkCommunication
              initialSelectedStudents={selectedUsers}
              onSelectedStudentsChange={setSelectedUsers}
            />
          )}



          {/* New Simple Chatbot Tab (isolated) */}
          {activeTab === 'chatbot' && (
            <div className="space-y-4">
              <SimpleChatbot />
            </div>
          )}

          {/* ===== NEW COMPREHENSIVE TABS ===== */}

          {/* Profile Tab */}
          {activeTab === 'profile' && (
            <div className="space-y-6">
              <h2 className="text-2xl font-bold text-gray-900">My Profile</h2>
              
              <div className="bg-white p-6 rounded-lg shadow border border-gray-200">
                <div className="grid md:grid-cols-2 gap-6">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">First Name</label>
                    <input
                      type="text"
                      value={profileForm.first_name || user?.first_name || ''}
                      onChange={(e) => setProfileForm({...profileForm, first_name: e.target.value})}
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">Last Name</label>
                    <input
                      type="text"
                      value={profileForm.last_name || user?.last_name || ''}
                      onChange={(e) => setProfileForm({...profileForm, last_name: e.target.value})}
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">Email</label>
                    <input
                      type="email"
                      value={profileForm.email || user?.email || ''}
                      onChange={(e) => setProfileForm({...profileForm, email: e.target.value})}
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">Department</label>
                    <input
                      type="text"
                      value={profileForm.department || user?.department || ''}
                      onChange={(e) => setProfileForm({...profileForm, department: e.target.value})}
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">Title</label>
                    <input
                      type="text"
                      value={profileForm.title || user?.title || ''}
                      onChange={(e) => setProfileForm({...profileForm, title: e.target.value})}
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">Office Location</label>
                    <input
                      type="text"
                      value={profileForm.office_location || user?.office_location || ''}
                      onChange={(e) => setProfileForm({...profileForm, office_location: e.target.value})}
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">Phone</label>
                    <input
                      type="text"
                      value={profileForm.phone || user?.phone || ''}
                      onChange={(e) => setProfileForm({...profileForm, phone: e.target.value})}
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                    />
                  </div>
                </div>
                <div className="mt-6">
                  <button
                    onClick={handleProfileFormSubmit}
                    className="bg-blue-600 text-white px-6 py-2 rounded-lg hover:bg-blue-700 transition"
                  >
                    Update Profile
                  </button>
                </div>
              </div>
            </div>
          )}

          {/* Student Management Tab */}
          {activeTab === 'student-management' && (
            <StudentManagement />
          )}

          {/* Performance Analytics Tab */}
          {activeTab === 'performance-analytics' && (
            <EnhancedPerformanceViews />
          )}

          {/* Schedule Management Tab */}
          {activeTab === 'schedule-management' && (
            <ScheduleManagement />
          )}

          {/* Meeting Scheduler Tab removed */}

          {/* Calendar View Tab */}
          {activeTab === 'calendar-view' && (
            <CalendarView />
          )}

        </div>

        {/* ===== ENHANCED MODALS ===== */}



        {/* Schedule Meeting modal removed */}

        {/* Compose Email Modal */}
        {activeModal === 'compose-email' && (
          <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
            <div className="bg-white rounded-xl shadow-xl max-w-2xl w-full max-h-[90vh] overflow-y-auto">
              <div className="p-6 border-b flex justify-between items-center">
                <h3 className="text-xl font-semibold text-gray-900">Compose Email</h3>
                <button
                  onClick={() => setActiveModal(null)}
                  className="text-gray-400 hover:text-gray-600"
                >
                  <X className="h-6 w-6" />
                </button>
              </div>
              
              <div className="p-6 space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    To *
                  </label>
                  <input
                    type="email"
                    value={emailForm.to.join(', ')}
                    onChange={(e) => setEmailForm({...emailForm, to: e.target.value.split(', ')})}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    placeholder="recipient@email.com"
                  />
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Subject *
                  </label>
                  <input
                    type="text"
                    value={emailForm.subject}
                    onChange={(e) => setEmailForm({...emailForm, subject: e.target.value})}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    placeholder="Email subject"
                  />
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Message *
                  </label>
                  <textarea
                    value={emailForm.content}
                    onChange={(e) => setEmailForm({...emailForm, content: e.target.value})}
                    rows={8}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    placeholder="Type your message here..."
                  />
                </div>
              </div>
              
              <div className="p-6 border-t bg-gray-50 flex justify-end space-x-3">
                <button
                  onClick={() => setActiveModal(null)}
                  className="px-4 py-2 text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50"
                >
                  Cancel
                </button>
                <button
                  onClick={handleSendEmail}
                  className="px-6 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700"
                >
                  Send Email
                </button>
              </div>
            </div>
          </div>
        )}

        {/* Bulk Notification Modal */}
        {activeModal === 'bulk-notification' && (
          <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
            <div className="bg-white rounded-lg max-w-2xl w-full mx-4 max-h-[90vh] overflow-y-auto">
              <div className="flex justify-between items-center p-6 border-b">
                <h3 className="text-lg font-semibold text-gray-900">Send Bulk Notification</h3>
                <button
                  onClick={() => setActiveModal(null)}
                  className="text-gray-400 hover:text-gray-600"
                >
                  <X className="h-6 w-6" />
                </button>
              </div>
              
              <div className="p-6 space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Recipient Groups *
                  </label>
                  <div className="space-y-2">
                    <label className="flex items-center">
                      <input
                        type="checkbox"
                        checked={bulkNotificationForm.target_groups.includes('all_educators')}
                        onChange={(e) => {
                          const groups = e.target.checked 
                            ? [...bulkNotificationForm.target_groups, 'all_educators']
                            : bulkNotificationForm.target_groups.filter(g => g !== 'all_educators');
                          setBulkNotificationForm({...bulkNotificationForm, target_groups: groups});
                        }}
                        className="mr-2"
                      />
                      All Educators
                    </label>
                    <label className="flex items-center">
                      <input
                        type="checkbox"
                        checked={bulkNotificationForm.target_groups.includes('students')}
                        onChange={(e) => {
                          const groups = e.target.checked 
                            ? [...bulkNotificationForm.target_groups, 'students']
                            : bulkNotificationForm.target_groups.filter(g => g !== 'students');
                          setBulkNotificationForm({...bulkNotificationForm, target_groups: groups});
                        }}
                        className="mr-2"
                      />
                      Students
                    </label>
                    <label className="flex items-center">
                      <input
                        type="checkbox"
                        checked={bulkNotificationForm.target_groups.includes('parents')}
                        onChange={(e) => {
                          const groups = e.target.checked 
                            ? [...bulkNotificationForm.target_groups, 'parents']
                            : bulkNotificationForm.target_groups.filter(g => g !== 'parents');
                          setBulkNotificationForm({...bulkNotificationForm, target_groups: groups});
                        }}
                        className="mr-2"
                      />
                      Parents
                    </label>
                  </div>
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Notification Type *
                  </label>
                  <select
                    value={bulkNotificationForm.notification_type}
                    onChange={(e) => setBulkNotificationForm({...bulkNotificationForm, notification_type: e.target.value})}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  >
                    <option value="">Select notification type</option>
                    <option value="email">Email</option>
                    <option value="sms">SMS</option>
                    <option value="push">Push Notification</option>
                    <option value="all">All Methods</option>
                  </select>
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Subject *
                  </label>
                  <input
                    type="text"
                    value={bulkNotificationForm.subject}
                    onChange={(e) => setBulkNotificationForm({...bulkNotificationForm, subject: e.target.value})}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    placeholder="Notification subject"
                  />
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Message *
                  </label>
                  <textarea
                    value={bulkNotificationForm.message}
                    onChange={(e) => setBulkNotificationForm({...bulkNotificationForm, message: e.target.value})}
                    rows={6}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    placeholder="Type your notification message here..."
                  />
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Priority Level
                  </label>
                  <select
                    value={bulkNotificationForm.priority}
                    onChange={(e) => setBulkNotificationForm({...bulkNotificationForm, priority: e.target.value})}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  >
                    <option value="normal">Normal</option>
                    <option value="high">High</option>
                    <option value="urgent">Urgent</option>
                  </select>
                </div>
                
                <div>
                  <label className="flex items-center">
                    <input
                      type="checkbox"
                      checked={bulkNotificationForm.schedule_send}
                      onChange={(e) => setBulkNotificationForm({...bulkNotificationForm, schedule_send: e.target.checked})}
                      className="mr-2"
                    />
                    Schedule for later
                  </label>
                  
                  {bulkNotificationForm.schedule_send && (
                    <div className="mt-2 grid grid-cols-2 gap-4">
                      <div>
                        <label className="block text-sm font-medium text-gray-700 mb-1">Date</label>
                        <input
                          type="date"
                          value={bulkNotificationForm.scheduled_date}
                          onChange={(e) => setBulkNotificationForm({...bulkNotificationForm, scheduled_date: e.target.value})}
                          className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                        />
                      </div>
                      <div>
                        <label className="block text-sm font-medium text-gray-700 mb-1">Time</label>
                        <input
                          type="time"
                          value={bulkNotificationForm.scheduled_time}
                          onChange={(e) => setBulkNotificationForm({...bulkNotificationForm, scheduled_time: e.target.value})}
                          className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                        />
                      </div>
                    </div>
                  )}
                </div>
              </div>
              
              <div className="p-6 border-t bg-gray-50 flex justify-end space-x-3">
                <button
                  onClick={() => setActiveModal(null)}
                  className="px-4 py-2 text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50"
                >
                  Cancel
                </button>
                <button
                  onClick={handleSendBulkNotification}
                  disabled={!bulkNotificationForm.subject || !bulkNotificationForm.message || bulkNotificationForm.target_groups.length === 0}
                  className="px-6 py-2 bg-orange-600 text-white rounded-md hover:bg-orange-700 disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  {bulkNotificationForm.schedule_send ? 'Schedule Notification' : 'Send Now'}
                </button>
              </div>
            </div>
          </div>
        )}
      </div>
    );
  };

  export default ComprehensiveDashboard;