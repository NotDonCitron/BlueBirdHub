/**
 * Analytics Dashboard Main - Master component that integrates all analytics features
 */

import React, { useState, useEffect } from 'react';
import AnalyticsDashboard from './AnalyticsDashboard';
import TimeTrackingDashboard from './TimeTrackingDashboard';
import KPIDashboard from './KPIDashboard';
import ReportGenerator from './ReportGenerator';
import './AnalyticsDashboardMain.css';

interface User {
  id: number;
  name: string;
  email: string;
}

interface DashboardSettings {
  defaultView: string;
  autoRefresh: boolean;
  refreshInterval: number;
  notifications: boolean;
  theme: 'light' | 'dark';
}

const AnalyticsDashboardMain: React.FC = () => {
  const [currentUser] = useState<User>({ id: 1, name: 'John Doe', email: 'john@example.com' }); // Mock user
  const [activeTab, setActiveTab] = useState<'overview' | 'time-tracking' | 'kpis' | 'reports' | 'settings'>('overview');
  const [settings, setSettings] = useState<DashboardSettings>({
    defaultView: 'overview',
    autoRefresh: true,
    refreshInterval: 30,
    notifications: true,
    theme: 'light'
  });
  const [isFullscreen, setIsFullscreen] = useState(false);
  const [showSettings, setShowSettings] = useState(false);

  // Auto-refresh functionality
  useEffect(() => {
    let interval: NodeJS.Timeout | null = null;
    
    if (settings.autoRefresh) {
      interval = setInterval(() => {
        // Trigger refresh of current view
        refreshCurrentView();
      }, settings.refreshInterval * 1000);
    }
    
    return () => {
      if (interval) clearInterval(interval);
    };
  }, [settings.autoRefresh, settings.refreshInterval]);

  // Keyboard shortcuts
  useEffect(() => {
    const handleKeyPress = (event: KeyboardEvent) => {
      if (event.ctrlKey || event.metaKey) {
        switch (event.key) {
          case '1':
            event.preventDefault();
            setActiveTab('overview');
            break;
          case '2':
            event.preventDefault();
            setActiveTab('time-tracking');
            break;
          case '3':
            event.preventDefault();
            setActiveTab('kpis');
            break;
          case '4':
            event.preventDefault();
            setActiveTab('reports');
            break;
          case 'f':
            event.preventDefault();
            toggleFullscreen();
            break;
          case 'r':
            event.preventDefault();
            refreshCurrentView();
            break;
        }
      }
    };

    window.addEventListener('keydown', handleKeyPress);
    return () => window.removeEventListener('keydown', handleKeyPress);
  }, []);

  const refreshCurrentView = () => {
    // This would trigger a refresh of the current active component
    console.log(`Refreshing ${activeTab} view`);
    // Dispatch custom event that components can listen to
    window.dispatchEvent(new CustomEvent('analytics-refresh'));
  };

  const toggleFullscreen = () => {
    if (!document.fullscreenElement) {
      document.documentElement.requestFullscreen();
      setIsFullscreen(true);
    } else {
      document.exitFullscreen();
      setIsFullscreen(false);
    }
  };

  const exportCurrentView = () => {
    console.log(`Exporting ${activeTab} view`);
    // This would trigger export functionality in the current view
    window.dispatchEvent(new CustomEvent('analytics-export', { detail: { view: activeTab } }));
  };

  const renderCurrentView = () => {
    switch (activeTab) {
      case 'overview':
        return <AnalyticsDashboard />;
      case 'time-tracking':
        return <TimeTrackingDashboard userId={currentUser.id} />;
      case 'kpis':
        return <KPIDashboard userId={currentUser.id} />;
      case 'reports':
        return <ReportGenerator userId={currentUser.id} />;
      case 'settings':
        return <SettingsPanel settings={settings} onSettingsChange={setSettings} />;
      default:
        return <AnalyticsDashboard />;
    }
  };

  return (
    <div className={`analytics-dashboard-main ${isFullscreen ? 'fullscreen' : ''} ${settings.theme}`}>
      {/* Header */}
      <header className="dashboard-main-header">
        <div className="header-left">
          <h1>Analytics Dashboard</h1>
          <div className="user-info">
            <span className="welcome-text">Welcome back, {currentUser.name}</span>
            <div className="last-activity">
              Last activity: {new Date().toLocaleTimeString()}
            </div>
          </div>
        </div>
        
        <div className="header-right">
          <div className="quick-actions">
            <button 
              onClick={refreshCurrentView} 
              className="action-btn refresh-btn"
              title="Refresh (Ctrl+R)"
            >
              🔄
            </button>
            
            <button 
              onClick={exportCurrentView} 
              className="action-btn export-btn"
              title="Export Current View"
            >
              📊
            </button>
            
            <button 
              onClick={toggleFullscreen} 
              className="action-btn fullscreen-btn"
              title="Toggle Fullscreen (Ctrl+F)"
            >
              {isFullscreen ? '🗗' : '🗖'}
            </button>
            
            <button 
              onClick={() => setShowSettings(!showSettings)} 
              className="action-btn settings-btn"
              title="Settings"
            >
              ⚙️
            </button>
          </div>

          {settings.autoRefresh && (
            <div className="auto-refresh-indicator">
              <div className="refresh-pulse"></div>
              <span>Auto-refresh: {settings.refreshInterval}s</span>
            </div>
          )}
        </div>
      </header>

      {/* Navigation */}
      <nav className="dashboard-nav">
        <div className="nav-tabs">
          <button
            className={`nav-tab ${activeTab === 'overview' ? 'active' : ''}`}
            onClick={() => setActiveTab('overview')}
            title="Overview Dashboard (Ctrl+1)"
          >
            <span className="tab-icon">📊</span>
            <span className="tab-label">Overview</span>
          </button>
          
          <button
            className={`nav-tab ${activeTab === 'time-tracking' ? 'active' : ''}`}
            onClick={() => setActiveTab('time-tracking')}
            title="Time Tracking (Ctrl+2)"
          >
            <span className="tab-icon">⏱️</span>
            <span className="tab-label">Time Tracking</span>
          </button>
          
          <button
            className={`nav-tab ${activeTab === 'kpis' ? 'active' : ''}`}
            onClick={() => setActiveTab('kpis')}
            title="KPIs & Goals (Ctrl+3)"
          >
            <span className="tab-icon">🎯</span>
            <span className="tab-label">KPIs & Goals</span>
          </button>
          
          <button
            className={`nav-tab ${activeTab === 'reports' ? 'active' : ''}`}
            onClick={() => setActiveTab('reports')}
            title="Report Generator (Ctrl+4)"
          >
            <span className="tab-icon">📋</span>
            <span className="tab-label">Reports</span>
          </button>
        </div>

        <div className="nav-indicators">
          {settings.notifications && (
            <div className="notification-indicator">
              <span className="notification-dot"></span>
              <span>3 new insights</span>
            </div>
          )}
        </div>
      </nav>

      {/* Settings Panel */}
      {showSettings && (
        <div className="settings-overlay" onClick={() => setShowSettings(false)}>
          <div className="settings-panel" onClick={(e) => e.stopPropagation()}>
            <div className="settings-header">
              <h3>Dashboard Settings</h3>
              <button 
                onClick={() => setShowSettings(false)}
                className="close-settings"
              >
                ×
              </button>
            </div>
            <SettingsPanel 
              settings={settings} 
              onSettingsChange={setSettings}
              onClose={() => setShowSettings(false)}
            />
          </div>
        </div>
      )}

      {/* Main Content */}
      <main className="dashboard-main-content">
        <div className="content-wrapper">
          {renderCurrentView()}
        </div>
      </main>

      {/* Keyboard Shortcuts Help */}
      <div className="keyboard-shortcuts">
        <div className="shortcuts-trigger" title="Keyboard Shortcuts">
          ⌨️
        </div>
        <div className="shortcuts-tooltip">
          <div className="shortcut-item">
            <kbd>Ctrl</kbd> + <kbd>1-4</kbd> - Switch tabs
          </div>
          <div className="shortcut-item">
            <kbd>Ctrl</kbd> + <kbd>R</kbd> - Refresh
          </div>
          <div className="shortcut-item">
            <kbd>Ctrl</kbd> + <kbd>F</kbd> - Fullscreen
          </div>
        </div>
      </div>
    </div>
  );
};

// Settings Panel Component
const SettingsPanel: React.FC<{
  settings: DashboardSettings;
  onSettingsChange: (settings: DashboardSettings) => void;
  onClose?: () => void;
}> = ({ settings, onSettingsChange, onClose }) => {
  const handleSettingChange = (key: keyof DashboardSettings, value: any) => {
    onSettingsChange({
      ...settings,
      [key]: value
    });
  };

  return (
    <div className="settings-content">
      <div className="settings-section">
        <h4>General</h4>
        
        <div className="setting-item">
          <label>Default View</label>
          <select
            value={settings.defaultView}
            onChange={(e) => handleSettingChange('defaultView', e.target.value)}
          >
            <option value="overview">Overview</option>
            <option value="time-tracking">Time Tracking</option>
            <option value="kpis">KPIs & Goals</option>
            <option value="reports">Reports</option>
          </select>
        </div>

        <div className="setting-item">
          <label>Theme</label>
          <select
            value={settings.theme}
            onChange={(e) => handleSettingChange('theme', e.target.value as 'light' | 'dark')}
          >
            <option value="light">Light</option>
            <option value="dark">Dark</option>
          </select>
        </div>
      </div>

      <div className="settings-section">
        <h4>Auto-Refresh</h4>
        
        <div className="setting-item">
          <label className="checkbox-label">
            <input
              type="checkbox"
              checked={settings.autoRefresh}
              onChange={(e) => handleSettingChange('autoRefresh', e.target.checked)}
            />
            Enable auto-refresh
          </label>
        </div>

        {settings.autoRefresh && (
          <div className="setting-item">
            <label>Refresh Interval (seconds)</label>
            <input
              type="number"
              min="10"
              max="300"
              value={settings.refreshInterval}
              onChange={(e) => handleSettingChange('refreshInterval', parseInt(e.target.value))}
            />
          </div>
        )}
      </div>

      <div className="settings-section">
        <h4>Notifications</h4>
        
        <div className="setting-item">
          <label className="checkbox-label">
            <input
              type="checkbox"
              checked={settings.notifications}
              onChange={(e) => handleSettingChange('notifications', e.target.checked)}
            />
            Enable notifications for insights and alerts
          </label>
        </div>
      </div>

      <div className="settings-section">
        <h4>Data & Privacy</h4>
        
        <div className="setting-item">
          <button className="secondary-btn">Export All Data</button>
        </div>
        
        <div className="setting-item">
          <button className="secondary-btn">Clear Cache</button>
        </div>
        
        <div className="setting-item">
          <button className="danger-btn">Reset Dashboard</button>
        </div>
      </div>

      {onClose && (
        <div className="settings-footer">
          <button onClick={onClose} className="primary-btn">
            Done
          </button>
        </div>
      )}
    </div>
  );
};

export default AnalyticsDashboardMain;