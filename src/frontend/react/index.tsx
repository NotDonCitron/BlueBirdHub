import React from 'react';
import { createRoot } from 'react-dom/client';
import './utils/consoleFilter'; // Apply console filtering for browser extensions
import ErrorBoundary from './components/ErrorBoundary';
import './styles/global.css';

// Import the full app with error boundary protection
const SimpleApp = React.lazy(() => import('./SimpleApp'));

// Loading component
const LoadingScreen: React.FC = () => (
  <div style={{ 
    display: 'flex', 
    justifyContent: 'center', 
    alignItems: 'center', 
    height: '100vh',
    backgroundColor: '#f0f0f0',
    fontFamily: 'Arial, sans-serif'
  }}>
    <div style={{ textAlign: 'center' }}>
      <div style={{ 
        fontSize: '48px', 
        marginBottom: '20px',
        animation: 'spin 2s linear infinite'
      }}>
        🧠
      </div>
      <h2 style={{ color: '#4a9eff', marginBottom: '10px' }}>Loading BlueBirdHub...</h2>
      <p style={{ color: '#666' }}>Initializing AI Agent System</p>
      <style dangerouslySetInnerHTML={{
        __html: `
          @keyframes spin {
            from { transform: rotate(0deg); }
            to { transform: rotate(360deg); }
          }
        `
      }} />
    </div>
  </div>
);

// Main App Component with Suspense
const App: React.FC = () => (
  <ErrorBoundary>
    <React.Suspense fallback={<LoadingScreen />}>
      <SimpleApp />
    </React.Suspense>
  </ErrorBoundary>
);

// Get the root element
const container = document.getElementById('root');
if (!container) {
  throw new Error('Failed to find the root element');
}

// Create root and render app
const root = createRoot(container);
root.render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
);