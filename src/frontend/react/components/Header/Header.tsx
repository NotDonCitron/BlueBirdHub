import React, { useState, useEffect, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../../contexts/AuthContext';
import { useSearch } from '../../hooks/useSearch';
import SearchResults from '../SearchBar/SearchResults';
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
  const { user, logout } = useAuth();
  const { setQuery, results, isLoading } = useSearch();
  const [localQuery, setLocalQuery] = useState('');
  const [isSearchFocused, setIsSearchFocused] = useState(false);
  const searchContainerRef = useRef<HTMLDivElement>(null);
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
    if (localQuery.trim()) {
      // Navigate to search page with query
      navigate(`/search?q=${encodeURIComponent(localQuery.trim())}`);
    } else {
      // Navigate to search page without query
      navigate('/search');
    }
  };

  const handleSearchKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter') {
      // Potentially navigate to a full search page
    }
  };

  useEffect(() => {
    const handler = setTimeout(() => {
      setQuery(localQuery);
    }, 300); // 300ms debounce delay

    return () => {
      clearTimeout(handler);
    };
  }, [localQuery, setQuery]);

  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (searchContainerRef.current && !searchContainerRef.current.contains(event.target as Node)) {
        setIsSearchFocused(false);
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
    };
  }, []);

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
        <div className="search-container" ref={searchContainerRef}>
          <input
            type="text"
            className="search-input"
            placeholder="Search everything..."
            value={localQuery}
            onChange={(e) => setLocalQuery(e.target.value)}
            onFocus={() => setIsSearchFocused(true)}
            onKeyDown={handleSearchKeyDown}
          />
           {isSearchFocused && <SearchResults results={results} isLoading={isLoading} onClose={() => setIsSearchFocused(false)} />}
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
          <button className="header-action-btn" title="Notifications">
            🔔
          </button>
          <button className="header-action-btn" title="Quick Actions">
            ⚡
          </button>
          <button className="header-action-btn" title="Help">
            ❓
          </button>
          {user && (
            <>
              <span className="user-info">👤 {user.username}</span>
              <button 
                className="btn btn-danger logout-btn-prominent" 
                title="Logout"
                onClick={logout}
                style={{
                  backgroundColor: '#dc3545',
                  color: 'white',
                  border: 'none',
                  padding: '8px 16px',
                  borderRadius: '4px',
                  marginLeft: '10px',
                  fontWeight: 'bold',
                  cursor: 'pointer'
                }}
              >
                🚪 Logout
              </button>
            </>
          )}
        </div>
      </div>
    </header>
  );
};

export default Header;