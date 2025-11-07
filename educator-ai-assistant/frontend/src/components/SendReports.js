import React, { useState, useEffect } from 'react';
import { Send, Users, User, FileText, Mail, Calendar, CheckCircle } from 'lucide-react';

const SendReportModal = ({ isOpen, onClose, onSendReport }) => {
  const [formData, setFormData] = useState({
    report_type: 'individual',
    recipient_type: 'both',
    title: '',
    description: '',
    comments: '',
    format: 'pdf',
    student_ids: [],
    section_id: null,
    subject_id: null
  });

  const [students, setStudents] = useState([]);
  const [sections, setSections] = useState([]);
  const [subjects, setSubjects] = useState([]);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (isOpen) {
      fetchData();
    }
  }, [isOpen]);

  const fetchData = async () => {
    try {
      const token = localStorage.getItem('token');
      const headers = { 'Authorization': `Bearer ${token}` };
      
      // Fetch sections first
      const sectionsRes = await fetch('/api/v1/students/sections', { headers });
      
      if (sectionsRes.ok) {
        const sectionsData = await sectionsRes.json();
        setSections(sectionsData);
        
        // Extract subjects from sections
        const allSubjects = [];
        sectionsData.forEach(section => {
          if (section.subjects) {
            allSubjects.push(...section.subjects);
          }
        });
        setSubjects(allSubjects);
        
        // Get students from all sections
        const allStudents = [];
        for (const section of sectionsData) {
          try {
            const studentsRes = await fetch(`/api/v1/students/sections/${section.id}/students`, { headers });
            if (studentsRes.ok) {
              const students = await studentsRes.json();
              allStudents.push(...students);
            }
          } catch (err) {
            console.error(`Error fetching students for section ${section.id}:`, err);
          }
        }
        setStudents(allStudents);
      }
    } catch (error) {
      console.error('Error fetching data:', error);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    
    try {
      await onSendReport(formData);
      onClose();
      setFormData({
        report_type: 'individual',
        recipient_type: 'both',
        title: '',
        description: '',
        comments: '',
        format: 'pdf',
        student_ids: [],
        section_id: null,
        subject_id: null
      });
    } catch (error) {
      console.error('Error sending report:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleStudentSelection = (studentId, isSelected) => {
    if (isSelected) {
      setFormData(prev => ({
        ...prev,
        student_ids: [...prev.student_ids, studentId]
      }));
    } else {
      setFormData(prev => ({
        ...prev,
        student_ids: prev.student_ids.filter(id => id !== studentId)
      }));
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-xl max-w-2xl w-full max-h-[90vh] overflow-y-auto">
        <div className="p-6 border-b border-gray-200">
          <h2 className="text-xl font-bold text-gray-900 flex items-center gap-2">
            <Send className="w-5 h-5" />
            Send Performance Report
          </h2>
        </div>

        <form onSubmit={handleSubmit} className="p-6 space-y-6">
          {/* Report Type */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Report Type
            </label>
            <select
              value={formData.report_type}
              onChange={(e) => setFormData(prev => ({ ...prev, report_type: e.target.value }))}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
            >
              <option value="individual">Individual Student Reports</option>
              <option value="section">Section Summary Report</option>
              <option value="subject">Subject Analysis Report</option>
            </select>
          </div>

          {/* Recipient Type */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Send To
            </label>
            <div className="grid grid-cols-3 gap-3">
              {['student', 'parent', 'both'].map((type) => (
                <label key={type} className="flex items-center space-x-2 cursor-pointer">
                  <input
                    type="radio"
                    name="recipient_type"
                    value={type}
                    checked={formData.recipient_type === type}
                    onChange={(e) => setFormData(prev => ({ ...prev, recipient_type: e.target.value }))}
                    className="w-4 h-4 text-blue-600"
                  />
                  <span className="text-sm capitalize flex items-center gap-1">
                    {type === 'student' && <User className="w-4 h-4" />}
                    {type === 'parent' && <Users className="w-4 h-4" />}
                    {type === 'both' && <Users className="w-4 h-4" />}
                    {type === 'both' ? 'Student & Parent' : type}
                  </span>
                </label>
              ))}
            </div>
          </div>

          {/* Conditional Selection Based on Report Type */}
          {formData.report_type === 'individual' && (
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Select Students
              </label>
              <div className="border border-gray-300 rounded-lg max-h-48 overflow-y-auto">
                {students.map((student) => (
                  <label key={student.id} className="flex items-center space-x-3 p-3 hover:bg-gray-50 cursor-pointer">
                    <input
                      type="checkbox"
                      checked={formData.student_ids.includes(student.id)}
                      onChange={(e) => handleStudentSelection(student.id, e.target.checked)}
                      className="w-4 h-4 text-blue-600"
                    />
                    <div>
                      <div className="font-medium">{student.full_name}</div>
                      <div className="text-sm text-gray-500">
                        {student.student_id} - {student.section_name}
                      </div>
                    </div>
                  </label>
                ))}
              </div>
              <div className="text-sm text-gray-500 mt-1">
                {formData.student_ids.length} student(s) selected
              </div>
            </div>
          )}

          {formData.report_type === 'section' && (
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Select Section
              </label>
              <select
                value={formData.section_id || ''}
                onChange={(e) => setFormData(prev => ({ ...prev, section_id: parseInt(e.target.value) }))}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
              >
                <option value="">Choose a section...</option>
                {sections.map((section) => (
                  <option key={section.id} value={section.id}>
                    {section.name} ({section.student_count} students)
                  </option>
                ))}
              </select>
            </div>
          )}

          {formData.report_type === 'subject' && (
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Select Subject
              </label>
              <select
                value={formData.subject_id || ''}
                onChange={(e) => setFormData(prev => ({ ...prev, subject_id: parseInt(e.target.value) }))}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
              >
                <option value="">Choose a subject...</option>
                {subjects.map((subject) => (
                  <option key={subject.id} value={subject.id}>
                    {subject.name} - {subject.code}
                  </option>
                ))}
              </select>
            </div>
          )}

          {/* Report Details */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Report Title *
            </label>
            <input
              type="text"
              required
              value={formData.title}
              onChange={(e) => setFormData(prev => ({ ...prev, title: e.target.value }))}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
              placeholder="e.g., Mid-Term Performance Report"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Description
            </label>
            <textarea
              value={formData.description}
              onChange={(e) => setFormData(prev => ({ ...prev, description: e.target.value }))}
              rows="3"
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
              placeholder="Brief description of the report content..."
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Additional Comments
            </label>
            <textarea
              value={formData.comments}
              onChange={(e) => setFormData(prev => ({ ...prev, comments: e.target.value }))}
              rows="2"
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
              placeholder="Any additional comments for students/parents..."
            />
          </div>

          {/* Format Selection */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Report Format
            </label>
            <div className="flex gap-4">
              {['pdf', 'excel', 'both'].map((format) => (
                <label key={format} className="flex items-center space-x-2 cursor-pointer">
                  <input
                    type="radio"
                    name="format"
                    value={format}
                    checked={formData.format === format}
                    onChange={(e) => setFormData(prev => ({ ...prev, format: e.target.value }))}
                    className="w-4 h-4 text-blue-600"
                  />
                  <span className="text-sm capitalize flex items-center gap-1">
                    <FileText className="w-4 h-4" />
                    {format.toUpperCase()}
                  </span>
                </label>
              ))}
            </div>
          </div>

          {/* Action Buttons */}
          <div className="flex justify-end space-x-3 pt-4 border-t border-gray-200">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2 text-gray-700 bg-gray-100 rounded-lg hover:bg-gray-200 transition-colors"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={loading || !formData.title || 
                (formData.report_type === 'individual' && formData.student_ids.length === 0) ||
                (formData.report_type === 'section' && !formData.section_id) ||
                (formData.report_type === 'subject' && !formData.subject_id)
              }
              className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2 transition-colors"
            >
              {loading ? (
                <>
                  <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
                  Sending...
                </>
              ) : (
                <>
                  <Send className="w-4 h-4" />
                  Send Report
                </>
              )}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

const SentReportsHistory = ({ sentReports, onRefresh }) => {
  return (
    <div className="bg-white rounded-xl shadow-sm border border-gray-200">
      <div className="p-6 border-b border-gray-200">
        <div className="flex items-center justify-between">
          <h3 className="text-lg font-semibold text-gray-900 flex items-center gap-2">
            <Mail className="w-5 h-5" />
            Sent Reports History
          </h3>
          <button
            onClick={onRefresh}
            className="text-blue-600 hover:text-blue-800 text-sm font-medium"
          >
            Refresh
          </button>
        </div>
      </div>

      <div className="divide-y divide-gray-200">
        {sentReports.length > 0 ? (
          sentReports.map((report) => (
            <div key={report.id} className="p-4 hover:bg-gray-50">
              <div className="flex items-start justify-between">
                <div className="flex-1">
                  <div className="flex items-center gap-2 mb-1">
                    <h4 className="font-medium text-gray-900">{report.title}</h4>
                    <span className={`px-2 py-1 text-xs rounded-full ${
                      report.recipient_type === 'both' 
                        ? 'bg-purple-100 text-purple-800'
                        : report.recipient_type === 'parent'
                        ? 'bg-blue-100 text-blue-800'
                        : 'bg-green-100 text-green-800'
                    }`}>
                      {report.recipient_type === 'both' ? 'Student & Parent' : report.recipient_type}
                    </span>
                  </div>
                  
                  <p className="text-sm text-gray-600 mb-2">{report.description}</p>
                  
                  <div className="flex items-center gap-4 text-xs text-gray-500">
                    <span className="flex items-center gap-1">
                      <Calendar className="w-3 h-3" />
                      {new Date(report.sent_at).toLocaleDateString()}
                    </span>
                    <span className="flex items-center gap-1">
                      <Users className="w-3 h-3" />
                      {report.students_count} student(s)
                    </span>
                    <span className="flex items-center gap-1">
                      <FileText className="w-3 h-3" />
                      {report.format.toUpperCase()}
                    </span>
                  </div>
                </div>
                
                <div className="flex flex-col items-end gap-1">
                  <div className="flex items-center gap-2">
                    {report.is_viewed_by_student && (
                      <div className="flex items-center gap-1 text-green-600">
                        <CheckCircle className="w-4 h-4" />
                        <span className="text-xs">Student Viewed</span>
                      </div>
                    )}
                    {report.is_viewed_by_parent && (
                      <div className="flex items-center gap-1 text-blue-600">
                        <CheckCircle className="w-4 h-4" />
                        <span className="text-xs">Parent Viewed</span>
                      </div>
                    )}
                  </div>
                  <span className={`px-2 py-1 text-xs rounded-full ${
                    report.status === 'viewed' 
                      ? 'bg-green-100 text-green-800'
                      : 'bg-yellow-100 text-yellow-800'
                  }`}>
                    {report.status}
                  </span>
                </div>
              </div>
            </div>
          ))
        ) : (
          <div className="p-8 text-center text-gray-500">
            <Mail className="w-12 h-12 mx-auto mb-3 text-gray-300" />
            <p>No reports sent yet</p>
          </div>
        )}
      </div>
    </div>
  );
};

export { SendReportModal, SentReportsHistory };