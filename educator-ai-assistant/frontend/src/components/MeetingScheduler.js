import React, { useState, useEffect } from 'react';
import { 
  Calendar, Users, User, Clock, MapPin, Link2, 
  Send, X, Plus, AlertCircle, CheckCircle2 
} from 'lucide-react';
import toast from 'react-hot-toast';
import { meetingScheduler } from '../services/api';

const MeetingScheduler = () => {
  const [meetings, setMeetings] = useState([]);
  const [sections, setSections] = useState([]);
  const [showCreateForm, setShowCreateForm] = useState(false);
  const [loading, setLoading] = useState(false);

  const [formData, setFormData] = useState({
    event_category: 'meeting', // 'meeting' or 'task'
    title: '',
    description: '',
    meeting_date: '',
    duration_minutes: 60,
    location: '',
    virtual_meeting_link: '',
    meeting_type: 'section',
    section_id: '',
    student_ids: [],
    notify_parents: true,
    requires_rsvp: false,
    send_reminders: true,
    reminder_minutes_before: 60,
    send_immediately: true,
    scheduled_send_at: '',
    attachments: []
  });

  useEffect(() => {
    fetchMeetings();
    fetchSections();
  }, []);

  const fetchMeetings = async () => {
    try {
      const response = await meetingScheduler.list();
      setMeetings(response.data);
    } catch (error) {
      console.error('Failed to fetch meetings:', error);
      toast.error('Failed to load meetings');
    }
  };

  const fetchSections = async () => {
    try {
      const response = await meetingScheduler.getMySections();
      console.log('🔍 Sections API Response:', response.data);
      console.log('🔍 Number of sections:', response.data?.length);
      response.data?.forEach((section, index) => {
        console.log(`🔍 Section ${index}:`, section.name, 'Students:', section.students?.length);
        section.students?.forEach(student => {
          console.log(`   - Student:`, student.first_name, student.last_name, student.student_id);
        });
      });
      setSections(response.data);
    } catch (error) {
      console.error('Failed to fetch sections:', error);
    }
  };

  const handleCreateMeeting = async (e) => {
    e.preventDefault();
    
    // Validate individual students selection
    if (formData.meeting_type === 'individual' && formData.student_ids.length === 0) {
      toast.error(`Please select at least one student for individual ${formData.event_category}s`);
      return;
    }
    
    setLoading(true);

    try {
      if (formData.event_category === 'meeting') {
        // Create meeting via meetings API
        const meetingData = {
          ...formData,
          meeting_date: formData.meeting_date ? new Date(formData.meeting_date).toISOString() : null,
          scheduled_send_at: formData.scheduled_send_at ? new Date(formData.scheduled_send_at).toISOString() : null,
          section_id: formData.section_id ? parseInt(formData.section_id) : null,
          student_ids: formData.student_ids.map(id => parseInt(id))
        };
        await meetingScheduler.create(meetingData);
        toast.success('Meeting scheduled successfully!');
      } else {
        // Create task via schedule API
        const taskData = {
          title: formData.title,
          description: formData.description,
          start_datetime: formData.meeting_date ? new Date(formData.meeting_date).toISOString() : null,
          end_datetime: formData.meeting_date ? new Date(formData.meeting_date).toISOString() : null, // Tasks typically have same start/end
          location: formData.location,
          event_type: 'task',
          meeting_type: formData.meeting_type,
          section_id: formData.section_id ? parseInt(formData.section_id) : null,
          student_ids: formData.student_ids.map(id => parseInt(id)),
          send_immediately: formData.send_immediately,
          scheduled_send_at: formData.scheduled_send_at ? new Date(formData.scheduled_send_at).toISOString() : null
        };
        
        // Call existing task scheduling API endpoint
        const response = await fetch('/api/v1/scheduling/tasks', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${localStorage.getItem('access_token')}`
          },
          body: JSON.stringify(taskData)
        });
        
        if (!response.ok) {
          throw new Error('Failed to create task');
        }
        
        toast.success('Task scheduled successfully!');
      }
      
      setShowCreateForm(false);
      resetForm();
      fetchMeetings();
    } catch (error) {
      console.error('Failed to create meeting:', error);
      toast.error(error.response?.data?.detail || 'Failed to schedule meeting');
    } finally {
      setLoading(false);
    }
  };

  const resetForm = () => {
    setFormData({
      event_category: 'meeting',
      title: '',
      description: '',
      meeting_date: '',
      duration_minutes: 60,
      location: '',
      virtual_meeting_link: '',
      meeting_type: 'section',
      section_id: '',
      student_ids: [],
      notify_parents: true,
      requires_rsvp: false,
      send_reminders: true,
      reminder_minutes_before: 60,
      send_immediately: true,
      scheduled_send_at: '',
      attachments: []
    });
  };

  const formatDateTime = (dateString) => {
    if (!dateString) return 'No date set';
    return new Date(dateString).toLocaleString();
  };

  const getMeetingTypeIcon = (type) => {
    switch (type) {
      case 'section': return <Users className="h-4 w-4" />;
      case 'individual': return <User className="h-4 w-4" />;
      default: return <Calendar className="h-4 w-4" />;
    }
  };

  const getMeetingTypeLabel = (type) => {
    switch (type) {
      case 'section': return 'Section Meeting';
      case 'individual': return 'Individual Meeting';
      default: return 'Custom Meeting';
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h2 className="text-2xl font-bold text-gray-900">Meeting Scheduler</h2>
          <p className="text-gray-600">Schedule meetings with students and parents</p>
        </div>
        <button
          onClick={() => setShowCreateForm(true)}
          className="bg-blue-600 text-white px-4 py-2 rounded-lg flex items-center gap-2 hover:bg-blue-700"
        >
          <Plus className="h-4 w-4" />
          Schedule Meeting
        </button>
      </div>

      {/* Create Meeting Modal */}
      {showCreateForm && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 w-full max-w-2xl max-h-[90vh] overflow-y-auto">
            <div className="flex justify-between items-center mb-6">
              <h3 className="text-xl font-semibold">Schedule New Meeting</h3>
              <button
                onClick={() => setShowCreateForm(false)}
                className="text-gray-400 hover:text-gray-600"
              >
                <X className="h-6 w-6" />
              </button>
            </div>

            <form onSubmit={handleCreateMeeting} className="space-y-6">
              {/* Event Category Selection */}
              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Event Type *
                  </label>
                  <div className="flex gap-6">
                    <label className="flex items-center">
                      <input
                        type="radio"
                        name="event_category"
                        value="meeting"
                        checked={formData.event_category === 'meeting'}
                        onChange={(e) => setFormData({...formData, event_category: e.target.value})}
                        className="mr-2"
                      />
                      📅 Meeting
                    </label>
                    <label className="flex items-center">
                      <input
                        type="radio"
                        name="event_category"
                        value="task"
                        checked={formData.event_category === 'task'}
                        onChange={(e) => setFormData({...formData, event_category: e.target.value})}
                        className="mr-2"
                      />
                      📋 Task
                    </label>
                  </div>
                </div>

                {/* Basic Meeting Info */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    {formData.event_category === 'meeting' ? 'Meeting Title' : 'Task Title'} *
                  </label>
                  <input
                    type="text"
                    required
                    value={formData.title}
                    onChange={(e) => setFormData({...formData, title: e.target.value})}
                    className="w-full p-3 border border-gray-300 rounded-lg"
                    placeholder={formData.event_category === 'meeting' ? 'e.g., Parent-Teacher Conference' : 'e.g., Math Homework Assignment'}
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Description
                  </label>
                  <textarea
                    value={formData.description}
                    onChange={(e) => setFormData({...formData, description: e.target.value})}
                    className="w-full p-3 border border-gray-300 rounded-lg"
                    rows={3}
                    placeholder={formData.event_category === 'meeting' ? 'Meeting details and agenda...' : 'Task instructions and requirements...'}
                  />
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Meeting Date & Time
                    </label>
                    <input
                      type="datetime-local"
                      value={formData.meeting_date}
                      onChange={(e) => setFormData({...formData, meeting_date: e.target.value})}
                      className="w-full p-3 border border-gray-300 rounded-lg"
                    />
                  </div>

                  {formData.event_category === 'meeting' && (
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">
                        Duration (minutes)
                      </label>
                      <select
                        value={formData.duration_minutes}
                        onChange={(e) => setFormData({...formData, duration_minutes: parseInt(e.target.value)})}
                        className="w-full p-3 border border-gray-300 rounded-lg"
                      >
                        <option value={30}>30 minutes</option>
                        <option value={60}>1 hour</option>
                        <option value={90}>1.5 hours</option>
                        <option value={120}>2 hours</option>
                      </select>
                    </div>
                  )}
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Location
                    </label>
                    <div className="relative">
                      <MapPin className="absolute left-3 top-3 h-5 w-5 text-gray-400" />
                      <input
                        type="text"
                        value={formData.location}
                        onChange={(e) => setFormData({...formData, location: e.target.value})}
                        className="w-full p-3 pl-10 border border-gray-300 rounded-lg"
                        placeholder="Room 101 or Address"
                      />
                    </div>
                  </div>

                  {formData.event_category === 'meeting' && (
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">
                        Virtual Meeting Link
                      </label>
                      <div className="relative">
                        <Link2 className="absolute left-3 top-3 h-5 w-5 text-gray-400" />
                        <input
                          type="url"
                          value={formData.virtual_meeting_link}
                          onChange={(e) => setFormData({...formData, virtual_meeting_link: e.target.value})}
                          className="w-full p-3 pl-10 border border-gray-300 rounded-lg"
                          placeholder="https://zoom.us/j/..."
                        />
                      </div>
                    </div>
                  )}
                </div>
              </div>

              {/* Recipients */}
              <div className="space-y-4">
                <h4 className="font-semibold text-gray-900">Recipients</h4>
                
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Meeting Type *
                  </label>
                  <select
                    required
                    value={formData.meeting_type}
                    onChange={(e) => setFormData({...formData, meeting_type: e.target.value})}
                    className="w-full p-3 border border-gray-300 rounded-lg"
                  >
                    <option value="section">Entire Section</option>
                    <option value="individual">Individual Students</option>
                  </select>
                </div>

                {formData.meeting_type === 'section' && (
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Select Section *
                    </label>
                    <select
                      required
                      value={formData.section_id}
                      onChange={(e) => setFormData({...formData, section_id: e.target.value})}
                      className="w-full p-3 border border-gray-300 rounded-lg"
                    >
                      <option value="">Choose a section...</option>
                      {sections.map(section => (
                        <option key={section.id} value={section.id}>
                          {section.name} ({section.student_count} students)
                        </option>
                      ))}
                    </select>
                  </div>
                )}

                {formData.meeting_type === 'individual' && (
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Select Students *
                    </label>
                    <p className="text-sm text-gray-500 mb-2">Choose which students to invite to this meeting</p>
                    
                    {/* Debug info */}
                    <div className="text-xs text-gray-400 mb-2">
                      Debug: {sections.length} sections loaded, Total students: {sections.reduce((acc, s) => acc + (s.students?.length || 0), 0)}
                    </div>
                    
                    <div className="max-h-32 overflow-y-auto border border-gray-300 rounded-lg p-3 space-y-2">
                      {sections.length === 0 && (
                        <p className="text-gray-500 text-sm">Loading students...</p>
                      )}
                      {sections.map(section => (
                        <div key={section.id}>
                          <h6 className="font-medium text-gray-600 mb-1">{section.name}</h6>
                          {section.students && section.students.length > 0 ? (
                            section.students.map(student => (
                              <div key={student.id} className="flex items-center gap-2 ml-4">
                                <input
                                  type="checkbox"
                                  id={`student-${student.id}`}
                                  checked={formData.student_ids.includes(student.id)}
                                  onChange={(e) => {
                                    if (e.target.checked) {
                                      setFormData({
                                        ...formData,
                                        student_ids: [...formData.student_ids, student.id]
                                      });
                                    } else {
                                      setFormData({
                                        ...formData,
                                        student_ids: formData.student_ids.filter(id => id !== student.id)
                                      });
                                    }
                                  }}
                                  className="h-4 w-4 text-blue-600"
                                />
                                <label htmlFor={`student-${student.id}`} className="text-sm text-gray-700">
                                  {student.first_name} {student.last_name} ({student.student_id})
                                </label>
                              </div>
                            ))
                          ) : (
                            <p className="text-gray-500 text-sm ml-4">No students in this section</p>
                          )}
                        </div>
                      ))}
                    </div>
                    {formData.meeting_type === 'individual' && formData.student_ids.length === 0 && (
                      <p className="text-red-500 text-sm mt-1">Please select at least one student</p>
                    )}
                  </div>
                )}

                <div className="flex items-center gap-2">
                  <input
                    type="checkbox"
                    id="notify_parents"
                    checked={formData.notify_parents}
                    onChange={(e) => setFormData({...formData, notify_parents: e.target.checked})}
                    className="h-4 w-4 text-blue-600"
                  />
                  <label htmlFor="notify_parents" className="text-sm text-gray-700">
                    Also notify parents
                  </label>
                </div>
              </div>

              {/* Meeting Options */}
              <div className="space-y-4">
                <h4 className="font-semibold text-gray-900">Options</h4>
                
                <div className="space-y-3">
                  <div className="flex items-center gap-2">
                    <input
                      type="checkbox"
                      id="requires_rsvp"
                      checked={formData.requires_rsvp}
                      onChange={(e) => setFormData({...formData, requires_rsvp: e.target.checked})}
                      className="h-4 w-4 text-blue-600"
                    />
                    <label htmlFor="requires_rsvp" className="text-sm text-gray-700">
                      Require RSVP response
                    </label>
                  </div>

                  <div className="flex items-center gap-2">
                    <input
                      type="checkbox"
                      id="send_reminders"
                      checked={formData.send_reminders}
                      onChange={(e) => setFormData({...formData, send_reminders: e.target.checked})}
                      className="h-4 w-4 text-blue-600"
                    />
                    <label htmlFor="send_reminders" className="text-sm text-gray-700">
                      Send reminders
                    </label>
                  </div>

                  {formData.send_reminders && (
                    <div className="ml-6">
                      <label className="block text-sm font-medium text-gray-700 mb-1">
                        Send reminder
                      </label>
                      <select
                        value={formData.reminder_minutes_before}
                        onChange={(e) => setFormData({...formData, reminder_minutes_before: parseInt(e.target.value)})}
                        className="w-48 p-2 border border-gray-300 rounded-lg"
                      >
                        <option value={15}>15 minutes before</option>
                        <option value={30}>30 minutes before</option>
                        <option value={60}>1 hour before</option>
                        <option value={120}>2 hours before</option>
                        <option value={1440}>1 day before</option>
                      </select>
                    </div>
                  )}
                </div>
              </div>

              {/* Scheduling */}
              <div className="space-y-4">
                <h4 className="font-semibold text-gray-900">Scheduling</h4>
                
                <div className="space-y-3">
                  <div className="flex items-center gap-2">
                    <input
                      type="radio"
                      id="send_now"
                      name="scheduling"
                      checked={formData.send_immediately}
                      onChange={() => setFormData({...formData, send_immediately: true})}
                      className="h-4 w-4 text-blue-600"
                    />
                    <label htmlFor="send_now" className="text-sm text-gray-700">
                      Send notification immediately
                    </label>
                  </div>

                  <div className="flex items-center gap-2">
                    <input
                      type="radio"
                      id="schedule_later"
                      name="scheduling"
                      checked={!formData.send_immediately}
                      onChange={() => setFormData({...formData, send_immediately: false})}
                      className="h-4 w-4 text-blue-600"
                    />
                    <label htmlFor="schedule_later" className="text-sm text-gray-700">
                      Schedule for later
                    </label>
                  </div>

                  {!formData.send_immediately && (
                    <div className="ml-6">
                      <label className="block text-sm font-medium text-gray-700 mb-1">
                        Send notification at
                      </label>
                      <input
                        type="datetime-local"
                        value={formData.scheduled_send_at}
                        onChange={(e) => setFormData({...formData, scheduled_send_at: e.target.value})}
                        className="w-64 p-2 border border-gray-300 rounded-lg"
                      />
                    </div>
                  )}
                </div>
              </div>

              {/* Form Actions */}
              <div className="flex gap-3 pt-6 border-t">
                <button
                  type="button"
                  onClick={() => setShowCreateForm(false)}
                  className="flex-1 px-4 py-2 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50"
                  disabled={loading}
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="flex-1 bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 flex items-center justify-center gap-2"
                  disabled={loading}
                >
                  {loading ? (
                    <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
                  ) : (
                    <>
                      <Send className="h-4 w-4" />
                      {formData.send_immediately ? 'Schedule & Send' : 'Schedule Meeting'}
                    </>
                  )}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Meetings List */}
      <div className="bg-white rounded-lg shadow">
        <div className="px-6 py-4 border-b border-gray-200">
          <h3 className="text-lg font-semibold text-gray-900">Recent Meetings</h3>
        </div>
        
        <div className="divide-y divide-gray-200">
          {meetings.length === 0 ? (
            <div className="px-6 py-12 text-center">
              <Calendar className="mx-auto h-12 w-12 text-gray-400" />
              <h3 className="mt-2 text-sm font-medium text-gray-900">No meetings scheduled</h3>
              <p className="mt-1 text-sm text-gray-500">
                Get started by scheduling your first meeting.
              </p>
            </div>
          ) : (
            meetings.map(meeting => (
              <div key={meeting.id} className="px-6 py-4 hover:bg-gray-50">
                <div className="flex items-start justify-between">
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 mb-2">
                      {getMeetingTypeIcon(meeting.meeting_type)}
                      <h4 className="text-lg font-medium text-gray-900">{meeting.title}</h4>
                      <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-100 text-blue-800">
                        {getMeetingTypeLabel(meeting.meeting_type)}
                      </span>
                    </div>
                    
                    {meeting.description && (
                      <p className="text-sm text-gray-600 mb-2">{meeting.description}</p>
                    )}
                    
                    <div className="flex flex-wrap items-center gap-4 text-sm text-gray-500">
                      {meeting.meeting_date && (
                        <div className="flex items-center gap-1">
                          <Calendar className="h-4 w-4" />
                          {formatDateTime(meeting.meeting_date)}
                        </div>
                      )}
                      
                      {meeting.duration_minutes && (
                        <div className="flex items-center gap-1">
                          <Clock className="h-4 w-4" />
                          {meeting.duration_minutes} minutes
                        </div>
                      )}
                      
                      {meeting.location && (
                        <div className="flex items-center gap-1">
                          <MapPin className="h-4 w-4" />
                          {meeting.location}
                        </div>
                      )}
                      
                      <div className="flex items-center gap-1">
                        <Users className="h-4 w-4" />
                        {meeting.recipient_count} recipients
                      </div>
                    </div>
                  </div>
                  
                  <div className="flex items-center gap-2 ml-4">
                    {meeting.sent_at ? (
                      <span className="inline-flex items-center gap-1 text-green-600">
                        <CheckCircle2 className="h-4 w-4" />
                        Sent
                      </span>
                    ) : (
                      <span className="inline-flex items-center gap-1 text-yellow-600">
                        <AlertCircle className="h-4 w-4" />
                        Pending
                      </span>
                    )}
                  </div>
                </div>
              </div>
            ))
          )}
        </div>
      </div>
    </div>
  );
};

export default MeetingScheduler;