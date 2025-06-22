import React, { useState, useEffect, useRef } from 'react';
import { useAuth, AuthProvider } from './contexts/AuthContext';
import Login from './components/Login/Login';
import TaskManager from './components/TaskManager/TaskManager';

// Simple Error Handling System
interface ErrorInfo {
  id: string;
  message: string;
  type: 'error' | 'warning' | 'info';
  timestamp: string;
  details?: string;
}

// Error Toast Component
const ErrorToast: React.FC<{ error: ErrorInfo; onDismiss: (id: string) => void }> = ({ error, onDismiss }) => {
  const bgColor = {
    error: '#fef2f2',
    warning: '#fffbeb', 
    info: '#eff6ff'
  }[error.type];
  
  const borderColor = {
    error: '#f87171',
    warning: '#fbbf24',
    info: '#60a5fa'
  }[error.type];

  const textColor = {
    error: '#dc2626',
    warning: '#d97706',
    info: '#2563eb'
  }[error.type];

  const icon = {
    error: '❌',
    warning: '⚠️',
    info: 'ℹ️'
  }[error.type];

  return (
    <div style={{
      position: 'fixed',
      top: '20px',
      right: '20px',
      background: bgColor,
      border: `2px solid ${borderColor}`,
      borderRadius: '8px',
      padding: '12px 16px',
      maxWidth: '400px',
      zIndex: 1000,
      boxShadow: '0 4px 12px rgba(0,0,0,0.15)'
    }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
        <div style={{ flex: 1 }}>
          <div style={{ display: 'flex', alignItems: 'center', marginBottom: '4px' }}>
            <span style={{ marginRight: '8px' }}>{icon}</span>
            <strong style={{ color: textColor, fontSize: '14px' }}>{error.message}</strong>
          </div>
          {error.details && (
            <p style={{ margin: 0, fontSize: '12px', color: '#6b7280' }}>{error.details}</p>
          )}
          <p style={{ margin: '4px 0 0 0', fontSize: '10px', color: '#9ca3af' }}>
            {new Date(error.timestamp).toLocaleTimeString()}
          </p>
        </div>
        <button
          onClick={() => onDismiss(error.id)}
          style={{
            background: 'none',
            border: 'none',
            cursor: 'pointer',
            padding: '2px',
            color: textColor,
            marginLeft: '8px'
          }}
        >
          ✕
        </button>
      </div>
    </div>
  );
};

// Error Context Hook
const useErrorHandler = () => {
  const [errors, setErrors] = useState<ErrorInfo[]>([]);

  const addError = (message: string, type: 'error' | 'warning' | 'info' = 'error', details?: string) => {
    const error: ErrorInfo = {
      id: `${Date.now()}-${Math.random()}`, // Use a more unique ID
      message,
      type,
      timestamp: new Date().toISOString(),
      details
    };
    
    console.log(`🚨 ${type.toUpperCase()}: ${message}`, details || '');
    
    setErrors(prev => [...prev, error]);
    
    // Auto-dismiss after 5 seconds
    setTimeout(() => {
      dismissError(error.id);
    }, 5000);
  };

  const dismissError = (id: string) => {
    setErrors(prev => prev.filter(error => error.id !== id));
  };

  const clearAllErrors = () => {
    setErrors([]);
  };

  return {
    errors,
    addError,
    dismissError,
    clearAllErrors
  };
};

// Search Component
interface SearchResult {
  type: 'task' | 'workspace';
  id: string;
  title: string;
  description?: string;
  color?: string;
  status?: string;
  priority?: string;
}

const SearchComponent: React.FC<{ 
  onResultClick: (result: SearchResult) => void;
  errorHandler: ReturnType<typeof useErrorHandler>;
}> = ({ onResultClick, errorHandler }) => {
  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState<SearchResult[]>([]);
  const [isSearching, setIsSearching] = useState(false);
  const [showResults, setShowResults] = useState(false);

  const performSearch = async (query: string) => {
    if (!query.trim()) {
      setSearchResults([]);
      setShowResults(false);
      return;
    }

    setIsSearching(true);
    try {
      // Search both tasks and workspaces in parallel
      const [tasksResponse, workspacesResponse] = await Promise.all([
        fetch('http://localhost:8000/tasks/taskmaster/all'),
        fetch('http://localhost:8000/workspaces')
      ]);

      if (!tasksResponse.ok || !workspacesResponse.ok) {
        throw new Error('Search failed');
      }

      const [tasksData, workspacesData] = await Promise.all([
        tasksResponse.json(),
        workspacesResponse.json()
      ]);

      const results: SearchResult[] = [];

      // Search tasks
      const tasks = tasksData.tasks || [];
      tasks.forEach((task: any) => {
        if (task.title.toLowerCase().includes(query.toLowerCase()) ||
            task.description?.toLowerCase().includes(query.toLowerCase())) {
          results.push({
            type: 'task',
            id: task.id,
            title: task.title,
            description: task.description,
            status: task.status,
            priority: task.priority
          });
        }
      });

      // Search workspaces
      workspacesData.forEach((workspace: any) => {
        if (workspace.name.toLowerCase().includes(query.toLowerCase()) ||
            workspace.description?.toLowerCase().includes(query.toLowerCase())) {
          results.push({
            type: 'workspace',
            id: workspace.id.toString(),
            title: workspace.name,
            description: workspace.description,
            color: workspace.color
          });
        }
      });

      setSearchResults(results);
      setShowResults(true);
    } catch (error) {
      errorHandler.addError('Search failed', 'error', 'Could not perform search');
    } finally {
      setIsSearching(false);
    }
  };

  // Debounced search
  useEffect(() => {
    const timeoutId = setTimeout(() => {
      performSearch(searchQuery);
    }, 300);

    return () => clearTimeout(timeoutId);
  }, [searchQuery]);

  const handleResultClick = (result: SearchResult) => {
    setShowResults(false);
    setSearchQuery('');
    onResultClick(result);
  };

  return (
    <div style={{ position: 'relative' }}>
      <div style={{ position: 'relative' }}>
        <input
          type="text"
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          placeholder="🔍 Search tasks & workspaces..."
          style={{
            padding: '8px 40px 8px 12px',
            border: '1px solid #d1d5db',
            borderRadius: '20px',
            fontSize: '14px',
            width: '250px',
            outline: 'none',
            transition: 'all 0.2s'
          }}
          onFocus={() => searchQuery && setShowResults(true)}
          onBlur={() => setTimeout(() => setShowResults(false), 200)}
        />
        {isSearching && (
          <div style={{
            position: 'absolute',
            right: '12px',
            top: '50%',
            transform: 'translateY(-50%)',
            width: '16px',
            height: '16px',
            border: '2px solid #f3f4f6',
            borderTop: '2px solid #3b82f6',
            borderRadius: '50%',
            animation: 'spin 1s linear infinite'
          }} />
        )}
      </div>

      {showResults && searchResults.length > 0 && (
        <div style={{
          position: 'absolute',
          top: '100%',
          left: 0,
          right: 0,
          background: 'white',
          border: '1px solid #d1d5db',
          borderRadius: '8px',
          boxShadow: '0 4px 12px rgba(0,0,0,0.1)',
          zIndex: 1000,
          maxHeight: '300px',
          overflowY: 'auto'
        }}>
          <div style={{ padding: '8px 0' }}>
            {searchResults.map((result, index) => (
              <div
                key={`${result.type}-${result.id}`}
                style={{
                  padding: '8px 12px',
                  cursor: 'pointer',
                  borderBottom: index < searchResults.length - 1 ? '1px solid #f3f4f6' : 'none',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '8px',
                  transition: 'background-color 0.1s'
                }}
                onMouseEnter={(e) => e.currentTarget.style.backgroundColor = '#f9fafb'}
                onMouseLeave={(e) => e.currentTarget.style.backgroundColor = 'white'}
                onClick={() => handleResultClick(result)}
              >
                <span style={{ fontSize: '16px' }}>
                  {result.type === 'task' ? '✅' : '📁'}
                </span>
                <div style={{ flex: 1 }}>
                  <div style={{ fontSize: '14px', fontWeight: 'bold', color: '#374151' }}>
                    {result.title}
                  </div>
                  {result.description && (
                    <div style={{ fontSize: '12px', color: '#6b7280' }}>
                      {result.description.substring(0, 50)}...
                    </div>
                  )}
                  <div style={{ fontSize: '10px', color: '#9ca3af', marginTop: '2px' }}>
                    {result.type === 'task' ? (
                      `${result.status} • ${result.priority} priority`
                    ) : (
                      'Workspace'
                    )}
                  </div>
                </div>
                {result.type === 'workspace' && result.color && (
                  <div style={{
                    width: '12px',
                    height: '12px',
                    backgroundColor: result.color,
                    borderRadius: '2px'
                  }} />
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      {showResults && searchResults.length === 0 && searchQuery.trim() && !isSearching && (
        <div style={{
          position: 'absolute',
          top: '100%',
          left: 0,
          right: 0,
          background: 'white',
          border: '1px solid #d1d5db',
          borderRadius: '8px',
          boxShadow: '0 4px 12px rgba(0,0,0,0.1)',
          zIndex: 1000,
          padding: '16px',
          textAlign: 'center',
          color: '#6b7280',
          fontSize: '14px'
        }}>
          No results found for "{searchQuery}"
        </div>
      )}
    </div>
  );
};

// Simple navigation component
const Navigation: React.FC<{ 
  currentView: string; 
  onViewChange: (view: string) => void;
  onSearchResult: (result: SearchResult) => void;
  errorHandler: ReturnType<typeof useErrorHandler>;
  onLogout: () => void;
}> = ({ currentView, onViewChange, onSearchResult, errorHandler, onLogout }) => {
  const navStyle = {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    gap: '10px',
    marginBottom: '20px',
    borderBottom: '2px solid #e5e7eb',
    paddingBottom: '10px'
  };

  const buttonStyle = (isActive: boolean) => ({
    padding: '8px 16px',
    border: 'none',
    borderRadius: '6px',
    cursor: 'pointer',
    background: isActive ? '#3b82f6' : '#f3f4f6',
    color: isActive ? 'white' : '#374151',
    fontWeight: isActive ? 'bold' : 'normal'
  });

  return (
    <nav style={navStyle}>
      <div style={{ display: 'flex', gap: '10px' }}>
        <button 
          style={buttonStyle(currentView === 'dashboard')}
          onClick={() => onViewChange('dashboard')}
        >
          📊 Dashboard
        </button>
        <button 
          style={buttonStyle(currentView === 'workspaces')}
          onClick={() => onViewChange('workspaces')}
        >
          📁 Workspaces
        </button>
        <button 
          style={buttonStyle(currentView === 'tasks')}
          onClick={() => onViewChange('tasks')}
        >
          ✅ Tasks
        </button>
        <button 
          style={buttonStyle(currentView === 'test')}
          onClick={() => onViewChange('test')}
        >
          🔧 API Test
        </button>
        <button 
          style={buttonStyle(currentView === 'errors')}
          onClick={() => onViewChange('errors')}
        >
          🚨 Error Log
        </button>
        <button 
          style={{
            ...buttonStyle(false),
            backgroundColor: '#dc3545',
            color: 'white',
            border: 'none',
            fontWeight: 'bold'
          }}
          onClick={onLogout}
        >
          🚪 Logout
        </button>
      </div>
      
      <SearchComponent 
        onResultClick={onSearchResult}
        errorHandler={errorHandler}
      />
    </nav>
  );
};

// Dashboard view
const Dashboard: React.FC<{ errorHandler: ReturnType<typeof useErrorHandler> }> = ({ errorHandler }) => {
  const [backendStatus, setBackendStatus] = useState<string>('checking...');

  useEffect(() => {
    checkBackendHealth();
  }, []);

  const checkBackendHealth = async () => {
    try {
      const response = await fetch('http://localhost:8000/health');
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }
      const data = await response.json();
      setBackendStatus(`✅ ${data.status} - ${data.backend}`);
      errorHandler.addError('Backend connection successful!', 'info', 'Health check passed');
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Unknown error';
      setBackendStatus('❌ Backend not responding');
      errorHandler.addError('Backend Connection Failed', 'error', errorMessage);
    }
  };

  return (
    <div>
      <h2>📊 Dashboard</h2>
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '15px' }}>
        <div style={{ background: '#f0f9ff', padding: '15px', borderRadius: '8px', border: '1px solid #0ea5e9' }}>
          <h3 style={{ margin: '0 0 10px 0', color: '#0369a1' }}>Backend Status</h3>
          <p style={{ margin: 0, fontSize: '14px' }}>{backendStatus}</p>
        </div>
        <div style={{ background: '#f0fdf4', padding: '15px', borderRadius: '8px', border: '1px solid #22c55e' }}>
          <h3 style={{ margin: '0 0 10px 0', color: '#166534' }}>Frontend Status</h3>
          <p style={{ margin: 0, fontSize: '14px' }}>✅ React app running</p>
        </div>
        <div style={{ background: '#fefce8', padding: '15px', borderRadius: '8px', border: '1px solid #eab308' }}>
          <h3 style={{ margin: '0 0 10px 0', color: '#a16207' }}>System Status</h3>
          <p style={{ margin: 0, fontSize: '14px' }}>✅ All systems operational</p>
        </div>
      </div>
    </div>
  );
};

// API Test view
const ApiTest: React.FC<{ errorHandler: ReturnType<typeof useErrorHandler> }> = ({ errorHandler }) => {
  const [testResults, setTestResults] = useState<string[]>([]);

  const runTest = async (endpoint: string, name: string) => {
    try {
      errorHandler.addError(`Testing ${name}...`, 'info', `Calling ${endpoint}`);
      const response = await fetch(`http://localhost:8000${endpoint}`);
      
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }
      
      const data = await response.json();
      setTestResults(prev => [...prev, `✅ ${name}: ${JSON.stringify(data).substring(0, 100)}...`]);
      errorHandler.addError(`${name} test successful!`, 'info', 'API endpoint responded correctly');
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Unknown error';
      setTestResults(prev => [...prev, `❌ ${name}: ${errorMessage}`]);
      errorHandler.addError(`${name} test failed`, 'error', errorMessage);
    }
  };

  const clearResults = () => setTestResults([]);

  return (
    <div>
      <h2>🔧 API Test Suite</h2>
      <div style={{ marginBottom: '15px' }}>
        <button onClick={() => runTest('/health', 'Health Check')} style={{ marginRight: '10px', padding: '8px 12px', background: '#10b981', color: 'white', border: 'none', borderRadius: '4px', cursor: 'pointer' }}>
          Test Health
        </button>
        <button onClick={() => runTest('/workspaces', 'Workspaces')} style={{ marginRight: '10px', padding: '8px 12px', background: '#3b82f6', color: 'white', border: 'none', borderRadius: '4px', cursor: 'pointer' }}>
          Test Workspaces
        </button>
        <button onClick={() => runTest('/tasks/taskmaster/all', 'Tasks')} style={{ marginRight: '10px', padding: '8px 12px', background: '#8b5cf6', color: 'white', border: 'none', borderRadius: '4px', cursor: 'pointer' }}>
          Test Tasks
        </button>
        <button onClick={clearResults} style={{ padding: '8px 12px', background: '#ef4444', color: 'white', border: 'none', borderRadius: '4px', cursor: 'pointer' }}>
          Clear Results
        </button>
      </div>
      <div style={{ background: '#f9fafb', padding: '15px', borderRadius: '8px', border: '1px solid #d1d5db', minHeight: '200px' }}>
        <h3>Test Results:</h3>
        {testResults.length === 0 ? (
          <p style={{ color: '#6b7280' }}>Click buttons above to test API endpoints</p>
        ) : (
          <div>
            {testResults.map((result, index) => (
              <div key={index} style={{ marginBottom: '8px', fontSize: '12px', fontFamily: 'monospace' }}>
                {result}
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

// Error Dashboard view
const ErrorDashboard: React.FC<{ errorHandler: ReturnType<typeof useErrorHandler> }> = ({ errorHandler }) => {
  const errorsByType = {
    error: errorHandler.errors.filter(e => e.type === 'error'),
    warning: errorHandler.errors.filter(e => e.type === 'warning'),
    info: errorHandler.errors.filter(e => e.type === 'info')
  };

  const testError = () => {
    errorHandler.addError('Test Error', 'error', 'This is a sample error message for testing');
  };

  const testWarning = () => {
    errorHandler.addError('Test Warning', 'warning', 'This is a sample warning message');
  };

  const testInfo = () => {
    errorHandler.addError('Test Info', 'info', 'This is a sample info message');
  };

  return (
    <div>
      <h2>🚨 Error Dashboard</h2>
      
      <div style={{ marginBottom: '20px' }}>
        <h3>Test Error System:</h3>
        <button onClick={testError} style={{ marginRight: '10px', padding: '8px 12px', background: '#ef4444', color: 'white', border: 'none', borderRadius: '4px', cursor: 'pointer' }}>
          Trigger Error
        </button>
        <button onClick={testWarning} style={{ marginRight: '10px', padding: '8px 12px', background: '#f59e0b', color: 'white', border: 'none', borderRadius: '4px', cursor: 'pointer' }}>
          Trigger Warning
        </button>
        <button onClick={testInfo} style={{ marginRight: '10px', padding: '8px 12px', background: '#3b82f6', color: 'white', border: 'none', borderRadius: '4px', cursor: 'pointer' }}>
          Trigger Info
        </button>
        <button onClick={errorHandler.clearAllErrors} style={{ padding: '8px 12px', background: '#6b7280', color: 'white', border: 'none', borderRadius: '4px', cursor: 'pointer' }}>
          Clear All Errors
        </button>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(250px, 1fr))', gap: '15px', marginBottom: '20px' }}>
        <div style={{ background: '#fef2f2', padding: '15px', borderRadius: '8px', border: '2px solid #f87171' }}>
          <h4 style={{ margin: '0 0 10px 0', color: '#dc2626' }}>❌ Errors ({errorsByType.error.length})</h4>
          <p style={{ margin: 0, fontSize: '12px', color: '#7f1d1d' }}>Critical issues that need attention</p>
        </div>
        <div style={{ background: '#fffbeb', padding: '15px', borderRadius: '8px', border: '2px solid #fbbf24' }}>
          <h4 style={{ margin: '0 0 10px 0', color: '#d97706' }}>⚠️ Warnings ({errorsByType.warning.length})</h4>
          <p style={{ margin: 0, fontSize: '12px', color: '#92400e' }}>Issues that should be reviewed</p>
        </div>
        <div style={{ background: '#eff6ff', padding: '15px', borderRadius: '8px', border: '2px solid #60a5fa' }}>
          <h4 style={{ margin: '0 0 10px 0', color: '#2563eb' }}>ℹ️ Info ({errorsByType.info.length})</h4>
          <p style={{ margin: 0, fontSize: '12px', color: '#1e40af' }}>Informational messages</p>
        </div>
      </div>

      <div style={{ background: '#f9fafb', padding: '15px', borderRadius: '8px', border: '1px solid #d1d5db' }}>
        <h3>Recent Messages:</h3>
        {errorHandler.errors.length === 0 ? (
          <p style={{ color: '#6b7280', fontStyle: 'italic' }}>No messages yet. Try testing the error system above!</p>
        ) : (
          <div style={{ maxHeight: '300px', overflowY: 'auto' }}>
            {[...errorHandler.errors].reverse().map((error) => (
              <div key={error.id} style={{ 
                marginBottom: '10px', 
                padding: '10px', 
                background: 'white', 
                borderRadius: '4px',
                borderLeft: `4px solid ${error.type === 'error' ? '#ef4444' : error.type === 'warning' ? '#f59e0b' : '#3b82f6'}`
              }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                  <div>
                    <strong style={{ fontSize: '14px' }}>{error.message}</strong>
                    {error.details && <p style={{ margin: '4px 0 0 0', fontSize: '12px', color: '#6b7280' }}>{error.details}</p>}
                    <p style={{ margin: '4px 0 0 0', fontSize: '10px', color: '#9ca3af' }}>
                      {new Date(error.timestamp).toLocaleString()}
                    </p>
                  </div>
                  <button
                    onClick={() => errorHandler.dismissError(error.id)}
                    style={{ background: 'none', border: 'none', cursor: 'pointer', color: '#6b7280' }}
                  >
                    ✕
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

// Workspace Management
interface Workspace {
  id: number;
  name: string;
  color: string;
  created_at: string;
  description?: string;
}

const Workspaces: React.FC<{ errorHandler: ReturnType<typeof useErrorHandler> }> = ({ errorHandler }) => {
  const [workspaces, setWorkspaces] = useState<Workspace[]>([]);
  const [tasks, setTasks] = useState<Task[]>([]);
  const [loading, setLoading] = useState(true);
  const [showCreateForm, setShowCreateForm] = useState(false);
  const [editingWorkspace, setEditingWorkspace] = useState<Workspace | null>(null);
  const [selectedWorkspace, setSelectedWorkspace] = useState<Workspace | null>(null);
  const [newWorkspace, setNewWorkspace] = useState({
    name: '',
    color: '#3b82f6',
    description: ''
  });

  useEffect(() => {
    loadWorkspaces();
  }, []);

  const loadWorkspaces = async () => {
    try {
      setLoading(true);
      
      // Load both workspaces and tasks in parallel
      const [workspacesResponse, tasksResponse] = await Promise.all([
        fetch('http://localhost:8000/workspaces'),
        fetch('http://localhost:8000/tasks/taskmaster/all')
      ]);
      
      if (!workspacesResponse.ok || !tasksResponse.ok) {
        throw new Error('Failed to load workspaces or tasks');
      }
      
      const [workspacesData, tasksData] = await Promise.all([
        workspacesResponse.json(),
        tasksResponse.json()
      ]);
      
      setWorkspaces(workspacesData);
      setTasks(tasksData.tasks || []);
      errorHandler.addError('Workspaces and tasks loaded successfully', 'info', `Found ${workspacesData.length} workspaces and ${tasksData.tasks?.length || 0} tasks`);
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Unknown error';
      errorHandler.addError('Failed to load workspaces', 'error', errorMessage);
    } finally {
      setLoading(false);
    }
  };

  const createWorkspace = async () => {
    if (!newWorkspace.name.trim()) {
      errorHandler.addError('Workspace name required', 'warning', 'Please enter a name for the workspace');
      return;
    }

    try {
      const response = await fetch('http://localhost:8000/workspaces', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(newWorkspace),
      });

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }

      const createdWorkspace = await response.json();
      setWorkspaces(prev => [...prev, createdWorkspace]);
      setNewWorkspace({ name: '', color: '#3b82f6', description: '' });
      setShowCreateForm(false);
      errorHandler.addError('Workspace created successfully', 'info', `Created "${createdWorkspace.name}"`);
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Unknown error';
      errorHandler.addError('Failed to create workspace', 'error', errorMessage);
    }
  };

  const deleteWorkspace = async (workspace: Workspace) => {
    if (!confirm(`Are you sure you want to delete "${workspace.name}"?`)) {
      return;
    }

    try {
      const response = await fetch(`http://localhost:8000/workspaces/${workspace.id}`, {
        method: 'DELETE',
      });

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }

      setWorkspaces(prev => prev.filter(w => w.id !== workspace.id));
      errorHandler.addError('Workspace deleted', 'info', `Removed "${workspace.name}"`);
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Unknown error';
      errorHandler.addError('Failed to delete workspace', 'error', errorMessage);
    }
  };

  const updateWorkspace = async () => {
    if (!editingWorkspace) return;

    try {
      const response = await fetch(`http://localhost:8000/workspaces/${editingWorkspace.id}`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          name: editingWorkspace.name,
          color: editingWorkspace.color,
          description: editingWorkspace.description || ''
        }),
      });

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }

      const updatedWorkspace = await response.json();
      setWorkspaces(prev => prev.map(w => w.id === updatedWorkspace.id ? updatedWorkspace : w));
      setEditingWorkspace(null);
      errorHandler.addError('Workspace updated', 'info', `Updated "${updatedWorkspace.name}"`);
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Unknown error';
      errorHandler.addError('Failed to update workspace', 'error', errorMessage);
    }
  };

  const openWorkspace = (workspace: Workspace) => {
    setSelectedWorkspace(workspace);
    errorHandler.addError(`Opened workspace: ${workspace.name}`, 'info', 'Now viewing workspace details');
  };

  const editWorkspace = (workspace: Workspace) => {
    setEditingWorkspace({ ...workspace });
  };

  const getWorkspaceTaskStats = (workspaceId: number) => {
    const workspaceTasks = tasks.filter(task => task.workspace_id === workspaceId);
    const totalTasks = workspaceTasks.length;
    const completedTasks = workspaceTasks.filter(task => task.status === 'done').length;
    const pendingTasks = workspaceTasks.filter(task => task.status === 'pending').length;
    const inProgressTasks = workspaceTasks.filter(task => task.status === 'in-progress').length;
    
    return {
      total: totalTasks,
      completed: completedTasks,
      pending: pendingTasks,
      inProgress: inProgressTasks
    };
  };

  const getStatusColor = (status: 'pending' | 'in-progress' | 'done' | 'blocked') => {
    switch (status) {
      case 'done': return '#10b981';
      case 'in-progress': return '#f59e0b';
      case 'pending': return '#6b7280';
      case 'blocked': return '#ef4444';
      default: return '#6b7280';
    }
  };

  const getPriorityIcon = (priority: 'low' | 'medium' | 'high') => {
    switch (priority) {
      case 'high': return '🔴';
      case 'medium': return '🟡';
      case 'low': return '🟢';
      default: return '⚪';
    }
  };

  const getTagColor = (tag: string) => {
    const colors = {
      'bug': '#ef4444',
      'feature': '#10b981', 
      'enhancement': '#3b82f6',
      'urgent': '#f59e0b',
      'backend': '#8b5cf6',
      'frontend': '#06b6d4',
      'ui': '#ec4899',
      'api': '#84cc16',
      'testing': '#f97316',
      'documentation': '#6b7280'
    };
    return colors[tag as keyof typeof colors] || '#6b7280';
  };

  const colorOptions = [
    '#3b82f6', '#ef4444', '#10b981', '#f59e0b', '#8b5cf6', 
    '#ec4899', '#06b6d4', '#84cc16', '#f97316', '#6366f1'
  ];

  if (loading) {
    return (
      <div>
        <h2>📁 Workspaces</h2>
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
          <div style={{ 
            width: '20px', 
            height: '20px', 
            border: '2px solid #f3f4f6', 
            borderTop: '2px solid #3b82f6', 
            borderRadius: '50%', 
            animation: 'spin 1s linear infinite' 
          }}></div>
          <span>Loading workspaces...</span>
        </div>
      </div>
    );
  }

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px' }}>
        <h2>📁 Workspaces ({workspaces.length})</h2>
        <button
          onClick={() => setShowCreateForm(!showCreateForm)}
          style={{
            padding: '10px 20px',
            background: '#3b82f6',
            color: 'white',
            border: 'none',
            borderRadius: '6px',
            cursor: 'pointer',
            fontWeight: 'bold'
          }}
        >
          {showCreateForm ? '✕ Cancel' : '+ Create Workspace'}
        </button>
      </div>

      {showCreateForm && (
        <div style={{
          background: '#f9fafb',
          border: '2px solid #e5e7eb',
          borderRadius: '8px',
          padding: '20px',
          marginBottom: '20px'
        }}>
          <h3>Create New Workspace</h3>
          <div style={{ display: 'grid', gap: '15px' }}>
            <div>
              <label style={{ display: 'block', marginBottom: '5px', fontWeight: 'bold' }}>
                Workspace Name *
              </label>
              <input
                type="text"
                value={newWorkspace.name}
                onChange={(e) => setNewWorkspace(prev => ({ ...prev, name: e.target.value }))}
                placeholder="Enter workspace name..."
                style={{
                  width: '100%',
                  padding: '8px 12px',
                  border: '1px solid #d1d5db',
                  borderRadius: '4px',
                  fontSize: '14px'
                }}
              />
            </div>
            
            <div>
              <label style={{ display: 'block', marginBottom: '5px', fontWeight: 'bold' }}>
                Color Theme
              </label>
              <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap' }}>
                {colorOptions.map(color => (
                  <button
                    key={color}
                    onClick={() => setNewWorkspace(prev => ({ ...prev, color }))}
                    style={{
                      width: '30px',
                      height: '30px',
                      backgroundColor: color,
                      border: newWorkspace.color === color ? '3px solid #000' : '1px solid #ccc',
                      borderRadius: '4px',
                      cursor: 'pointer'
                    }}
                  />
                ))}
              </div>
            </div>

            <div>
              <label style={{ display: 'block', marginBottom: '5px', fontWeight: 'bold' }}>
                Description (Optional)
              </label>
              <textarea
                value={newWorkspace.description}
                onChange={(e) => setNewWorkspace(prev => ({ ...prev, description: e.target.value }))}
                placeholder="Describe this workspace..."
                rows={3}
                style={{
                  width: '100%',
                  padding: '8px 12px',
                  border: '1px solid #d1d5db',
                  borderRadius: '4px',
                  fontSize: '14px',
                  resize: 'vertical'
                }}
              />
            </div>

            <div style={{ display: 'flex', gap: '10px' }}>
              <button
                onClick={createWorkspace}
                style={{
                  padding: '10px 20px',
                  background: '#10b981',
                  color: 'white',
                  border: 'none',
                  borderRadius: '4px',
                  cursor: 'pointer',
                  fontWeight: 'bold'
                }}
              >
                ✓ Create Workspace
              </button>
              <button
                onClick={() => setShowCreateForm(false)}
                style={{
                  padding: '10px 20px',
                  background: '#6b7280',
                  color: 'white',
                  border: 'none',
                  borderRadius: '4px',
                  cursor: 'pointer'
                }}
              >
                Cancel
              </button>
            </div>
          </div>
        </div>
      )}

      {editingWorkspace && (
        <div style={{
          background: '#fff7ed',
          border: '2px solid #fb923c',
          borderRadius: '8px',
          padding: '20px',
          marginBottom: '20px'
        }}>
          <h3>Edit Workspace: {editingWorkspace.name}</h3>
          <div style={{ display: 'grid', gap: '15px' }}>
            <div>
              <label style={{ display: 'block', marginBottom: '5px', fontWeight: 'bold' }}>
                Workspace Name *
              </label>
              <input
                type="text"
                value={editingWorkspace.name}
                onChange={(e) => setEditingWorkspace(prev => prev ? { ...prev, name: e.target.value } : null)}
                style={{
                  width: '100%',
                  padding: '8px 12px',
                  border: '1px solid #d1d5db',
                  borderRadius: '4px',
                  fontSize: '14px'
                }}
              />
            </div>
            
            <div>
              <label style={{ display: 'block', marginBottom: '5px', fontWeight: 'bold' }}>
                Description
              </label>
              <textarea
                value={editingWorkspace.description || ''}
                onChange={(e) => setEditingWorkspace(prev => prev ? { ...prev, description: e.target.value } : null)}
                placeholder="Describe this workspace..."
                style={{
                  width: '100%',
                  padding: '8px 12px',
                  border: '1px solid #d1d5db',
                  borderRadius: '4px',
                  fontSize: '14px',
                  minHeight: '60px',
                  resize: 'vertical'
                }}
              />
            </div>
            
            <div>
              <label style={{ display: 'block', marginBottom: '5px', fontWeight: 'bold' }}>
                Color Theme
              </label>
              <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap' }}>
                {colorOptions.map(color => (
                  <button
                    key={color}
                    onClick={() => setEditingWorkspace(prev => prev ? { ...prev, color } : null)}
                    style={{
                      width: '30px',
                      height: '30px',
                      backgroundColor: color,
                      border: editingWorkspace.color === color ? '3px solid #000' : '1px solid #ccc',
                      borderRadius: '4px',
                      cursor: 'pointer'
                    }}
                  />
                ))}
              </div>
            </div>
            
            <div style={{ display: 'flex', gap: '10px' }}>
              <button
                onClick={updateWorkspace}
                style={{
                  padding: '10px 20px',
                  background: '#f97316',
                  color: 'white',
                  border: 'none',
                  borderRadius: '4px',
                  cursor: 'pointer',
                  fontWeight: 'bold'
                }}
              >
                ✓ Save Changes
              </button>
              <button
                onClick={() => setEditingWorkspace(null)}
                style={{
                  padding: '10px 20px',
                  background: '#6b7280',
                  color: 'white',
                  border: 'none',
                  borderRadius: '4px',
                  cursor: 'pointer'
                }}
              >
                Cancel
              </button>
            </div>
          </div>
        </div>
      )}

      {selectedWorkspace && (
        <div style={{
          background: '#eff6ff',
          border: '2px solid #3b82f6',
          borderRadius: '8px',
          padding: '20px',
          marginBottom: '20px'
        }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
            <div>
              <h3 style={{ margin: '0 0 10px 0', color: selectedWorkspace.color, fontSize: '20px' }}>
                📂 {selectedWorkspace.name}
              </h3>
              {selectedWorkspace.description && (
                <p style={{ margin: '0 0 10px 0', color: '#6b7280', fontSize: '14px' }}>
                  {selectedWorkspace.description}
                </p>
              )}
              <div style={{ fontSize: '12px', color: '#9ca3af' }}>
                Created: {new Date(selectedWorkspace.created_at).toLocaleDateString()}
              </div>
            </div>
            <button
              onClick={() => setSelectedWorkspace(null)}
              style={{
                background: 'none',
                border: 'none',
                cursor: 'pointer',
                color: '#6b7280',
                fontSize: '16px',
                padding: '2px'
              }}
            >
              ✕
            </button>
          </div>
          
          <div style={{ marginTop: '15px', padding: '15px', background: 'white', borderRadius: '6px' }}>
            <h4 style={{ margin: '0 0 10px 0', color: '#374151' }}>Workspace Statistics</h4>
            {(() => {
              const stats = getWorkspaceTaskStats(selectedWorkspace.id);
              return (
                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(120px, 1fr))', gap: '10px' }}>
                  <div style={{ textAlign: 'center', padding: '10px', background: '#f3f4f6', borderRadius: '4px' }}>
                    <div style={{ fontSize: '18px', fontWeight: 'bold', color: selectedWorkspace.color }}>
                      {stats.total}
                    </div>
                    <div style={{ fontSize: '12px', color: '#6b7280' }}>Total Tasks</div>
                  </div>
                  <div style={{ textAlign: 'center', padding: '10px', background: '#f3f4f6', borderRadius: '4px' }}>
                    <div style={{ fontSize: '18px', fontWeight: 'bold', color: '#10b981' }}>{stats.completed}</div>
                    <div style={{ fontSize: '12px', color: '#6b7280' }}>Completed</div>
                  </div>
                  <div style={{ textAlign: 'center', padding: '10px', background: '#f3f4f6', borderRadius: '4px' }}>
                    <div style={{ fontSize: '18px', fontWeight: 'bold', color: '#f59e0b' }}>{stats.pending}</div>
                    <div style={{ fontSize: '12px', color: '#6b7280' }}>Pending</div>
                  </div>
                  <div style={{ textAlign: 'center', padding: '10px', background: '#f3f4f6', borderRadius: '4px' }}>
                    <div style={{ fontSize: '18px', fontWeight: 'bold', color: '#3b82f6' }}>{stats.inProgress}</div>
                    <div style={{ fontSize: '12px', color: '#6b7280' }}>In Progress</div>
                  </div>
                </div>
              );
            })()}
          </div>
          
          {/* Tasks List for this Workspace */}
          <div style={{ marginTop: '20px', padding: '15px', background: 'white', borderRadius: '6px' }}>
            <h4 style={{ margin: '0 0 15px 0', color: '#374151' }}>Tasks in this Workspace</h4>
            {(() => {
              const workspaceTasks = tasks.filter(task => task.workspace_id === selectedWorkspace.id);
              
              if (workspaceTasks.length === 0) {
                return (
                  <div style={{
                    textAlign: 'center',
                    padding: '30px',
                    background: '#f9fafb',
                    borderRadius: '6px',
                    border: '2px dashed #d1d5db'
                  }}>
                    <p style={{ color: '#6b7280', margin: 0 }}>No tasks in this workspace yet</p>
                    <p style={{ color: '#9ca3af', fontSize: '12px', margin: '5px 0 0 0' }}>
                      Create tasks and assign them to this workspace to see them here
                    </p>
                  </div>
                );
              }
              
              return (
                <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
                  {workspaceTasks.map(task => (
                    <div
                      key={task.id}
                      style={{
                        background: '#f9fafb',
                        border: `2px solid ${getStatusColor(task.status)}20`,
                        borderLeft: `4px solid ${getStatusColor(task.status)}`,
                        borderRadius: '6px',
                        padding: '12px',
                        transition: 'transform 0.2s, box-shadow 0.2s'
                      }}
                      onMouseEnter={(e) => {
                        e.currentTarget.style.transform = 'translateY(-1px)';
                        e.currentTarget.style.boxShadow = '0 2px 8px rgba(0,0,0,0.1)';
                      }}
                      onMouseLeave={(e) => {
                        e.currentTarget.style.transform = 'translateY(0)';
                        e.currentTarget.style.boxShadow = 'none';
                      }}
                    >
                      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                        <div style={{ flex: 1 }}>
                          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '5px' }}>
                            <span>{getPriorityIcon(task.priority)}</span>
                            <h5 style={{ margin: 0, fontSize: '14px', color: '#1f2937' }}>{task.title}</h5>
                            <span style={{ fontSize: '10px', color: '#9ca3af' }}>#{task.id}</span>
                          </div>
                          
                          {task.description && (
                            <p style={{ margin: '0 0 8px 0', color: '#6b7280', fontSize: '12px' }}>
                              {task.description}
                            </p>
                          )}
                          
                          <div style={{ display: 'flex', gap: '10px', alignItems: 'center', fontSize: '11px' }}>
                            <span style={{
                              padding: '2px 6px',
                              backgroundColor: getStatusColor(task.status),
                              color: 'white',
                              borderRadius: '3px',
                              fontWeight: 'bold'
                            }}>
                              {task.status === 'pending' && '⏳ Pending'}
                              {task.status === 'in-progress' && '🔄 In Progress'}
                              {task.status === 'done' && '✅ Done'}
                              {task.status === 'blocked' && '🚫 Blocked'}
                            </span>
                            
                            <span style={{ color: '#6b7280' }}>
                              Priority: {task.priority}
                            </span>
                            
                            {task.due_date && (
                              <span style={{ color: '#6b7280' }}>
                                Due: {new Date(task.due_date).toLocaleDateString()}
                              </span>
                            )}
                          </div>
                          
                          {task.tags && task.tags.length > 0 && (
                            <div style={{ marginTop: '8px' }}>
                              <div style={{ display: 'flex', flexWrap: 'wrap', gap: '4px' }}>
                                {task.tags.map(tag => (
                                  <span
                                    key={tag}
                                    style={{
                                      padding: '2px 6px',
                                      background: `${getTagColor(tag)}15`,
                                      border: `1px solid ${getTagColor(tag)}40`,
                                      borderRadius: '8px',
                                      fontSize: '10px',
                                      color: getTagColor(tag),
                                      fontWeight: 'bold'
                                    }}
                                  >
                                    🏷️ {tag}
                                  </span>
                                ))}
                              </div>
                            </div>
                          )}
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              );
            })()}
          </div>
        </div>
      )}

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(300px, 1fr))', gap: '20px' }}>
        {workspaces.map(workspace => (
          <div
            key={workspace.id}
            style={{
              background: 'white',
              border: '2px solid #e5e7eb',
              borderLeft: `6px solid ${workspace.color}`,
              borderRadius: '8px',
              padding: '20px',
              boxShadow: '0 2px 4px rgba(0,0,0,0.1)',
              transition: 'transform 0.2s, box-shadow 0.2s'
            }}
            onMouseEnter={(e) => {
              e.currentTarget.style.transform = 'translateY(-2px)';
              e.currentTarget.style.boxShadow = '0 4px 12px rgba(0,0,0,0.15)';
            }}
            onMouseLeave={(e) => {
              e.currentTarget.style.transform = 'translateY(0)';
              e.currentTarget.style.boxShadow = '0 2px 4px rgba(0,0,0,0.1)';
            }}
          >
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '10px' }}>
              <h3 style={{ margin: 0, color: workspace.color, fontSize: '18px' }}>
                {workspace.name}
              </h3>
              <button
                onClick={() => deleteWorkspace(workspace)}
                style={{
                  background: 'none',
                  border: 'none',
                  cursor: 'pointer',
                  color: '#ef4444',
                  fontSize: '16px',
                  padding: '2px'
                }}
                title="Delete workspace"
              >
                🗑️
              </button>
            </div>
            
            {workspace.description && (
              <p style={{ margin: '0 0 10px 0', color: '#6b7280', fontSize: '14px' }}>
                {workspace.description}
              </p>
            )}
            
            <div style={{ fontSize: '12px', color: '#9ca3af' }}>
              Created: {new Date(workspace.created_at).toLocaleDateString()}
            </div>
            
            <div style={{ marginTop: '15px', display: 'flex', gap: '8px' }}>
              <button
                onClick={() => openWorkspace(workspace)}
                style={{
                  padding: '6px 12px',
                  background: workspace.color,
                  color: 'white',
                  border: 'none',
                  borderRadius: '4px',
                  cursor: 'pointer',
                  fontSize: '12px'
                }}
              >
                📂 Open
              </button>
              <button
                onClick={() => editWorkspace(workspace)}
                style={{
                  padding: '6px 12px',
                  background: '#f3f4f6',
                  color: '#374151',
                  border: '1px solid #d1d5db',
                  borderRadius: '4px',
                  cursor: 'pointer',
                  fontSize: '12px'
                }}
              >
                ✏️ Edit
              </button>
            </div>
          </div>
        ))}
      </div>

      {workspaces.length === 0 && !loading && (
        <div style={{
          textAlign: 'center',
          padding: '40px',
          background: '#f9fafb',
          borderRadius: '8px',
          border: '2px dashed #d1d5db'
        }}>
          <h3 style={{ color: '#6b7280', margin: '0 0 10px 0' }}>No workspaces yet</h3>
          <p style={{ color: '#9ca3af', margin: '0 0 15px 0' }}>
            Create your first workspace to start organizing your projects!
          </p>
          <button
            onClick={() => setShowCreateForm(true)}
            style={{
              padding: '10px 20px',
              background: '#3b82f6',
              color: 'white',
              border: 'none',
              borderRadius: '6px',
              cursor: 'pointer',
              fontWeight: 'bold'
            }}
          >
            + Create Your First Workspace
          </button>
        </div>
      )}
    </div>
  );
};

const AppWrapper: React.FC = () => (
  <AuthProvider>
    <SimpleApp />
  </AuthProvider>
);

// Final component to render
const SimpleApp: React.FC = () => {
  const { isAuthenticated, isLoading, logout } = useAuth();
  const [currentView, setCurrentView] = useState('dashboard');
  const errorHandler = useErrorHandler();

  const handleSearchResult = (result: SearchResult) => {
    // Handle search result click, e.g., switch view and highlight
    console.log('Search result clicked:', result);
    if (result.type === 'task') {
      setCurrentView('tasks');
    } else if (result.type === 'workspace') {
      setCurrentView('workspaces');
    }
  };

  const renderView = () => {
    switch (currentView) {
      case 'dashboard':
        return <Dashboard errorHandler={errorHandler} />;
      case 'workspaces':
        return <Workspaces errorHandler={errorHandler} />;
      case 'tasks':
        return <TaskManager />;
      case 'test':
        return <ApiTest errorHandler={errorHandler} />;
      case 'errors':
        return <ErrorDashboard errorHandler={errorHandler} />;
      default:
        return <div>Unknown view: {currentView}</div>;
    }
  };
  
  // Show a loading screen while checking auth status
  if (isLoading) {
    return (
      <div style={{
        display: 'flex',
        flexDirection: 'column',
        justifyContent: 'center',
        alignItems: 'center',
        height: '100vh',
        background: '#f9fafb',
        color: '#374151'
      }}>
        <div style={{ 
          width: '40px', 
          height: '40px', 
          border: '4px solid #f3f4f6', 
          borderTop: '4px solid #3b82f6', 
          borderRadius: '50%', 
          animation: 'spin 1s linear infinite' 
        }}></div>
        <p style={{ marginTop: '15px', fontSize: '18px' }}>Authenticating...</p>
      </div>
    );
  }

  // If not authenticated, show the login view
  if (!isAuthenticated) {
    return <Login />;
  }
  
  // Main app view for authenticated users
  return (
    <div style={{ 
      padding: '20px', 
      fontFamily: "'Segoe UI', 'Roboto', 'Helvetica Neue', sans-serif", 
      background: '#f9fafb', 
      minHeight: '100vh',
      overflowY: 'auto',
      maxHeight: '100vh'
    }}>
      
      {/* Error Toasts */}
      <div style={{
        position: 'fixed',
        top: '20px',
        right: '20px',
        zIndex: 1001
      }}>
        {errorHandler.errors.map((error, index) => (
          <div key={error.id} style={{ marginBottom: index < errorHandler.errors.length - 1 ? '10px' : '0' }}>
            <ErrorToast error={error} onDismiss={errorHandler.dismissError} />
          </div>
        ))}
      </div>

      <Navigation 
        currentView={currentView} 
        onViewChange={setCurrentView}
        onSearchResult={handleSearchResult}
        errorHandler={errorHandler}
        onLogout={logout}
      />
      
      <main style={{ 
        overflowY: 'auto',
        maxHeight: 'calc(100vh - 120px)', // Subtract space for navigation and padding
        paddingRight: '5px' // Small padding to avoid content touching scrollbar
      }}>
        {renderView()}
      </main>
    </div>
  );
};

export default AppWrapper;