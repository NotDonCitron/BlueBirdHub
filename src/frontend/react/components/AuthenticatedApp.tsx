import React, { Suspense } from 'react';
import { WorkspaceManager, TaskManager } from './LazyComponents';
import LoadingSkeleton from './LoadingSkeleton/LoadingSkeleton';
import VoiceCommandManager from './VoiceCommands/VoiceCommandManager';
import { useAuth } from '../contexts/AuthContext';
import Login from './Login/Login';

const AuthenticatedApp: React.FC = () => {
  const { isAuthenticated, isLoading, login } = useAuth();

  if (isLoading) {
    return (
      <div className="app-loading">
        <div className="loading-spinner"></div>
        <p>Loading...</p>
      </div>
    );
  }

  if (!isAuthenticated) {
    return <Login onLogin={login} />;
  }

  return (
    <div data-testid="authenticated-app">
      <Suspense fallback={<LoadingSkeleton />}>
        <WorkspaceManager />
        <TaskManager />
      </Suspense>
      <VoiceCommandManager />
    </div>
  );
};

export default AuthenticatedApp;