import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';

const ScheduleManagement = () => {
  const [tasks, setTasks] = useState([]);
  const [sections, setSections] = useState([]);
  const [teachers, setTeachers] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [showTaskModal, setShowTaskModal] = useState(false);
  const [editingTask, setEditingTask] = useState(null);
  const [conflicts, setConflicts] = useState(null);
  const navigate = useNavigate();

  useEffect(() => {
    fetchTasks();
    fetchSections();
    fetchTeachers();
  }, []);

  const fetchTasks = async () => {
    try {
      const token = localStorage.getItem('token');
      const response = await axios.get('http://localhost:8003/api/v1/scheduling/tasks', {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      console.log('Tasks API response:', response.data);
      setTasks(response.data.tasks || []); // Extract the tasks array from the response
    } catch (error) {
      console.error('Error fetching tasks:', error);
      setError('Failed to load tasks');
      setTasks([]); // Set empty array as fallback
    }
  };

  const fetchSections = async () => {
    try {
      const token = localStorage.getItem('token');
      const response = await axios.get('http://localhost:8003/api/v1/students/sections', {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      setSections(response.data);
    } catch (error) {
      console.error('Error fetching sections:', error);
    }
  };

  const fetchTeachers = async () => {
    // Mock teachers data - in real app, you'd have an endpoint for this
    setTeachers([
      { id: 1, name: 'Dr. Smith', email: 'smith@university.edu' },
      { id: 2, name: 'Prof. Johnson', email: 'johnson@university.edu' },
      { id: 3, name: 'Dr. Brown', email: 'brown@university.edu' }
    ]);
  };

  const checkConflicts = async (date, time, duration = 60) => {
    try {
      const token = localStorage.getItem('token');
      const response = await axios.get(
        `http://localhost:8003/api/v1/scheduling/tasks/conflicts?scheduled_date=${date}&scheduled_time=${time}&duration_minutes=${duration}`,
        { headers: { 'Authorization': `Bearer ${token}` } }
      );
      setConflicts(response.data);
      return response.data.has_conflict;
    } catch (error) {
      console.error('Error checking conflicts:', error);
      return false;
    }
  };

  const createTask = async (taskData) => {
    try {
      console.log('🚀 Sending task data:', taskData);
      const token = localStorage.getItem('token');
      await axios.post('http://localhost:8003/api/v1/scheduling/tasks/simple', taskData, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      setShowTaskModal(false);
      fetchTasks();
      setError(null);
      console.log('✅ Task created successfully');
    } catch (error) {
      console.error('❌ Error creating task:', error);
      if (error.response) {
        console.error('Response data:', error.response.data);
        console.error('Response status:', error.response.status);
      }
      setError('Failed to create task: ' + (error.response?.data?.detail || error.message));
    }
  };

  const formatDateTime = (date, time) => {
    try {
      if (!date || !time) {
        return 'Invalid Date';
      }
      
      // Handle different date formats
      let formattedDate = date;
      if (date.length === 10 && !date.includes('T')) {
        // Date is in YYYY-MM-DD format
        formattedDate = date;
      }
      
      // Handle different time formats
      let formattedTime = time;
      if (time.length === 5) {
        // Time is in HH:MM format, add seconds
        formattedTime = `${time}:00`;
      }
      
      const dateTimeString = `${formattedDate}T${formattedTime}`;
      const dateObj = new Date(dateTimeString);
      
      if (isNaN(dateObj.getTime())) {
        return 'Invalid Date';
      }
      
      return dateObj.toLocaleString('en-US', {
        weekday: 'short',
        year: 'numeric',
        month: 'short',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
      });
    } catch (error) {
      console.error('Error formatting date/time:', error, { date, time });
      return 'Invalid Date';
    }
  };

  const getTaskTypeLabel = (type) => {
    const labels = {
      'meeting_teachers': 'Teacher Meeting',
      'parent_teacher_meeting': 'Parent-Teacher Meeting',
      'student_review': 'Student Review',
      'personal_reminder': 'Personal Reminder',
      'exam_schedule': 'Exam Schedule'
    };
    return labels[type] || type;
  };

  const getTaskTypeBadge = (type) => {
    const colors = {
      'meeting_teachers': 'bg-blue-100 text-blue-800',
      'parent_teacher_meeting': 'bg-green-100 text-green-800',
      'student_review': 'bg-yellow-100 text-yellow-800',
      'personal_reminder': 'bg-purple-100 text-purple-800',
      'exam_schedule': 'bg-red-100 text-red-800'
    };
    
    return (
      <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${colors[type] || 'bg-gray-100 text-gray-800'}`}>
        {getTaskTypeLabel(type)}
      </span>
    );
  };

  return (
    <div className="max-w-7xl mx-auto p-6">
      <div className="mb-6">
        <div className="flex justify-between items-center">
          <div>
            <h1 className="text-3xl font-bold text-gray-900">Schedule Management</h1>
            <p className="text-gray-600 mt-2">Manage your tasks, meetings, and calendar events</p>
          </div>
          <button
            onClick={() => setShowTaskModal(true)}
            className="bg-blue-600 text-white px-4 py-2 rounded-md hover:bg-blue-700 flex items-center"
          >
            <svg className="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
            </svg>
            Schedule Task
          </button>
        </div>
      </div>

      {/* Conflict Warning */}
      {conflicts && conflicts.has_conflict && (
        <div className="bg-yellow-50 border border-yellow-200 rounded-md p-4 mb-6">
          <h3 className="text-yellow-800 font-medium">Scheduling Conflicts Detected</h3>
          <p className="text-yellow-700 text-sm mt-1">
            You have {conflicts.conflicting_tasks.length} conflicting task(s) at this time.
          </p>
          {conflicts.suggested_times.length > 0 && (
            <p className="text-yellow-700 text-sm mt-1">
              Suggested times: {conflicts.suggested_times.join(', ')}
            </p>
          )}
        </div>
      )}

      {/* Tasks List */}
      {loading ? (
        <div className="text-center py-8">
          <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
          <p className="mt-2 text-gray-600">Loading tasks...</p>
        </div>
      ) : error ? (
        <div className="bg-red-50 border border-red-200 rounded-md p-4">
          <p className="text-red-600">{error}</p>
          <button
            onClick={fetchTasks}
            className="mt-2 text-sm text-red-600 hover:text-red-800 underline"
          >
            Try again
          </button>
        </div>
      ) : (
        <div className="bg-white shadow rounded-lg overflow-hidden">
          <div className="px-4 py-5 sm:p-6">
            <h3 className="text-lg font-medium text-gray-900 mb-4">
              Scheduled Tasks ({tasks.length})
            </h3>
            
            {tasks.length === 0 ? (
              <div className="text-center py-8">
                <p className="text-gray-500">No scheduled tasks found</p>
                <button
                  onClick={() => setShowTaskModal(true)}
                  className="mt-2 text-blue-600 hover:text-blue-800 underline"
                >
                  Schedule your first task
                </button>
              </div>
            ) : (
              <div className="space-y-4">
                {Array.isArray(tasks) && tasks.map((task) => (
                  <div key={task.id} className="border border-gray-200 rounded-lg p-4 hover:bg-gray-50">
                    <div className="flex justify-between items-start">
                      <div className="flex-1">
                        <div className="flex items-center space-x-3">
                          <h4 className="text-lg font-medium text-gray-900">{task.title}</h4>
                          {getTaskTypeBadge(task.task_type)}
                        </div>
                        <p className="text-gray-600 mt-1">{task.description}</p>
                        <div className="flex items-center space-x-4 mt-2 text-sm text-gray-500">
                          <div className="flex items-center">
                            <svg className="w-4 h-4 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
                            </svg>
                            {formatDateTime(task.scheduled_date, task.scheduled_time)}
                          </div>
                          <div className="flex items-center">
                            <svg className="w-4 h-4 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                            </svg>
                            {task.duration_minutes} minutes
                          </div>
                          {task.location && (
                            <div className="flex items-center">
                              <svg className="w-4 h-4 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z" />
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 11a3 3 0 11-6 0 3 3 0 016 0z" />
                              </svg>
                              {task.location}
                            </div>
                          )}
                        </div>
                        
                        {/* Participants */}
                        {task.participants && task.participants.length > 0 && (
                          <div className="mt-3">
                            <p className="text-sm font-medium text-gray-700 mb-1">Participants:</p>
                            <div className="flex flex-wrap gap-1">
                              {task.participants.map((participant, index) => (
                                <span key={index} className="inline-flex items-center px-2 py-1 rounded-md text-xs bg-gray-100 text-gray-700">
                                  {participant.name || participant.email}
                                  {participant.type === 'section' && participant.student_count && (
                                    <span className="ml-1 text-gray-500">({participant.student_count} students)</span>
                                  )}
                                </span>
                              ))}
                            </div>
                          </div>
                        )}
                        
                        {/* Additional Details */}
                        {(task.preparation_notes || task.materials_needed) && (
                          <div className="mt-3 space-y-2">
                            {task.preparation_notes && (
                              <div>
                                <p className="text-sm font-medium text-gray-700">Preparation Notes:</p>
                                <p className="text-sm text-gray-600">{task.preparation_notes}</p>
                              </div>
                            )}
                            {task.materials_needed && (
                              <div>
                                <p className="text-sm font-medium text-gray-700">Materials Needed:</p>
                                <p className="text-sm text-gray-600">{task.materials_needed}</p>
                              </div>
                            )}
                          </div>
                        )}
                        
                        {/* Priority */}
                        {task.priority && task.priority !== 'medium' && (
                          <div className="mt-2">
                            <span className={`inline-flex items-center px-2 py-1 rounded-md text-xs font-medium ${
                              task.priority === 'high' ? 'bg-red-100 text-red-800' :
                              task.priority === 'low' ? 'bg-gray-100 text-gray-800' :
                              'bg-blue-100 text-blue-800'
                            }`}>
                              {task.priority.charAt(0).toUpperCase() + task.priority.slice(1)} Priority
                            </span>
                          </div>
                        )}
                      </div>
                      
                      <div className="flex items-center space-x-2">
                        {task.is_completed ? (
                          <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-800">
                            Completed
                          </span>
                        ) : (
                          <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-yellow-100 text-yellow-800">
                            Scheduled
                          </span>
                        )}
                        
                        <button
                          onClick={() => {
                            setEditingTask(task);
                            setShowTaskModal(true);
                          }}
                          className="text-blue-600 hover:text-blue-800 text-sm"
                        >
                          Edit
                        </button>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      )}

      {/* Task Modal */}
      {showTaskModal && (
        <TaskModal
          task={editingTask}
          sections={sections}
          teachers={teachers}
          onClose={() => {
            setShowTaskModal(false);
            setEditingTask(null);
            setConflicts(null);
          }}
          onSave={createTask}
          onCheckConflicts={checkConflicts}
        />
      )}
    </div>
  );
};

// Task Modal Component
const TaskModal = ({ task, sections, teachers, onClose, onSave, onCheckConflicts }) => {
  const [formData, setFormData] = useState({
    title: task?.title || '',
    description: task?.description || '',
    task_type: task?.task_type || 'personal_reminder',
    scheduled_date: task?.scheduled_date || '',
    scheduled_time: task?.scheduled_time || '',
    duration_minutes: task?.duration_minutes || 60,
    location: task?.location || '',
    participants: task?.participants || [],
    send_notifications: true
  });

  const [newParticipant, setNewParticipant] = useState({
    type: 'student',
    id: '',
    email: '',
    name: ''
  });

  const handleInputChange = (field, value) => {
    setFormData(prev => ({
      ...prev,
      [field]: value
    }));
  };

  const addParticipant = () => {
    if (newParticipant.type === 'section' && newParticipant.id) {
      const section = sections.find(s => s.id === parseInt(newParticipant.id));
      if (section) {
        setFormData(prev => ({
          ...prev,
          participants: [...prev.participants, {
            type: 'section',
            id: section.id,
            name: section.name
          }]
        }));
      }
    } else if (newParticipant.type === 'teacher' && newParticipant.id) {
      const teacher = teachers.find(t => t.id === parseInt(newParticipant.id));
      if (teacher) {
        setFormData(prev => ({
          ...prev,
          participants: [...prev.participants, {
            type: 'teacher',
            id: teacher.id,
            name: teacher.name,
            email: teacher.email
          }]
        }));
      }
    } else if (newParticipant.email && newParticipant.name) {
      setFormData(prev => ({
        ...prev,
        participants: [...prev.participants, {
          type: newParticipant.type,
          email: newParticipant.email,
          name: newParticipant.name
        }]
      }));
    }

    setNewParticipant({
      type: 'student',
      id: '',
      email: '',
      name: ''
    });
  };

  const removeParticipant = (index) => {
    setFormData(prev => ({
      ...prev,
      participants: prev.participants.filter((_, i) => i !== index)
    }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    // Check for conflicts first
    if (formData.scheduled_date && formData.scheduled_time) {
      const hasConflict = await onCheckConflicts(
        formData.scheduled_date,
        formData.scheduled_time,
        formData.duration_minutes
      );
      
      if (hasConflict) {
        if (!window.confirm('There are scheduling conflicts. Do you want to proceed anyway?')) {
          return;
        }
      }
    }
    
    onSave(formData);
  };

  const taskTypes = [
    { value: 'meeting_teachers', label: 'Teacher Meeting' },
    { value: 'parent_teacher_meeting', label: 'Parent-Teacher Meeting' },
    { value: 'student_review', label: 'Student Review' },
    { value: 'personal_reminder', label: 'Personal Reminder' },
    { value: 'exam_schedule', label: 'Exam Schedule' }
  ];

  return (
    <div className="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full z-50">
      <div className="relative top-10 mx-auto p-5 border w-11/12 md:w-3/4 lg:w-2/3 shadow-lg rounded-md bg-white">
        <form onSubmit={handleSubmit}>
          <div className="flex justify-between items-center mb-4">
            <h3 className="text-lg font-medium text-gray-900">
              {task ? 'Edit Task' : 'Schedule New Task'}
            </h3>
            <button
              type="button"
              onClick={onClose}
              className="text-gray-400 hover:text-gray-600"
            >
              <svg className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-6">
            {/* Title */}
            <div className="md:col-span-2">
              <label className="block text-sm font-medium text-gray-700 mb-1">Title</label>
              <input
                type="text"
                required
                value={formData.title}
                onChange={(e) => handleInputChange('title', e.target.value)}
                className="block w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                placeholder="e.g., Section A Review Meeting"
              />
            </div>

            {/* Task Type */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Task Type</label>
              <select
                value={formData.task_type}
                onChange={(e) => handleInputChange('task_type', e.target.value)}
                className="block w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-blue-500 focus:border-blue-500"
              >
                {taskTypes.map(type => (
                  <option key={type.value} value={type.value}>{type.label}</option>
                ))}
              </select>
            </div>

            {/* Location */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Location</label>
              <input
                type="text"
                value={formData.location}
                onChange={(e) => handleInputChange('location', e.target.value)}
                className="block w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                placeholder="e.g., Teacher's Cabin, Room 101"
              />
            </div>

            {/* Date */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Date</label>
              <input
                type="date"
                required
                value={formData.scheduled_date}
                onChange={(e) => handleInputChange('scheduled_date', e.target.value)}
                min={new Date().toISOString().split('T')[0]}
                className="block w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-blue-500 focus:border-blue-500"
              />
            </div>

            {/* Time */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Time</label>
              <input
                type="time"
                required
                value={formData.scheduled_time}
                onChange={(e) => handleInputChange('scheduled_time', e.target.value)}
                className="block w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-blue-500 focus:border-blue-500"
              />
            </div>

            {/* Duration */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Duration (minutes)</label>
              <input
                type="number"
                min="15"
                max="480"
                value={formData.duration_minutes}
                onChange={(e) => handleInputChange('duration_minutes', parseInt(e.target.value))}
                className="block w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-blue-500 focus:border-blue-500"
              />
            </div>

            {/* Description */}
            <div className="md:col-span-2">
              <label className="block text-sm font-medium text-gray-700 mb-1">Description</label>
              <textarea
                rows="3"
                value={formData.description}
                onChange={(e) => handleInputChange('description', e.target.value)}
                className="block w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                placeholder="Additional details about the task..."
              />
            </div>
          </div>

          {/* Participants */}
          <div className="mb-6">
            <h4 className="text-md font-medium text-gray-900 mb-3">Participants</h4>
            
            {/* Add Participant */}
            <div className="border border-gray-200 rounded-lg p-4 mb-4">
              <div className="grid grid-cols-1 md:grid-cols-4 gap-3">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Type</label>
                  <select
                    value={newParticipant.type}
                    onChange={(e) => setNewParticipant(prev => ({ ...prev, type: e.target.value, id: '', email: '', name: '' }))}
                    className="block w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                  >
                    <option value="section">Section</option>
                    <option value="teacher">Teacher</option>
                    <option value="parent">Parent</option>
                    <option value="student">Student</option>
                  </select>
                </div>

                {newParticipant.type === 'section' && (
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">Section</label>
                    <select
                      value={newParticipant.id}
                      onChange={(e) => setNewParticipant(prev => ({ ...prev, id: e.target.value }))}
                      className="block w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                    >
                      <option value="">Select Section</option>
                      {sections.map(section => (
                        <option key={section.id} value={section.id}>{section.name}</option>
                      ))}
                    </select>
                  </div>
                )}

                {newParticipant.type === 'teacher' && (
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">Teacher</label>
                    <select
                      value={newParticipant.id}
                      onChange={(e) => setNewParticipant(prev => ({ ...prev, id: e.target.value }))}
                      className="block w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                    >
                      <option value="">Select Teacher</option>
                      {teachers.map(teacher => (
                        <option key={teacher.id} value={teacher.id}>{teacher.name}</option>
                      ))}
                    </select>
                  </div>
                )}

                {(newParticipant.type === 'parent' || newParticipant.type === 'student') && (
                  <>
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">Name</label>
                      <input
                        type="text"
                        value={newParticipant.name}
                        onChange={(e) => setNewParticipant(prev => ({ ...prev, name: e.target.value }))}
                        className="block w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                        placeholder="Full name"
                      />
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">Email</label>
                      <input
                        type="email"
                        value={newParticipant.email}
                        onChange={(e) => setNewParticipant(prev => ({ ...prev, email: e.target.value }))}
                        className="block w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                        placeholder="email@example.com"
                      />
                    </div>
                  </>
                )}

                <div className="flex items-end">
                  <button
                    type="button"
                    onClick={addParticipant}
                    className="w-full px-3 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700"
                  >
                    Add
                  </button>
                </div>
              </div>
            </div>

            {/* Participants List */}
            {formData.participants.length > 0 && (
              <div className="space-y-2">
                <p className="text-sm font-medium text-gray-700">Added Participants:</p>
                {formData.participants.map((participant, index) => (
                  <div key={index} className="flex items-center justify-between p-2 bg-gray-50 rounded-md">
                    <span className="text-sm">
                      {participant.name} ({participant.type})
                      {participant.email && <span className="text-gray-500"> - {participant.email}</span>}
                    </span>
                    <button
                      type="button"
                      onClick={() => removeParticipant(index)}
                      className="text-red-600 hover:text-red-800"
                    >
                      Remove
                    </button>
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* Send Notifications */}
          <div className="mb-6">
            <label className="flex items-center">
              <input
                type="checkbox"
                checked={formData.send_notifications}
                onChange={(e) => handleInputChange('send_notifications', e.target.checked)}
                className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
              />
              <span className="ml-2 text-sm text-gray-700">Send notifications to participants</span>
            </label>
          </div>

          {/* Actions */}
          <div className="flex justify-end space-x-3">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2 text-sm font-medium text-gray-700 bg-gray-200 rounded-md hover:bg-gray-300"
            >
              Cancel
            </button>
            <button
              type="submit"
              className="px-4 py-2 text-sm font-medium text-white bg-blue-600 rounded-md hover:bg-blue-700"
            >
              {task ? 'Update Task' : 'Schedule Task'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

export default ScheduleManagement;