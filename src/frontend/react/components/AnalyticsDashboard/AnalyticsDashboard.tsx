import React, { useState, useEffect } from 'react';
import { makeApiRequest } from '../../lib/api';
import './AnalyticsDashboard.css';

interface AnalyticsData {
  productivity: any;
  storage: any;
  recent_activity: any[];
  quick_stats: {
    total_tasks: number;
    total_files: number;
    total_workspaces: number;
    active_automations: number;
  };
}

interface ChartProps {
  data: any;
  type: 'bar' | 'pie' | 'line';
  title: string;
}

const AnalyticsDashboard: React.FC = () => {
  const [analyticsData, setAnalyticsData] = useState<AnalyticsData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedTimeRange, setSelectedTimeRange] = useState('7d');
  const [activeTab, setActiveTab] = useState('overview');

  useEffect(() => {
    loadAnalytics();
  }, [selectedTimeRange]);

  const loadAnalytics = async () => {
    setLoading(true);
    setError(null);
    
    try {
      const data = await makeApiRequest('/analytics/dashboard', 'GET');
      setAnalyticsData(data);
    } catch (err: any) {
      setError(err.message || 'Failed to load analytics');
    } finally {
      setLoading(false);
    }
  };

  const generateReport = async (reportType: string) => {
    try {
      const report = await makeApiRequest('/analytics/generate-report', 'POST', {
        type: reportType,
        date_range: selectedTimeRange
      });
      
      // Download report as JSON for now (could be enhanced to PDF/Excel)
      const blob = new Blob([JSON.stringify(report, null, 2)], { 
        type: 'application/json' 
      });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `${reportType}-report-${selectedTimeRange}.json`;
      a.click();
      URL.revokeObjectURL(url);
    } catch (err: any) {
      setError(`Failed to generate report: ${err.message}`);
    }
  };

  const SimpleChart: React.FC<ChartProps> = ({ data, type, title }) => {
    if (type === 'bar' && data?.priority_distribution) {
      const priorities = data.priority_distribution;
      const maxValue = Math.max(...Object.values(priorities) as number[]);
      
      return (
        <div className="chart-container">
          <h4>{title}</h4>
          <div className="bar-chart">
            {Object.entries(priorities).map(([priority, count]) => (
              <div key={priority} className="bar-item">
                <div className="bar-label">{priority}</div>
                <div className="bar-container">
                  <div 
                    className={`bar bar-${priority}`}
                    style={{ 
                      height: `${maxValue > 0 ? (count as number) / maxValue * 100 : 0}%` 
                    }}
                  ></div>
                </div>
                <div className="bar-value">{count as number}</div>
              </div>
            ))}
          </div>
        </div>
      );
    }
    
    if (type === 'pie' && data?.category_breakdown) {
      const categories = data.category_breakdown;
      const total = Object.values(categories).reduce((sum: number, cat: any) => sum + cat.count, 0);
      
      return (
        <div className="chart-container">
          <h4>{title}</h4>
          <div className="pie-chart">
            <div className="pie-legend">
              {Object.entries(categories).map(([category, info]: [string, any]) => (
                <div key={category} className="pie-item">
                  <div className={`pie-color color-${category}`}></div>
                  <span>{category}: {info.count} files</span>
                  <span className="percentage">
                    ({total > 0 ? Math.round((info.count / total) * 100) : 0}%)
                  </span>
                </div>
              ))}
            </div>
          </div>
        </div>
      );
    }
    
    return (
      <div className="chart-container">
        <h4>{title}</h4>
        <div className="chart-placeholder">
          <p>Chart visualization for {type} type</p>
        </div>
      </div>
    );
  };

  if (loading) {
    return (
      <div className="analytics-dashboard loading">
        <div className="loading-spinner"></div>
        <p>Loading analytics...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="analytics-dashboard error">
        <p>Error: {error}</p>
        <button onClick={loadAnalytics}>Retry</button>
      </div>
    );
  }

  if (!analyticsData) {
    return (
      <div className="analytics-dashboard">
        <p>No analytics data available</p>
      </div>
    );
  }

  return (
    <div className="analytics-dashboard">
      <div className="dashboard-header">
        <h2>📊 Analytics Dashboard</h2>
        <div className="dashboard-controls">
          <select 
            value={selectedTimeRange} 
            onChange={(e) => setSelectedTimeRange(e.target.value)}
            className="time-range-select"
          >
            <option value="7d">Last 7 Days</option>
            <option value="30d">Last 30 Days</option>
            <option value="90d">Last 90 Days</option>
          </select>
          <button onClick={loadAnalytics} className="refresh-btn">
            🔄 Refresh
          </button>
        </div>
      </div>

      <div className="dashboard-tabs">
        <button 
          className={`tab ${activeTab === 'overview' ? 'active' : ''}`}
          onClick={() => setActiveTab('overview')}
        >
          Overview
        </button>
        <button 
          className={`tab ${activeTab === 'productivity' ? 'active' : ''}`}
          onClick={() => setActiveTab('productivity')}
        >
          Productivity
        </button>
        <button 
          className={`tab ${activeTab === 'storage' ? 'active' : ''}`}
          onClick={() => setActiveTab('storage')}
        >
          Storage
        </button>
        <button 
          className={`tab ${activeTab === 'activity' ? 'active' : ''}`}
          onClick={() => setActiveTab('activity')}
        >
          Activity
        </button>
      </div>

      {activeTab === 'overview' && (
        <div className="tab-content">
          <div className="quick-stats">
            <div className="stat-card">
              <div className="stat-icon">📋</div>
              <div className="stat-info">
                <div className="stat-value">{analyticsData.quick_stats.total_tasks}</div>
                <div className="stat-label">Total Tasks</div>
              </div>
            </div>
            <div className="stat-card">
              <div className="stat-icon">📁</div>
              <div className="stat-info">
                <div className="stat-value">{analyticsData.quick_stats.total_files}</div>
                <div className="stat-label">Files Managed</div>
              </div>
            </div>
            <div className="stat-card">
              <div className="stat-icon">🏢</div>
              <div className="stat-info">
                <div className="stat-value">{analyticsData.quick_stats.total_workspaces}</div>
                <div className="stat-label">Workspaces</div>
              </div>
            </div>
            <div className="stat-card">
              <div className="stat-icon">🤖</div>
              <div className="stat-info">
                <div className="stat-value">{analyticsData.quick_stats.active_automations}</div>
                <div className="stat-label">Active Rules</div>
              </div>
            </div>
          </div>

          <div className="overview-charts">
            <SimpleChart 
              data={analyticsData.productivity}
              type="bar"
              title="Task Priority Distribution"
            />
            <SimpleChart 
              data={analyticsData.storage}
              type="pie"
              title="File Categories"
            />
          </div>
        </div>
      )}

      {activeTab === 'productivity' && (
        <div className="tab-content">
          <div className="productivity-metrics">
            <div className="metric-card">
              <h3>📈 Completion Rate</h3>
              <div className="metric-value">
                {analyticsData.productivity.metrics.completion_rate}%
              </div>
              <div className="metric-progress">
                <div 
                  className="progress-bar"
                  style={{ width: `${analyticsData.productivity.metrics.completion_rate}%` }}
                ></div>
              </div>
            </div>

            <div className="task-breakdown">
              <h3>📊 Task Status Breakdown</h3>
              <div className="breakdown-items">
                <div className="breakdown-item completed">
                  <span>Completed</span>
                  <span>{analyticsData.productivity.metrics.completed_tasks}</span>
                </div>
                <div className="breakdown-item in-progress">
                  <span>In Progress</span>
                  <span>{analyticsData.productivity.metrics.in_progress_tasks}</span>
                </div>
                <div className="breakdown-item pending">
                  <span>Pending</span>
                  <span>{analyticsData.productivity.metrics.pending_tasks}</span>
                </div>
              </div>
            </div>
          </div>

          <div className="productivity-actions">
            <button 
              onClick={() => generateReport('productivity')}
              className="report-btn"
            >
              📄 Generate Productivity Report
            </button>
          </div>
        </div>
      )}

      {activeTab === 'storage' && (
        <div className="tab-content">
          <div className="storage-overview">
            <div className="storage-stats">
              <div className="storage-stat">
                <h4>Total Files</h4>
                <div className="storage-value">
                  {analyticsData.storage.metrics.total_files}
                </div>
              </div>
              <div className="storage-stat">
                <h4>Total Size</h4>
                <div className="storage-value">
                  {analyticsData.storage.metrics.total_size_mb} MB
                </div>
              </div>
            </div>

            <SimpleChart 
              data={analyticsData.storage}
              type="pie"
              title="Storage Usage by Category"
            />
          </div>

          <div className="storage-actions">
            <button 
              onClick={() => generateReport('storage')}
              className="report-btn"
            >
              📄 Generate Storage Report
            </button>
          </div>
        </div>
      )}

      {activeTab === 'activity' && (
        <div className="tab-content">
          <div className="activity-feed">
            <h3>🔄 Recent Activity</h3>
            {analyticsData.recent_activity.length > 0 ? (
              <div className="activity-list">
                {analyticsData.recent_activity.map((activity, index) => (
                  <div key={index} className="activity-item">
                    <div className="activity-icon">
                      {activity.action === 'task_created' && '➕'}
                      {activity.action === 'task_completed' && '✅'}
                      {activity.action === 'file_uploaded' && '📁'}
                      {activity.action === 'member_added' && '👤'}
                    </div>
                    <div className="activity-content">
                      <div className="activity-action">{activity.action}</div>
                      <div className="activity-time">
                        {new Date(activity.timestamp).toLocaleDateString()}
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <div className="no-activity">
                <p>No recent activity to display</p>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
};

export default AnalyticsDashboard;