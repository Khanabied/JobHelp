import React, { useState } from 'react';
import { FileText, Mail, Lock, User, ArrowRight, Zap } from 'lucide-react';
import toast from 'react-hot-toast';

const AuthPage = ({ onLogin, onRegister }) => {
  const [isLogin, setIsLogin] = useState(true);
  const [loading, setLoading] = useState(false);
  const [formData, setFormData] = useState({
    email: '',
    password: '',
    fullName: ''
  });

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    if (!formData.email || !formData.password) {
      toast.error('Please fill in all required fields');
      return;
    }

    if (!isLogin && !formData.fullName) {
      toast.error('Please enter your full name');
      return;
    }

    setLoading(true);
    
    try {
      let success;
      if (isLogin) {
        success = await onLogin(formData.email, formData.password);
      } else {
        success = await onRegister(formData.email, formData.password, formData.fullName);
      }
      
      if (!success) {
        setLoading(false);
      }
    } catch (error) {
      console.error('Auth error:', error);
      setLoading(false);
    }
  };

  const handleInputChange = (e) => {
    setFormData({
      ...formData,
      [e.target.name]: e.target.value
    });
  };

  return (
    <div className="min-h-screen flex">
      {/* Left Side - Branding */}
      <div className="hidden lg:flex lg:w-1/2 bg-gradient-to-br from-indigo-600 via-purple-600 to-cyan-600 relative overflow-hidden">
        <div className="absolute inset-0 bg-black/20"></div>
        <div className="relative z-10 flex flex-col justify-center px-8 text-white">
          <div className="max-w-md">
            <div className="flex items-center mb-8">
              <div className="h-12 w-12 bg-white/20 backdrop-blur-sm rounded-xl flex items-center justify-center mr-4">
                <FileText className="h-6 w-6 text-white" />
              </div>
              <div>
                <h1 className="text-3xl font-bold">JobSasa</h1>
                <p className="text-indigo-100">AI Career Optimization</p>
              </div>
            </div>
            
            <h2 className="text-4xl font-bold mb-6 leading-tight">
              Transform Your Career with AI-Powered Optimization
            </h2>
            
            <div className="space-y-4 text-lg text-indigo-100">
              <div className="flex items-center">
                <Zap className="w-5 h-5 mr-3 text-yellow-300" />
                8 AI agents analyze your profile
              </div>
              <div className="flex items-center">
                <Zap className="w-5 h-5 mr-3 text-yellow-300" />
                ATS-optimized resume generation
              </div>
              <div className="flex items-center">
                <Zap className="w-5 h-5 mr-3 text-yellow-300" />
                Personalized cover letters & LinkedIn optimization
              </div>
              <div className="flex items-center">
                <Zap className="w-5 h-5 mr-3 text-yellow-300" />
                Professional document generation (DOCX/PDF)
              </div>
            </div>
            
            <div className="mt-8 p-6 bg-white/10 backdrop-blur-sm rounded-xl">
              <p className="text-sm text-indigo-100">
                "JobSasa helped me land my dream job! The AI-generated resume and cover letter were spot-on."
              </p>
              <p className="text-xs text-indigo-200 mt-2">- Sarah K., Software Engineer</p>
            </div>
          </div>
        </div>
      </div>

      {/* Right Side - Auth Form */}
      <div className="w-full lg:w-1/2 flex flex-col justify-center px-8 bg-white">
        <div className="max-w-md mx-auto w-full">
          {/* Mobile Logo */}
          <div className="lg:hidden text-center mb-8">
            <div className="h-16 w-16 bg-gradient-to-r from-indigo-500 to-cyan-500 rounded-2xl flex items-center justify-center mx-auto mb-4">
              <FileText className="h-8 w-8 text-white" />
            </div>
            <h1 className="text-2xl font-bold gradient-text">JobSasa</h1>
            <p className="text-gray-600">AI Career Optimization</p>
          </div>

          <div className="text-center mb-8">
            <h2 className="text-3xl font-bold text-gray-900 mb-2">
              {isLogin ? 'Welcome Back' : 'Get Started'}
            </h2>
            <p className="text-gray-600">
              {isLogin ? 'Continue your career transformation' : 'Start optimizing your career today'}
            </p>
          </div>

          <form onSubmit={handleSubmit} className="space-y-6">
            {!isLogin && (
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Full Name
                </label>
                <div className="relative">
                  <User className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-5 h-5" />
                  <input
                    type="text"
                    name="fullName"
                    value={formData.fullName}
                    onChange={handleInputChange}
                    className="w-full pl-10 pr-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-transparent transition-all"
                    placeholder="Enter your full name"
                    required={!isLogin}
                  />
                </div>
              </div>
            )}

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Email Address
              </label>
              <div className="relative">
                <Mail className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-5 h-5" />
                <input
                  type="email"
                  name="email"
                  value={formData.email}
                  onChange={handleInputChange}
                  className="w-full pl-10 pr-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-transparent transition-all"
                  placeholder="Enter your email"
                  required
                />
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Password
              </label>
              <div className="relative">
                <Lock className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-5 h-5" />
                <input
                  type="password"
                  name="password"
                  value={formData.password}
                  onChange={handleInputChange}
                  className="w-full pl-10 pr-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-transparent transition-all"
                  placeholder="Enter your password"
                  required
                />
              </div>
            </div>

            <button
              type="submit"
              disabled={loading}
              className="w-full btn-primary py-3 bg-gradient-to-r from-indigo-500 to-cyan-500 text-white rounded-lg font-medium hover:shadow-lg transition-all disabled:opacity-50 flex items-center justify-center"
            >
              {loading ? (
                <div className="w-5 h-5 border-2 border-white border-t-transparent rounded-full animate-spin mr-2"></div>
              ) : (
                <ArrowRight className="w-5 h-5 mr-2" />
              )}
              {isLogin ? 'Sign In' : 'Create Account'}
            </button>
          </form>

          <div className="mt-8 text-center">
            <p className="text-gray-600">
              {isLogin ? "Don't have an account?" : "Already have an account?"}
              <button
                onClick={() => {
                  setIsLogin(!isLogin);
                  setFormData({ email: '', password: '', fullName: '' });
                }}
                className="ml-2 text-indigo-600 font-medium hover:text-indigo-500 transition-colors"
              >
                {isLogin ? 'Sign Up' : 'Sign In'}
              </button>
            </p>
          </div>

          {/* Features Preview */}
          <div className="mt-8 p-6 bg-gradient-to-r from-indigo-50 to-cyan-50 rounded-xl">
            <h3 className="font-semibold text-gray-900 mb-3 text-center">🚀 What You'll Get:</h3>
            <div className="space-y-2 text-sm text-gray-700">
              <div>✨ AI-powered resume optimization</div>
              <div>📝 Personalized cover letters</div>
              <div>💼 LinkedIn profile enhancement</div>
              <div>🎯 Interview preparation guides</div>
              <div>📄 Professional DOCX/PDF documents</div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default AuthPage;