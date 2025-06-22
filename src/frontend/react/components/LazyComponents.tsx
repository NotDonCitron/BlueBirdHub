import { lazy, Suspense } from 'react';
import React from 'react';

// Loading component
const LoadingFallback = () => (
  <div className="loading-container">
    <div className="loading-spinner"></div>
    <p>Loading component...</p>
  </div>
);

// Lazy load major components
export const WorkspaceManager = lazy(() => 
  import(/* webpackChunkName: "workspace-manager" */ './WorkspaceManager')
);

export const TaskManager = lazy(() => 
  import(/* webpackChunkName: "task-manager" */ './TaskManager')
);

export const FileManager = lazy(() => 
  import(/* webpackChunkName: "file-manager" */ './FileManager')
);

export const Dashboard = lazy(() => 
  import(/* webpackChunkName: "dashboard" */ './Dashboard')
);

export const SmartSearch = lazy(() => 
  import(/* webpackChunkName: "smart-search" */ './SmartSearch')
);

export const AIAssistant = lazy(() => 
  import(/* webpackChunkName: "ai-assistant" */ './AIAssistant')
);

export const AutomationCenter = lazy(() => 
  import(/* webpackChunkName: "automation-center" */ './AutomationCenter')
);

// Wrapper component with Suspense
export const withLazyLoading = (Component: React.LazyExoticComponent<any>) => {
  return (props: any) => (
    <Suspense fallback={<LoadingFallback />}>
      <Component {...props} />
    </Suspense>
  );
};

// Preload critical components
export const preloadCriticalComponents = () => {
  // Preload workspace and task managers as they're commonly used
  import(/* webpackChunkName: "workspace-manager" */ './WorkspaceManager');
  import(/* webpackChunkName: "task-manager" */ './TaskManager');
};

// Export wrapped components for easy use
export const LazyWorkspaceManager = withLazyLoading(WorkspaceManager);
export const LazyTaskManager = withLazyLoading(TaskManager);
export const LazyFileManager = withLazyLoading(FileManager);
export const LazyDashboard = withLazyLoading(Dashboard);
export const LazySmartSearch = withLazyLoading(SmartSearch);
export const LazyAIAssistant = withLazyLoading(AIAssistant);
export const LazyAutomationCenter = withLazyLoading(AutomationCenter);