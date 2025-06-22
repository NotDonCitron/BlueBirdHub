import React, { useState, useEffect } from 'react';
import { apiClient } from '../../config/apiClient';
import TaskCompletionLineChart from '../ProgressCharts/TaskCompletionLineChart';
import WorkspacePieChart from '../ProgressCharts/WorkspacePieChart';
import '../ProgressCharts/ProgressCharts.css';
import './Dashboard.css';
import { ResponsiveContainer } from 'recharts';

interface DashboardStats {
  totalTasks: number;
  completedTasks: number;
  activeWorkspaces: number;
  totalFiles: number;
}

const Dashboard: React.FC = () => {
  const [stats, setStats] = useState<DashboardStats>({
    totalTasks: 0,
    completedTasks: 0,
    activeWorkspaces: 0,
    totalFiles: 0,
  });
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const loadData = async () => {
      try {
        setLoading(true);
        const [statsData, progressData] = await Promise.all([
          apiClient.get<DashboardStats>('/api/dashboard/stats'),
          apiClient.getProgressStats<any>() // Using <any> for now
        ]);
        setStats(statsData);
        // Here you would set the data for the charts
        // For example: setLineChartData(progressData.task_completion_over_time);
      } catch (err) {
        setError('Failed to load dashboard data.');
        console.error(err);
      } finally {
        setLoading(false);
      }
    };

    loadData();
  }, []);

  const getCompletionPercentage = () => {
    if (stats.totalTasks === 0) return 0;
    return Math.round((stats.completedTasks / stats.totalTasks) * 100);
  };

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
        {error && <p className="dashboard-error">{error}</p>}
      </div>

      <div className="dashboard-stats">
        <div className="stat-card">
          <div className="stat-icon">✅</div>
          <div className="stat-content">
            <div className="stat-value">{stats.totalTasks}</div>
            <div className="stat-label">Total Tasks</div>
          </div>
        </div>

        <div className="stat-card">
          <div className="stat-icon">🎯</div>
          <div className="stat-content">
            <div className="stat-value">{stats.completedTasks}</div>
            <div className="stat-label">Completed</div>
          </div>
        </div>

        <div className="stat-card">
          <div className="stat-icon">🏠</div>
          <div className="stat-content">
            <div className="stat-value">{stats.activeWorkspaces}</div>
            <div className="stat-label">Workspaces</div>
          </div>
        </div>

        <div className="stat-card">
          <div className="stat-icon">📁</div>
          <div className="stat-content">
            <div className="stat-value">{stats.totalFiles}</div>
            <div className="stat-label">Files Indexed</div>
          </div>
        </div>
      </div>

      <div className="dashboard-content">
        <div className="dashboard-section-full">
          <h3>Progress Visualization</h3>
          <div className="charts-grid">
            <div className="chart-container">
              <h3>Tasks Completion Over Time</h3>
              <ResponsiveContainer width="100%" height={300}>
                <TaskCompletionLineChart data={stats?.taskCompletion?.week} />
              </ResponsiveContainer>
            </div>
            <div className="chart-container">
              <h3>Tasks by Workspace</h3>
              <ResponsiveContainer width="100%" height={300}>
                <WorkspacePieChart data={stats?.tasksByWorkspace} />
              </ResponsiveContainer>
            </div>
          </div>
        </div>

        <div className="dashboard-section">
          <h3>Task Progress</h3>
          <div className="progress-card">
            <div className="progress-header">
              <span>Overall Completion</span>
              <span className="progress-percentage">{getCompletionPercentage()}%</span>
            </div>
            <div className="progress-bar">
              <div 
                className="progress-fill"
                style={{ width: `${getCompletionPercentage()}%` }}
              ></div>
            </div>
            <div className="progress-details">
              {stats.completedTasks} of {stats.totalTasks} tasks completed
            </div>
          </div>
        </div>

        <div className="dashboard-section">
          <h3>Quick Actions</h3>
          <div className="quick-actions">
            <button className="action-card">
              <div className="action-icon">➕</div>
              <div className="action-label">New Task</div>
            </button>
            <button className="action-card">
              <div className="action-icon">🏠</div>
              <div className="action-label">New Workspace</div>
            </button>
            <button className="action-card">
              <div className="action-icon">📊</div>
              <div className="action-label">Analytics</div>
            </button>
            <button className="action-card">
              <div className="action-icon">🤖</div>
              <div className="action-label">AI Assistant</div>
            </button>
          </div>
        </div>

        <div className="dashboard-section">
          <h3>Recent Activity</h3>
          <div className="activity-list">
            <div className="activity-item">
              <div className="activity-icon">✅</div>
              <div className="activity-content">
                <div className="activity-text">Completed task "Review project proposal"</div>
                <div className="activity-time">2 hours ago</div>
              </div>
            </div>
            <div className="activity-item">
              <div className="activity-icon">🏠</div>
              <div className="activity-content">
                <div className="activity-text">Created new workspace "Marketing Campaign"</div>
                <div className="activity-time">Yesterday</div>
              </div>
            </div>
            <div className="activity-item">
              <div className="activity-icon">📁</div>
              <div className="activity-content">
                <div className="activity-text">Organized 15 files in Documents folder</div>
                <div className="activity-time">2 days ago</div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Dashboard;