import React from 'react';
import { Link } from 'react-router-dom';

const PortalSelection = () => {
  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-500 to-purple-600 flex items-center justify-center p-4">
      <div className="bg-white rounded-lg shadow-xl p-8 w-full max-w-md">
        <div className="text-center mb-8">
          <h1 className="text-3xl font-bold text-gray-800 mb-2">Education Portal</h1>
          <p className="text-gray-600">Choose your portal to continue</p>
        </div>

        <div className="space-y-4">
          <Link
            to="/login"
            className="w-full flex items-center justify-center px-6 py-4 border border-transparent rounded-md shadow-sm text-lg font-medium text-white bg-blue-600 hover:bg-blue-700 transition-colors"
          >
            <span className="mr-3">�</span>
            Education Portal Login
          </Link>
          
          <p className="text-center text-gray-600 text-sm">
            Select Teacher or Student portal after clicking login
          </p>
        </div>

        <div className="mt-8 text-center">
          <h3 className="text-sm font-medium text-gray-700 mb-4">Demo Accounts</h3>
          
          <div className="text-xs text-gray-600 space-y-2">
            <div className="border rounded p-2">
              <p className="font-medium">Teacher Login:</p>
              <p>Email: shaafiya07@gmail.com</p>
              <p>Password: password123</p>
            </div>
            
            <div className="border rounded p-2">
              <p className="font-medium">Student Login Examples:</p>
              <p>S101@gmail.com, S102@gmail.com, S201@gmail.com</p>
              <p>Password: password123</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default PortalSelection;