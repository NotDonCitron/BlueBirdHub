import { lazy } from 'react';

// Lazy load heavy components to improve initial bundle size
export const LazyWorkspaceList = lazy(() => import('./WorkspaceList'));
export const LazyTaskList = lazy(() => import('./TaskList'));
export const LazyAIChat = lazy(() => import('./AIChat'));
export const LazyAutomationCenter = lazy(() => import('./AutomationCenter'));
export const LazyCollaborationHub = lazy(() => import('./CollaborationHub'));
export const LazySmartSearch = lazy(() => import('./SmartSearch'));
export const LazySettings = lazy(() => import('./Settings'));
export const LazyDashboard = lazy(() => import('./Dashboard'));

// Preload components on idle for better UX
export const preloadComponents = () => {
  if ('requestIdleCallback' in window) {
    requestIdleCallback(() => {
      import('./WorkspaceList');
      import('./TaskList');
    });
    
    requestIdleCallback(() => {
      import('./AIChat');
      import('./Settings');
    });
  }
};