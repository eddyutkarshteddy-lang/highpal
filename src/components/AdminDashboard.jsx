/**
 * Admin Dashboard
 * Main admin panel interface with tabs for different functions
 */

import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import ContentUpload from './ContentUpload';
import ContentManagement from './ContentManagement';
import StatisticsDashboard from './StatisticsDashboard';
import './AdminDashboard.css';

const AdminDashboard = () => {
  const [activeTab, setActiveTab] = useState('upload');
  const { currentUser, logout } = useAuth();
  const navigate = useNavigate();

  const handleLogout = async () => {
    const result = await logout();
    if (result.success) {
      navigate('/admin/login');
    }
  };

  const tabs = [
    { id: 'upload', label: '📤 Upload Content', icon: '📤' },
    { id: 'manage', label: '📚 Manage Content', icon: '📚' },
    { id: 'stats', label: '📊 Statistics', icon: '📊' }
  ];

  return (
    <div className="admin-dashboard">
      {/* Header */}
      <header className="admin-header">
        <div className="header-left">
          <h1>🎓 HighPal Admin Panel</h1>
          <p className="subtitle">Educational Content Management System</p>
        </div>
        <div className="header-right">
          <div className="user-info">
            <span className="user-email">{currentUser?.email}</span>
            <span className="user-badge">Admin</span>
          </div>
          <button className="logout-btn" onClick={handleLogout}>
            🚪 Logout
          </button>
        </div>
      </header>

      {/* Navigation Tabs */}
      <nav className="admin-nav">
        {tabs.map(tab => (
          <button
            key={tab.id}
            className={`tab-btn ${activeTab === tab.id ? 'active' : ''}`}
            onClick={() => setActiveTab(tab.id)}
          >
            <span className="tab-icon">{tab.icon}</span>
            <span className="tab-label">{tab.label}</span>
          </button>
        ))}
      </nav>

      {/* Main Content Area */}
      <main className="admin-content">
        {activeTab === 'upload' && <ContentUpload />}
        {activeTab === 'manage' && <ContentManagement />}
        {activeTab === 'stats' && <StatisticsDashboard />}
      </main>

      {/* Footer */}
      <footer className="admin-footer">
        <p>© 2025 HighPal - Admin Panel v5.1.0 with Vector Embeddings</p>
        <div className="footer-links">
          <a href="/" target="_blank" rel="noopener noreferrer">Student Portal</a>
          <span>•</span>
          <a href="/admin/docs" onClick={(e) => { e.preventDefault(); alert('Documentation coming soon!'); }}>Documentation</a>
          <span>•</span>
          <a href="/admin/support" onClick={(e) => { e.preventDefault(); alert('Support: admin@highpal.com'); }}>Support</a>
        </div>
      </footer>
    </div>
  );
};

export default AdminDashboard;
