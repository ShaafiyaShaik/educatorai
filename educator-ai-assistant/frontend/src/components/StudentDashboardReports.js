import React, { useState, useEffect } from 'react';
import { 
  FileText, Eye, Download, Calendar, User, Users, 
  BookOpen, Award, AlertCircle, Clock
} from 'lucide-react';

const StudentReportsView = ({ isParentMode = false }) => {
  const [reports, setReports] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selectedReport, setSelectedReport] = useState(null);

  useEffect(() => {
    fetchReports();
  }, [isParentMode]);

  const fetchReports = async () => {
    try {
  // The student dashboard stores the student JWT under 'studentToken'
  const token = localStorage.getItem('studentToken') || localStorage.getItem('token');
  const endpoint = isParentMode ? '/api/v1/student-dashboard/parent-reports' : '/api/v1/student-dashboard/reports';
      
      const response = await fetch(`http://localhost:8003${endpoint}`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      
      if (response.ok) {
        const data = await response.json();
        setReports(data);
      }
    } catch (error) {
      console.error('Error fetching reports:', error);
    } finally {
      setLoading(false);
    }
  };

  const markAsViewed = async (reportId) => {
    try {
  const token = localStorage.getItem('studentToken') || localStorage.getItem('token');
      const viewerType = isParentMode ? 'parent' : 'student';
      
  await fetch(`http://localhost:8003/api/v1/student-dashboard/reports/${reportId}/mark-viewed?viewer_type=${viewerType}`, {
        method: 'POST',
        headers: { 'Authorization': `Bearer ${token}` }
      });
      
      // Update local state
      setReports(prev => prev.map(report => 
        report.id === reportId 
          ? { 
              ...report, 
              [isParentMode ? 'is_viewed_by_parent' : 'is_viewed_by_student']: true 
            }
          : report
      ));
    } catch (error) {
      console.error('Error marking report as viewed:', error);
    }
  };

  const downloadReport = async (reportId, title) => {
    try {
  const token = localStorage.getItem('studentToken') || localStorage.getItem('token');
      const response = await fetch(`http://localhost:8003/api/v1/student-dashboard/reports/${reportId}/download`, {
        headers: { 'Authorization': `Bearer ${token}` },
        responseType: 'blob'
      });
      
      if (response.ok) {
        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        const link = document.createElement('a');
        link.href = url;
        link.setAttribute('download', `${title}.pdf`);
        document.body.appendChild(link);
        link.click();
        link.remove();
        window.URL.revokeObjectURL(url);
      }
    } catch (error) {
      console.error('Error downloading report:', error);
    }
  };

  const getReportIcon = (reportType) => {
    switch (reportType) {
      case 'individual_student': return <User className="w-5 h-5" />;
      case 'section_summary': return <Users className="w-5 h-5" />;
      case 'subject_analysis': return <BookOpen className="w-5 h-5" />;
      default: return <FileText className="w-5 h-5" />;
    }
  };

  const getStatusColor = (report) => {
    const isViewed = isParentMode ? report.is_viewed_by_parent : report.is_viewed_by_student;
    return isViewed ? 'text-green-600' : 'text-orange-600';
  };

  const getStatusText = (report) => {
    const isViewed = isParentMode ? report.is_viewed_by_parent : report.is_viewed_by_student;
    return isViewed ? 'Viewed' : 'New';
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500"></div>
      </div>
    );
  }

  return (
    <div className="max-w-4xl mx-auto p-6">
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-gray-900 flex items-center gap-2">
          {isParentMode ? <Users className="w-6 h-6" /> : <User className="w-6 h-6" />}
          {isParentMode ? 'Parent Dashboard - Reports' : 'My Reports'}
        </h1>
        <p className="text-gray-600 mt-1">
          {isParentMode 
            ? 'View your child\'s performance reports and teacher communications' 
            : 'View your performance reports from teachers'
          }
        </p>
      </div>

      {reports.length > 0 ? (
        <div className="space-y-4">
          {reports.map((report) => {
            const isViewed = isParentMode ? report.is_viewed_by_parent : report.is_viewed_by_student;
            
            return (
              <div 
                key={report.id} 
                className={`bg-white rounded-lg border-2 p-6 hover:shadow-md transition-shadow ${
                  !isViewed ? 'border-blue-200 bg-blue-50' : 'border-gray-200'
                }`}
              >
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <div className="flex items-center gap-3 mb-2">
                      <div className={`p-2 rounded-lg ${
                        report.report_type === 'individual_student' ? 'bg-blue-100 text-blue-600' :
                        report.report_type === 'section_summary' ? 'bg-green-100 text-green-600' :
                        'bg-purple-100 text-purple-600'
                      }`}>
                        {getReportIcon(report.report_type)}
                      </div>
                      
                      <div>
                        <h3 className="text-lg font-semibold text-gray-900">{report.title}</h3>
                        <p className="text-sm text-gray-600">From: {report.from_educator}</p>
                      </div>
                      
                      <span className={`px-3 py-1 text-sm font-medium rounded-full ${getStatusColor(report)} ${
                        isViewed ? 'bg-green-50' : 'bg-orange-50'
                      }`}>
                        {getStatusText(report)}
                      </span>
                    </div>

                    <p className="text-gray-700 mb-3">{report.description}</p>

                    {report.comments && (
                      <div className="bg-yellow-50 border-l-4 border-yellow-400 p-3 mb-3">
                        <div className="flex items-start">
                          <AlertCircle className="w-5 h-5 text-yellow-400 mt-0.5 mr-2" />
                          <div>
                            <p className="text-sm font-medium text-yellow-800">Teacher's Note:</p>
                            <p className="text-sm text-yellow-700">{report.comments}</p>
                          </div>
                        </div>
                      </div>
                    )}

                    <div className="flex items-center gap-4 text-sm text-gray-500">
                      <span className="flex items-center gap-1">
                        <Calendar className="w-4 h-4" />
                        {new Date(report.sent_at).toLocaleDateString('en-US', {
                          year: 'numeric',
                          month: 'short',
                          day: 'numeric'
                        })}
                      </span>
                      
                      <span className="flex items-center gap-1">
                        <Award className="w-4 h-4" />
                        {report.academic_year}
                      </span>
                      
                      <span className="flex items-center gap-1">
                        <FileText className="w-4 h-4" />
                        {report.report_format.toUpperCase()}
                      </span>

                      {report.recipient_type === 'both' && (
                        <span className="flex items-center gap-1">
                          <Users className="w-4 h-4" />
                          Student & Parent
                        </span>
                      )}
                    </div>
                  </div>

                  <div className="flex flex-col gap-2 ml-4">
                    {!isViewed && (
                      <button
                        onClick={() => markAsViewed(report.id)}
                        className="flex items-center gap-2 px-3 py-2 bg-blue-600 text-white text-sm rounded-lg hover:bg-blue-700 transition-colors"
                      >
                        <Eye className="w-4 h-4" />
                        Mark as Read
                      </button>
                    )}
                    
                    <button
                      onClick={() => downloadReport(report.id, report.title)}
                      className="flex items-center gap-2 px-3 py-2 bg-green-600 text-white text-sm rounded-lg hover:bg-green-700 transition-colors"
                    >
                      <Download className="w-4 h-4" />
                      Download
                    </button>
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      ) : (
        <div className="text-center py-12">
          <FileText className="w-16 h-16 mx-auto text-gray-300 mb-4" />
          <h3 className="text-lg font-medium text-gray-900 mb-2">No Reports Yet</h3>
          <p className="text-gray-600">
            {isParentMode 
              ? 'No reports have been sent for your child yet. Check back later for updates from teachers.'
              : 'You haven\'t received any reports yet. Your teachers will send performance reports here.'
            }
          </p>
        </div>
      )}
    </div>
  );
};

// Parent Mode Toggle Component
const ParentModeToggle = ({ isParentMode, onToggle }) => {
  return (
    <div className="bg-white p-4 rounded-lg border border-gray-200 mb-6">
      <div className="flex items-center justify-between">
        <div>
          <h3 className="text-sm font-medium text-gray-900">Dashboard View</h3>
          <p className="text-sm text-gray-600">
            Switch between student and parent perspectives
          </p>
        </div>
        <button
          onClick={onToggle}
          className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${
            isParentMode ? 'bg-blue-600' : 'bg-gray-200'
          }`}
        >
          <span
            className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${
              isParentMode ? 'translate-x-6' : 'translate-x-1'
            }`}
          />
        </button>
      </div>
      <div className="flex items-center gap-4 mt-2 text-sm">
        <span className={`flex items-center gap-1 ${!isParentMode ? 'text-blue-600 font-medium' : 'text-gray-500'}`}>
          <User className="w-4 h-4" />
          Student Mode
        </span>
        <span className={`flex items-center gap-1 ${isParentMode ? 'text-blue-600 font-medium' : 'text-gray-500'}`}>
          <Users className="w-4 h-4" />
          Parent Mode
        </span>
      </div>
    </div>
  );
};

// Main Student Dashboard Component
const StudentDashboardReports = () => {
  const [isParentMode, setIsParentMode] = useState(false);

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-6xl mx-auto py-6">
        <ParentModeToggle 
          isParentMode={isParentMode}
          onToggle={() => setIsParentMode(!isParentMode)}
        />
        
        <StudentReportsView isParentMode={isParentMode} />
      </div>
    </div>
  );
};

export { StudentReportsView, ParentModeToggle };
export default StudentDashboardReports;