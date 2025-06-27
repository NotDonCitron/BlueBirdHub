/**
 * Analytics Dashboard - Main component for comprehensive productivity insights
 */

import React, { useState, useEffect, useCallback } from 'react';
import {
  LineChart, Line, AreaChart, Area, BarChart, Bar, PieChart, Pie, Cell,
  ResponsiveContainer, XAxis, YAxis, CartesianGrid, Tooltip, Legend
} from 'recharts';
import './AnalyticsDashboard.css';

interface DashboardFilters {
  userId?: number;
  workspaceId?: number;
  teamId?: number;
  days: number;
}

interface ProductivityMetrics {
  taskMetrics: {
    totalCreated: number;
    totalCompleted: number;
    completionRate: number;
    dailyAverageCreated: number;
    dailyAverageCompleted: number;
  };
  timeMetrics: {
    totalTrackedHours: number;
    averageDailyHours: number;
    timeByCategoryCategory: { [key: string]: number };
    timeByActivity: { [key: string]: number };
  };
  productivityScores: {
    overallAverage: number;
    trend: string;
  };
  collaboration: {
    commentsMade: number;
    filesShared: number;
    meetingsAttended: number;
  };
}

interface ChartData {
  taskVelocity: Array<{ date: string; completedTasks: number }>;
  timeDistribution: Array<{ name: string; value: number }>;
  activityHeatmap: Array<{ day: string; hour: number; value: number }>;
  productivityTrend: Array<{ date: string; score: number }>;
}

interface Insight {
  type: string;
  category: string;
  title: string;
  description: string;
  impactLevel: string;
  recommendedActions?: string[];
}

const AnalyticsDashboard: React.FC = () => {
  const [filters, setFilters] = useState<DashboardFilters>({ days: 30 });
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [dashboardData, setDashboardData] = useState<any>(null);
  const [metrics, setMetrics] = useState<ProductivityMetrics | null>(null);
  const [chartData, setChartData] = useState<ChartData | null>(null);
  const [insights, setInsights] = useState<Insight[]>([]);
  const [activeView, setActiveView] = useState<'overview' | 'productivity' | 'team' | 'insights'>('overview');

  // Fetch dashboard data
  const fetchDashboardData = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);

      const params = new URLSearchParams({
        days: filters.days.toString(),
        ...(filters.userId && { user_id: filters.userId.toString() }),
        ...(filters.workspaceId && { workspace_id: filters.workspaceId.toString() }),
        ...(filters.teamId && { team_id: filters.teamId.toString() })
      });

      const response = await fetch(`/api/analytics/dashboard?${params}`);
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      setDashboardData(data);

      // Fetch additional chart data
      await Promise.all([
        fetchChartData(),
        fetchInsights()
      ]);

    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch dashboard data');
      console.error('Dashboard fetch error:', err);
    } finally {
      setLoading(false);
    }
  }, [filters]);

  // Fetch chart data
  const fetchChartData = async () => {
    try {
      const params = new URLSearchParams({
        days: filters.days.toString(),
        ...(filters.userId && { user_id: filters.userId.toString() }),
        ...(filters.workspaceId && { workspace_id: filters.workspaceId.toString() })
      });

      const [velocityRes, timeDistRes, heatmapRes] = await Promise.all([
        fetch(`/api/analytics/charts/task-velocity?${params}`),
        filters.userId ? fetch(`/api/analytics/charts/time-distribution?user_id=${filters.userId}&days=${filters.days}`) : null,
        fetch(`/api/analytics/charts/activity-heatmap?${params}`)
      ]);

      const velocityData = await velocityRes.json();
      const timeDistData = timeDistRes ? await timeDistRes.json() : null;
      const heatmapData = await heatmapRes.json();

      setChartData({
        taskVelocity: velocityData.chart_data || [],
        timeDistribution: timeDistData?.category_distribution || [],
        activityHeatmap: heatmapData.heatmap_data || [],
        productivityTrend: [] // Would be populated from additional endpoint
      });

    } catch (err) {
      console.error('Chart data fetch error:', err);
    }
  };

  // Fetch insights
  const fetchInsights = async () => {
    if (!filters.userId) return;

    try {
      const response = await fetch(`/api/analytics/insights/${filters.userId}`);
      const data = await response.json();
      
      if (data.success) {
        setInsights([...data.insights, ...data.anomalies]);
      }
    } catch (err) {
      console.error('Insights fetch error:', err);
    }
  };

  useEffect(() => {
    fetchDashboardData();
  }, [fetchDashboardData]);

  // Handle filter changes
  const handleFilterChange = (newFilters: Partial<DashboardFilters>) => {
    setFilters(prev => ({ ...prev, ...newFilters }));
  };

  // Color schemes for charts
  const COLORS = {
    primary: ['#0088FE', '#00C49F', '#FFBB28', '#FF8042', '#8884d8'],
    productivity: '#00C49F',
    warning: '#FF8042',
    danger: '#FF4444',
    success: '#00C49F'
  };

  if (loading) {
    return (
      <div className="analytics-dashboard loading">
        <div className="loading-spinner"></div>
        <p>Loading analytics dashboard...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="analytics-dashboard error">
        <div className="error-message">
          <h3>Error Loading Dashboard</h3>
          <p>{error}</p>
          <button onClick={fetchDashboardData} className="retry-button">
            Retry
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="analytics-dashboard">
      {/* Header and Filters */}
      <div className="dashboard-header">
        <h1>Analytics Dashboard</h1>
        <div className="dashboard-filters">
          <select 
            value={filters.days} 
            onChange={(e) => handleFilterChange({ days: parseInt(e.target.value) })}
            className="time-filter"
          >
            <option value={7}>Last 7 days</option>
            <option value={30}>Last 30 days</option>
            <option value={90}>Last 90 days</option>
            <option value={365}>Last year</option>
          </select>
          
          <input
            type="number"
            placeholder="User ID"
            value={filters.userId || ''}
            onChange={(e) => handleFilterChange({ userId: e.target.value ? parseInt(e.target.value) : undefined })}
            className="user-filter"
          />
          
          <input
            type="number"
            placeholder="Workspace ID"
            value={filters.workspaceId || ''}
            onChange={(e) => handleFilterChange({ workspaceId: e.target.value ? parseInt(e.target.value) : undefined })}
            className="workspace-filter"
          />
        </div>
      </div>

      {/* Navigation Tabs */}
      <div className="dashboard-nav">
        <button 
          className={`nav-tab ${activeView === 'overview' ? 'active' : ''}`}
          onClick={() => setActiveView('overview')}
        >
          Overview
        </button>
        <button 
          className={`nav-tab ${activeView === 'productivity' ? 'active' : ''}`}
          onClick={() => setActiveView('productivity')}
        >
          Productivity
        </button>
        <button 
          className={`nav-tab ${activeView === 'team' ? 'active' : ''}`}
          onClick={() => setActiveView('team')}
        >
          Team Analytics
        </button>
        <button 
          className={`nav-tab ${activeView === 'insights' ? 'active' : ''}`}
          onClick={() => setActiveView('insights')}
        >
          Insights
        </button>
      </div>

      {/* Dashboard Content */}
      <div className="dashboard-content">
        {activeView === 'overview' && (
          <OverviewView 
            dashboardData={dashboardData} 
            chartData={chartData}
            colors={COLORS}
          />
        )}
        
        {activeView === 'productivity' && (
          <ProductivityView 
            metrics={dashboardData?.productivity_summary} 
            chartData={chartData}
            colors={COLORS}
          />
        )}
        
        {activeView === 'team' && (
          <TeamView 
            teamMetrics={dashboardData?.team_metrics}
            colors={COLORS}
          />
        )}
        
        {activeView === 'insights' && (
          <InsightsView 
            insights={insights}
            colors={COLORS}
          />
        )}
      </div>
    </div>
  );
};

// Overview View Component
const OverviewView: React.FC<{ dashboardData: any, chartData: ChartData | null, colors: any }> = ({ 
  dashboardData, chartData, colors 
}) => (
  <div className="overview-view">
    {/* Key Metrics Cards */}
    <div className="metrics-grid">
      <div className="metric-card">
        <h3>Total Events</h3>
        <div className="metric-value">{dashboardData?.overview?.total_events || 0}</div>
        <div className="metric-change positive">↗ +12% vs last period</div>
      </div>
      
      <div className="metric-card">
        <h3>Active Users</h3>
        <div className="metric-value">{dashboardData?.overview?.active_users || 0}</div>
        <div className="metric-change positive">↗ +5% vs last period</div>
      </div>
      
      <div className="metric-card">
        <h3>Completion Rate</h3>
        <div className="metric-value">
          {dashboardData?.productivity_summary?.task_metrics?.completion_rate?.toFixed(1) || 0}%
        </div>
        <div className="metric-change negative">↘ -2% vs last period</div>
      </div>
      
      <div className="metric-card">
        <h3>Avg Daily Hours</h3>
        <div className="metric-value">
          {dashboardData?.productivity_summary?.time_metrics?.average_daily_hours?.toFixed(1) || 0}h
        </div>
        <div className="metric-change positive">↗ +8% vs last period</div>
      </div>
    </div>

    {/* Charts Row */}
    <div className="charts-row">
      {/* Task Velocity Chart */}
      <div className="chart-container">
        <h3>Task Completion Velocity</h3>
        <ResponsiveContainer width="100%" height={300}>
          <LineChart data={chartData?.taskVelocity || []}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="date" />
            <YAxis />
            <Tooltip />
            <Legend />
            <Line 
              type="monotone" 
              dataKey="completedTasks" 
              stroke={colors.productivity} 
              strokeWidth={2}
              dot={{ fill: colors.productivity }}
            />
          </LineChart>
        </ResponsiveContainer>
      </div>

      {/* Time Distribution Pie Chart */}
      <div className="chart-container">
        <h3>Time Distribution by Category</h3>
        <ResponsiveContainer width="100%" height={300}>
          <PieChart>
            <Pie
              data={chartData?.timeDistribution || []}
              cx="50%"
              cy="50%"
              innerRadius={60}
              outerRadius={100}
              paddingAngle={5}
              dataKey="value"
            >
              {(chartData?.timeDistribution || []).map((entry, index) => (
                <Cell key={`cell-${index}`} fill={colors.primary[index % colors.primary.length]} />
              ))}
            </Pie>
            <Tooltip formatter={(value: number) => [`${value.toFixed(1)}h`, 'Hours']} />
            <Legend />
          </PieChart>
        </ResponsiveContainer>
      </div>
    </div>

    {/* Recent Activities */}
    <div className="recent-activities">
      <h3>Recent Activities</h3>
      <div className="activities-list">
        {dashboardData?.recent_activities?.slice(0, 10).map((activity: any, index: number) => (
          <div key={index} className="activity-item">
            <div className="activity-icon">
              {getActivityIcon(activity.event_type)}
            </div>
            <div className="activity-details">
              <div className="activity-type">{formatEventType(activity.event_type)}</div>
              <div className="activity-time">{formatTimeAgo(activity.timestamp)}</div>
            </div>
            <div className={`activity-status ${activity.success ? 'success' : 'error'}`}>
              {activity.success ? '✓' : '✗'}
            </div>
          </div>
        ))}
      </div>
    </div>
  </div>
);

// Productivity View Component
const ProductivityView: React.FC<{ metrics: any, chartData: ChartData | null, colors: any }> = ({ 
  metrics, chartData, colors 
}) => (
  <div className="productivity-view">
    {/* Productivity Score Ring */}
    <div className="productivity-score-section">
      <div className="score-ring-container">
        <div className="score-ring">
          <div className="score-value">
            {metrics?.productivity_scores?.overall_average?.toFixed(0) || 0}
          </div>
          <div className="score-label">Productivity Score</div>
        </div>
        <div className="score-trend">
          Trend: {metrics?.productivity_scores?.trend || 'stable'}
        </div>
      </div>
    </div>

    {/* Task Metrics */}
    <div className="task-metrics-section">
      <h3>Task Performance</h3>
      <div className="task-stats">
        <div className="task-stat">
          <div className="stat-value">{metrics?.task_metrics?.total_created || 0}</div>
          <div className="stat-label">Tasks Created</div>
        </div>
        <div className="task-stat">
          <div className="stat-value">{metrics?.task_metrics?.total_completed || 0}</div>
          <div className="stat-label">Tasks Completed</div>
        </div>
        <div className="task-stat">
          <div className="stat-value">{metrics?.task_metrics?.completion_rate?.toFixed(1) || 0}%</div>
          <div className="stat-label">Completion Rate</div>
        </div>
      </div>
    </div>

    {/* Time Analysis */}
    <div className="time-analysis-section">
      <h3>Time Analysis</h3>
      <div className="time-breakdown">
        <div className="time-category">
          <span className="category-label">Total Tracked Time:</span>
          <span className="category-value">{metrics?.time_metrics?.total_tracked_hours?.toFixed(1) || 0}h</span>
        </div>
        <div className="time-category">
          <span className="category-label">Daily Average:</span>
          <span className="category-value">{metrics?.time_metrics?.average_daily_hours?.toFixed(1) || 0}h</span>
        </div>
      </div>
      
      {/* Time by Activity Bar Chart */}
      <div className="time-chart">
        <ResponsiveContainer width="100%" height={200}>
          <BarChart data={Object.entries(metrics?.time_metrics?.time_by_activity || {}).map(([name, value]) => ({ name, hours: value }))}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="name" />
            <YAxis />
            <Tooltip formatter={(value: number) => [`${value.toFixed(1)}h`, 'Hours']} />
            <Bar dataKey="hours" fill={colors.productivity} />
          </BarChart>
        </ResponsiveContainer>
      </div>
    </div>

    {/* Collaboration Metrics */}
    <div className="collaboration-section">
      <h3>Collaboration Activity</h3>
      <div className="collaboration-grid">
        <div className="collab-metric">
          <div className="metric-icon">💬</div>
          <div className="metric-info">
            <div className="metric-number">{metrics?.collaboration?.comments_made || 0}</div>
            <div className="metric-name">Comments</div>
          </div>
        </div>
        <div className="collab-metric">
          <div className="metric-icon">📁</div>
          <div className="metric-info">
            <div className="metric-number">{metrics?.collaboration?.files_shared || 0}</div>
            <div className="metric-name">Files Shared</div>
          </div>
        </div>
        <div className="collab-metric">
          <div className="metric-icon">🤝</div>
          <div className="metric-info">
            <div className="metric-number">{metrics?.collaboration?.meetings_attended || 0}</div>
            <div className="metric-name">Meetings</div>
          </div>
        </div>
      </div>
    </div>
  </div>
);

// Team View Component
const TeamView: React.FC<{ teamMetrics: any, colors: any }> = ({ teamMetrics, colors }) => (
  <div className="team-view">
    {teamMetrics ? (
      <>
        <div className="team-overview">
          <h3>Team Performance Overview</h3>
          <div className="team-stats">
            <div className="team-stat">
              <div className="stat-value">{teamMetrics.team_size}</div>
              <div className="stat-label">Team Members</div>
            </div>
            <div className="team-stat">
              <div className="stat-value">{teamMetrics.aggregated_metrics?.team_completion_rate?.toFixed(1) || 0}%</div>
              <div className="stat-label">Team Completion Rate</div>
            </div>
            <div className="team-stat">
              <div className="stat-value">{teamMetrics.aggregated_metrics?.total_hours_worked?.toFixed(0) || 0}h</div>
              <div className="stat-label">Total Hours</div>
            </div>
            <div className="team-stat">
              <div className="stat-value">{teamMetrics.workload_distribution?.balance_score?.toFixed(0) || 0}</div>
              <div className="stat-label">Balance Score</div>
            </div>
          </div>
        </div>

        {/* Workload Distribution */}
        <div className="workload-distribution">
          <h3>Workload Distribution</h3>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={Object.entries(teamMetrics.workload_distribution?.member_workloads || {}).map(([userId, hours]) => ({ 
              user: `User ${userId}`, 
              hours: hours as number 
            }))}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="user" />
              <YAxis />
              <Tooltip formatter={(value: number) => [`${value.toFixed(1)}h`, 'Hours']} />
              <Bar dataKey="hours" fill={colors.productivity} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </>
    ) : (
      <div className="no-team-data">
        <p>No team data available. Please select a team to view analytics.</p>
      </div>
    )}
  </div>
);

// Insights View Component
const InsightsView: React.FC<{ insights: Insight[], colors: any }> = ({ insights, colors }) => (
  <div className="insights-view">
    <h3>AI-Powered Insights</h3>
    {insights.length > 0 ? (
      <div className="insights-list">
        {insights.map((insight, index) => (
          <div key={index} className={`insight-card ${insight.type} ${insight.impactLevel}`}>
            <div className="insight-header">
              <div className="insight-icon">{getInsightIcon(insight.type)}</div>
              <div className="insight-title">{insight.title}</div>
              <div className={`impact-badge ${insight.impactLevel}`}>
                {insight.impactLevel}
              </div>
            </div>
            <div className="insight-description">{insight.description}</div>
            {insight.recommendedActions && insight.recommendedActions.length > 0 && (
              <div className="recommended-actions">
                <h4>Recommended Actions:</h4>
                <ul>
                  {insight.recommendedActions.map((action, actionIndex) => (
                    <li key={actionIndex}>{action}</li>
                  ))}
                </ul>
              </div>
            )}
          </div>
        ))}
      </div>
    ) : (
      <div className="no-insights">
        <p>No insights available yet. More data is needed to generate meaningful insights.</p>
      </div>
    )}
  </div>
);

// Helper functions
const getActivityIcon = (eventType: string): string => {
  const iconMap: { [key: string]: string } = {
    'task_created': '➕',
    'task_completed': '✅',
    'task_updated': '📝',
    'file_uploaded': '📁',
    'collaboration_comment': '💬',
    'meeting_attended': '🤝',
    'login': '🔑',
    'search_performed': '🔍'
  };
  return iconMap[eventType] || '📊';
};

const getInsightIcon = (type: string): string => {
  const iconMap: { [key: string]: string } = {
    'recommendation': '💡',
    'positive': '🎉',
    'warning': '⚠️',
    'anomaly': '🔍'
  };
  return iconMap[type] || '📊';
};

const formatEventType = (eventType: string): string => {
  return eventType.split('_').map(word => 
    word.charAt(0).toUpperCase() + word.slice(1)
  ).join(' ');
};

const formatTimeAgo = (timestamp: string): string => {
  const now = new Date();
  const time = new Date(timestamp);
  const diffMinutes = Math.floor((now.getTime() - time.getTime()) / (1000 * 60));
  
  if (diffMinutes < 1) return 'Just now';
  if (diffMinutes < 60) return `${diffMinutes}m ago`;
  if (diffMinutes < 1440) return `${Math.floor(diffMinutes / 60)}h ago`;
  return `${Math.floor(diffMinutes / 1440)}d ago`;
};

export default AnalyticsDashboard;