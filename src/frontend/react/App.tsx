import React, { useState, useEffect, useCallback } from 'react';
import { BrowserRouter as Router } from 'react-router-dom';
import AuthenticatedApp from './components/AuthenticatedApp';
import ErrorBoundary from './components/ErrorBoundary';
import { ThemeProvider } from './contexts/ThemeContext';
import { ApiProvider } from './contexts/ApiContext';
import { AuthProvider } from './contexts/AuthContext';
import { performanceMonitor } from './utils/performanceMonitor';
import { resourcePreloader } from './utils/resourcePreloader';
import { preloadCriticalComponents } from './components/LazyComponents';
import './styles/App.css';

const App: React.FC = () => {
  const [isLoading, setIsLoading] = useState(true);
  const [apiStatus, setApiStatus] = useState<'connected' | 'disconnected' | 'checking'>('checking');

  const initializeApp = useCallback(async () => {
    // Start performance monitoring
    performanceMonitor.startContinuousMonitoring();
    
    // Preload critical resources
    const resourceResults = await resourcePreloader.preloadCriticalResources();
    console.log('Resource preload results:', resourceResults);
    
    // Preload critical components
    preloadCriticalComponents();
    
    // Check API connection
    await checkApiConnection();
  }, []);

  useEffect(() => {
    initializeApp();
    
    return () => {
      performanceMonitor.dispose();
    };
  }, [initializeApp]);

  const checkApiConnection = useCallback(async () => {
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
        const response = await fetch('http://127.0.0.1:8000/');
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
  }, []);

  if (isLoading) {
    return (
      <div className="app-loading">
        <div className="loading-spinner"></div>
        <p>Initializing OrdnungsHub...</p>
      </div>
    );
  }

  return (
    <ErrorBoundary>
      <Router>
        <ThemeProvider>
          <ApiProvider apiStatus={apiStatus} onRetryConnection={checkApiConnection}>
            <AuthProvider>
              <div className="app">
                <AuthenticatedApp />
              </div>
            </AuthProvider>
          </ApiProvider>
        </ThemeProvider>
      </Router>
    </ErrorBoundary>
  );
};

export default App;