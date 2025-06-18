import React, { useState, useEffect } from 'react';
import { useErrorHandler } from '../hooks/useErrorHandler';

interface DashboardStats {
  totalTasks: number;
  completedTasks: number;
  totalWorkspaces: number;
  activeProjects: number;
}

interface RecentActivity {
  id: string;
  type: 'task_completed' | 'workspace_created' | 'file_uploaded' | 'team_member_added';
  description: string;
  timestamp: string;
}

const Dashboard: React.FC = () => {
  const [stats, setStats] = useState<DashboardStats>({
    totalTasks: 0,
    completedTasks: 0,
    totalWorkspaces: 0,
    activeProjects: 0
  });
  const [recentActivities, setRecentActivities] = useState<RecentActivity[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const { handleError } = useErrorHandler({ component: 'Dashboard' });

  useEffect(() => {
    loadDashboardData();
  }, []);

  const loadDashboardData = async () => {
    try {
      setLoading(true);
      setError(null);
      
      // Mock data for now - replace with actual API calls
      const mockStats: DashboardStats = {
        totalTasks: 24,
        completedTasks: 18,
        totalWorkspaces: 5,
        activeProjects: 3
      };

      const mockActivities: RecentActivity[] = [
        {
          id: '1',
          type: 'task_completed',
          description: 'Completed "Design user interface mockups"',
          timestamp: new Date(Date.now() - 3600000).toISOString() // 1 hour ago
        },
        {
          id: '2',
          type: 'workspace_created',
          description: 'Created new workspace "Q1 Marketing Campaign"',
          timestamp: new Date(Date.now() - 7200000).toISOString() // 2 hours ago
        },
        {
          id: '3',
          type: 'file_uploaded',
          description: 'Uploaded 3 files to "Product Documentation"',
          timestamp: new Date(Date.now() - 14400000).toISOString() // 4 hours ago
        },
        {
          id: '4',
          type: 'team_member_added',
          description: 'Added John Doe to "Development Team" workspace',
          timestamp: new Date(Date.now() - 86400000).toISOString() // 1 day ago
        }
      ];
      
      setStats(mockStats);
      setRecentActivities(mockActivities);
    } catch (err) {
      const message = handleError(err);
      setError(message);
    } finally {
      setLoading(false);
    }
  };

  const getActivityIcon = (type: RecentActivity['type']) => {
    switch (type) {
      case 'task_completed': return '✅';
      case 'workspace_created': return '📁';
      case 'file_uploaded': return '📄';
      case 'team_member_added': return '👤';
      default: return '📝';
    }
  };

  const formatRelativeTime = (timestamp: string) => {
    const now = new Date();
    const time = new Date(timestamp);
    const diffInSeconds = Math.floor((now.getTime() - time.getTime()) / 1000);

    if (diffInSeconds < 60) return 'Just now';
    if (diffInSeconds < 3600) return `${Math.floor(diffInSeconds / 60)}m ago`;
    if (diffInSeconds < 86400) return `${Math.floor(diffInSeconds / 3600)}h ago`;
    if (diffInSeconds < 604800) return `${Math.floor(diffInSeconds / 86400)}d ago`;
    return time.toLocaleDateString();
  };

  const calculateCompletionRate = () => {
    if (stats.totalTasks === 0) return 0;
    return Math.round((stats.completedTasks / stats.totalTasks) * 100);
  };

  if (loading) {
    return (
      <div className="dashboard-loading">
        <div className="spinner"></div>
        <p>Loading dashboard...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="dashboard-error">
        <p>Error: {error}</p>
        <button onClick={loadDashboardData}>Retry</button>
      </div>
    );
  }

  return (
    <div className="dashboard">
      <div className="dashboard-header">
        <h1>Dashboard</h1>
        <p className="dashboard-subtitle">
          Welcome back! Here's what's happening with your projects.
        </p>
      </div>

      {/* Stats Cards */}
      <div className="stats-grid">
        <div className="stat-card">
          <div className="stat-icon">📊</div>
          <div className="stat-content">
            <h3>{stats.totalTasks}</h3>
            <p>Total Tasks</p>
            <div className="stat-detail">
              {stats.completedTasks} completed
            </div>
          </div>
        </div>

        <div className="stat-card">
          <div className="stat-icon">📁</div>
          <div className="stat-content">
            <h3>{stats.totalWorkspaces}</h3>
            <p>Workspaces</p>
            <div className="stat-detail">
              {stats.activeProjects} active projects
            </div>
          </div>
        </div>

        <div className="stat-card">
          <div className="stat-icon">📈</div>
          <div className="stat-content">
            <h3>{calculateCompletionRate()}%</h3>
            <p>Completion Rate</p>
            <div className="stat-detail">
              Tasks completed this week
            </div>
          </div>
        </div>

        <div className="stat-card">
          <div className="stat-icon">🎯</div>
          <div className="stat-content">
            <h3>{stats.activeProjects}</h3>
            <p>Active Projects</p>
            <div className="stat-detail">
              Currently in progress
            </div>
          </div>
        </div>
      </div>

      {/* Progress Section */}
      <div className="progress-section">
        <h2>Task Progress</h2>
        <div className="progress-bar">
          <div 
            className="progress-fill"
            style={{ width: `${calculateCompletionRate()}%` }}
          ></div>
        </div>
        <div className="progress-labels">
          <span>{stats.completedTasks} completed</span>
          <span>{stats.totalTasks - stats.completedTasks} remaining</span>
        </div>
      </div>

      {/* Recent Activity */}
      <div className="recent-activity">
        <h2>Recent Activity</h2>
        <div className="activity-list">
          {recentActivities.map(activity => (
            <div key={activity.id} className="activity-item">
              <div className="activity-icon">
                {getActivityIcon(activity.type)}
              </div>
              <div className="activity-content">
                <p>{activity.description}</p>
                <span className="activity-time">
                  {formatRelativeTime(activity.timestamp)}
                </span>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Quick Actions */}
      <div className="quick-actions">
        <h2>Quick Actions</h2>
        <div className="actions-grid">
          <button className="action-btn primary">
            <span className="action-icon">➕</span>
            Create Task
          </button>
          <button className="action-btn secondary">
            <span className="action-icon">📁</span>
            New Workspace
          </button>
          <button className="action-btn secondary">
            <span className="action-icon">📤</span>
            Upload Files
          </button>
          <button className="action-btn secondary">
            <span className="action-icon">👥</span>
            Invite Team
          </button>
        </div>
      </div>

      <style jsx>{`
        .dashboard {
          padding: 24px;
          max-width: 1200px;
          margin: 0 auto;
          background: #f9fafb;
          min-height: 100vh;
        }

        .dashboard-header {
          margin-bottom: 32px;
        }

        .dashboard-header h1 {
          margin: 0 0 8px 0;
          font-size: 32px;
          font-weight: 700;
          color: #1f2937;
        }

        .dashboard-subtitle {
          color: #6b7280;
          font-size: 16px;
          margin: 0;
        }

        .stats-grid {
          display: grid;
          grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
          gap: 20px;
          margin-bottom: 32px;
        }

        .stat-card {
          background: white;
          border-radius: 12px;
          padding: 24px;
          box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
          display: flex;
          align-items: center;
          gap: 16px;
        }

        .stat-icon {
          font-size: 32px;
          width: 60px;
          height: 60px;
          display: flex;
          align-items: center;
          justify-content: center;
          background: #f3f4f6;
          border-radius: 12px;
        }

        .stat-content h3 {
          margin: 0 0 4px 0;
          font-size: 28px;
          font-weight: 700;
          color: #1f2937;
        }

        .stat-content p {
          margin: 0 0 8px 0;
          color: #6b7280;
          font-weight: 500;
        }

        .stat-detail {
          color: #9ca3af;
          font-size: 14px;
        }

        .progress-section {
          background: white;
          border-radius: 12px;
          padding: 24px;
          margin-bottom: 32px;
          box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
        }

        .progress-section h2 {
          margin: 0 0 20px 0;
          font-size: 20px;
          font-weight: 600;
          color: #1f2937;
        }

        .progress-bar {
          width: 100%;
          height: 12px;
          background: #f3f4f6;
          border-radius: 6px;
          overflow: hidden;
          margin-bottom: 12px;
        }

        .progress-fill {
          height: 100%;
          background: linear-gradient(90deg, #10b981, #34d399);
          border-radius: 6px;
          transition: width 0.3s ease;
        }

        .progress-labels {
          display: flex;
          justify-content: space-between;
          font-size: 14px;
          color: #6b7280;
        }

        .recent-activity {
          background: white;
          border-radius: 12px;
          padding: 24px;
          margin-bottom: 32px;
          box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
        }

        .recent-activity h2 {
          margin: 0 0 20px 0;
          font-size: 20px;
          font-weight: 600;
          color: #1f2937;
        }

        .activity-list {
          display: flex;
          flex-direction: column;
          gap: 16px;
        }

        .activity-item {
          display: flex;
          align-items: center;
          gap: 16px;
          padding: 16px;
          background: #f9fafb;
          border-radius: 8px;
        }

        .activity-icon {
          font-size: 20px;
          width: 40px;
          height: 40px;
          display: flex;
          align-items: center;
          justify-content: center;
          background: white;
          border-radius: 8px;
          box-shadow: 0 1px 2px rgba(0, 0, 0, 0.1);
        }

        .activity-content {
          flex: 1;
        }

        .activity-content p {
          margin: 0 0 4px 0;
          color: #1f2937;
          font-weight: 500;
        }

        .activity-time {
          color: #9ca3af;
          font-size: 14px;
        }

        .quick-actions {
          background: white;
          border-radius: 12px;
          padding: 24px;
          box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
        }

        .quick-actions h2 {
          margin: 0 0 20px 0;
          font-size: 20px;
          font-weight: 600;
          color: #1f2937;
        }

        .actions-grid {
          display: grid;
          grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
          gap: 16px;
        }

        .action-btn {
          display: flex;
          align-items: center;
          gap: 12px;
          padding: 16px;
          border: none;
          border-radius: 8px;
          cursor: pointer;
          font-weight: 500;
          font-size: 14px;
          transition: all 0.2s ease;
        }

        .action-btn.primary {
          background: #3b82f6;
          color: white;
        }

        .action-btn.primary:hover {
          background: #2563eb;
          transform: translateY(-1px);
        }

        .action-btn.secondary {
          background: #f9fafb;
          color: #374151;
          border: 1px solid #e5e7eb;
        }

        .action-btn.secondary:hover {
          background: #f3f4f6;
          transform: translateY(-1px);
        }

        .action-icon {
          font-size: 16px;
        }

        .dashboard-loading, 
        .dashboard-error {
          text-align: center;
          padding: 60px 20px;
        }

        .spinner {
          width: 40px;
          height: 40px;
          border: 4px solid #f3f4f6;
          border-top: 4px solid #3b82f6;
          border-radius: 50%;
          animation: spin 1s linear infinite;
          margin: 0 auto 20px;
        }

        @keyframes spin {
          0% { transform: rotate(0deg); }
          100% { transform: rotate(360deg); }
        }
      `}</style>
    </div>
  );
};

export default Dashboard;