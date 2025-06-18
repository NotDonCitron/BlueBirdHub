import React, { useState, useEffect } from 'react';

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
      id: Date.now().toString(),
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
}> = ({ currentView, onViewChange, onSearchResult, errorHandler }) => {
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
      const response = await fetch('http://localhost:8000/workspaces');
      
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }
      
      const data = await response.json();
      setWorkspaces(data);
      errorHandler.addError('Workspaces loaded successfully', 'info', `Found ${data.length} workspaces`);
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
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(120px, 1fr))', gap: '10px' }}>
              <div style={{ textAlign: 'center', padding: '10px', background: '#f3f4f6', borderRadius: '4px' }}>
                <div style={{ fontSize: '18px', fontWeight: 'bold', color: selectedWorkspace.color }}>
                  {/* This could be dynamic based on actual task count */}
                  3
                </div>
                <div style={{ fontSize: '12px', color: '#6b7280' }}>Total Tasks</div>
              </div>
              <div style={{ textAlign: 'center', padding: '10px', background: '#f3f4f6', borderRadius: '4px' }}>
                <div style={{ fontSize: '18px', fontWeight: 'bold', color: '#10b981' }}>1</div>
                <div style={{ fontSize: '12px', color: '#6b7280' }}>Completed</div>
              </div>
              <div style={{ textAlign: 'center', padding: '10px', background: '#f3f4f6', borderRadius: '4px' }}>
                <div style={{ fontSize: '18px', fontWeight: 'bold', color: '#f59e0b' }}>2</div>
                <div style={{ fontSize: '12px', color: '#6b7280' }}>Pending</div>
              </div>
            </div>
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

// Task Management with Taskmaster API Integration
interface Task {
  id: string;
  title: string;
  description?: string;
  status: 'pending' | 'in-progress' | 'done' | 'blocked';
  priority: 'low' | 'medium' | 'high';
  dependencies?: string[];
  workspace_id?: number;
  completed_at?: string;
  due_date?: string;
  created_at?: string;
  tags?: string[];
  parent_task_id?: string;
  subtasks?: string[];
  attachments?: number[];
}

interface FileAttachment {
  id: number;
  file_id: string;
  original_name: string;
  stored_name: string;
  size: number;
  size_formatted: string;
  mime_type: string;
  icon: string;
  entity_type: string;
  entity_id: string;
  uploaded_at: string;
}

interface TaskProgress {
  total_tasks: number;
  completed_tasks: number;
  in_progress_tasks: number;
  pending_tasks: number;
  overdue_tasks: number;
  completion_percentage: number;
}

const Tasks: React.FC<{ errorHandler: ReturnType<typeof useErrorHandler> }> = ({ errorHandler }) => {
  const [tasks, setTasks] = useState<Task[]>([]);
  const [progress, setProgress] = useState<TaskProgress | null>(null);
  const [nextTask, setNextTask] = useState<Task | null>(null);
  const [loading, setLoading] = useState(true);
  const [availableTags, setAvailableTags] = useState<string[]>([]);
  const [expandedTasks, setExpandedTasks] = useState<Set<string>>(new Set());
  const [subtasksCache, setSubtasksCache] = useState<{[key: string]: Task[]}>({});
  const [filter, setFilter] = useState<{
    status: string;
    priority: string;
    workspace: string;
    tag: string;
  }>({
    status: 'all',
    priority: 'all',
    workspace: 'all',
    tag: 'all'
  });
  const [showCreateForm, setShowCreateForm] = useState(false);
  const [newTask, setNewTask] = useState({
    title: '',
    description: '',
    priority: 'medium' as 'low' | 'medium' | 'high',
    workspace_id: 1,
    due_date: '',
    tags: [] as string[],
    parent_task_id: undefined as string | undefined
  });
  const [showSubtaskForm, setShowSubtaskForm] = useState<string | null>(null);
  const [viewMode, setViewMode] = useState<'list' | 'kanban'>('list');
  const [draggedTask, setDraggedTask] = useState<Task | null>(null);
  const [dragOverColumn, setDragOverColumn] = useState<Task['status'] | null>(null);
  const [filesCache, setFilesCache] = useState<{[taskId: string]: FileAttachment[]}>({});
  const [uploadingFiles, setUploadingFiles] = useState<Set<string>>(new Set());
  const [selectedTasks, setSelectedTasks] = useState<Set<string>>(new Set());
  const [bulkOperationMode, setBulkOperationMode] = useState(false);
  const [draggedTaskForReorder, setDraggedTaskForReorder] = useState<Task | null>(null);
  const [reorderMode, setReorderMode] = useState(false);
  const [subtaskMoveMode, setSubtaskMoveMode] = useState(false);
  const [draggedSubtask, setDraggedSubtask] = useState<Task | null>(null);

  useEffect(() => {
    loadAllData();
  }, []);

  const loadAllData = async () => {
    try {
      setLoading(true);
      
      // Load all data in parallel
      const [tasksResponse, progressResponse, nextResponse, tagsResponse] = await Promise.all([
        fetch('http://localhost:8000/tasks/taskmaster/all'),
        fetch('http://localhost:8000/tasks/taskmaster/progress'),
        fetch('http://localhost:8000/tasks/taskmaster/next'),
        fetch('http://localhost:8000/tasks/tags/all')
      ]);

      if (!tasksResponse.ok || !progressResponse.ok || !nextResponse.ok || !tagsResponse.ok) {
        throw new Error('One or more API calls failed');
      }

      const [tasksData, progressData, nextData, tagsData] = await Promise.all([
        tasksResponse.json(),
        progressResponse.json(),
        nextResponse.json(),
        tagsResponse.json()
      ]);

      setTasks(tasksData.tasks || []);
      setProgress(progressData);
      setNextTask(nextData.task);
      setAvailableTags(tagsData.tags || []);
      
      errorHandler.addError('Tasks and tags loaded successfully', 'info', `Found ${tasksData.tasks?.length || 0} tasks and ${tagsData.tags?.length || 0} tags`);
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Unknown error';
      errorHandler.addError('Failed to load tasks', 'error', errorMessage);
    } finally {
      setLoading(false);
    }
  };

  const updateTaskStatus = async (taskId: string, newStatus: Task['status']) => {
    try {
      const task = tasks.find(t => t.id === taskId);
      if (!task) return;

      const response = await fetch(`http://localhost:8000/tasks/taskmaster/${taskId}`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          ...task,
          status: newStatus
        }),
      });

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }

      const updatedTask = await response.json();
      
      // Update local state with backend response
      setTasks(prev => prev.map(t => 
        t.id === taskId ? updatedTask : t
      ));

      errorHandler.addError(`Task status updated`, 'info', `Changed "${task.title}" to ${newStatus}`);
      
      // Reload progress data
      setTimeout(() => loadAllData(), 500);
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Unknown error';
      errorHandler.addError('Failed to update task', 'error', errorMessage);
    }
  };

  const createTask = async () => {
    if (!newTask.title.trim()) {
      errorHandler.addError('Task title required', 'warning', 'Please enter a title for the task');
      return;
    }

    try {
      const response = await fetch('http://localhost:8000/tasks/taskmaster', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          title: newTask.title,
          description: newTask.description,
          status: 'pending',
          priority: newTask.priority,
          workspace_id: newTask.workspace_id,
          due_date: newTask.due_date || undefined,
          tags: newTask.tags,
          parent_task_id: newTask.parent_task_id
        }),
      });

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }

      const createdTask = await response.json();
      
      setTasks(prev => [...prev, createdTask]);
      setNewTask({ title: '', description: '', priority: 'medium', workspace_id: 1, due_date: '', tags: [], parent_task_id: undefined });
      setShowCreateForm(false);
      setShowSubtaskForm(null);
      
      // If it was a subtask, refresh the subtasks cache
      if (newTask.parent_task_id) {
        loadSubtasks(newTask.parent_task_id);
      }
      
      errorHandler.addError('Task created successfully', 'info', `Created "${createdTask.title}"`);
      
      // Reload progress data
      setTimeout(() => loadAllData(), 500);
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Unknown error';
      errorHandler.addError('Failed to create task', 'error', errorMessage);
    }
  };

  const deleteTask = async (taskId: string) => {
    const task = tasks.find(t => t.id === taskId);
    if (!task) return;

    if (!confirm(`Are you sure you want to delete "${task.title}"?`)) {
      return;
    }

    try {
      const response = await fetch(`http://localhost:8000/tasks/taskmaster/${taskId}`, {
        method: 'DELETE',
      });

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }

      setTasks(prev => prev.filter(t => t.id !== taskId));
      errorHandler.addError('Task deleted', 'info', `Removed "${task.title}"`);
      
      // Reload progress data
      setTimeout(() => loadAllData(), 500);
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Unknown error';
      errorHandler.addError('Failed to delete task', 'error', errorMessage);
    }
  };

  // Bulk Operations Functions
  const toggleTaskSelection = (taskId: string) => {
    setSelectedTasks(prev => {
      const newSet = new Set(prev);
      if (newSet.has(taskId)) {
        newSet.delete(taskId);
      } else {
        newSet.add(taskId);
      }
      return newSet;
    });
  };

  const selectAllVisibleTasks = () => {
    const visibleTaskIds = getFilteredTasks().map(task => task.id);
    setSelectedTasks(new Set(visibleTaskIds));
  };

  const clearSelection = () => {
    setSelectedTasks(new Set());
  };

  const bulkDelete = async () => {
    if (selectedTasks.size === 0) return;
    
    if (!confirm(`Are you sure you want to delete ${selectedTasks.size} selected tasks?`)) {
      return;
    }

    try {
      const response = await fetch('http://localhost:8000/tasks/bulk', {
        method: 'DELETE',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ task_ids: Array.from(selectedTasks) })
      });

      if (!response.ok) throw new Error(`HTTP ${response.status}`);

      const result = await response.json();
      
      setTasks(prev => prev.filter(t => !selectedTasks.has(t.id)));
      setSelectedTasks(new Set());
      setBulkOperationMode(false);
      
      errorHandler.addError('Bulk delete completed', 'info', `Deleted ${result.deleted_count} tasks`);
      setTimeout(() => loadAllData(), 500);
    } catch (error) {
      errorHandler.addError('Bulk delete failed', 'error', error instanceof Error ? error.message : 'Unknown error');
    }
  };

  const bulkUpdateStatus = async (status: Task['status']) => {
    if (selectedTasks.size === 0) return;

    try {
      const response = await fetch('http://localhost:8000/tasks/bulk', {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ 
          task_ids: Array.from(selectedTasks),
          updates: { status }
        })
      });

      if (!response.ok) throw new Error(`HTTP ${response.status}`);

      const result = await response.json();
      
      setTasks(prev => prev.map(task => 
        selectedTasks.has(task.id) ? { ...task, status } : task
      ));
      setSelectedTasks(new Set());
      setBulkOperationMode(false);
      
      errorHandler.addError('Bulk status update completed', 'info', `Updated ${result.updated_count} tasks to ${status}`);
      setTimeout(() => loadAllData(), 500);
    } catch (error) {
      errorHandler.addError('Bulk update failed', 'error', error instanceof Error ? error.message : 'Unknown error');
    }
  };

  const bulkUpdatePriority = async (priority: Task['priority']) => {
    if (selectedTasks.size === 0) return;

    try {
      const response = await fetch('http://localhost:8000/tasks/bulk', {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ 
          task_ids: Array.from(selectedTasks),
          updates: { priority }
        })
      });

      if (!response.ok) throw new Error(`HTTP ${response.status}`);

      const result = await response.json();
      
      setTasks(prev => prev.map(task => 
        selectedTasks.has(task.id) ? { ...task, priority } : task
      ));
      setSelectedTasks(new Set());
      setBulkOperationMode(false);
      
      errorHandler.addError('Bulk priority update completed', 'info', `Updated ${result.updated_count} tasks to ${priority} priority`);
      setTimeout(() => loadAllData(), 500);
    } catch (error) {
      errorHandler.addError('Bulk update failed', 'error', error instanceof Error ? error.message : 'Unknown error');
    }
  };

  const bulkAddTags = async (tagsToAdd: string[]) => {
    if (selectedTasks.size === 0 || tagsToAdd.length === 0) return;

    try {
      const response = await fetch('http://localhost:8000/tasks/bulk', {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ 
          task_ids: Array.from(selectedTasks),
          updates: { tags: tagsToAdd, tag_operation: 'add' }
        })
      });

      if (!response.ok) throw new Error(`HTTP ${response.status}`);

      const result = await response.json();
      
      // Update local state
      setTasks(prev => prev.map(task => {
        if (selectedTasks.has(task.id)) {
          const currentTags = task.tags || [];
          const newTags = [...new Set([...currentTags, ...tagsToAdd])];
          return { ...task, tags: newTags };
        }
        return task;
      }));
      
      setSelectedTasks(new Set());
      setBulkOperationMode(false);
      
      errorHandler.addError('Bulk tag addition completed', 'info', `Added tags to ${result.updated_count} tasks`);
      setTimeout(() => loadAllData(), 500);
    } catch (error) {
      errorHandler.addError('Bulk tag addition failed', 'error', error instanceof Error ? error.message : 'Unknown error');
    }
  };

  const bulkRemoveTags = async (tagsToRemove: string[]) => {
    if (selectedTasks.size === 0 || tagsToRemove.length === 0) return;

    try {
      const response = await fetch('http://localhost:8000/tasks/bulk', {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ 
          task_ids: Array.from(selectedTasks),
          updates: { tags: tagsToRemove, tag_operation: 'remove' }
        })
      });

      if (!response.ok) throw new Error(`HTTP ${response.status}`);

      const result = await response.json();
      
      // Update local state
      setTasks(prev => prev.map(task => {
        if (selectedTasks.has(task.id)) {
          const currentTags = task.tags || [];
          const newTags = currentTags.filter(tag => !tagsToRemove.includes(tag));
          return { ...task, tags: newTags };
        }
        return task;
      }));
      
      setSelectedTasks(new Set());
      setBulkOperationMode(false);
      
      errorHandler.addError('Bulk tag removal completed', 'info', `Removed tags from ${result.updated_count} tasks`);
      setTimeout(() => loadAllData(), 500);
    } catch (error) {
      errorHandler.addError('Bulk tag removal failed', 'error', error instanceof Error ? error.message : 'Unknown error');
    }
  };

  // Priority Reordering Functions
  const handleReorderDragStart = (e: React.DragEvent, task: Task) => {
    setDraggedTaskForReorder(task);
    e.dataTransfer.effectAllowed = 'move';
  };

  const handleReorderDragEnd = () => {
    setDraggedTaskForReorder(null);
  };

  const handleReorderDrop = (e: React.DragEvent, targetTask: Task) => {
    e.preventDefault();
    
    if (!draggedTaskForReorder || draggedTaskForReorder.id === targetTask.id) {
      return;
    }

    // Only allow reordering within the same status
    if (draggedTaskForReorder.status !== targetTask.status) {
      errorHandler.addError('Priority reordering only works within the same status', 'warning', 'Drag tasks to different columns to change status');
      return;
    }

    // Get tasks with the same status, sorted by current priority order
    const sameStatusTasks = getFilteredTasks()
      .filter(task => task.status === targetTask.status)
      .sort((a, b) => {
        const priorityOrder = { 'high': 0, 'medium': 1, 'low': 2 };
        return priorityOrder[a.priority] - priorityOrder[b.priority];
      });

    const draggedIndex = sameStatusTasks.findIndex(task => task.id === draggedTaskForReorder.id);
    const targetIndex = sameStatusTasks.findIndex(task => task.id === targetTask.id);

    if (draggedIndex === -1 || targetIndex === -1) return;

    // Determine new priority based on position
    let newPriority: Task['priority'];
    if (targetIndex === 0) {
      newPriority = 'high';
    } else if (targetIndex === sameStatusTasks.length - 1) {
      newPriority = 'low';
    } else {
      // Place in middle - use medium priority
      newPriority = 'medium';
    }

    // Update the dragged task's priority
    updateTaskPriority(draggedTaskForReorder.id, newPriority);
  };

  const updateTaskPriority = async (taskId: string, newPriority: Task['priority']) => {
    try {
      const response = await fetch(`http://localhost:8000/tasks/taskmaster/${taskId}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ priority: newPriority })
      });

      if (!response.ok) throw new Error(`HTTP ${response.status}`);

      setTasks(prev => prev.map(task => 
        task.id === taskId ? { ...task, priority: newPriority } : task
      ));

      errorHandler.addError('Task priority updated', 'info', `Changed to ${newPriority} priority`);
    } catch (error) {
      errorHandler.addError('Priority update failed', 'error', error instanceof Error ? error.message : 'Unknown error');
    }
  };

  // Subtask Moving Functions
  const handleSubtaskDragStart = (e: React.DragEvent, subtask: Task) => {
    setDraggedSubtask(subtask);
    e.dataTransfer.effectAllowed = 'move';
  };

  const handleSubtaskDragEnd = () => {
    setDraggedSubtask(null);
  };

  const handleParentTaskDrop = async (e: React.DragEvent, newParentTask: Task) => {
    e.preventDefault();
    
    if (!draggedSubtask || !draggedSubtask.parent_task_id) {
      return;
    }

    // Don't allow moving to the same parent
    if (draggedSubtask.parent_task_id === newParentTask.id) {
      return;
    }

    // Don't allow moving a parent task as a subtask to its own subtask
    if (newParentTask.parent_task_id === draggedSubtask.id) {
      errorHandler.addError('Cannot move parent to its own subtask', 'warning', 'This would create a circular dependency');
      return;
    }

    try {
      // Update the subtask's parent
      const response = await fetch(`http://localhost:8000/tasks/taskmaster/${draggedSubtask.id}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ 
          parent_task_id: newParentTask.id,
          workspace_id: newParentTask.workspace_id // Inherit workspace from new parent
        })
      });

      if (!response.ok) throw new Error(`HTTP ${response.status}`);

      // Update local state
      setTasks(prev => prev.map(task => 
        task.id === draggedSubtask.id 
          ? { ...task, parent_task_id: newParentTask.id, workspace_id: newParentTask.workspace_id }
          : task
      ));

      // Clear subtasks cache to force reload
      setSubtasksCache(prev => {
        const newCache = { ...prev };
        delete newCache[draggedSubtask.parent_task_id!];
        delete newCache[newParentTask.id];
        return newCache;
      });

      errorHandler.addError('Subtask moved successfully', 'info', `Moved "${draggedSubtask.title}" to "${newParentTask.title}"`);
      
      // Reload data to get fresh subtask relationships
      setTimeout(() => loadAllData(), 500);
    } catch (error) {
      errorHandler.addError('Failed to move subtask', 'error', error instanceof Error ? error.message : 'Unknown error');
    }
  };

  const getFilteredTasks = () => {
    return tasks.filter(task => {
      // Only show main tasks (not subtasks) in the main list
      if (task.parent_task_id) return false;
      
      if (filter.status !== 'all' && task.status !== filter.status) return false;
      if (filter.priority !== 'all' && task.priority !== filter.priority) return false;
      if (filter.workspace !== 'all' && task.workspace_id?.toString() !== filter.workspace) return false;
      if (filter.tag !== 'all' && (!task.tags || !task.tags.includes(filter.tag))) return false;
      return true;
    });
  };

  const getStatusColor = (status: Task['status']) => {
    switch (status) {
      case 'done': return '#10b981';
      case 'in-progress': return '#f59e0b';
      case 'pending': return '#6b7280';
      case 'blocked': return '#ef4444';
      default: return '#6b7280';
    }
  };

  const getPriorityIcon = (priority: Task['priority']) => {
    switch (priority) {
      case 'high': return '🔴';
      case 'medium': return '🟡';
      case 'low': return '🟢';
      default: return '⚪';
    }
  };

  const formatDueDate = (dueDate?: string) => {
    if (!dueDate) return null;
    
    const due = new Date(dueDate);
    const now = new Date();
    const diffTime = due.getTime() - now.getTime();
    const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));
    
    if (diffDays < 0) {
      return { text: `Overdue by ${Math.abs(diffDays)} days`, color: '#ef4444', icon: '🚨' };
    } else if (diffDays === 0) {
      return { text: 'Due today', color: '#f59e0b', icon: '⚠️' };
    } else if (diffDays === 1) {
      return { text: 'Due tomorrow', color: '#f59e0b', icon: '⏰' };
    } else if (diffDays <= 7) {
      return { text: `Due in ${diffDays} days`, color: '#10b981', icon: '📅' };
    } else {
      return { text: `Due ${due.toLocaleDateString()}`, color: '#6b7280', icon: '📅' };
    }
  };

  const formatDateForInput = (dateString?: string) => {
    if (!dateString) return '';
    const date = new Date(dateString);
    const year = date.getFullYear();
    const month = String(date.getMonth() + 1).padStart(2, '0');
    const day = String(date.getDate()).padStart(2, '0');
    const hours = String(date.getHours()).padStart(2, '0');
    const minutes = String(date.getMinutes()).padStart(2, '0');
    return `${year}-${month}-${day}T${hours}:${minutes}`;
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

  const addTagToTask = (tag: string) => {
    if (!newTask.tags.includes(tag)) {
      setNewTask(prev => ({ ...prev, tags: [...prev.tags, tag] }));
    }
  };

  const removeTagFromTask = (tag: string) => {
    setNewTask(prev => ({ ...prev, tags: prev.tags.filter(t => t !== tag) }));
  };

  const loadSubtasks = async (parentTaskId: string) => {
    try {
      const response = await fetch(`http://localhost:8000/tasks/${parentTaskId}/subtasks`);
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }
      
      const data = await response.json();
      setSubtasksCache(prev => ({
        ...prev,
        [parentTaskId]: data.subtasks || []
      }));
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Unknown error';
      errorHandler.addError('Failed to load subtasks', 'error', errorMessage);
    }
  };

  const toggleTaskExpanded = async (taskId: string) => {
    const newExpanded = new Set(expandedTasks);
    
    if (newExpanded.has(taskId)) {
      newExpanded.delete(taskId);
    } else {
      newExpanded.add(taskId);
      // Load subtasks if not already cached
      if (!subtasksCache[taskId]) {
        await loadSubtasks(taskId);
      }
    }
    
    setExpandedTasks(newExpanded);
  };

  const createSubtask = (parentTaskId: string) => {
    setNewTask(prev => ({ 
      ...prev, 
      parent_task_id: parentTaskId,
      workspace_id: tasks.find(t => t.id === parentTaskId)?.workspace_id || 1
    }));
    setShowSubtaskForm(parentTaskId);
    setShowCreateForm(true);
  };

  const getSubtaskProgress = (parentTask: Task) => {
    const subtasks = subtasksCache[parentTask.id] || [];
    if (subtasks.length === 0) return null;
    
    const doneCount = subtasks.filter(st => st.status === 'done').length;
    const totalCount = subtasks.length;
    const percentage = (doneCount / totalCount) * 100;
    
    return {
      done: doneCount,
      total: totalCount,
      percentage: Math.round(percentage)
    };
  };

  // File Attachment Functions
  const loadTaskFiles = async (taskId: string) => {
    try {
      const response = await fetch(`http://localhost:8000/tasks/${taskId}/files`);
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }
      
      const data = await response.json();
      setFilesCache(prev => ({
        ...prev,
        [taskId]: data.files || []
      }));
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Unknown error';
      errorHandler.addError('Failed to load task files', 'error', errorMessage);
    }
  };

  const uploadFile = async (file: File, taskId: string) => {
    const uploadId = `${taskId}-${Date.now()}`;
    setUploadingFiles(prev => new Set([...prev, uploadId]));
    
    try {
      // Convert file to base64
      const fileData = await new Promise<string>((resolve, reject) => {
        const reader = new FileReader();
        reader.onload = () => {
          const result = reader.result as string;
          const base64 = result.split(',')[1]; // Remove data:... prefix
          resolve(base64);
        };
        reader.onerror = reject;
        reader.readAsDataURL(file);
      });

      const response = await fetch('http://localhost:8000/files/upload', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          file_data: fileData,
          filename: file.name,
          task_id: taskId
        }),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.error || `HTTP ${response.status}`);
      }

      const result = await response.json();
      
      // Reload task files
      await loadTaskFiles(taskId);
      
      // Reload tasks to get updated attachment count
      setTimeout(() => loadAllData(), 500);
      
      errorHandler.addError(`File "${file.name}" uploaded successfully`, 'info', `${result.file.size_formatted} attached to task`);
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Unknown error';
      errorHandler.addError('Failed to upload file', 'error', errorMessage);
    } finally {
      setUploadingFiles(prev => {
        const newSet = new Set(prev);
        newSet.delete(uploadId);
        return newSet;
      });
    }
  };

  const handleFileSelect = (event: React.ChangeEvent<HTMLInputElement>, taskId: string) => {
    const files = event.target.files;
    if (files && files.length > 0) {
      Array.from(files).forEach(file => {
        uploadFile(file, taskId);
      });
      // Reset input
      event.target.value = '';
    }
  };

  const downloadFile = (fileId: number, filename: string) => {
    const link = document.createElement('a');
    link.href = `http://localhost:8000/files/${fileId}/download`;
    link.download = filename;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  // Drag & Drop Functions
  const handleDragStart = (e: React.DragEvent, task: Task) => {
    setDraggedTask(task);
    e.dataTransfer.effectAllowed = 'move';
    e.dataTransfer.setData('text/plain', task.id);
    
    // Add visual feedback
    const target = e.target as HTMLElement;
    target.style.opacity = '0.5';
    target.style.transform = 'rotate(5deg)';
    
    errorHandler.addError(`Dragging "${task.title}"`, 'info', 'Drop on a column to change status');
  };

  const handleDragEnd = (e: React.DragEvent) => {
    setDraggedTask(null);
    setDragOverColumn(null);
    
    // Reset visual feedback
    const target = e.target as HTMLElement;
    target.style.opacity = '1';
    target.style.transform = 'rotate(0deg)';
  };

  const handleDragOver = (e: React.DragEvent, status: Task['status']) => {
    e.preventDefault();
    e.dataTransfer.dropEffect = 'move';
    setDragOverColumn(status);
  };

  const handleDragLeave = (e: React.DragEvent) => {
    // Only clear if we're leaving the column entirely
    const rect = e.currentTarget.getBoundingClientRect();
    const x = e.clientX;
    const y = e.clientY;
    
    if (x < rect.left || x > rect.right || y < rect.top || y > rect.bottom) {
      setDragOverColumn(null);
    }
  };

  const handleDrop = async (e: React.DragEvent, newStatus: Task['status']) => {
    e.preventDefault();
    setDragOverColumn(null);
    
    if (!draggedTask || draggedTask.status === newStatus) {
      return;
    }
    
    try {
      await updateTaskStatus(draggedTask.id, newStatus);
      errorHandler.addError(`Task moved to ${newStatus}`, 'info', `"${draggedTask.title}" status updated`);
    } catch (error) {
      errorHandler.addError('Failed to move task', 'error', 'Drag & drop operation failed');
    }
  };

  const getTasksByStatus = (status: Task['status']) => {
    return filteredTasks.filter(task => task.status === status);
  };

  const getColumnColor = (status: Task['status']) => {
    switch (status) {
      case 'pending': return { bg: '#f9fafb', border: '#6b7280', text: '#374151' };
      case 'in-progress': return { bg: '#fef3c7', border: '#f59e0b', text: '#92400e' };
      case 'done': return { bg: '#f0fdf4', border: '#10b981', text: '#065f46' };
      case 'blocked': return { bg: '#fef2f2', border: '#ef4444', text: '#991b1b' };
      default: return { bg: '#f9fafb', border: '#6b7280', text: '#374151' };
    }
  };

  // TaskCard Component for both List and Kanban views
  const TaskCard: React.FC<{ task: Task; isDraggable?: boolean; showCheckbox?: boolean; isReorderable?: boolean }> = ({ task, isDraggable = false, showCheckbox = false, isReorderable = false }) => (
    <div
      draggable={isDraggable || isReorderable}
      onDragStart={
        isDraggable 
          ? (e) => handleDragStart(e, task)
          : isReorderable 
            ? (e) => handleReorderDragStart(e, task)
            : undefined
      }
      onDragEnd={
        isDraggable 
          ? handleDragEnd
          : isReorderable 
            ? handleReorderDragEnd
            : undefined
      }
      onDragOver={
        isReorderable 
          ? (e) => e.preventDefault()
          : (subtaskMoveMode && !task.parent_task_id)
            ? (e) => e.preventDefault()
            : undefined
      }
      onDrop={
        isReorderable 
          ? (e) => handleReorderDrop(e, task)
          : (subtaskMoveMode && !task.parent_task_id)
            ? (e) => handleParentTaskDrop(e, task)
            : undefined
      }
      style={{
        background: showCheckbox && selectedTasks.has(task.id) 
          ? '#f0f9ff' 
          : (subtaskMoveMode && !task.parent_task_id && draggedSubtask)
            ? '#fdf2f8'
            : 'white',
        border: showCheckbox && selectedTasks.has(task.id) 
          ? '2px solid #3b82f6' 
          : (subtaskMoveMode && !task.parent_task_id && draggedSubtask)
            ? '2px dashed #ec4899'
            : '2px solid #e5e7eb',
        borderLeft: `6px solid ${getStatusColor(task.status)}`,
        borderRadius: '8px',
        padding: isDraggable ? '15px' : '20px',
        boxShadow: '0 2px 4px rgba(0,0,0,0.1)',
        transition: 'transform 0.2s, box-shadow 0.2s',
        cursor: isDraggable ? 'grab' : isReorderable ? 'move' : 'default',
        marginBottom: isDraggable ? '12px' : '0',
        opacity: draggedTaskForReorder?.id === task.id ? 0.5 : 1
      }}
      onMouseEnter={(e) => {
        if (!isDraggable) {
          e.currentTarget.style.transform = 'translateY(-2px)';
          e.currentTarget.style.boxShadow = '0 4px 12px rgba(0,0,0,0.15)';
        }
      }}
      onMouseLeave={(e) => {
        if (!isDraggable) {
          e.currentTarget.style.transform = 'translateY(0)';
          e.currentTarget.style.boxShadow = '0 2px 4px rgba(0,0,0,0.1)';
        }
      }}
    >
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '10px' }}>
        <div style={{ flex: 1 }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '5px' }}>
            {showCheckbox && (
              <input
                type="checkbox"
                checked={selectedTasks.has(task.id)}
                onChange={() => toggleTaskSelection(task.id)}
                style={{
                  width: '18px',
                  height: '18px',
                  cursor: 'pointer',
                  accentColor: '#3b82f6'
                }}
                onClick={(e) => e.stopPropagation()}
              />
            )}
            <span>{getPriorityIcon(task.priority)}</span>
            <h3 style={{ margin: 0, fontSize: isDraggable ? '16px' : '18px', color: '#1f2937' }}>{task.title}</h3>
            <span style={{ fontSize: '12px', color: '#6b7280' }}>#{task.id}</span>
          </div>
          
          {task.description && (
            <p style={{ margin: '0 0 10px 0', color: '#6b7280', fontSize: '14px' }}>
              {task.description}
            </p>
          )}

          <div style={{ display: 'flex', gap: '15px', fontSize: '12px', color: '#9ca3af' }}>
            <span>Priority: {task.priority}</span>
            <span>Workspace: {task.workspace_id}</span>
            {task.completed_at && <span>Completed: {new Date(task.completed_at).toLocaleDateString()}</span>}
          </div>

          {/* Due Date Display */}
          {task.due_date && (
            <div style={{ marginTop: '10px' }}>
              {(() => {
                const dueDateInfo = formatDueDate(task.due_date);
                return dueDateInfo ? (
                  <div style={{
                    display: 'inline-flex',
                    alignItems: 'center',
                    gap: '6px',
                    padding: '4px 8px',
                    background: `${dueDateInfo.color}15`,
                    border: `1px solid ${dueDateInfo.color}40`,
                    borderRadius: '12px',
                    fontSize: '12px',
                    color: dueDateInfo.color,
                    fontWeight: 'bold'
                  }}>
                    <span>{dueDateInfo.icon}</span>
                    <span>{dueDateInfo.text}</span>
                  </div>
                ) : null;
              })()}
            </div>
          )}

          {/* Tags Display */}
          {task.tags && task.tags.length > 0 && (
            <div style={{ marginTop: '10px' }}>
              <div style={{ display: 'flex', flexWrap: 'wrap', gap: '6px' }}>
                {task.tags.map(tag => (
                  <span
                    key={tag}
                    style={{
                      display: 'inline-flex',
                      alignItems: 'center',
                      gap: '4px',
                      padding: '3px 8px',
                      background: `${getTagColor(tag)}15`,
                      border: `1px solid ${getTagColor(tag)}40`,
                      borderRadius: '12px',
                      fontSize: '11px',
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

          {/* Subtask Progress and Controls - Only for main tasks */}
          {!task.parent_task_id && (
            <div style={{ marginTop: '10px' }}>
              {(() => {
                const progress = getSubtaskProgress(task);
                return progress ? (
                  <div style={{
                    display: 'flex',
                    alignItems: 'center',
                    gap: '10px',
                    padding: '8px 12px',
                    background: '#f0f9ff',
                    border: '1px solid #0ea5e9',
                    borderRadius: '8px',
                    fontSize: '12px'
                  }}>
                    <span style={{ fontWeight: 'bold', color: '#0369a1' }}>📝 Subtasks:</span>
                    <div style={{ 
                      flex: 1,
                      background: '#e5e7eb', 
                      borderRadius: '6px', 
                      height: '6px', 
                      overflow: 'hidden' 
                    }}>
                      <div 
                        style={{ 
                          background: '#10b981', 
                          height: '100%', 
                          width: `${progress.percentage}%`,
                          transition: 'width 0.3s ease'
                        }}
                      ></div>
                    </div>
                    <span style={{ color: '#0369a1', fontWeight: 'bold' }}>
                      {progress.done}/{progress.total} ({progress.percentage}%)
                    </span>
                  </div>
                ) : (
                  <div style={{
                    padding: '8px 12px',
                    background: '#f9fafb',
                    border: '1px solid #d1d5db',
                    borderRadius: '8px',
                    fontSize: '12px',
                    color: '#6b7280',
                    textAlign: 'center'
                  }}>
                    📝 No subtasks yet
                  </div>
                );
              })()} 
            </div>
          )}
        </div>

        <button
          onClick={() => deleteTask(task.id)}
          style={{
            background: 'none',
            border: 'none',
            cursor: 'pointer',
            color: '#ef4444',
            fontSize: '16px',
            padding: '2px',
            marginLeft: '10px'
          }}
          title="Delete task"
        >
          🗑️
        </button>
      </div>

      <div style={{ display: 'flex', gap: '8px', alignItems: 'center', flexWrap: 'wrap' }}>
        <span style={{ fontSize: '12px', fontWeight: 'bold', color: '#374151' }}>Status:</span>
        {isDraggable ? (
          <span style={{
            padding: '4px 8px',
            backgroundColor: getStatusColor(task.status),
            color: 'white',
            borderRadius: '4px',
            fontSize: '12px',
            fontWeight: 'bold'
          }}>
            {task.status === 'pending' && '⏳ Pending'}
            {task.status === 'in-progress' && '🔄 In Progress'}
            {task.status === 'done' && '✅ Done'}
            {task.status === 'blocked' && '🚫 Blocked'}
          </span>
        ) : (
          <select
            value={task.status}
            onChange={(e) => updateTaskStatus(task.id, e.target.value as Task['status'])}
            style={{
              padding: '4px 8px',
              border: '1px solid #d1d5db',
              borderRadius: '4px',
              fontSize: '12px',
              backgroundColor: getStatusColor(task.status),
              color: 'white',
              fontWeight: 'bold'
            }}
          >
            <option value="pending">⏳ Pending</option>
            <option value="in-progress">🔄 In Progress</option>
            <option value="done">✅ Done</option>
            <option value="blocked">🚫 Blocked</option>
          </select>
        )}

        {/* Subtask Actions - Only for main tasks and not in Kanban mode */}
        {!task.parent_task_id && !isDraggable && (
          <div style={{ display: 'flex', gap: '6px', marginLeft: 'auto' }}>
            <button
              onClick={() => createSubtask(task.id)}
              style={{
                padding: '4px 8px',
                background: '#3b82f6',
                color: 'white',
                border: 'none',
                borderRadius: '4px',
                cursor: 'pointer',
                fontSize: '11px',
                fontWeight: 'bold'
              }}
              title="Add subtask"
            >
              📝 Add Subtask
            </button>
            
            {(task.subtasks && task.subtasks.length > 0) && (
              <button
                onClick={() => toggleTaskExpanded(task.id)}
                style={{
                  padding: '4px 8px',
                  background: expandedTasks.has(task.id) ? '#ef4444' : '#10b981',
                  color: 'white',
                  border: 'none',
                  borderRadius: '4px',
                  cursor: 'pointer',
                  fontSize: '11px',
                  fontWeight: 'bold'
                }}
                title={expandedTasks.has(task.id) ? 'Hide subtasks' : 'Show subtasks'}
              >
                {expandedTasks.has(task.id) ? '🔼 Hide' : '🔽 Show'} ({task.subtasks.length})
              </button>
            )}
          </div>
        )}
      </div>

      {/* File Attachments Section */}
      {task.attachments && task.attachments.length > 0 && (
        <div style={{ marginTop: '15px' }}>
          <div style={{
            display: 'flex',
            alignItems: 'center',
            gap: '8px',
            marginBottom: '8px'
          }}>
            <span style={{ fontSize: '12px', fontWeight: 'bold', color: '#374151' }}>📎 Attachments:</span>
            <span style={{ fontSize: '11px', color: '#6b7280' }}>({task.attachments.length})</span>
            {!isDraggable && (
              <button
                onClick={() => {
                  if (!filesCache[task.id]) {
                    loadTaskFiles(task.id);
                  }
                }}
                style={{
                  padding: '2px 6px',
                  background: '#3b82f6',
                  color: 'white',
                  border: 'none',
                  borderRadius: '3px',
                  cursor: 'pointer',
                  fontSize: '10px'
                }}
              >
                {filesCache[task.id] ? 'Refresh' : 'Load'}
              </button>
            )}
          </div>
          
          {filesCache[task.id] && (
            <div style={{ display: 'flex', flexWrap: 'wrap', gap: '6px' }}>
              {filesCache[task.id].map(file => (
                <div
                  key={file.id}
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    gap: '6px',
                    padding: '4px 8px',
                    background: '#f3f4f6',
                    border: '1px solid #d1d5db',
                    borderRadius: '6px',
                    fontSize: '11px'
                  }}
                >
                  <span>{file.icon}</span>
                  <span style={{ fontWeight: 'bold', color: '#374151' }}>{file.original_name}</span>
                  <span style={{ color: '#6b7280' }}>({file.size_formatted})</span>
                  {!isDraggable && (
                    <button
                      onClick={() => downloadFile(file.id, file.original_name)}
                      style={{
                        background: 'none',
                        border: 'none',
                        cursor: 'pointer',
                        color: '#3b82f6',
                        fontSize: '10px',
                        padding: '2px'
                      }}
                      title="Download file"
                    >
                      ⬇️
                    </button>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* File Upload Section - Only in List view */}
      {!isDraggable && (
        <div style={{ marginTop: '15px' }}>
          <div style={{
            border: '2px dashed #d1d5db',
            borderRadius: '8px',
            padding: '12px',
            textAlign: 'center',
            background: '#f9fafb'
          }}>
            <input
              type="file"
              id={`file-upload-${task.id}`}
              style={{ display: 'none' }}
              multiple
              onChange={(e) => handleFileSelect(e, task.id)}
              accept=".pdf,.doc,.docx,.txt,.md,.jpg,.jpeg,.png,.gif,.webp,.mp4,.mov,.avi,.webm,.mp3,.wav,.m4a,.zip,.rar,.tar,.gz,.xlsx,.xls,.csv,.pptx,.ppt"
            />
            <label
              htmlFor={`file-upload-${task.id}`}
              style={{
                cursor: 'pointer',
                color: '#3b82f6',
                fontSize: '12px',
                fontWeight: 'bold'
              }}
            >
              📎 Click to attach files or drag & drop
            </label>
            <div style={{ fontSize: '10px', color: '#6b7280', marginTop: '4px' }}>
              Supports: Documents, Images, Videos, Audio, Archives (Max 50MB each)
            </div>
          </div>
        </div>
      )}

      {/* Expanded Subtasks Display - Only in List view */}
      {!task.parent_task_id && !isDraggable && expandedTasks.has(task.id) && subtasksCache[task.id] && (
        <div style={{
          marginTop: '15px',
          paddingLeft: '20px',
          borderLeft: '3px solid #e5e7eb'
        }}>
          <h4 style={{ 
            margin: '0 0 10px 0', 
            fontSize: '14px', 
            color: '#4b5563',
            display: 'flex',
            alignItems: 'center',
            gap: '6px'
          }}>
            📝 Subtasks ({subtasksCache[task.id].length})
          </h4>
          
          {subtasksCache[task.id].map(subtask => (
            <div
              key={subtask.id}
              draggable={subtaskMoveMode}
              onDragStart={subtaskMoveMode ? (e) => handleSubtaskDragStart(e, subtask) : undefined}
              onDragEnd={subtaskMoveMode ? handleSubtaskDragEnd : undefined}
              style={{
                background: draggedSubtask?.id === subtask.id ? '#fef3c7' : '#f9fafb',
                border: draggedSubtask?.id === subtask.id ? '2px solid #ec4899' : '1px solid #e5e7eb',
                borderLeft: `4px solid ${getStatusColor(subtask.status)}`,
                borderRadius: '6px',
                padding: '12px',
                marginBottom: '8px',
                cursor: subtaskMoveMode ? 'grab' : 'default',
                opacity: draggedSubtask?.id === subtask.id ? 0.6 : 1,
                transition: 'all 0.2s'
              }}
            >
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                <div style={{ flex: 1 }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '6px', marginBottom: '4px' }}>
                    <span>{getPriorityIcon(subtask.priority)}</span>
                    <h5 style={{ margin: 0, fontSize: '14px', color: '#1f2937' }}>{subtask.title}</h5>
                    <span style={{ fontSize: '10px', color: '#9ca3af' }}>#{subtask.id}</span>
                  </div>
                  
                  {subtask.description && (
                    <p style={{ margin: '0 0 8px 0', color: '#6b7280', fontSize: '12px' }}>
                      {subtask.description}
                    </p>
                  )}

                  {subtask.tags && subtask.tags.length > 0 && (
                    <div style={{ marginBottom: '8px' }}>
                      <div style={{ display: 'flex', flexWrap: 'wrap', gap: '4px' }}>
                        {subtask.tags.map(tag => (
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

                <button
                  onClick={() => deleteTask(subtask.id)}
                  style={{
                    background: 'none',
                    border: 'none',
                    cursor: 'pointer',
                    color: '#ef4444',
                    fontSize: '12px',
                    padding: '2px',
                    marginLeft: '8px'
                  }}
                  title="Delete subtask"
                >
                  🗑️
                </button>
              </div>

              <div style={{ display: 'flex', gap: '6px', alignItems: 'center', marginTop: '8px' }}>
                <span style={{ fontSize: '11px', fontWeight: 'bold', color: '#374151' }}>Status:</span>
                <select
                  value={subtask.status}
                  onChange={(e) => updateTaskStatus(subtask.id, e.target.value as Task['status'])}
                  style={{
                    padding: '3px 6px',
                    border: '1px solid #d1d5db',
                    borderRadius: '3px',
                    fontSize: '11px',
                    backgroundColor: getStatusColor(subtask.status),
                    color: 'white',
                    fontWeight: 'bold'
                  }}
                >
                  <option value="pending">⏳ Pending</option>
                  <option value="in-progress">🔄 In Progress</option>
                  <option value="done">✅ Done</option>
                  <option value="blocked">🚫 Blocked</option>
                </select>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );

  if (loading) {
    return (
      <div>
        <h2>✅ Tasks</h2>
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
          <div style={{ 
            width: '20px', 
            height: '20px', 
            border: '2px solid #f3f4f6', 
            borderTop: '2px solid #3b82f6', 
            borderRadius: '50%', 
            animation: 'spin 1s linear infinite' 
          }}></div>
          <span>Loading tasks from Taskmaster API...</span>
        </div>
      </div>
    );
  }

  const filteredTasks = getFilteredTasks();

  return (
    <div>
      {/* Header with Create Button and View Toggle */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px' }}>
        <h2>✅ Tasks ({filteredTasks.length}/{tasks.length})</h2>
        <div style={{ display: 'flex', gap: '10px', alignItems: 'center' }}>
          {/* View Toggle */}
          <div style={{ display: 'flex', background: '#f3f4f6', borderRadius: '6px', padding: '2px' }}>
            <button
              onClick={() => setViewMode('list')}
              style={{
                padding: '6px 12px',
                background: viewMode === 'list' ? '#3b82f6' : 'transparent',
                color: viewMode === 'list' ? 'white' : '#6b7280',
                border: 'none',
                borderRadius: '4px',
                cursor: 'pointer',
                fontSize: '12px',
                fontWeight: 'bold',
                transition: 'all 0.2s'
              }}
            >
              📋 List
            </button>
            <button
              onClick={() => setViewMode('kanban')}
              style={{
                padding: '6px 12px',
                background: viewMode === 'kanban' ? '#3b82f6' : 'transparent',
                color: viewMode === 'kanban' ? 'white' : '#6b7280',
                border: 'none',
                borderRadius: '4px',
                cursor: 'pointer',
                fontSize: '12px',
                fontWeight: 'bold',
                transition: 'all 0.2s'
              }}
            >
              🎯 Kanban
            </button>
          </div>
          
          <button
            onClick={() => setShowCreateForm(!showCreateForm)}
            style={{
              padding: '10px 20px',
              background: '#10b981',
              color: 'white',
              border: 'none',
              borderRadius: '6px',
              cursor: 'pointer',
              fontWeight: 'bold'
            }}
          >
            {showCreateForm ? '✕ Cancel' : '+ Create Task'}
          </button>
          
          <button
            onClick={() => setBulkOperationMode(!bulkOperationMode)}
            style={{
              padding: '10px 20px',
              background: bulkOperationMode ? '#ef4444' : '#6366f1',
              color: 'white',
              border: 'none',
              borderRadius: '6px',
              cursor: 'pointer',
              fontWeight: 'bold'
            }}
          >
            {bulkOperationMode ? '✕ Exit Bulk' : '☑️ Bulk Select'}
          </button>
          
          <button
            onClick={() => setReorderMode(!reorderMode)}
            style={{
              padding: '10px 20px',
              background: reorderMode ? '#ef4444' : '#8b5cf6',
              color: 'white',
              border: 'none',
              borderRadius: '6px',
              cursor: 'pointer',
              fontWeight: 'bold'
            }}
          >
            {reorderMode ? '✕ Exit Reorder' : '↕️ Reorder Priority'}
          </button>
          
          <button
            onClick={() => setSubtaskMoveMode(!subtaskMoveMode)}
            style={{
              padding: '10px 20px',
              background: subtaskMoveMode ? '#ef4444' : '#ec4899',
              color: 'white',
              border: 'none',
              borderRadius: '6px',
              cursor: 'pointer',
              fontWeight: 'bold'
            }}
          >
            {subtaskMoveMode ? '✕ Exit Move' : '🔄 Move Subtasks'}
          </button>
        </div>
      </div>

      {/* Reorder Mode Info */}
      {reorderMode && (
        <div style={{
          background: '#f3e8ff',
          border: '2px solid #8b5cf6',
          borderRadius: '8px',
          padding: '15px',
          marginBottom: '20px'
        }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
            <span style={{ fontSize: '20px' }}>↕️</span>
            <div>
              <div style={{ fontWeight: 'bold', color: '#6b21a8', marginBottom: '5px' }}>
                Priority Reordering Mode Active
              </div>
              <div style={{ fontSize: '12px', color: '#7c3aed' }}>
                Drag tasks up/down within the same status to change their priority order. 
                Higher position = Higher priority. Only works in List view.
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Subtask Move Mode Info */}
      {subtaskMoveMode && (
        <div style={{
          background: '#fdf2f8',
          border: '2px solid #ec4899',
          borderRadius: '8px',
          padding: '15px',
          marginBottom: '20px'
        }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
            <span style={{ fontSize: '20px' }}>🔄</span>
            <div>
              <div style={{ fontWeight: 'bold', color: '#be185d', marginBottom: '5px' }}>
                Subtask Moving Mode Active
              </div>
              <div style={{ fontSize: '12px', color: '#ec4899' }}>
                Drag subtasks from their expanded parent sections and drop them onto different parent tasks 
                to move them between parents. Only works in List view.
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Bulk Operations Toolbar */}
      {bulkOperationMode && (
        <div style={{
          background: '#fef3c7',
          border: '2px solid #f59e0b',
          borderRadius: '8px',
          padding: '15px',
          marginBottom: '20px'
        }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '10px' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '15px' }}>
              <span style={{ fontWeight: 'bold', color: '#92400e' }}>
                ☑️ {selectedTasks.size} tasks selected
              </span>
              
              <div style={{ display: 'flex', gap: '8px' }}>
                <button
                  onClick={selectAllVisibleTasks}
                  style={{
                    padding: '6px 12px',
                    background: '#3b82f6',
                    color: 'white',
                    border: 'none',
                    borderRadius: '4px',
                    cursor: 'pointer',
                    fontSize: '12px'
                  }}
                >
                  Select All ({filteredTasks.length})
                </button>
                
                <button
                  onClick={clearSelection}
                  style={{
                    padding: '6px 12px',
                    background: '#6b7280',
                    color: 'white',
                    border: 'none',
                    borderRadius: '4px',
                    cursor: 'pointer',
                    fontSize: '12px'
                  }}
                >
                  Clear
                </button>
              </div>
            </div>
            
            {selectedTasks.size > 0 && (
              <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap' }}>
                {/* Status Updates */}
                <div style={{ display: 'flex', gap: '4px' }}>
                  <button onClick={() => bulkUpdateStatus('pending')} style={{ padding: '6px 8px', background: '#6b7280', color: 'white', border: 'none', borderRadius: '4px', cursor: 'pointer', fontSize: '11px' }}>
                    → Pending
                  </button>
                  <button onClick={() => bulkUpdateStatus('in-progress')} style={{ padding: '6px 8px', background: '#f59e0b', color: 'white', border: 'none', borderRadius: '4px', cursor: 'pointer', fontSize: '11px' }}>
                    → In Progress
                  </button>
                  <button onClick={() => bulkUpdateStatus('done')} style={{ padding: '6px 8px', background: '#10b981', color: 'white', border: 'none', borderRadius: '4px', cursor: 'pointer', fontSize: '11px' }}>
                    → Done
                  </button>
                  <button onClick={() => bulkUpdateStatus('blocked')} style={{ padding: '6px 8px', background: '#ef4444', color: 'white', border: 'none', borderRadius: '4px', cursor: 'pointer', fontSize: '11px' }}>
                    → Blocked
                  </button>
                </div>
                
                {/* Priority Updates */}
                <div style={{ display: 'flex', gap: '4px' }}>
                  <button onClick={() => bulkUpdatePriority('low')} style={{ padding: '6px 8px', background: '#10b981', color: 'white', border: 'none', borderRadius: '4px', cursor: 'pointer', fontSize: '11px' }}>
                    🟢 Low
                  </button>
                  <button onClick={() => bulkUpdatePriority('medium')} style={{ padding: '6px 8px', background: '#f59e0b', color: 'white', border: 'none', borderRadius: '4px', cursor: 'pointer', fontSize: '11px' }}>
                    🟡 Medium
                  </button>
                  <button onClick={() => bulkUpdatePriority('high')} style={{ padding: '6px 8px', background: '#ef4444', color: 'white', border: 'none', borderRadius: '4px', cursor: 'pointer', fontSize: '11px' }}>
                    🔴 High
                  </button>
                </div>
                
                {/* Tag Operations */}
                <div style={{ display: 'flex', gap: '4px', flexDirection: 'column' }}>
                  <div style={{ display: 'flex', gap: '4px' }}>
                    {availableTags.slice(0, 4).map(tag => (
                      <button
                        key={`add-${tag}`}
                        onClick={() => bulkAddTags([tag])}
                        style={{
                          padding: '4px 6px',
                          background: '#10b981',
                          color: 'white',
                          border: 'none',
                          borderRadius: '3px',
                          cursor: 'pointer',
                          fontSize: '10px'
                        }}
                        title={`Add "${tag}" tag to selected tasks`}
                      >
                        +{tag}
                      </button>
                    ))}
                  </div>
                  {availableTags.length > 4 && (
                    <div style={{ display: 'flex', gap: '4px' }}>
                      {availableTags.slice(4, 8).map(tag => (
                        <button
                          key={`add2-${tag}`}
                          onClick={() => bulkAddTags([tag])}
                          style={{
                            padding: '4px 6px',
                            background: '#10b981',
                            color: 'white',
                            border: 'none',
                            borderRadius: '3px',
                            cursor: 'pointer',
                            fontSize: '10px'
                          }}
                          title={`Add "${tag}" tag to selected tasks`}
                        >
                          +{tag}
                        </button>
                      ))}
                    </div>
                  )}
                  <div style={{ display: 'flex', gap: '4px' }}>
                    {availableTags.slice(0, 4).map(tag => (
                      <button
                        key={`remove-${tag}`}
                        onClick={() => bulkRemoveTags([tag])}
                        style={{
                          padding: '4px 6px',
                          background: '#ef4444',
                          color: 'white',
                          border: 'none',
                          borderRadius: '3px',
                          cursor: 'pointer',
                          fontSize: '10px'
                        }}
                        title={`Remove "${tag}" tag from selected tasks`}
                      >
                        -{tag}
                      </button>
                    ))}
                  </div>
                </div>
                
                {/* Delete */}
                <button
                  onClick={bulkDelete}
                  style={{
                    padding: '6px 12px',
                    background: '#dc2626',
                    color: 'white',
                    border: 'none',
                    borderRadius: '4px',
                    cursor: 'pointer',
                    fontSize: '11px',
                    fontWeight: 'bold'
                  }}
                >
                  🗑️ Delete ({selectedTasks.size})
                </button>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Progress Overview */}
      {progress && (
        <div style={{
          background: '#f0f9ff',
          border: '2px solid #0ea5e9',
          borderRadius: '8px',
          padding: '20px',
          marginBottom: '20px'
        }}>
          <h3 style={{ margin: '0 0 15px 0', color: '#0369a1' }}>📊 Project Progress</h3>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(100px, 1fr))', gap: '15px', marginBottom: '15px' }}>
            <div style={{ textAlign: 'center' }}>
              <div style={{ fontSize: '24px', fontWeight: 'bold', color: '#10b981' }}>{progress.completed_tasks}</div>
              <div style={{ fontSize: '12px', color: '#6b7280' }}>Completed</div>
            </div>
            <div style={{ textAlign: 'center' }}>
              <div style={{ fontSize: '24px', fontWeight: 'bold', color: '#f59e0b' }}>{progress.in_progress_tasks}</div>
              <div style={{ fontSize: '12px', color: '#6b7280' }}>In Progress</div>
            </div>
            <div style={{ textAlign: 'center' }}>
              <div style={{ fontSize: '24px', fontWeight: 'bold', color: '#6b7280' }}>{progress.pending_tasks}</div>
              <div style={{ fontSize: '12px', color: '#6b7280' }}>Pending</div>
            </div>
            <div style={{ textAlign: 'center' }}>
              <div style={{ fontSize: '24px', fontWeight: 'bold', color: '#ef4444' }}>{progress.overdue_tasks}</div>
              <div style={{ fontSize: '12px', color: '#6b7280' }}>🚨 Overdue</div>
            </div>
            <div style={{ textAlign: 'center' }}>
              <div style={{ fontSize: '24px', fontWeight: 'bold', color: '#3b82f6' }}>{progress.completion_percentage.toFixed(1)}%</div>
              <div style={{ fontSize: '12px', color: '#6b7280' }}>Complete</div>
            </div>
          </div>
          <div style={{ background: '#e5e7eb', borderRadius: '10px', height: '10px', overflow: 'hidden' }}>
            <div 
              style={{ 
                background: '#10b981', 
                height: '100%', 
                width: `${progress.completion_percentage}%`,
                transition: 'width 0.5s ease'
              }}
            ></div>
          </div>
        </div>
      )}

      {/* Next Recommended Task */}
      {nextTask && (
        <div style={{
          background: '#fef3c7',
          border: '2px solid #f59e0b',
          borderRadius: '8px',
          padding: '15px',
          marginBottom: '20px'
        }}>
          <h3 style={{ margin: '0 0 10px 0', color: '#92400e' }}>⭐ Next Recommended Task</h3>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <div>
              <strong style={{ color: '#92400e' }}>{nextTask.title}</strong>
              <p style={{ margin: '5px 0 0 0', fontSize: '14px', color: '#78350f' }}>{nextTask.description}</p>
            </div>
            <button
              onClick={() => updateTaskStatus(nextTask.id, 'in-progress')}
              style={{
                padding: '8px 16px',
                background: '#f59e0b',
                color: 'white',
                border: 'none',
                borderRadius: '4px',
                cursor: 'pointer',
                fontWeight: 'bold'
              }}
            >
              🚀 Start Task
            </button>
          </div>
        </div>
      )}

      {/* Filters */}
      <div style={{
        background: '#f9fafb',
        border: '1px solid #e5e7eb',
        borderRadius: '8px',
        padding: '15px',
        marginBottom: '20px'
      }}>
        <h3 style={{ margin: '0 0 10px 0' }}>🔍 Filter Tasks</h3>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(150px, 1fr))', gap: '10px' }}>
          <select
            value={filter.status}
            onChange={(e) => setFilter(prev => ({ ...prev, status: e.target.value }))}
            style={{ padding: '8px', border: '1px solid #d1d5db', borderRadius: '4px' }}
          >
            <option value="all">All Status</option>
            <option value="pending">Pending</option>
            <option value="in-progress">In Progress</option>
            <option value="done">Done</option>
            <option value="blocked">Blocked</option>
          </select>
          
          <select
            value={filter.priority}
            onChange={(e) => setFilter(prev => ({ ...prev, priority: e.target.value }))}
            style={{ padding: '8px', border: '1px solid #d1d5db', borderRadius: '4px' }}
          >
            <option value="all">All Priorities</option>
            <option value="high">High Priority</option>
            <option value="medium">Medium Priority</option>
            <option value="low">Low Priority</option>
          </select>

          <select
            value={filter.workspace}
            onChange={(e) => setFilter(prev => ({ ...prev, workspace: e.target.value }))}
            style={{ padding: '8px', border: '1px solid #d1d5db', borderRadius: '4px' }}
          >
            <option value="all">All Workspaces</option>
            <option value="1">Personal</option>
            <option value="2">Work</option>
            <option value="3">Projects</option>
          </select>

          <select
            value={filter.tag}
            onChange={(e) => setFilter(prev => ({ ...prev, tag: e.target.value }))}
            style={{ padding: '8px', border: '1px solid #d1d5db', borderRadius: '4px' }}
          >
            <option value="all">All Tags</option>
            {availableTags.map(tag => (
              <option key={tag} value={tag}>🏷️ {tag}</option>
            ))}
          </select>

          <button
            onClick={() => setFilter({ status: 'all', priority: 'all', workspace: 'all', tag: 'all' })}
            style={{
              padding: '8px 12px',
              background: '#6b7280',
              color: 'white',
              border: 'none',
              borderRadius: '4px',
              cursor: 'pointer'
            }}
          >
            Clear Filters
          </button>
        </div>
      </div>

      {/* Create Task Form */}
      {showCreateForm && (
        <div style={{
          background: '#f0fdf4',
          border: '2px solid #22c55e',
          borderRadius: '8px',
          padding: '20px',
          marginBottom: '20px'
        }}>
          <h3>{showSubtaskForm ? `Create New Subtask for Task: ${tasks.find(t => t.id === showSubtaskForm)?.title}` : 'Create New Task'}</h3>
          <div style={{ display: 'grid', gap: '15px' }}>
            <div>
              <label style={{ display: 'block', marginBottom: '5px', fontWeight: 'bold' }}>
                Task Title *
              </label>
              <input
                type="text"
                value={newTask.title}
                onChange={(e) => setNewTask(prev => ({ ...prev, title: e.target.value }))}
                placeholder="Enter task title..."
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
                value={newTask.description}
                onChange={(e) => setNewTask(prev => ({ ...prev, description: e.target.value }))}
                placeholder="Describe the task..."
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

            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: '15px' }}>
              <div>
                <label style={{ display: 'block', marginBottom: '5px', fontWeight: 'bold' }}>
                  Priority
                </label>
                <select
                  value={newTask.priority}
                  onChange={(e) => setNewTask(prev => ({ ...prev, priority: e.target.value as 'low' | 'medium' | 'high' }))}
                  style={{ width: '100%', padding: '8px', border: '1px solid #d1d5db', borderRadius: '4px' }}
                >
                  <option value="low">🟢 Low</option>
                  <option value="medium">🟡 Medium</option>
                  <option value="high">🔴 High</option>
                </select>
              </div>

              <div>
                <label style={{ display: 'block', marginBottom: '5px', fontWeight: 'bold' }}>
                  Workspace
                </label>
                <select
                  value={newTask.workspace_id}
                  onChange={(e) => setNewTask(prev => ({ ...prev, workspace_id: parseInt(e.target.value) }))}
                  style={{ width: '100%', padding: '8px', border: '1px solid #d1d5db', borderRadius: '4px' }}
                >
                  <option value={1}>Personal</option>
                  <option value={2}>Work</option>
                  <option value={3}>Projects</option>
                </select>
              </div>

              <div>
                <label style={{ display: 'block', marginBottom: '5px', fontWeight: 'bold' }}>
                  📅 Due Date
                </label>
                <input
                  type="datetime-local"
                  value={newTask.due_date}
                  onChange={(e) => setNewTask(prev => ({ ...prev, due_date: e.target.value }))}
                  style={{
                    width: '100%',
                    padding: '8px',
                    border: '1px solid #d1d5db',
                    borderRadius: '4px',
                    fontSize: '14px'
                  }}
                />
              </div>
            </div>

            {/* Tags Section */}
            <div>
              <label style={{ display: 'block', marginBottom: '5px', fontWeight: 'bold' }}>
                🏷️ Tags
              </label>
              
              {/* Selected Tags */}
              {newTask.tags.length > 0 && (
                <div style={{ marginBottom: '10px' }}>
                  <div style={{ display: 'flex', flexWrap: 'wrap', gap: '6px' }}>
                    {newTask.tags.map(tag => (
                      <span
                        key={tag}
                        style={{
                          display: 'inline-flex',
                          alignItems: 'center',
                          gap: '4px',
                          padding: '4px 8px',
                          background: getTagColor(tag),
                          color: 'white',
                          borderRadius: '12px',
                          fontSize: '12px',
                          fontWeight: 'bold'
                        }}
                      >
                        {tag}
                        <button
                          onClick={() => removeTagFromTask(tag)}
                          style={{
                            background: 'none',
                            border: 'none',
                            color: 'white',
                            cursor: 'pointer',
                            padding: '0',
                            fontSize: '12px'
                          }}
                        >
                          ✕
                        </button>
                      </span>
                    ))}
                  </div>
                </div>
              )}
              
              {/* Available Tags */}
              <div style={{ display: 'flex', flexWrap: 'wrap', gap: '6px' }}>
                {availableTags.filter(tag => !newTask.tags.includes(tag)).map(tag => (
                  <button
                    key={tag}
                    onClick={() => addTagToTask(tag)}
                    style={{
                      padding: '4px 8px',
                      background: '#f3f4f6',
                      border: `1px solid ${getTagColor(tag)}40`,
                      borderRadius: '12px',
                      fontSize: '12px',
                      color: getTagColor(tag),
                      cursor: 'pointer',
                      transition: 'all 0.2s'
                    }}
                    onMouseEnter={(e) => {
                      e.currentTarget.style.background = `${getTagColor(tag)}15`;
                    }}
                    onMouseLeave={(e) => {
                      e.currentTarget.style.background = '#f3f4f6';
                    }}
                  >
                    + {tag}
                  </button>
                ))}
              </div>
            </div>

            <div style={{ display: 'flex', gap: '10px' }}>
              <button
                onClick={createTask}
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
                ✓ Create Task
              </button>
              <button
                onClick={() => {
                  setShowCreateForm(false);
                  setShowSubtaskForm(null);
                  setNewTask({ title: '', description: '', priority: 'medium', workspace_id: 1, due_date: '', tags: [], parent_task_id: undefined });
                }}
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

      {/* Tasks Display - List vs Kanban View */}
      {viewMode === 'list' ? (
        /* List View */
        <div style={{ display: 'grid', gap: '15px' }}>
          {filteredTasks
            .sort((a, b) => {
              if (reorderMode) {
                // Sort by priority when in reorder mode to show current order
                const priorityOrder = { 'high': 0, 'medium': 1, 'low': 2 };
                return priorityOrder[a.priority] - priorityOrder[b.priority];
              }
              return 0;
            })
            .map(task => (
              <TaskCard 
                key={task.id} 
                task={task} 
                isDraggable={false} 
                showCheckbox={bulkOperationMode}
                isReorderable={reorderMode && viewMode === 'list'}
              />
            ))}
        </div>
      ) : (
        /* Kanban Board View */
        <div>
          {/* Kanban Instructions */}
          <div style={{
            background: '#e0f2fe',
            border: '1px solid #0891b2',
            borderRadius: '8px',
            padding: '12px',
            marginBottom: '20px',
            textAlign: 'center'
          }}>
            <span style={{ fontSize: '14px', color: '#0e7490', fontWeight: 'bold' }}>
              🎯 Drag & Drop Mode: Drag tasks between columns to change their status
            </span>
          </div>
          
          <div style={{ 
            display: 'grid', 
            gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', 
            gap: '20px'
          }}>
          {(['pending', 'in-progress', 'done', 'blocked'] as const).map(status => {
            const columnTasks = getTasksByStatus(status);
            const colors = getColumnColor(status);
            const isDropTarget = dragOverColumn === status;
            
            return (
              <div
                key={status}
                style={{
                  background: colors.bg,
                  border: `2px solid ${isDropTarget ? colors.border : '#e5e7eb'}`,
                  borderRadius: '12px',
                  padding: '15px',
                  minHeight: '500px',
                  transition: 'all 0.2s ease',
                  transform: isDropTarget ? 'scale(1.02)' : 'scale(1)',
                  boxShadow: isDropTarget ? '0 8px 24px rgba(0,0,0,0.15)' : '0 2px 8px rgba(0,0,0,0.1)'
                }}
                onDragOver={(e) => handleDragOver(e, status)}
                onDragLeave={handleDragLeave}
                onDrop={(e) => handleDrop(e, status)}
              >
                {/* Column Header */}
                <div style={{ 
                  marginBottom: '15px',
                  textAlign: 'center',
                  padding: '10px',
                  background: 'white',
                  borderRadius: '8px',
                  border: `2px solid ${colors.border}`
                }}>
                  <h3 style={{ 
                    margin: 0, 
                    color: colors.text,
                    fontSize: '16px',
                    fontWeight: 'bold',
                    textTransform: 'capitalize'
                  }}>
                    {status === 'in-progress' ? '🔄 In Progress' : 
                     status === 'pending' ? '⏳ Pending' :
                     status === 'done' ? '✅ Done' : '🚫 Blocked'}
                  </h3>
                  <div style={{ 
                    fontSize: '12px', 
                    color: colors.text,
                    opacity: 0.7,
                    marginTop: '4px'
                  }}>
                    {columnTasks.length} {columnTasks.length === 1 ? 'task' : 'tasks'}
                  </div>
                </div>

                {/* Task Cards */}
                <div style={{ 
                  display: 'flex', 
                  flexDirection: 'column',
                  gap: '12px'
                }}>
                  {columnTasks.map(task => (
                    <TaskCard key={task.id} task={task} isDraggable={true} showCheckbox={bulkOperationMode} />
                  ))}
                  
                  {/* Drop Zone Indicator */}
                  {columnTasks.length === 0 && (
                    <div style={{
                      padding: '40px 20px',
                      border: '2px dashed #d1d5db',
                      borderRadius: '8px',
                      textAlign: 'center',
                      color: '#9ca3af',
                      fontSize: '14px',
                      fontStyle: 'italic'
                    }}>
                      Drop tasks here
                    </div>
                  )}
                </div>
              </div>
            );
          })}
          </div>
        </div>
      )}

      {filteredTasks.length === 0 && !loading && (
        <div style={{
          textAlign: 'center',
          padding: '40px',
          background: '#f9fafb',
          borderRadius: '8px',
          border: '2px dashed #d1d5db'
        }}>
          <h3 style={{ color: '#6b7280', margin: '0 0 10px 0' }}>
            {tasks.length === 0 ? 'No tasks yet' : 'No tasks match your filters'}
          </h3>
          <p style={{ color: '#9ca3af', margin: '0 0 15px 0' }}>
            {tasks.length === 0 
              ? 'Create your first task to start organizing your work!'
              : 'Try adjusting your filters or create a new task.'
            }
          </p>
          <button
            onClick={() => setShowCreateForm(true)}
            style={{
              padding: '10px 20px',
              background: '#10b981',
              color: 'white',
              border: 'none',
              borderRadius: '6px',
              cursor: 'pointer',
              fontWeight: 'bold'
            }}
          >
            + Create Your First Task
          </button>
        </div>
      )}
    </div>
  );
};

const SimpleApp: React.FC = () => {
  const [currentView, setCurrentView] = useState('dashboard');
  const errorHandler = useErrorHandler();

  // Show welcome message when app starts
  useEffect(() => {
    errorHandler.addError('OrdnungsHub loaded successfully!', 'info', 'Application initialized and ready to use');
  }, []);

  const handleSearchResult = (result: SearchResult) => {
    if (result.type === 'task') {
      setCurrentView('tasks');
      errorHandler.addError(`Found task: ${result.title}`, 'info', `Navigated to Tasks tab`);
    } else if (result.type === 'workspace') {
      setCurrentView('workspaces');
      errorHandler.addError(`Found workspace: ${result.title}`, 'info', `Navigated to Workspaces tab`);
    }
  };

  const renderView = () => {
    switch (currentView) {
      case 'dashboard':
        return <Dashboard errorHandler={errorHandler} />;
      case 'workspaces':
        return <Workspaces errorHandler={errorHandler} />;
      case 'tasks':
        return <Tasks errorHandler={errorHandler} />;
      case 'test':
        return <ApiTest errorHandler={errorHandler} />;
      case 'errors':
        return <ErrorDashboard errorHandler={errorHandler} />;
      default:
        return <Dashboard errorHandler={errorHandler} />;
    }
  };

  return (
    <div style={{ padding: '20px', fontFamily: 'Arial, sans-serif', maxWidth: '1200px', margin: '0 auto' }}>
      <h1 style={{ color: '#2563eb', marginBottom: '10px' }}>🚀 OrdnungsHub</h1>
      <p style={{ color: '#6b7280', marginBottom: '20px' }}>AI-Powered System Organizer - Progressive Build with Search</p>
      
      <Navigation 
        currentView={currentView} 
        onViewChange={setCurrentView}
        onSearchResult={handleSearchResult}
        errorHandler={errorHandler}
      />
      
      <main>
        {renderView()}
      </main>

      {/* Error Toast Notifications */}
      {errorHandler.errors.map((error) => (
        <ErrorToast 
          key={error.id} 
          error={error} 
          onDismiss={errorHandler.dismissError} 
        />
      ))}
    </div>
  );
};

export default SimpleApp;