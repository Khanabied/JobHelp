import React, { useState, useEffect } from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import toast, { Toaster } from 'react-hot-toast';
import './App.css';

// Import components
import AuthPage from './components/AuthPage';
import Dashboard from './components/Dashboard';
import AdminDashboard from './components/AdminDashboard';
import LoadingSpinner from './components/LoadingSpinner';

// API service
import { authService, apiService } from './services/api';

function App() {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // Check for existing auth on app load
    checkAuth();
  }, []);

  const checkAuth = async () => {
    try {
      const token = localStorage.getItem('authToken');
      if (token) {
        const userData = await authService.getMe();
        setUser(userData);
      }
    } catch (error) {
      console.error('Auth check failed:', error);
      localStorage.removeItem('authToken');
    } finally {
      setLoading(false);
    }
  };

  const handleLogin = async (email, password) => {
    try {
      const response = await authService.login(email, password);
      localStorage.setItem('authToken', response.access_token);
      setUser(response.user);
      toast.success('Welcome to JobSasa!');
      return true;
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Login failed');
      return false;
    }
  };

  const handleRegister = async (email, password, fullName) => {
    try {
      const response = await authService.register(email, password, fullName);
      localStorage.setItem('authToken', response.access_token);
      setUser(response.user);
      toast.success('Welcome to JobSasa! Account created successfully!');
      return true;
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Registration failed');
      return false;
    }
  };

  const handleLogout = () => {
    localStorage.removeItem('authToken');
    setUser(null);
    toast.success('Logged out successfully');
  };

  // Check if user is admin
  const isAdmin = user && (user.email.endsWith('@admin.jobsasa.com') || user.email === 'admin@example.com');

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-indigo-50 via-white to-cyan-50">
        <div className="text-center">
          <LoadingSpinner />
          <div className="mt-4">
            <h1 className="text-3xl font-bold bg-gradient-to-r from-indigo-600 to-cyan-600 bg-clip-text text-transparent">
              JobSasa
            </h1>
            <p className="text-gray-600 mt-2">Loading your career optimization platform...</p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <Router>
      <div className="min-h-screen bg-gradient-to-br from-indigo-50 via-white to-cyan-50">
        <Toaster 
          position="top-right"
          toastOptions={{
            duration: 4000,
            style: {
              background: '#1f2937',
              color: '#fff',
            },
            success: {
              style: {
                background: '#059669',
              },
            },
            error: {
              style: {
                background: '#dc2626',
              },
            },
          }}
        />
        
        <Routes>
          <Route
            path="/auth"
            element={
              user ? <Navigate to="/dashboard" /> : 
              <AuthPage onLogin={handleLogin} onRegister={handleRegister} />
            }
          />
          <Route
            path="/dashboard"
            element={
              user ? <Dashboard user={user} onLogout={handleLogout} /> : 
              <Navigate to="/auth" />
            }
          />
          <Route
            path="/admin"
            element={
              isAdmin ? <AdminDashboard user={user} onLogout={handleLogout} /> : 
              <Navigate to="/dashboard" />
            }
          />
          <Route
            path="/"
            element={<Navigate to={user ? "/dashboard" : "/auth"} />}
          />
        </Routes>
      </div>
    </Router>
  );
}

export default App;