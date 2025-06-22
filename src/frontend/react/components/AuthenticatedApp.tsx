import React, { Suspense } from 'react';
import { LazyLayout, LazyErrorDashboard, LazyPerformanceDashboard } from './LazyComponents';
import LoadingSkeleton from './LoadingSkeleton/LoadingSkeleton';
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
    <Suspense fallback={<LoadingSkeleton />}>
      <LazyLayout />
      <LazyErrorDashboard />
      <LazyPerformanceDashboard />
    </Suspense>
  );
};

export default AuthenticatedApp;