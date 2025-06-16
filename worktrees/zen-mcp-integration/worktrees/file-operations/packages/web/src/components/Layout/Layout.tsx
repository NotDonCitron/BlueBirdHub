import React, { useState } from 'react';
import { Routes, Route, useNavigate, useLocation } from 'react-router-dom';
import Sidebar from '../Sidebar/Sidebar';
import Header from '../Header/Header';
import Dashboard from '../Dashboard/Dashboard';
import AIAssistant from '../AIAssistant/AIAssistant';
import AIContentAssignment from '../AIContentAssignment/AIContentAssignment';
import WorkspaceManager from '../WorkspaceManager/WorkspaceManager';
import TaskManager from '../TaskManager/TaskManager';
import FileManager from '../FileManager/FileManager';
import SmartSearch from '../SmartSearch/SmartSearch';
import AutomationCenter from '../AutomationCenter/AutomationCenter';
import Settings from '../Settings/Settings';
import { useApi } from '../../contexts/ApiContext';
import './Layout.css';

const Layout: React.FC = () => {
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);
  const { apiStatus } = useApi();
  const navigate = useNavigate();
  const location = useLocation();

  const currentView = location.pathname.slice(1) || 'dashboard';

  const handleSidebarToggle = () => {
    setSidebarCollapsed(!sidebarCollapsed);
  };

  const handleViewChange = (view: string) => {
    navigate(`/${view}`);
  };

  return (
    <div className={`layout ${sidebarCollapsed ? 'sidebar-collapsed' : ''}`}>
      <Sidebar 
        collapsed={sidebarCollapsed}
        currentView={currentView}
        onViewChange={handleViewChange}
        onToggle={handleSidebarToggle}
      />
      
      <div className="layout-main">
        <Header 
          currentView={currentView}
          apiStatus={apiStatus}
          onSidebarToggle={handleSidebarToggle}
        />
        
        <main className="layout-content">
          <Routes>
            <Route path="/" element={<Dashboard />} />
            <Route path="/dashboard" element={<Dashboard />} />
            <Route path="/tasks" element={<TaskManager />} />
            <Route path="/workspaces" element={<WorkspaceManager />} />
            <Route path="/files" element={<FileManager />} />
            <Route path="/search" element={<SmartSearch />} />
            <Route path="/automation" element={<AutomationCenter />} />
            <Route path="/ai-assistant" element={<AIAssistant />} />
            <Route path="/ai-content" element={<AIContentAssignment />} />
            <Route path="/settings" element={<Settings />} />
          </Routes>
        </main>
      </div>
      
      {apiStatus === 'disconnected' && (
        <div className="api-status-overlay">
          <div className="api-status-message">
            <h3>Connection Lost</h3>
            <p>Unable to connect to the OrdnungsHub backend. Please check if the server is running.</p>
            <button 
              className="btn btn-primary"
              onClick={() => window.location.reload()}
            >
              Retry Connection
            </button>
          </div>
        </div>
      )}
    </div>
  );
};

export default Layout;