import React, { useState, useEffect } from 'react';
import { BrowserRouter as Router } from 'react-router-dom';
import Layout from './components/Layout/Layout';
import { ThemeProvider } from './contexts/ThemeContext';
import { ApiProvider } from './contexts/ApiContext';
import './styles/App.css';

const App: React.FC = () => {
  const [isLoading, setIsLoading] = useState(true);
  const [apiStatus, setApiStatus] = useState<'connected' | 'disconnected' | 'checking'>('checking');

  useEffect(() => {
    // Check API connection on startup
    checkApiConnection();
  }, []);

  const checkApiConnection = async () => {
    try {
      // Add global object for browser compatibility
  (window as any).global = window;
  
  // Check if we're running in Electron
  if ((window as any).electronAPI) {
        const response = await (window as any).electronAPI.apiRequest('/', 'GET');
        if (response.status === 'running') {
          setApiStatus('connected');
        } else {
          setApiStatus('disconnected');
        }
      } else {
        // Fallback for development in browser
        const response = await fetch('http://127.0.0.1:8001/');
        const data = await response.json();
        if (data.status === 'running') {
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

  if (isLoading) {
    return (
      <div className="app-loading">
        <div className="loading-spinner"></div>
        <p>Initializing OrdnungsHub...</p>
      </div>
    );
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

export default App;