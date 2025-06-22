import React, { useState, useEffect, useCallback, useMemo, memo } from 'react';
import { useApi } from '../../contexts/ApiContext';
import { useRenderTime } from '../../utils/performanceMonitor';
import './Dashboard.css';

interface DashboardStats {
  totalTasks: number;
  completedTasks: number;
  activeWorkspaces: number;
  totalFiles: number;
}

interface StatCardProps {
  icon: string;
  value: number;
  label: string;
}

interface ActivityItemProps {
  icon: string;
  text: string;
  time: string;
}

interface ActionCardProps {
  icon: string;
  label: string;
  onClick?: () => void;
}

// Memoized components to prevent unnecessary re-renders
const StatCard = memo<StatCardProps>(({ icon, value, label }) => (
  <div className="stat-card">
    <div className="stat-icon">{icon}</div>
    <div className="stat-content">
      <div className="stat-value">{value}</div>
      <div className="stat-label">{label}</div>
    </div>
  </div>
));

StatCard.displayName = 'StatCard';

const ActivityItem = memo<ActivityItemProps>(({ icon, text, time }) => (
  <div className="activity-item">
    <div className="activity-icon">{icon}</div>
    <div className="activity-content">
      <div className="activity-text">{text}</div>
      <div className="activity-time">{time}</div>
    </div>
  </div>
));

ActivityItem.displayName = 'ActivityItem';

const ActionCard = memo<ActionCardProps>(({ icon, label, onClick }) => (
  <button className="action-card" onClick={onClick}>
    <div className="action-icon">{icon}</div>
    <div className="action-label">{label}</div>
  </button>
));

ActionCard.displayName = 'ActionCard';

// Progress bar component with optimized rendering
const ProgressBar = memo<{ completed: number; total: number }>(({ completed, total }) => {
  const percentage = useMemo(() => {
    if (total === 0) return 0;
    return Math.round((completed / total) * 100);
  }, [completed, total]);

  return (
    <div className="progress-card">
      <div className="progress-header">
        <span>Overall Completion</span>
        <span className="progress-percentage">{percentage}%</span>
      </div>
      <div className="progress-bar">
        <div 
          className="progress-fill"
          style={{ width: `${percentage}%` }}
        />
      </div>
      <div className="progress-details">
        {completed} of {total} tasks completed
      </div>
    </div>
  );
});

ProgressBar.displayName = 'ProgressBar';

const OptimizedDashboard: React.FC = () => {
  // Performance monitoring
  useRenderTime('OptimizedDashboard');

  const [stats, setStats] = useState<DashboardStats>({
    totalTasks: 0,
    completedTasks: 0,
    activeWorkspaces: 0,
    totalFiles: 0,
  });
  const [loading, setLoading] = useState(true);
  const { apiStatus, makeApiRequest } = useApi();

  // Memoized callback to prevent recreation on every render
  const loadDashboardData = useCallback(async () => {
    try {
      setLoading(true);
      
      // Try to load real data from the API
      if (makeApiRequest) {
        try {
          const response = await makeApiRequest('/dashboard/stats');
          if (response.success && response.stats) {
            setStats({
              totalTasks: response.stats.total_tasks,
              completedTasks: response.stats.completed_tasks,
              activeWorkspaces: response.stats.active_workspaces,
              totalFiles: response.stats.total_files,
            });
            return;
          }
        } catch (apiError) {
          console.warn('API request failed, using mock data:', apiError);
        }
      }
      
      // Fallback to mock data if API is unavailable
      setStats({
        totalTasks: 15,
        completedTasks: 8,
        activeWorkspaces: 3,
        totalFiles: 247,
      });
    } catch (error) {
      console.error('Failed to load dashboard data:', error);
      // Use minimal fallback data
      setStats({
        totalTasks: 0,
        completedTasks: 0,
        activeWorkspaces: 0,
        totalFiles: 0,
      });
    } finally {
      setLoading(false);
    }
  }, [makeApiRequest]);

  useEffect(() => {
    if (apiStatus === 'connected') {
      loadDashboardData();
    }
  }, [apiStatus, loadDashboardData]);

  // Memoized stat cards to prevent recreation
  const statCards = useMemo(() => [
    { icon: '✅', value: stats.totalTasks, label: 'Total Tasks' },
    { icon: '🎯', value: stats.completedTasks, label: 'Completed' },
    { icon: '🏠', value: stats.activeWorkspaces, label: 'Workspaces' },
    { icon: '📁', value: stats.totalFiles, label: 'Files Indexed' },
  ], [stats]);

  // Memoized activity items
  const activityItems = useMemo(() => [
    { icon: '✅', text: 'Completed task "Review project proposal"', time: '2 hours ago' },
    { icon: '🏠', text: 'Created new workspace "Marketing Campaign"', time: 'Yesterday' },
    { icon: '📁', text: 'Organized 15 files in Documents folder', time: '2 days ago' },
  ], []);

  // Memoized action handlers
  const handleNewTask = useCallback(() => {
    console.log('Navigate to new task');
  }, []);

  const handleNewWorkspace = useCallback(() => {
    console.log('Navigate to new workspace');
  }, []);

  const handleAnalytics = useCallback(() => {
    console.log('Navigate to analytics');
  }, []);

  const handleAIAssistant = useCallback(() => {
    console.log('Open AI assistant');
  }, []);

  const actionCards = useMemo(() => [
    { icon: '➕', label: 'New Task', onClick: handleNewTask },
    { icon: '🏠', label: 'New Workspace', onClick: handleNewWorkspace },
    { icon: '📊', label: 'Analytics', onClick: handleAnalytics },
    { icon: '🤖', label: 'AI Assistant', onClick: handleAIAssistant },
  ], [handleNewTask, handleNewWorkspace, handleAnalytics, handleAIAssistant]);

  if (loading) {
    return (
      <div className="dashboard-loading">
        <div className="loading-spinner"></div>
        <p>Loading dashboard...</p>
      </div>
    );
  }

  return (
    <div className="dashboard">
      <div className="dashboard-header">
        <h2>Welcome to OrdnungsHub</h2>
        <p>Your AI-powered system organizer is ready to help you stay productive.</p>
      </div>

      <div className="dashboard-stats">
        {statCards.map((card, index) => (
          <StatCard
            key={`${card.label}-${index}`}
            icon={card.icon}
            value={card.value}
            label={card.label}
          />
        ))}
      </div>

      <div className="dashboard-content">
        <div className="dashboard-section">
          <h3>Task Progress</h3>
          <ProgressBar 
            completed={stats.completedTasks} 
            total={stats.totalTasks} 
          />
        </div>

        <div className="dashboard-section">
          <h3>Quick Actions</h3>
          <div className="quick-actions">
            {actionCards.map((action, index) => (
              <ActionCard
                key={`${action.label}-${index}`}
                icon={action.icon}
                label={action.label}
                onClick={action.onClick}
              />
            ))}
          </div>
        </div>

        <div className="dashboard-section">
          <h3>Recent Activity</h3>
          <div className="activity-list">
            {activityItems.map((item, index) => (
              <ActivityItem
                key={`${item.text}-${index}`}
                icon={item.icon}
                text={item.text}
                time={item.time}
              />
            ))}
          </div>
        </div>
      </div>
    </div>
  );
};

export default memo(OptimizedDashboard);