import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { API_BASE_URL } from '../services/api';

const CalendarView = () => {
  const [events, setEvents] = useState([]);
  const [currentDate, setCurrentDate] = useState(new Date());
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [viewMode, setViewMode] = useState('month'); // 'month', 'week', 'day'

  useEffect(() => {
    fetchEvents();
  }, [currentDate, viewMode]);

  const fetchEvents = async () => {
    setLoading(true);
    try {
      const token = localStorage.getItem('token');
      
      // Calculate date range based on view mode
      let startDate, endDate;
      const year = currentDate.getFullYear();
      const month = currentDate.getMonth();
      
      if (viewMode === 'month') {
        startDate = new Date(year, month, 1);
        endDate = new Date(year, month + 1, 0);
      } else if (viewMode === 'week') {
        const day = currentDate.getDay();
        startDate = new Date(currentDate);
        startDate.setDate(currentDate.getDate() - day);
        endDate = new Date(startDate);
        endDate.setDate(startDate.getDate() + 6);
      } else { // day
        startDate = new Date(currentDate);
        endDate = new Date(currentDate);
      }
      
      const response = await axios.get(
        `${API_BASE_URL}/api/v1/scheduling/calendar?start_date=${startDate.toISOString().split('T')[0]}&end_date=${endDate.toISOString().split('T')[0]}`,
        { headers: { 'Authorization': `Bearer ${token}` } }
      );
      
      setEvents(response.data.events || []);
      setError(null);
    } catch (error) {
      console.error('Error fetching calendar events:', error);
      setError('Failed to load calendar events');
      setEvents([]);
    } finally {
      setLoading(false);
    }
  };

  const navigateDate = (direction) => {
    const newDate = new Date(currentDate);
    
    if (viewMode === 'month') {
      newDate.setMonth(currentDate.getMonth() + direction);
    } else if (viewMode === 'week') {
      newDate.setDate(currentDate.getDate() + (direction * 7));
    } else { // day
      newDate.setDate(currentDate.getDate() + direction);
    }
    
    setCurrentDate(newDate);
  };

  const goToToday = () => {
    setCurrentDate(new Date());
  };

  const formatDateRange = () => {
    if (viewMode === 'month') {
      return currentDate.toLocaleDateString('en-US', { month: 'long', year: 'numeric' });
    } else if (viewMode === 'week') {
      const startOfWeek = new Date(currentDate);
      startOfWeek.setDate(currentDate.getDate() - currentDate.getDay());
      const endOfWeek = new Date(startOfWeek);
      endOfWeek.setDate(startOfWeek.getDate() + 6);
      
      if (startOfWeek.getMonth() === endOfWeek.getMonth()) {
        return `${startOfWeek.getDate()}-${endOfWeek.getDate()} ${startOfWeek.toLocaleDateString('en-US', { month: 'long', year: 'numeric' })}`;
      } else {
        return `${startOfWeek.toLocaleDateString('en-US', { month: 'short', day: 'numeric' })} - ${endOfWeek.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' })}`;
      }
    } else { // day
      return currentDate.toLocaleDateString('en-US', { weekday: 'long', month: 'long', day: 'numeric', year: 'numeric' });
    }
  };

  const getEventsForDate = (date) => {
    // Convert the calendar date to YYYY-MM-DD format in local timezone
    const year = date.getFullYear();
    const month = String(date.getMonth() + 1).padStart(2, '0');
    const day = String(date.getDate()).padStart(2, '0');
    const dateStr = `${year}-${month}-${day}`;
    
    console.log(`Looking for events on ${dateStr}`);
    
    return events.filter(event => {
      // Try multiple ways to extract the date from event
      let eventDateStr = null;
      
      // Method 1: Use explicit local_date if available
      if (event.local_date) {
        eventDateStr = event.local_date;
        console.log(`Event "${event.title}" has local_date: ${eventDateStr}`);
      }
      // Method 2: Extract date from start_datetime or start string
      else {
        const eventStart = event.start_datetime || event.start;
        if (eventStart) {
          // For ISO strings like "2025-10-18T20:53:00", just take the date part
          if (typeof eventStart === 'string') {
            eventDateStr = eventStart.split('T')[0];
            console.log(`Event "${event.title}" extracted date from start: ${eventDateStr}`);
          }
        }
      }
      
      const matches = eventDateStr === dateStr;
      if (matches) {
        console.log(`✅ Event "${event.title}" matches date ${dateStr}`);
      }
      
      return matches;
    });
  };

  const getEventTypeColor = (event) => {
    const colors = {
      'task': 'bg-blue-500',
      'class': 'bg-green-500',
      'meeting': 'bg-purple-500',
      'exam': 'bg-red-500',
      'office_hours': 'bg-yellow-500',
      'conference': 'bg-indigo-500',
      'deadline': 'bg-orange-500',
      'workshop': 'bg-pink-500'
    };
    
    if (event.type === 'task') {
      const taskColors = {
        'meeting_teachers': 'bg-blue-500',
        'parent_teacher_meeting': 'bg-green-500',
        'student_review': 'bg-yellow-500',
        'personal_reminder': 'bg-purple-500',
        'exam_schedule': 'bg-red-500'
      };
      return taskColors[event.task_type] || 'bg-gray-500';
    }
    
    return colors[event.type] || 'bg-gray-500';
  };

  const renderMonthView = () => {
    const year = currentDate.getFullYear();
    const month = currentDate.getMonth();
    const firstDay = new Date(year, month, 1);
    const lastDay = new Date(year, month + 1, 0);
    const daysInMonth = lastDay.getDate();
    const startingDayOfWeek = firstDay.getDay();
    
    const days = [];
    
    // Add empty cells for days before the first day of the month
    for (let i = 0; i < startingDayOfWeek; i++) {
      days.push(<div key={`empty-${i}`} className="h-32 border border-gray-200"></div>);
    }
    
    // Add cells for each day of the month
    for (let day = 1; day <= daysInMonth; day++) {
      const date = new Date(year, month, day);
      const dayEvents = getEventsForDate(date);
      const isToday = date.toDateString() === new Date().toDateString();
      
      days.push(
        <div key={day} className={`h-32 border border-gray-200 p-1 overflow-y-auto ${isToday ? 'bg-blue-50' : 'bg-white'}`}>
          <div className={`text-sm font-medium mb-1 ${isToday ? 'text-blue-600' : 'text-gray-900'}`}>
            {day}
          </div>
          <div className="space-y-1">
            {dayEvents.slice(0, 3).map((event, index) => (
              <div
                key={index}
                className={`text-xs p-1 rounded text-white truncate ${getEventTypeColor(event)}`}
                title={`${event.title} - ${new Date(event.start_datetime || event.start).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}`}
              >
                {event.title}
              </div>
            ))}
            {dayEvents.length > 3 && (
              <div className="text-xs text-gray-500">
                +{dayEvents.length - 3} more
              </div>
            )}
          </div>
        </div>
      );
    }
    
    return (
      <div className="grid grid-cols-7 gap-0">
        {/* Day headers */}
        {['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'].map(day => (
          <div key={day} className="bg-gray-100 p-2 text-center text-sm font-medium text-gray-700 border border-gray-200">
            {day}
          </div>
        ))}
        {days}
      </div>
    );
  };

  const renderWeekView = () => {
    const startOfWeek = new Date(currentDate);
    startOfWeek.setDate(currentDate.getDate() - currentDate.getDay());
    
    const weekDays = [];
    for (let i = 0; i < 7; i++) {
      const day = new Date(startOfWeek);
      day.setDate(startOfWeek.getDate() + i);
      weekDays.push(day);
    }
    
    const hours = [];
    for (let hour = 0; hour < 24; hour++) {
      hours.push(hour);
    }
    
    return (
      <div className="flex flex-col">
        {/* Day headers */}
        <div className="grid grid-cols-8 gap-0 mb-2">
          <div className="p-2"></div> {/* Empty cell for time column */}
          {weekDays.map((day, index) => {
            const isToday = day.toDateString() === new Date().toDateString();
            return (
              <div key={index} className={`p-2 text-center border border-gray-200 ${isToday ? 'bg-blue-50' : 'bg-gray-50'}`}>
                <div className="text-sm font-medium text-gray-900">
                  {day.toLocaleDateString('en-US', { weekday: 'short' })}
                </div>
                <div className={`text-lg ${isToday ? 'text-blue-600 font-bold' : 'text-gray-600'}`}>
                  {day.getDate()}
                </div>
              </div>
            );
          })}
        </div>
        
        {/* Time grid */}
        <div className="grid grid-cols-8 gap-0 flex-1 overflow-y-auto max-h-96">
          {hours.map(hour => (
            <React.Fragment key={hour}>
              <div className="p-2 text-xs text-gray-500 border-r border-gray-200 bg-gray-50">
                {hour === 0 ? '12 AM' : hour < 12 ? `${hour} AM` : hour === 12 ? '12 PM' : `${hour - 12} PM`}
              </div>
              {weekDays.map((day, dayIndex) => {
                const dayEvents = getEventsForDate(day).filter(event => {
                  const eventHour = new Date(event.start_datetime || event.start).getHours();
                  return eventHour === hour;
                });
                
                return (
                  <div key={dayIndex} className="border border-gray-200 p-1 h-12 relative">
                    {dayEvents.map((event, eventIndex) => (
                      <div
                        key={eventIndex}
                        className={`text-xs p-1 rounded text-white truncate ${getEventTypeColor(event)} absolute inset-1`}
                        title={`${event.title} - ${new Date(event.start_datetime || event.start).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}`}
                      >
                        {event.title}
                      </div>
                    ))}
                  </div>
                );
              })}
            </React.Fragment>
          ))}
        </div>
      </div>
    );
  };

  const renderDayView = () => {
    const dayEvents = getEventsForDate(currentDate).sort((a, b) => new Date(a.start) - new Date(b.start));
    
    return (
      <div className="space-y-4">
        {dayEvents.length === 0 ? (
          <div className="text-center py-8 text-gray-500">
            No events scheduled for this day
          </div>
        ) : (
          dayEvents.map((event, index) => (
            <div key={index} className="bg-white border border-gray-200 rounded-lg p-4 shadow-sm">
              <div className="flex items-start justify-between">
                <div className="flex items-start space-x-3">
                  <div className={`w-3 h-3 rounded-full mt-1 ${getEventTypeColor(event)}`}></div>
                  <div>
                    <h3 className="text-lg font-medium text-gray-900">{event.title}</h3>
                    <p className="text-sm text-gray-600 mt-1">{event.description}</p>
                    <div className="flex items-center space-x-4 mt-2 text-sm text-gray-500">
                      <div className="flex items-center">
                        <svg className="w-4 h-4 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                        </svg>
                        {new Date(event.start_datetime || event.start).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })} - 
                        {new Date(event.end_datetime || event.end).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                      </div>
                      {event.location && (
                        <div className="flex items-center">
                          <svg className="w-4 h-4 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z" />
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 11a3 3 0 11-6 0 3 3 0 016 0z" />
                          </svg>
                          {event.location}
                        </div>
                      )}
                    </div>
                    
                    {/* Participants for tasks */}
                    {event.type === 'task' && event.participants && event.participants.length > 0 && (
                      <div className="mt-3">
                        <p className="text-sm font-medium text-gray-700 mb-1">Participants:</p>
                        <div className="flex flex-wrap gap-1">
                          {event.participants.map((participant, pIndex) => (
                            <span key={pIndex} className="inline-flex items-center px-2 py-1 rounded-md text-xs bg-gray-100 text-gray-700">
                              {participant.name}
                            </span>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>
                </div>
                <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                  event.status === 'completed' ? 'bg-green-100 text-green-800' : 
                  event.status === 'cancelled' ? 'bg-red-100 text-red-800' :
                  'bg-yellow-100 text-yellow-800'
                }`}>
                  {event.status}
                </span>
              </div>
            </div>
          ))
        )}
      </div>
    );
  };

  return (
    <div className="max-w-7xl mx-auto p-6">
      {/* Header */}
      <div className="mb-6">
        <div className="flex justify-between items-center">
          <div>
            <h1 className="text-3xl font-bold text-gray-900">Calendar</h1>
            <p className="text-gray-600 mt-2">View your schedule and upcoming events</p>
          </div>
          
          {/* View Mode Selector */}
          <div className="flex space-x-1 bg-gray-100 rounded-lg p-1">
            {['month', 'week', 'day'].map(mode => (
              <button
                key={mode}
                onClick={() => setViewMode(mode)}
                className={`px-3 py-1 rounded-md text-sm font-medium capitalize ${
                  viewMode === mode ? 'bg-white text-gray-900 shadow-sm' : 'text-gray-600 hover:text-gray-900'
                }`}
              >
                {mode}
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Navigation */}
      <div className="flex justify-between items-center mb-6">
        <div className="flex items-center space-x-4">
          <button
            onClick={() => navigateDate(-1)}
            className="p-2 rounded-md border border-gray-300 hover:bg-gray-50"
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
            </svg>
          </button>
          
          <h2 className="text-xl font-semibold text-gray-900 min-w-64 text-center">
            {formatDateRange()}
          </h2>
          
          <button
            onClick={() => navigateDate(1)}
            className="p-2 rounded-md border border-gray-300 hover:bg-gray-50"
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
            </svg>
          </button>
        </div>
        
        <button
          onClick={goToToday}
          className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700"
        >
          Today
        </button>
      </div>

      {/* Calendar Content */}
      {loading ? (
        <div className="text-center py-8">
          <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
          <p className="mt-2 text-gray-600">Loading calendar...</p>
        </div>
      ) : error ? (
        <div className="bg-red-50 border border-red-200 rounded-md p-4">
          <p className="text-red-600">{error}</p>
          <button
            onClick={fetchEvents}
            className="mt-2 text-sm text-red-600 hover:text-red-800 underline"
          >
            Try again
          </button>
        </div>
      ) : (
        <div className="bg-white rounded-lg shadow overflow-hidden">
          {viewMode === 'month' && renderMonthView()}
          {viewMode === 'week' && renderWeekView()}
          {viewMode === 'day' && renderDayView()}
        </div>
      )}

      {/* Legend */}
      <div className="mt-6 bg-white p-4 rounded-lg shadow">
        <h3 className="text-sm font-medium text-gray-900 mb-3">Event Types</h3>
        <div className="flex flex-wrap gap-4">
          {[
            { type: 'meeting_teachers', label: 'Teacher Meeting', color: 'bg-blue-500' },
            { type: 'parent_teacher_meeting', label: 'Parent Meeting', color: 'bg-green-500' },
            { type: 'student_review', label: 'Student Review', color: 'bg-yellow-500' },
            { type: 'personal_reminder', label: 'Personal', color: 'bg-purple-500' },
            { type: 'exam_schedule', label: 'Exam', color: 'bg-red-500' },
            { type: 'class', label: 'Class', color: 'bg-indigo-500' }
          ].map(item => (
            <div key={item.type} className="flex items-center space-x-2">
              <div className={`w-3 h-3 rounded-full ${item.color}`}></div>
              <span className="text-sm text-gray-700">{item.label}</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};

export default CalendarView;