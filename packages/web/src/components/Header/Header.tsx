import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import './Header.css';

interface HeaderProps {
  currentView: string;
  apiStatus: 'connected' | 'disconnected' | 'checking';
  onSidebarToggle: () => void;
}

const viewTitles: Record<string, string> = {
  dashboard: 'Dashboard',
  tasks: 'Task Management',
  workspaces: 'Workspaces',
  files: 'File Manager',
  search: 'Smart Search',
  'ai-assistant': 'AI Assistant',
  'ai-content': 'AI Content',
  settings: 'Settings',
};

const Header: React.FC<HeaderProps> = ({ 
  currentView, 
  apiStatus, 
  onSidebarToggle 
}) => {
  const navigate = useNavigate();
  const [searchQuery, setSearchQuery] = useState('');
  const getStatusColor = (status: string) => {
    switch (status) {
      case 'connected':
        return 'var(--color-success)';
      case 'disconnected':
        return 'var(--color-danger)';
      case 'checking':
        return 'var(--color-warning)';
      default:
        return 'var(--text-muted)';
    }
  };

  const getStatusText = (status: string) => {
    switch (status) {
      case 'connected':
        return 'Connected';
      case 'disconnected':
        return 'Disconnected';
      case 'checking':
        return 'Connecting...';
      default:
        return 'Unknown';
    }
  };

  const handleSearch = () => {
    if (searchQuery.trim()) {
      // Navigate to search page with query
      navigate(`/search?q=${encodeURIComponent(searchQuery.trim())}`);
    } else {
      // Navigate to search page without query
      navigate('/search');
    }
  };

  const handleSearchKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter') {
      handleSearch();
    }
  };

  const handleNotifications = () => {
    alert('Notifications feature coming soon!\nYou will receive alerts for:\n• Task deadlines\n• System updates\n• Collaboration requests');
  };

  const handleQuickActions = () => {
    const action = window.confirm('Quick Actions:\n\nOK = Create new task\nCancel = Open AI Assistant');
    if (action) {
      navigate('/tasks');
    } else {
      navigate('/ai-assistant');
    }
  };

  const handleHelp = () => {
    const helpText = `OrdnungsHub Help:

🏠 Dashboard - Overview and quick actions
📋 Tasks - AI-powered task management
🗂️ Workspaces - File organization
📁 Files - File management
🔍 Search - Smart search across all data
🤖 AI Assistant - AI-powered analysis
⚙️ Settings - System configuration

Tips:
• Use AI workspace suggestions when creating tasks
• Analyze task complexity before starting
• Use dependencies to order your work
• Let AI organize your files automatically`;
    alert(helpText);
  };

  return (
    <header className="header">
      <div className="header-left">
        <button 
          className="mobile-sidebar-toggle"
          onClick={onSidebarToggle}
          title="Toggle sidebar"
        >
          ☰
        </button>
        <h1 className="header-title">
          {viewTitles[currentView] || 'OrdnungsHub'}
        </h1>
      </div>

      <div className="header-center">
        <div className="search-container">
          <input
            type="text"
            className="search-input"
            placeholder="Search everything..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            onKeyDown={handleSearchKeyDown}
          />
          <button 
            className="search-button" 
            title="Search"
            onClick={handleSearch}
          >
            🔍
          </button>
        </div>
      </div>

      <div className="header-right">
        <div className="header-status">
          <div 
            className="status-indicator"
            style={{ backgroundColor: getStatusColor(apiStatus) }}
            title={`Backend status: ${getStatusText(apiStatus)}`}
          ></div>
          <span className="status-text">{getStatusText(apiStatus)}</span>
        </div>

        <div className="header-actions">
          <button className="header-action-btn" title="Notifications" onClick={handleNotifications}>
            🔔
          </button>
          <button className="header-action-btn" title="Quick Actions" onClick={handleQuickActions}>
            ⚡
          </button>
          <button className="header-action-btn" title="Help" onClick={handleHelp}>
            ❓
          </button>
        </div>
      </div>
    </header>
  );
};

export default Header;