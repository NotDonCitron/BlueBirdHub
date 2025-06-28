import React, { useState, useEffect } from 'react';
import { BrowserRouter as Router } from 'react-router-dom';
import Layout from '../components/Layout/Layout';
import { ThemeProvider } from '../contexts/ThemeContext';
import { ApiProvider } from '../contexts/ApiContext';
import { AuthProvider, useAuth } from '../contexts/AuthContext';
import '../styles/App.css';

const LoginComponent: React.FC = () => {
  const { loginWithCredentials, isLoading } = useAuth();
  const [credentials, setCredentials] = useState({ username: 'admin', password: 'admin123' });

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    await loginWithCredentials(credentials.username, credentials.password);
  };

  return (
    <div className="login-container" style={{ 
      display: 'flex', 
      justifyContent: 'center', 
      alignItems: 'center', 
      height: '100vh',
      backgroundColor: '#f5f5f5'
    }}>
      <div style={{ 
        background: 'white', 
        padding: '2rem', 
        borderRadius: '8px', 
        boxShadow: '0 2px 10px rgba(0,0,0,0.1)',
        minWidth: '300px'
      }}>
        <h2 style={{ textAlign: 'center', marginBottom: '1.5rem' }}>OrdnungsHub Login</h2>
        <form onSubmit={handleLogin}>
          <div style={{ marginBottom: '1rem' }}>
            <input
              type="text"
              placeholder="Username"
              value={credentials.username}
              onChange={(e) => setCredentials({...credentials, username: e.target.value})}
              style={{ 
                width: '100%', 
                padding: '0.5rem', 
                border: '1px solid #ddd', 
                borderRadius: '4px',
                boxSizing: 'border-box'
              }}
            />
          </div>
          <div style={{ marginBottom: '1.5rem' }}>
            <input
              type="password"
              placeholder="Password"
              value={credentials.password}
              onChange={(e) => setCredentials({...credentials, password: e.target.value})}
              style={{ 
                width: '100%', 
                padding: '0.5rem', 
                border: '1px solid #ddd', 
                borderRadius: '4px',
                boxSizing: 'border-box'
              }}
            />
          </div>
          <button
            type="submit"
            disabled={isLoading}
            style={{ 
              width: '100%', 
              padding: '0.75rem', 
              backgroundColor: '#007bff', 
              color: 'white', 
              border: 'none', 
              borderRadius: '4px',
              cursor: 'pointer',
              fontSize: '1rem'
            }}
          >
            {isLoading ? 'Logging in...' : 'Login'}
          </button>
        </form>
        <div style={{ 
          textAlign: 'center', 
          marginTop: '1rem', 
          fontSize: '0.9rem', 
          color: '#666' 
        }}>
          <p><strong>Default credentials:</strong></p>
          <p>Username: <code>admin</code><br/>Password: <code>admin123</code></p>
          <p>Or username: <code>demo</code> with password: <code>demo</code></p>
        </div>
      </div>
    </div>
  );
};

const AppContent: React.FC = () => {
  const [isLoading, setIsLoading] = useState(true);
  const [apiStatus, setApiStatus] = useState<'connected' | 'disconnected' | 'checking'>('checking');
  const { isAuthenticated, isLoading: authLoading } = useAuth();

  useEffect(() => {
    // Check API connection on startup
    checkApiConnection();
  }, []);

  const checkApiConnection = async () => {
    try {
      // Add global object for browser compatibility
      (window as any).global = window;
      
      // Check if we're running in Electron
      if (window.electronAPI) {
        const response = await window.electronAPI.apiRequest('/', 'GET');
        if (response.status === 'running') {
          setApiStatus('connected');
        } else {
          setApiStatus('disconnected');
        }
      } else {
        // Use localhost instead of 127.0.0.1 for Docker compatibility
        const response = await fetch('http://localhost:8000/health');
        const data = await response.json();
        if (data.status === 'healthy') {
          setApiStatus('connected');
        } else {
          setApiStatus('disconnected');
        }
      }
    } catch (error) {
      console.error('Failed to connect to API:', error);
      setApiStatus('disconnected');
    } finally {
      setIsLoading(false);
    }
  };

  if (authLoading || isLoading) {
    return (
      <div className="app-loading">
        <div className="loading-spinner"></div>
        <p>Initializing OrdnungsHub...</p>
      </div>
    );
  }

  if (!isAuthenticated) {
    return <LoginComponent />;
  }

  return (
    <Router>
      <ThemeProvider>
        <ApiProvider apiStatus={apiStatus} onRetryConnection={checkApiConnection}>
          <div className="app">
            <Layout />
          </div>
        </ApiProvider>
      </ThemeProvider>
    </Router>
  );
};

const App: React.FC = () => {
  return (
    <AuthProvider>
      <AppContent />
    </AuthProvider>
  );
};

export default App;