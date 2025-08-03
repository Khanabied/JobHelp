import React, { useState, useEffect } from 'react';
import { 
  BarChart3, Users, FileText, Download, TrendingUp, 
  Activity, Settings, LogOut, RefreshCw, Calendar,
  UserCheck, FileAnalytics, Target, Zap
} from 'lucide-react';
import toast from 'react-hot-toast';
import LoadingSpinner from './LoadingSpinner';
import { apiService } from '../services/api';

const AdminDashboard = ({ user, onLogout }) => {
  const [dashboardData, setDashboardData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [periodDays, setPeriodDays] = useState(30);
  const [activeTab, setActiveTab] = useState('overview');
  const [users, setUsers] = useState([]);
  const [usersLoading, setUsersLoading] = useState(false);

  useEffect(() => {
    fetchDashboardData();
  }, [periodDays]);

  useEffect(() => {
    if (activeTab === 'users') {
      fetchUsers();
    }
  }, [activeTab]);

  const fetchDashboardData = async () => {
    try {
      setLoading(true);
      const response = await apiService.get(`/api/admin/dashboard?period_days=${periodDays}`);
      setDashboardData(response);
    } catch (error) {
      toast.error('Failed to load dashboard data');
      console.error('Dashboard error:', error);
    } finally {
      setLoading(false);
    }
  };

  const fetchUsers = async () => {
    try {
      setUsersLoading(true);
      const response = await apiService.get('/api/admin/users?page=1&limit=100');
      setUsers(response.users);
    } catch (error) {
      toast.error('Failed to load users');
      console.error('Users error:', error);
    } finally {
      setUsersLoading(false);
    }
  };

  const MetricCard = ({ title, value, change, icon: Icon, color = 'blue' }) => {
    const colorClasses = {
      blue: 'text-blue-600 bg-blue-50 border-blue-200',
      green: 'text-green-600 bg-green-50 border-green-200',
      purple: 'text-purple-600 bg-purple-50 border-purple-200',
      orange: 'text-orange-600 bg-orange-50 border-orange-200',
      cyan: 'text-cyan-600 bg-cyan-50 border-cyan-200'
    };

    return (
      <div className="admin-card">
        <div className="flex items-center justify-between mb-4">
          <div className={`p-3 rounded-lg ${colorClasses[color]}`}>
            <Icon className="w-6 h-6" />
          </div>
          {change && (
            <span className={`text-sm font-medium ${
              change > 0 ? 'text-green-600' : 'text-red-600'
            }`}>
              {change > 0 ? '+' : ''}{change}%
            </span>
          )}
        </div>
        <h3 className="text-2xl font-bold text-gray-900 mb-1">{value}</h3>
        <p className="text-gray-600 text-sm">{title}</p>
      </div>
    );
  };

  const renderOverview = () => {
    if (!dashboardData) return null;

    const { user_metrics, analysis_metrics, document_metrics, engagement_metrics, system_metrics } = dashboardData;

    return (
      <div className="space-y-6">
        {/* Key Metrics Grid */}
        <div className="admin-grid">
          <MetricCard
            title="Total Users"
            value={user_metrics.total_users}
            icon={Users}
            color="blue"
          />
          <MetricCard
            title="Active Users (30d)"
            value={user_metrics.active_users_period}
            icon={UserCheck}
            color="green"
          />
          <MetricCard
            title="Total Analyses"
            value={analysis_metrics.total_analyses}
            icon={FileAnalytics}
            color="purple"
          />
          <MetricCard
            title="Documents Generated"
            value={document_metrics.total_documents}
            icon={FileText}
            color="orange"
          />
          <MetricCard
            title="New Registrations (30d)"
            value={user_metrics.new_users_period}
            icon={TrendingUp}
            color="cyan"
          />
          <MetricCard
            title="Processing Success Rate"
            value={`${system_metrics.processing_success_rate}%`}
            icon={Target}
            color="green"
          />
        </div>

        {/* Analysis Breakdown */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <div className="chart-container">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">Analysis Types</h3>
            <div className="space-y-3">
              {Object.entries(analysis_metrics.analysis_types).map(([type, count]) => (
                <div key={type} className="flex items-center justify-between">
                  <span className="text-gray-600 capitalize">{type.replace('_', ' ')}</span>
                  <div className="flex items-center">
                    <div className="w-32 bg-gray-200 rounded-full h-2 mr-3">
                      <div 
                        className="bg-gradient-to-r from-blue-500 to-purple-500 h-2 rounded-full"
                        style={{ 
                          width: `${(count / analysis_metrics.total_analyses * 100)}%` 
                        }}
                      ></div>
                    </div>
                    <span className="text-sm font-medium text-gray-900">{count}</span>
                  </div>
                </div>
              ))}
            </div>
          </div>

          <div className="chart-container">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">Feature Usage</h3>
            <div className="space-y-4">
              <div className="flex items-center justify-between p-3 bg-blue-50 rounded-lg">
                <span className="text-blue-800 font-medium">Basic Analysis</span>
                <span className="text-blue-600 font-bold">{engagement_metrics.feature_usage.basic_analysis}</span>
              </div>
              <div className="flex items-center justify-between p-3 bg-purple-50 rounded-lg">
                <span className="text-purple-800 font-medium">Extended Analysis</span>
                <span className="text-purple-600 font-bold">{engagement_metrics.feature_usage.extended_analysis}</span>
              </div>
              <div className="p-3 bg-gray-50 rounded-lg">
                <div className="text-sm text-gray-600">Average per user</div>
                <div className="text-lg font-bold text-gray-900">{engagement_metrics.avg_analyses_per_user}</div>
              </div>
            </div>
          </div>
        </div>

        {/* Top Users */}
        <div className="chart-container">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Most Active Users</h3>
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="border-b border-gray-200">
                  <th className="text-left py-2 text-sm font-medium text-gray-600">User</th>
                  <th className="text-left py-2 text-sm font-medium text-gray-600">Analyses</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100">
                {engagement_metrics.top_active_users.slice(0, 5).map((user, idx) => (
                  <tr key={idx}>
                    <td className="py-2 text-sm text-gray-900">{user.user_email}</td>
                    <td className="py-2 text-sm font-medium text-gray-900">{user.analysis_count}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    );
  };

  const renderUsers = () => {
    if (usersLoading) {
      return (
        <div className="flex items-center justify-center py-12">
          <LoadingSpinner />
        </div>
      );
    }

    return (
      <div className="chart-container">
        <div className="flex items-center justify-between mb-6">
          <h3 className="text-lg font-semibold text-gray-900">User Management</h3>
          <button
            onClick={fetchUsers}
            className="flex items-center px-4 py-2 text-sm bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
          >
            <RefreshCw className="w-4 h-4 mr-2" />
            Refresh
          </button>
        </div>
        
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead>
              <tr className="border-b border-gray-200">
                <th className="text-left py-3 text-sm font-medium text-gray-600">Email</th>
                <th className="text-left py-3 text-sm font-medium text-gray-600">Full Name</th>
                <th className="text-left py-3 text-sm font-medium text-gray-600">Analyses</th>
                <th className="text-left py-3 text-sm font-medium text-gray-600">Joined</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100">
              {users.map((user, idx) => (
                <tr key={idx} className="hover:bg-gray-50">
                  <td className="py-3 text-sm text-gray-900">{user.email}</td>
                  <td className="py-3 text-sm text-gray-900">{user.full_name}</td>
                  <td className="py-3 text-sm font-medium text-blue-600">{user.analysis_count}</td>
                  <td className="py-3 text-sm text-gray-600">
                    {new Date(user.created_at).toLocaleDateString()}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    );
  };

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <LoadingSpinner size="large" />
          <p className="mt-4 text-gray-600">Loading admin dashboard...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white shadow-sm border-b">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center py-4">
            <div className="flex items-center">
              <div className="h-10 w-10 bg-gradient-to-r from-indigo-500 to-cyan-500 rounded-lg flex items-center justify-center">
                <BarChart3 className="h-6 w-6 text-white" />
              </div>
              <div className="ml-3">
                <h1 className="text-xl font-bold gradient-text">JobSasa Admin</h1>
                <p className="text-sm text-gray-500">Analytics & Management</p>
              </div>
            </div>
            
            <div className="flex items-center space-x-4">
              <select
                value={periodDays}
                onChange={(e) => setPeriodDays(Number(e.target_value))}
                className="text-sm border border-gray-300 rounded-lg px-3 py-1"
              >
                <option value={7}>Last 7 days</option>
                <option value={30}>Last 30 days</option>
                <option value={90}>Last 90 days</option>
              </select>
              
              <div className="flex items-center text-sm text-gray-600">
                <Settings className="h-4 w-4 mr-1" />
                Admin: {user.full_name}
              </div>
              
              <button
                onClick={onLogout}
                className="flex items-center text-sm text-gray-600 hover:text-gray-900 transition-colors"
              >
                <LogOut className="h-4 w-4 mr-1" />
                Logout
              </button>
            </div>
          </div>
        </div>
      </header>

      {/* Tab Navigation */}
      <div className="bg-white border-b">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <nav className="tab-nav flex space-x-8">
            <button
              onClick={() => setActiveTab('overview')}
              className={`tab-button ${activeTab === 'overview' ? 'active' : ''}`}
            >
              <Activity className="w-4 h-4 inline mr-2" />
              Overview
            </button>
            <button
              onClick={() => setActiveTab('users')}
              className={`tab-button ${activeTab === 'users' ? 'active' : ''}`}
            >
              <Users className="w-4 h-4 inline mr-2" />
              Users
            </button>
          </nav>
        </div>
      </div>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {activeTab === 'overview' && renderOverview()}
        {activeTab === 'users' && renderUsers()}
      </main>
    </div>
  );
};

export default AdminDashboard;