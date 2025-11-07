import React, { useState } from 'react';
import axios from 'axios';

const StudentLogin = ({ onLogin }) => {
  const [formData, setFormData] = useState({
    email: '',
    password: ''
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleChange = (e) => {
    setFormData({
      ...formData,
      [e.target.name]: e.target.value
    });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');

    try {
      const response = await axios.post('http://localhost:8001/api/v1/student-auth/login', formData);
      
      // Store token and student data
      localStorage.setItem('studentToken', response.data.access_token);
      localStorage.setItem('studentData', JSON.stringify(response.data.student));
      
      // Call parent component callback
      onLogin(response.data.student);
      
    } catch (error) {
      console.error('Login error:', error);
      if (error.response) {
        setError(error.response.data.detail || 'Login failed');
      } else {
        setError('Network error. Please try again.');
      }
    } finally {
      setLoading(false);
    }
  };

  const handleQuickLogin = (email) => {
    setFormData({
      email: email,
      password: 'password123'
    });
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-500 to-purple-600 flex items-center justify-center p-4">
      <div className="bg-white rounded-lg shadow-xl p-8 w-full max-w-md">
        <div className="text-center mb-8">
          <h1 className="text-3xl font-bold text-gray-800 mb-2">Student Portal</h1>
          <p className="text-gray-600">Welcome back! Please sign in to continue.</p>
        </div>

        {error && (
          <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded mb-4">
            {error}
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-6">
          <div>
            <label htmlFor="email" className="block text-sm font-medium text-gray-700 mb-2">
              Email Address
            </label>
            <input
              id="email"
              name="email"
              type="email"
              required
              value={formData.email}
              onChange={handleChange}
              className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              placeholder="Enter your email (e.g., S101@gmail.com)"
            />
          </div>

          <div>
            <label htmlFor="password" className="block text-sm font-medium text-gray-700 mb-2">
              Password
            </label>
            <input
              id="password"
              name="password"
              type="password"
              required
              value={formData.password}
              onChange={handleChange}
              className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              placeholder="Enter your password"
            />
          </div>

          <button
            type="submit"
            disabled={loading}
            className="w-full flex justify-center py-2 px-4 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {loading ? 'Signing in...' : 'Sign In'}
          </button>
        </form>

        {/* Demo accounts for quick login */}
        <div className="mt-8">
          <div className="relative">
            <div className="absolute inset-0 flex items-center">
              <div className="w-full border-t border-gray-300" />
            </div>
            <div className="relative flex justify-center text-sm">
              <span className="px-2 bg-white text-gray-500">Demo Accounts</span>
            </div>
          </div>

          <div className="mt-6 space-y-2">
            <p className="text-sm text-gray-600 text-center">Quick login with demo accounts:</p>
            
            <div className="grid grid-cols-2 gap-2">
              <button
                onClick={() => handleQuickLogin('S101@gmail.com')}
                className="text-xs bg-gray-100 hover:bg-gray-200 px-3 py-2 rounded transition-colors"
              >
                S101@gmail.com
                <br />
                <span className="text-gray-500">Alice (Sec A)</span>
              </button>
              <button
                onClick={() => handleQuickLogin('S102@gmail.com')}
                className="text-xs bg-gray-100 hover:bg-gray-200 px-3 py-2 rounded transition-colors"
              >
                S102@gmail.com
                <br />
                <span className="text-gray-500">Bob (Sec A)</span>
              </button>
              <button
                onClick={() => handleQuickLogin('S201@gmail.com')}
                className="text-xs bg-gray-100 hover:bg-gray-200 px-3 py-2 rounded transition-colors"
              >
                S201@gmail.com
                <br />
                <span className="text-gray-500">Fiona (Sec B)</span>
              </button>
              <button
                onClick={() => handleQuickLogin('S301@gmail.com')}
                className="text-xs bg-gray-100 hover:bg-gray-200 px-3 py-2 rounded transition-colors"
              >
                S301@gmail.com
                <br />
                <span className="text-gray-500">Ian (Sec C)</span>
              </button>
            </div>
            
            <p className="text-xs text-gray-500 text-center mt-2">
              Password for all demo accounts: <strong>password123</strong>
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default StudentLogin;