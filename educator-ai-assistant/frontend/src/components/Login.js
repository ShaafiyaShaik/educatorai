import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { Eye, EyeOff, User, Lock, GraduationCap, UserCheck, Users } from 'lucide-react';
import toast from 'react-hot-toast';
import { educators, API_BASE_URL } from '../services/api';
import axios from 'axios';

const Login = ({ setIsAuthenticated }) => {
  const [portalType, setPortalType] = useState('teacher'); // 'teacher' or 'student'
  const [formData, setFormData] = useState({
    email: '',
    password: ''
  });
  const [showPassword, setShowPassword] = useState(false);
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);

    try {
      if (portalType === 'teacher') {
        // Teacher login
        console.log('Attempting teacher login with:', formData.email);
        
        const response = await educators.login({
          email: formData.email,
          password: formData.password
        });
        
        console.log('Teacher login response:', response.data);
        
        const { access_token } = response.data;
        if (access_token) {
          localStorage.setItem('token', access_token);
          console.log('Setting authentication to true and redirecting to dashboard');
          setIsAuthenticated(true);
          toast.success('Welcome back, Teacher! 🎉');
          // Force a hard redirect to ensure the dashboard loads properly
          window.location.href = '/dashboard';
        } else {
          toast.error('No access token received');
        }
      } else {
        // Student login
        console.log('Attempting student login with:', formData.email);
        
        const response = await axios.post(`${API_BASE_URL}/api/v1/student-auth/login`, {
          email: formData.email,
          password: formData.password
        });
        
        console.log('Student login response:', response.data);
        
        // Store student token and data
        localStorage.setItem('studentToken', response.data.access_token);
        localStorage.setItem('studentData', JSON.stringify(response.data.student));
        
        toast.success('Welcome back, Student! 🎓');
        // Redirect to student portal
        navigate('/student');
      }
    } catch (error) {
      console.error('Login error details:', error.response || error);
      if (error.response?.data?.detail) {
        toast.error(error.response.data.detail);
      } else {
        toast.error(`${portalType === 'teacher' ? 'Teacher' : 'Student'} login failed`);
      }
    } finally {
      setLoading(false);
    }
  };

  const handleChange = (e) => {
    setFormData({
      ...formData,
      [e.target.name]: e.target.value
    });
  };

  return (
    <div className="min-h-screen flex items-center justify-center gradient-bg px-4">
      <div className="max-w-md w-full">
        {/* Logo and Title */}
        <div className="text-center mb-8 animate-fade-in">
          <div className="flex justify-center mb-4">
            <div className="bg-white rounded-full p-4 shadow-lg">
              <GraduationCap className="h-12 w-12 text-blue-600" />
            </div>
          </div>
          <h1 className="text-4xl font-bold text-white mb-2">
            Educator AI
          </h1>
          <p className="text-white/80 text-lg">
            Your Smart Administrative Assistant
          </p>
        </div>

        {/* Login Form */}
        <div className="bg-white/10 backdrop-blur-lg rounded-2xl shadow-2xl p-8 border border-white/20 animate-slide-up">
          {/* Portal Selection */}
          <div className="mb-6">
            <h3 className="text-white text-sm font-semibold mb-3 text-center">Select Portal</h3>
            <div className="grid grid-cols-2 gap-3">
              <button
                type="button"
                onClick={() => setPortalType('teacher')}
                className={`flex items-center justify-center p-3 rounded-lg transition-all duration-200 ${
                  portalType === 'teacher'
                    ? 'bg-white text-blue-600 shadow-lg'
                    : 'bg-white/20 text-white hover:bg-white/30'
                }`}
              >
                <UserCheck className="h-5 w-5 mr-2" />
                Teacher
              </button>
              <button
                type="button"
                onClick={() => setPortalType('student')}
                className={`flex items-center justify-center p-3 rounded-lg transition-all duration-200 ${
                  portalType === 'student'
                    ? 'bg-white text-blue-600 shadow-lg'
                    : 'bg-white/20 text-white hover:bg-white/30'
                }`}
              >
                <Users className="h-5 w-5 mr-2" />
                Student
              </button>
            </div>
          </div>

          <form onSubmit={handleSubmit} className="space-y-6">
            <div>
              <label className="block text-white text-sm font-semibold mb-2">
                Email Address
              </label>
              <div className="relative">
                <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                  <User className="h-5 w-5 text-white/50" />
                </div>
                <input
                  type="email"
                  name="email"
                  value={formData.email}
                  onChange={handleChange}
                  className="w-full pl-10 pr-4 py-3 bg-white/20 border border-white/30 rounded-lg text-white placeholder-white/50 focus:ring-2 focus:ring-white/50 focus:border-transparent transition duration-200"
                  placeholder={portalType === 'teacher' ? 'Enter teacher email' : 'Enter student email (e.g., S101@gmail.com)'}
                  required
                />
              </div>
            </div>

            <div>
              <label className="block text-white text-sm font-semibold mb-2">
                Password
              </label>
              <div className="relative">
                <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                  <Lock className="h-5 w-5 text-white/50" />
                </div>
                <input
                  type={showPassword ? 'text' : 'password'}
                  name="password"
                  value={formData.password}
                  onChange={handleChange}
                  className="w-full pl-10 pr-12 py-3 bg-white/20 border border-white/30 rounded-lg text-white placeholder-white/50 focus:ring-2 focus:ring-white/50 focus:border-transparent transition duration-200"
                  placeholder="Enter your password"
                  required
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  className="absolute inset-y-0 right-0 pr-3 flex items-center"
                >
                  {showPassword ? (
                    <EyeOff className="h-5 w-5 text-white/50 hover:text-white transition" />
                  ) : (
                    <Eye className="h-5 w-5 text-white/50 hover:text-white transition" />
                  )}
                </button>
              </div>
            </div>

            <button
              type="submit"
              disabled={loading}
              className="w-full bg-white text-blue-600 font-semibold py-3 px-4 rounded-lg hover:bg-white/90 transform transition duration-200 hover:scale-105 shadow-lg disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {loading ? (
                <div className="flex items-center justify-center">
                  <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-blue-600 mr-2"></div>
                  Signing In...
                </div>
              ) : (
                'Sign In'
              )}
            </button>
          </form>

          <div className="mt-6 text-center">
            <p className="text-white/80">
              Don't have an account?{' '}
              <Link
                to="/register"
                className="text-white font-semibold hover:underline transition"
              >
                Create Account
              </Link>
            </p>
          </div>
        </div>

        {/* Demo Credentials */}
        <div className="mt-6 bg-white/10 backdrop-blur-lg rounded-lg p-4 border border-white/20">
          <p className="text-white/80 text-sm text-center mb-3">
            💡 <strong>Demo Credentials:</strong>
          </p>
          <div className="space-y-2 text-xs text-white/70">
            <div className="text-center">
              <p><strong>Teacher:</strong> ananya.rao@school.com | Ananya@123</p>
              <p className="mt-2"><strong>Students:</strong></p>
              <p>jennifer.colon@student.edu | student123</p>
              <p>nichole.smith@student.edu | student123</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Login;