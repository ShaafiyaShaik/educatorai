import axios from 'axios';
import toast from 'react-hot-toast';

// Allow configuring the API base URL via environment variable at build time
// or via a runtime `window.API_BASE_URL` set by hosting platform. Fallback
// to localhost for local development.
const API_BASE_URL = process.env.REACT_APP_API_URL || (typeof window !== 'undefined' && window.API_BASE_URL) || 'http://localhost:8003';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor to add auth token
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Response interceptor to handle errors
api.interceptors.response.use(
  (response) => {
    return response;
  },
  (error) => {
    const isLoginAttempt = error.config?.url?.includes('/login');
    
    if (error.response?.status === 401) {
      if (isLoginAttempt) {
        // Don't redirect on login attempts, just show the error
        if (error.response?.data?.detail) {
          toast.error(error.response.data.detail);
        } else {
          toast.error('Invalid email or password');
        }
      } else {
        // Only redirect if user was already logged in and session expired
        localStorage.removeItem('token');
        toast.error('Session expired. Please login again.');
        window.location.href = '/login';
      }
    } else if (error.response?.data) {
      // Handle FastAPI validation errors
      const errorData = error.response.data;
      
      if (errorData.detail) {
        // If detail is an array of validation errors
        if (Array.isArray(errorData.detail)) {
          const messages = errorData.detail.map(err => {
            if (typeof err === 'object' && err.msg) {
              return `${err.loc ? err.loc.join('.') + ': ' : ''}${err.msg}`;
            }
            return String(err);
          });
          toast.error(messages.join(', '));
        } else {
          // If detail is a string
          toast.error(errorData.detail);
        }
      } else {
        toast.error('An error occurred');
      }
    } else {
      toast.error('Network error');
    }
    return Promise.reject(error);
  }
);

// ===== EDUCATORS API =====
export const educatorsAPI = {
  // POST /api/v1/educators/register - Register Educator
  register: (userData) => api.post('/api/v1/educators/register', userData),
  
  // POST /api/v1/educators/login - Login Educator
  login: (credentials) => {
    const formData = new FormData();
    formData.append('username', credentials.email || credentials.username);
    formData.append('password', credentials.password);
    return api.post('/api/v1/educators/login', formData, {
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' }
    });
  },
  
  // GET /api/v1/educators/me - Get Current Educator Profile
  getProfile: () => api.get('/api/v1/educators/me'),
  
  // PUT /api/v1/educators/me - Update Educator Profile
  updateProfile: (profileData) => api.put('/api/v1/educators/me', profileData),
  
  // GET /api/v1/educators/ - List Educators
  list: (params) => api.get('/api/v1/educators/', { params }),
  
  // GET /api/v1/educators/{educator_id} - Get Educator
  getById: (educatorId) => api.get(`/api/v1/educators/${educatorId}`)
};

// ===== SCHEDULING API =====
export const schedulingAPI = {
  // POST /api/v1/scheduling/ - Create Schedule Event
  create: (eventData) => api.post('/api/v1/scheduling/', eventData),
  
  // GET /api/v1/scheduling/ - Get Schedules
  list: (params) => api.get('/api/v1/scheduling/', { params }),
  
  // GET /api/v1/scheduling/{schedule_id} - Get Schedule Event
  getById: (scheduleId) => api.get(`/api/v1/scheduling/${scheduleId}`),
  
  // PUT /api/v1/scheduling/{schedule_id} - Update Schedule Event
  update: (scheduleId, eventData) => api.put(`/api/v1/scheduling/${scheduleId}`, eventData),
  
  // DELETE /api/v1/scheduling/{schedule_id} - Delete Schedule Event
  delete: (scheduleId) => api.delete(`/api/v1/scheduling/${scheduleId}`),
  
  // GET /api/v1/scheduling/today/events - Get Today Events
  getTodayEvents: () => api.get('/api/v1/scheduling/today/events'),
  
  // GET /api/v1/scheduling/upcoming/week - Get Week Schedule
  getWeekSchedule: () => api.get('/api/v1/scheduling/upcoming/week')
};

// ===== RECORDS API =====
export const recordsAPI = {
  // GET /api/v1/records/ - List Records
  list: (params) => api.get('/api/v1/records/', { params }),
  
  // POST /api/v1/records/ - Create Record
  create: (recordData) => api.post('/api/v1/records/', recordData)
};

// ===== COMPLIANCE API =====
export const complianceAPI = {
  // GET /api/v1/compliance/ - List Compliance Reports
  list: (params) => api.get('/api/v1/compliance/', { params }),
  
  // POST /api/v1/compliance/generate - Generate Compliance Report
  generate: (reportData) => api.post('/api/v1/compliance/generate', reportData)
};

// ===== COMMUNICATIONS API =====
export const communicationsAPI = {
  // GET /api/v1/communications/ - List Communications
  list: (params) => api.get('/api/v1/communications/', { params }),
  
  // GET /api/v1/communications/incoming - Get Incoming Communications
  getIncoming: (params) => api.get('/api/v1/communications/incoming', { params }),
  
  // POST /api/v1/communications/send-email - Send Email
  sendEmail: (emailData) => api.post('/api/v1/communications/send-email', emailData),
  
  // POST /api/v1/communications/bulk-notification - Send Bulk Notification
  sendBulkNotification: (notificationData) => api.post('/api/v1/communications/bulk-notification', notificationData),
  
  // POST /api/v1/communications/generate-template - Generate Communication Template
  generateTemplate: (templateData) => api.post('/api/v1/communications/generate-template', templateData),
  
  // POST /api/v1/communications/schedule-reminder - Schedule Reminder
  scheduleReminder: (reminderData) => api.post('/api/v1/communications/schedule-reminder', reminderData),
  
  // GET /api/v1/communications/templates - Get Communication Templates
  getTemplates: (params) => api.get('/api/v1/communications/templates', { params }),
  
  // GET /api/v1/communications/notification-history - Get Notification History
  getNotificationHistory: (params) => api.get('/api/v1/communications/notification-history', { params })
};

// ===== BULK COMMUNICATION API =====
export const bulkCommunicationAPI = {
  // POST /api/v1/bulk-communication/bulk-email - Send Bulk Performance Emails
  sendBulkEmail: (requestData) => api.post('/api/v1/bulk-communication/bulk-email', requestData),
  
  // GET /api/v1/bulk-communication/sections - Get Available Sections
  getSections: () => api.get('/api/v1/bulk-communication/sections'),
  
  // GET /api/v1/bulk-communication/students - Get Students
  getStudents: (params) => api.get('/api/v1/bulk-communication/students', { params }),
  
  // GET /api/v1/bulk-communication/email-templates - Get Email Templates
  getEmailTemplates: () => api.get('/api/v1/bulk-communication/email-templates'),
  
  // GET /api/v1/bulk-communication/sent-history - Get Sent Communication History
  getSentHistory: (params) => api.get('/api/v1/bulk-communication/sent-history', { params })
};

// ===== USERS API =====
export const usersAPI = {
  // GET /api/v1/users/search - Search Users
  search: (query, params) => api.get('/api/v1/users/search', { params: { q: query, ...params } }),
  
  // GET /api/v1/users/availability/{user_id} - Check User Availability
  getAvailability: (userId, params) => api.get(`/api/v1/users/availability/${userId}`, { params })
};

// ===== MEETING REQUESTS API =====
export const meetingRequestsAPI = {
  // POST /api/v1/meeting-requests/meeting-requests - Create Meeting Request
  create: (requestData) => api.post('/api/v1/meeting-requests/meeting-requests', requestData),
  
  // GET /api/v1/meeting-requests/meeting-requests/incoming - Get Incoming Requests
  getIncoming: (params) => api.get('/api/v1/meeting-requests/meeting-requests/incoming', { params }),
  
  // GET /api/v1/meeting-requests/meeting-requests/outgoing - Get Outgoing Requests
  getOutgoing: (params) => api.get('/api/v1/meeting-requests/meeting-requests/outgoing', { params }),
  
  // POST /api/v1/meeting-requests/meeting-requests/{request_id}/respond - Respond To Meeting Request
  respond: (requestId, responseData) => api.post(`/api/v1/meeting-requests/meeting-requests/${requestId}/respond`, responseData),
  
  // GET /api/v1/meeting-requests/conflicts - Check Schedule Conflicts
  checkConflicts: (params) => api.get('/api/v1/meeting-requests/conflicts', { params })
};

// ===== MEETING SCHEDULER API =====
export const meetingSchedulerAPI = {
  // POST /api/v1/meetings/ - Create Meeting
  create: (meetingData) => api.post('/api/v1/meetings/', meetingData),
  
  // GET /api/v1/meetings/ - Get My Meetings
  list: (params) => api.get('/api/v1/meetings/', { params }),
  
  // GET /api/v1/meetings/{meeting_id}/recipients - Get Meeting Recipients
  getRecipients: (meetingId) => api.get(`/api/v1/meetings/${meetingId}/recipients`),
  
  // DELETE /api/v1/meetings/{meeting_id} - Cancel Meeting
  cancel: (meetingId) => api.delete(`/api/v1/meetings/${meetingId}`),
  
  // GET /api/v1/meetings/my-sections - Get My Sections for Meetings
  getMySections: () => api.get('/api/v1/meetings/my-sections')
};

// ===== AI ASSISTANT API =====
export const aiAssistantAPI = {
  // POST /api/v1/gemini-assistant/enhanced-chat - Process AI Command with Gemini
  processCommand: (commandData) => api.post('/api/v1/gemini-assistant/enhanced-chat', {
    message: commandData.message || commandData.command,
    autonomy_mode: commandData.autonomy_mode || 'assist',
    language: commandData.language || 'en'
  }),
  
  // POST /api/v1/gemini-assistant/approve-action - Approve AI Action  
  approveAction: (actionId, approved, feedback) => api.post('/api/v1/gemini-assistant/approve-action', {
    action_id: actionId,
    approved: approved,
    feedback: feedback
  }),
  
  // GET /api/v1/gemini-assistant/status - Get Assistant Status
  getStatus: () => api.get('/api/v1/gemini-assistant/status'),
  
  // POST /api/v1/gemini-assistant/settings - Update Assistant Settings
  updateSettings: (settings) => api.post('/api/v1/gemini-assistant/settings', settings),
  
  // Legacy fallback to old assistant if needed
  processCommandLegacy: (commandData) => api.post('/api/v1/assistant/command', commandData),
  getSettings: () => api.get('/api/v1/assistant/settings'),
  getActivityLog: (limit = 50) => api.get('/api/v1/assistant/activity-log', { params: { limit } }),
  undoAction: (actionId) => api.post(`/api/v1/assistant/action/${actionId}/undo`)
};

// ===== HEALTH API =====
export const healthAPI = {
  // GET / - Root
  root: () => api.get('/'),
  
  // GET /health - Health Check
  healthCheck: () => api.get('/health')
};

// Export individual APIs and default api instance
export {
  educatorsAPI as educators,
  schedulingAPI as scheduling,
  recordsAPI as records,
  complianceAPI as compliance,
  communicationsAPI as communications,
  usersAPI as users,
  meetingRequestsAPI as meetingRequests,
  meetingSchedulerAPI as meetingScheduler,
  bulkCommunicationAPI as bulkCommunication,
  aiAssistantAPI as aiAssistant,
  healthAPI as health
};

export default api;