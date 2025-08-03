import React, { useState, useEffect } from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import toast, { Toaster } from 'react-hot-toast';
import './App.css';

// Import components
import AuthPage from './components/AuthPage';
import Dashboard from './components/Dashboard';
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
      toast.success('Login successful!');
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
      toast.success('Registration successful!');
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

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50">
        <LoadingSpinner />
      </div>
    );
  }

  return (
    <Router>
      <div className="min-h-screen bg-gray-50">
        <Toaster 
          position="top-right"
          toastOptions={{
            duration: 4000,
            style: {
              background: '#363636',
              color: '#fff',
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
            path="/"
            element={<Navigate to={user ? "/dashboard" : "/auth"} />}
          />
        </Routes>
      </div>
    </Router>
  );
}

export default App;