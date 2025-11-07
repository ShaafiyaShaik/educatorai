import React, { useState, useRef, useEffect } from 'react';
import { 
  MessageCircle, 
  Send, 
  Settings, 
  Bot, 
  User, 
  CheckCircle,
  AlertTriangle,
  Clock,
  Loader,
  Volume2,
  Globe
} from 'lucide-react';
import toast from 'react-hot-toast';
import api from '../services/api';

const EnhancedAIAssistant = () => {
  const [messages, setMessages] = useState([]);
  const [inputMessage, setInputMessage] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [assistantStatus, setAssistantStatus] = useState({
    state: 'idle',
    autonomy_mode: 'assist',
    language: 'en'
  });
  const [showSettings, setShowSettings] = useState(false);
  const [pendingActions, setPendingActions] = useState([]);
  const [auditLog, setAuditLog] = useState([]);
  const messagesEndRef = useRef(null);

  const autonomyModes = [
    { value: 'manual', label: 'Manual - Always ask for confirmation' },
    { value: 'assist', label: 'Assist - Auto low-risk, ask for high-risk' },
    { value: 'autonomous', label: 'Autonomous - Auto all allowed actions' }
  ];

  const languages = [
    { value: 'en', label: 'English' },
    { value: 'te', label: 'Telugu (తెలుగు)' }
  ];

  const teluguExamples = [
    "నా షెడ్యూల్ చూపించు",
    "విద్యార్థుల గ్రేడ్స్ చూపించు", 
    "ఇమెయిల్ పంపించు",
    "రిపోర్ట్ తయారు చేయి",
    "రేపటి మీటింగ్లు ఏవైనా ఉన్నాయా?"
  ];

  const quickActions = [
    { id: 'daily_summary', label: 'Daily Summary', icon: '📊' },
    { id: 'check_calendar', label: 'Check Calendar', icon: '📅' },
    { id: 'student_alerts', label: 'Student Alerts', icon: '🚨' },
    { id: 'performance_overview', label: 'Performance Overview', icon: '📈' },
    { id: 'compliance_status', label: 'Compliance Status', icon: '✅' }
  ];

  useEffect(() => {
    // Load persisted messages from localStorage (persist chat between reloads)
    try {
      const saved = localStorage.getItem('eduassist_messages');
      if (saved) {
        setMessages(JSON.parse(saved));
      } else {
        fetchAssistantStatus();
      }
    } catch (e) {
      fetchAssistantStatus();
    }
    scrollToBottom();
  }, []);

  useEffect(() => {
    scrollToBottom();
    // Persist messages to localStorage whenever they change
    try {
      localStorage.setItem('eduassist_messages', JSON.stringify(messages));
    } catch (e) {
      // ignore storage errors
    }
  }, [messages]);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  const fetchAssistantStatus = async () => {
    try {
      const response = await api.get('/api/v1/gemini-assistant/enhanced-status');
      setAssistantStatus(response.data);
      
      // Add welcome message if no messages
      if (messages.length === 0) {
        const welcomeMessage = {
          id: Date.now(),
          type: 'assistant',
          content: `Hello! I'm EduAssist AI, your intelligent administrative assistant. I'm currently in ${response.data.autonomy_mode} mode and ready to help you manage your administrative tasks efficiently.`,
          timestamp: new Date().toISOString(),
          actions: []
        };
        setMessages([welcomeMessage]);
      }
    } catch (error) {
      console.error('Failed to fetch assistant status:', error);
      toast.error('Failed to connect to AI assistant');
    }
  };

  const sendMessage = async () => {
    if (!inputMessage.trim() || isLoading) return;

    const userMessage = {
      id: Date.now(),
      type: 'user',
      content: inputMessage,
      timestamp: new Date().toISOString()
    };

    setMessages(prev => [...prev, userMessage]);
    setIsLoading(true);
    
    const messageToSend = inputMessage;
    setInputMessage('');

    try {
      // Include recent conversation history when calling backend so Gemini can maintain context
      const history = messages.map(m => ({ type: m.type, content: m.content, timestamp: m.timestamp }));
      const response = await api.post('/api/v1/gemini-assistant/enhanced-chat', {
        message: messageToSend,
        autonomy_mode: assistantStatus.autonomy_mode,
        language: assistantStatus.language,
        history
      });

      const assistantMessage = {
        id: Date.now() + 1,
        type: 'assistant',
        content: response.data.response,
        timestamp: response.data.timestamp,
        actions: response.data.actions,
        requires_approval: response.data.requires_approval,
        state: response.data.state
      };

      setMessages(prev => [...prev, assistantMessage]);
      setAssistantStatus(prev => ({ ...prev, state: response.data.state }));
      
      if (response.data.requires_approval && response.data.actions.length > 0) {
        setPendingActions(response.data.actions.filter(action => !action.executed));
      }

      if (response.data.audit_log) {
        setAuditLog(response.data.audit_log);
      }

    } catch (error) {
      console.error('Chat error:', error);
      const errorMessage = {
        id: Date.now() + 1,
        type: 'assistant',
        content: 'I apologize, but I encountered an error processing your request. Please try again.',
        timestamp: new Date().toISOString(),
        actions: [],
        error: true
      };
      setMessages(prev => [...prev, errorMessage]);
      toast.error('Failed to send message');
    } finally {
      setIsLoading(false);
    }
  };

  const executeQuickAction = async (actionId) => {
    try {
      setIsLoading(true);
      const response = await api.post(`/api/v1/gemini-assistant/quick-actions/${actionId}`);
      
      const quickActionMessage = {
        id: Date.now(),
        type: 'assistant',
        content: response.data.result.response,
        timestamp: new Date().toISOString(),
        actions: response.data.result.actions,
        quickAction: actionId
      };

      setMessages(prev => [...prev, quickActionMessage]);
      toast.success(`Quick action "${actionId}" executed`);
    } catch (error) {
      console.error('Quick action error:', error);
      toast.error('Failed to execute quick action');
    } finally {
      setIsLoading(false);
    }
  };

  const approveAction = async (actionId, approved) => {
    try {
      await api.post('/api/v1/gemini-assistant/approve-action', {
        action_id: actionId,
        approved: approved
      });

      setPendingActions(prev => prev.filter(action => action.id !== actionId));
      toast.success(approved ? 'Action approved' : 'Action rejected');
    } catch (error) {
      console.error('Action approval error:', error);
      toast.error('Failed to process action approval');
    }
  };

  const updateSettings = async (newSettings) => {
    try {
      await api.post('/api/v1/gemini-assistant/settings', newSettings);
      setAssistantStatus(prev => ({ ...prev, ...newSettings }));
      toast.success('Settings updated successfully');
      setShowSettings(false);
    } catch (error) {
      console.error('Settings update error:', error);
      toast.error('Failed to update settings');
    }
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  const getStateIcon = (state) => {
    switch (state) {
      case 'thinking': return <Loader className="animate-spin" size={16} />;
      case 'acting': return <Clock className="animate-pulse" size={16} />;
      case 'waiting_approval': return <AlertTriangle size={16} />;
      default: return <CheckCircle size={16} />;
    }
  };

  const getStateColor = (state) => {
    switch (state) {
      case 'thinking': return 'text-blue-500';
      case 'acting': return 'text-orange-500';
      case 'waiting_approval': return 'text-yellow-500';
      default: return 'text-green-500';
    }
  };

  return (
    <div className="flex flex-col h-full bg-white rounded-lg shadow-lg">
      {/* Header */}
      <div className="flex items-center justify-between p-4 border-b bg-gradient-to-r from-blue-500 to-purple-600 text-white rounded-t-lg">
        <div className="flex items-center space-x-3">
          <Bot size={24} />
          <div>
            <h3 className="font-semibold">EduAssist AI</h3>
            <div className="flex items-center space-x-2 text-sm opacity-90">
              {getStateIcon(assistantStatus.state)}
              <span className="capitalize">{assistantStatus.state}</span>
              <span>•</span>
              <span className="capitalize">{assistantStatus.autonomy_mode}</span>
              {assistantStatus.language === 'te' && (
                <>
                  <span>•</span>
                  <Globe size={12} />
                  <span>తెలుగు</span>
                </>
              )}
            </div>
          </div>
        </div>
        <button
          onClick={() => setShowSettings(!showSettings)}
          className="p-2 hover:bg-white/20 rounded-lg transition-colors"
        >
          <Settings size={20} />
        </button>
      </div>

      {/* Settings Panel */}
      {showSettings && (
        <div className="p-4 bg-gray-50 border-b">
          <h4 className="font-medium mb-3">Assistant Settings</h4>
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Autonomy Mode
              </label>
              <select
                value={assistantStatus.autonomy_mode}
                onChange={(e) => updateSettings({ autonomy_mode: e.target.value })}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 text-sm"
              >
                {autonomyModes.map(mode => (
                  <option key={mode.value} value={mode.value}>
                    {mode.label}
                  </option>
                ))}
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Language
              </label>
              <select
                value={assistantStatus.language}
                onChange={(e) => updateSettings({ language: e.target.value })}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 text-sm"
              >
                {languages.map(lang => (
                  <option key={lang.value} value={lang.value}>
                    {lang.label}
                  </option>
                ))}
              </select>
            </div>
          </div>
        </div>
      )}

      {/* Quick Actions */}
      <div className="p-4 border-b">
        <h4 className="text-sm font-medium text-gray-700 mb-2">Quick Actions</h4>
        <div className="flex flex-wrap gap-2">
          {quickActions.map(action => (
            <button
              key={action.id}
              onClick={() => executeQuickAction(action.id)}
              disabled={isLoading}
              className="flex items-center space-x-1 px-3 py-1 bg-blue-100 text-blue-700 rounded-full text-sm hover:bg-blue-200 transition-colors disabled:opacity-50"
            >
              <span>{action.icon}</span>
              <span>{action.label}</span>
            </button>
          ))}
        </div>
        
        {/* Telugu Examples */}
        {assistantStatus.language === 'te' && (
          <div className="mt-3">
            <h5 className="text-xs font-medium text-gray-600 mb-1">Telugu Examples:</h5>
            <div className="flex flex-wrap gap-1">
              {teluguExamples.map((example, index) => (
                <button
                  key={index}
                  onClick={() => setInputMessage(example)}
                  className="px-2 py-1 bg-purple-100 text-purple-700 rounded text-xs hover:bg-purple-200 transition-colors"
                >
                  {example}
                </button>
              ))}
            </div>
          </div>
        )}
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {messages.map((message) => (
          <div
            key={message.id}
            className={`flex ${message.type === 'user' ? 'justify-end' : 'justify-start'}`}
          >
            <div
              className={`max-w-[80%] rounded-lg p-3 ${
                message.type === 'user'
                  ? 'bg-blue-500 text-white'
                  : message.error
                  ? 'bg-red-100 text-red-800 border border-red-200'
                  : 'bg-gray-100 text-gray-800'
              }`}
            >
              <div className="flex items-start space-x-2">
                <div className="flex-shrink-0 mt-1">
                  {message.type === 'user' ? (
                    <User size={16} />
                  ) : (
                    <Bot size={16} className={message.error ? 'text-red-500' : 'text-blue-500'} />
                  )}
                </div>
                <div className="flex-1">
                  <p className="text-sm whitespace-pre-wrap">{message.content}</p>
                  
                  {/* Actions */}
                  {message.actions && message.actions.length > 0 && (
                    <div className="mt-2 space-y-2">
                      {message.actions.map((action, index) => (
                        <div
                          key={index}
                          className="bg-white/50 rounded p-2 text-xs border"
                        >
                          <div className="flex items-center justify-between">
                            <span className="font-medium">{action.action.description}</span>
                            <span className={`px-2 py-1 rounded text-xs ${
                              action.executed 
                                ? 'bg-green-100 text-green-800' 
                                : 'bg-yellow-100 text-yellow-800'
                            }`}>
                              {action.executed ? 'Executed' : 'Pending Approval'}
                            </span>
                          </div>
                          {!action.executed && message.requires_approval && (
                            <div className="flex space-x-2 mt-2">
                              <button
                                onClick={() => approveAction(action.action.id, true)}
                                className="px-2 py-1 bg-green-100 text-green-800 rounded text-xs hover:bg-green-200"
                              >
                                Approve
                              </button>
                              <button
                                onClick={() => approveAction(action.action.id, false)}
                                className="px-2 py-1 bg-red-100 text-red-800 rounded text-xs hover:bg-red-200"
                              >
                                Reject
                              </button>
                            </div>
                          )}
                        </div>
                      ))}
                    </div>
                  )}
                  
                  <div className="flex items-center justify-between mt-2 text-xs opacity-70">
                    <span>{new Date(message.timestamp).toLocaleTimeString()}</span>
                    {message.state && (
                      <div className={`flex items-center space-x-1 ${getStateColor(message.state)}`}>
                        {getStateIcon(message.state)}
                        <span className="capitalize">{message.state}</span>
                      </div>
                    )}
                  </div>
                </div>
              </div>
            </div>
          </div>
        ))}
        
        {isLoading && (
          <div className="flex justify-start">
            <div className="bg-gray-100 rounded-lg p-3 max-w-[80%]">
              <div className="flex items-center space-x-2">
                <Bot size={16} className="text-blue-500" />
                <Loader className="animate-spin" size={16} />
                <span className="text-sm text-gray-600">AI is thinking...</span>
              </div>
            </div>
          </div>
        )}
        
        <div ref={messagesEndRef} />
      </div>

      {/* Input */}
      <div className="p-4 border-t">
        <div className="flex space-x-2">
          <input
            type="text"
            value={inputMessage}
            onChange={(e) => setInputMessage(e.target.value)}
            onKeyPress={handleKeyPress}
            placeholder={
              assistantStatus.language === 'te' 
                ? "మీ సందేశం టైప్ చేయండి..." 
                : "Type your message..."
            }
            disabled={isLoading}
            className="flex-1 px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 disabled:opacity-50"
          />
          <button
            onClick={sendMessage}
            disabled={!inputMessage.trim() || isLoading}
            className="px-4 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600 disabled:opacity-50 disabled:cursor-not-allowed flex items-center space-x-2"
          >
            <Send size={16} />
          </button>
        </div>
        
        <div className="flex items-center justify-between mt-2 text-xs text-gray-500">
          <span>
            Mode: <span className="capitalize font-medium">{assistantStatus.autonomy_mode}</span>
            {assistantStatus.language === 'te' && " • తెలుగు"}
          </span>
          <span>Press Enter to send</span>
        </div>
      </div>
    </div>
  );
};

export default EnhancedAIAssistant;