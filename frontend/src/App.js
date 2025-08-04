import React from "react";
import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import { Toaster } from 'react-hot-toast';
import { AuthProvider } from './contexts/AuthContext';
import Layout from './components/Layout/Layout';
import ProtectedRoute from './components/ProtectedRoute';

// Auth Pages
import Login from './pages/Auth/Login';
import Register from './pages/Auth/Register';

// Main Pages
import Dashboard from './pages/Dashboard/Dashboard';

// Import styles
import "./App.css";

function App() {
  return (
    <AuthProvider>
      <BrowserRouter>
        <Layout>
          <Routes>
            {/* Public Routes */}
            <Route path="/login" element={<Login />} />
            <Route path="/register" element={<Register />} />
            
            {/* Protected Routes */}
            <Route path="/dashboard" element={
              <ProtectedRoute>
                <Dashboard />
              </ProtectedRoute>
            } />
            
            {/* Resume Tool */}
            <Route path="/resume" element={
              <ProtectedRoute>
                <div className="text-center py-12">
                  <h1 className="text-2xl font-bold text-gray-900">Resume Optimizer</h1>
                  <p className="text-gray-600 mt-2">Coming soon...</p>
                </div>
              </ProtectedRoute>
            } />
            
            {/* Cover Letter Tool */}
            <Route path="/cover-letter" element={
              <ProtectedRoute>
                <div className="text-center py-12">
                  <h1 className="text-2xl font-bold text-gray-900">Cover Letter Writer</h1>
                  <p className="text-gray-600 mt-2">Coming soon...</p>
                </div>
              </ProtectedRoute>
            } />
            
            {/* LinkedIn Tool */}
            <Route path="/linkedin" element={
              <ProtectedRoute>
                <div className="text-center py-12">
                  <h1 className="text-2xl font-bold text-gray-900">LinkedIn Optimizer</h1>
                  <p className="text-gray-600 mt-2">Coming soon...</p>
                </div>
              </ProtectedRoute>
            } />
            
            {/* Interview Prep Tool */}
            <Route path="/interview" element={
              <ProtectedRoute>
                <div className="text-center py-12">
                  <h1 className="text-2xl font-bold text-gray-900">Interview Preparation</h1>
                  <p className="text-gray-600 mt-2">Coming soon...</p>
                </div>
              </ProtectedRoute>
            } />
            
            {/* Admin Panel */}
            <Route path="/admin" element={
              <ProtectedRoute adminOnly={true}>
                <div className="text-center py-12">
                  <h1 className="text-2xl font-bold text-gray-900">Admin Panel</h1>
                  <p className="text-gray-600 mt-2">Coming soon...</p>
                </div>
              </ProtectedRoute>
            } />
            
            {/* Default redirect */}
            <Route path="/" element={<Navigate to="/dashboard" replace />} />
          </Routes>
        </Layout>
      </BrowserRouter>
      
      <Toaster
        position="top-right"
        toastOptions={{
          duration: 4000,
          style: {
            background: '#363636',
            color: '#fff',
          },
          success: {
            duration: 3000,
          },
        }}
      />
    </AuthProvider>
  );
}

export default App;
