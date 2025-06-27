/**
 * Time Tracking Dashboard - Specialized component for time management and analysis
 */

import React, { useState, useEffect, useCallback } from 'react';
import {
  LineChart, Line, AreaChart, Area, BarChart, Bar, PieChart, Pie, Cell,
  ResponsiveContainer, XAxis, YAxis, CartesianGrid, Tooltip, Legend
} from 'recharts';
import './TimeTrackingDashboard.css';

interface TimeTrackingSession {
  id: number;
  startTime: string;
  endTime?: string;
  currentDurationSeconds: number;
  currentDurationHours: number;
  activityType: string;
  category: string;
  description?: string;
  workspaceId?: number;
  taskId?: number;
}

interface TimeEntry {
  id: number;
  userId: number;
  workspaceId?: number;
  taskId?: number;
  startTime: string;
  endTime?: string;
  durationSeconds?: number;
  activityType: string;
  category: string;
  description?: string;
  focusScore?: number;
  isManual: boolean;
}

interface TimeDistribution {
  categoryDistribution: Array<{ name: string; value: number }>;
  activityDistribution: Array<{ name: string; value: number }>;
  totalHours: number;
  periodDays: number;
}

const TimeTrackingDashboard: React.FC<{ userId: number }> = ({ userId }) => {
  const [activeSessions, setActiveSessions] = useState<TimeTrackingSession[]>([]);
  const [timeDistribution, setTimeDistribution] = useState<TimeDistribution | null>(null);
  const [recentEntries, setRecentEntries] = useState<TimeEntry[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [startingSession, setStartingSession] = useState(false);
  
  // New session form state
  const [newSession, setNewSession] = useState({
    activityType: 'focus',
    category: 'work',
    description: '',
    workspaceId: undefined as number | undefined,
    taskId: undefined as number | undefined
  });

  // Fetch active time tracking sessions
  const fetchActiveSessions = useCallback(async () => {
    try {
      const response = await fetch(`/api/analytics/time-tracking/active/${userId}`);
      if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
      const sessions = await response.json();
      setActiveSessions(sessions);
    } catch (err) {
      console.error('Failed to fetch active sessions:', err);
    }
  }, [userId]);

  // Fetch time distribution data
  const fetchTimeDistribution = useCallback(async (days: number = 30) => {
    try {
      const response = await fetch(`/api/analytics/charts/time-distribution?user_id=${userId}&days=${days}`);
      if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
      const data = await response.json();
      setTimeDistribution(data);
    } catch (err) {
      console.error('Failed to fetch time distribution:', err);
    }
  }, [userId]);

  // Fetch recent time entries
  const fetchRecentEntries = useCallback(async () => {
    try {
      // This would be implemented as a separate endpoint
      // For now, we'll use a placeholder
      setRecentEntries([]);
    } catch (err) {
      console.error('Failed to fetch recent entries:', err);
    }
  }, [userId]);

  // Load all data
  const loadData = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      
      await Promise.all([
        fetchActiveSessions(),
        fetchTimeDistribution(),
        fetchRecentEntries()
      ]);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load time tracking data');
    } finally {
      setLoading(false);
    }
  }, [fetchActiveSessions, fetchTimeDistribution, fetchRecentEntries]);

  useEffect(() => {
    loadData();
    
    // Refresh active sessions every 30 seconds
    const interval = setInterval(fetchActiveSessions, 30000);
    return () => clearInterval(interval);
  }, [loadData, fetchActiveSessions]);

  // Start time tracking
  const startTimeTracking = async () => {
    try {
      setStartingSession(true);
      
      const response = await fetch('/api/analytics/time-tracking/start', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          user_id: userId,
          workspace_id: newSession.workspaceId,
          task_id: newSession.taskId,
          activity_type: newSession.activityType,
          category: newSession.category,
          description: newSession.description || undefined
        })
      });

      if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
      
      const result = await response.json();
      
      // Reset form and refresh sessions
      setNewSession({
        activityType: 'focus',
        category: 'work',
        description: '',
        workspaceId: undefined,
        taskId: undefined
      });
      
      await fetchActiveSessions();
      
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to start time tracking');
    } finally {
      setStartingSession(false);
    }
  };

  // End time tracking
  const endTimeTracking = async (sessionId: number, focusScore?: number) => {
    try {
      const params = new URLSearchParams();
      if (focusScore !== undefined) {
        params.append('focus_score', focusScore.toString());
      }
      
      const response = await fetch(`/api/analytics/time-tracking/${sessionId}/end?${params}`, {
        method: 'POST'
      });

      if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
      
      await Promise.all([
        fetchActiveSessions(),
        fetchTimeDistribution()
      ]);
      
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to end time tracking');
    }
  };

  // Format duration for display
  const formatDuration = (seconds: number): string => {
    const hours = Math.floor(seconds / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    const secs = seconds % 60;
    
    if (hours > 0) {
      return `${hours}h ${minutes}m ${secs}s`;
    } else if (minutes > 0) {
      return `${minutes}m ${secs}s`;
    } else {
      return `${secs}s`;
    }
  };

  // Colors for charts
  const COLORS = ['#0088FE', '#00C49F', '#FFBB28', '#FF8042', '#8884d8', '#82ca9d'];

  if (loading) {
    return (
      <div className="time-tracking-dashboard loading">
        <div className="loading-spinner"></div>
        <p>Loading time tracking data...</p>
      </div>
    );
  }

  return (
    <div className="time-tracking-dashboard">
      <div className="dashboard-header">
        <h2>Time Tracking Dashboard</h2>
        <div className="quick-stats">
          <div className="stat-item">
            <span className="stat-label">Active Sessions</span>
            <span className="stat-value">{activeSessions.length}</span>
          </div>
          <div className="stat-item">
            <span className="stat-label">Today's Total</span>
            <span className="stat-value">
              {activeSessions.reduce((total, session) => total + session.currentDurationHours, 0).toFixed(1)}h
            </span>
          </div>
        </div>
      </div>

      {error && (
        <div className="error-banner">
          <span>⚠️ {error}</span>
          <button onClick={loadData} className="retry-btn">Retry</button>
        </div>
      )}

      {/* Active Sessions */}
      <div className="active-sessions-section">
        <h3>Active Time Tracking Sessions</h3>
        
        {activeSessions.length > 0 ? (
          <div className="active-sessions-list">
            {activeSessions.map((session) => (
              <ActiveSessionCard
                key={session.id}
                session={session}
                onEnd={(focusScore) => endTimeTracking(session.id, focusScore)}
                formatDuration={formatDuration}
              />
            ))}
          </div>
        ) : (
          <div className="no-active-sessions">
            <p>No active time tracking sessions</p>
          </div>
        )}

        {/* Start New Session */}
        <div className="start-session-form">
          <h4>Start New Time Tracking Session</h4>
          <div className="form-grid">
            <div className="form-group">
              <label>Activity Type</label>
              <select
                value={newSession.activityType}
                onChange={(e) => setNewSession({ ...newSession, activityType: e.target.value })}
              >
                <option value="focus">Focus Work</option>
                <option value="meeting">Meeting</option>
                <option value="research">Research</option>
                <option value="planning">Planning</option>
                <option value="learning">Learning</option>
                <option value="break">Break</option>
              </select>
            </div>
            
            <div className="form-group">
              <label>Category</label>
              <select
                value={newSession.category}
                onChange={(e) => setNewSession({ ...newSession, category: e.target.value })}
              >
                <option value="work">Work</option>
                <option value="personal">Personal</option>
                <option value="learning">Learning</option>
                <option value="admin">Administrative</option>
              </select>
            </div>
            
            <div className="form-group">
              <label>Workspace ID (optional)</label>
              <input
                type="number"
                value={newSession.workspaceId || ''}
                onChange={(e) => setNewSession({ 
                  ...newSession, 
                  workspaceId: e.target.value ? parseInt(e.target.value) : undefined 
                })}
                placeholder="Enter workspace ID"
              />
            </div>
            
            <div className="form-group">
              <label>Task ID (optional)</label>
              <input
                type="number"
                value={newSession.taskId || ''}
                onChange={(e) => setNewSession({ 
                  ...newSession, 
                  taskId: e.target.value ? parseInt(e.target.value) : undefined 
                })}
                placeholder="Enter task ID"
              />
            </div>
          </div>
          
          <div className="form-group full-width">
            <label>Description (optional)</label>
            <input
              type="text"
              value={newSession.description}
              onChange={(e) => setNewSession({ ...newSession, description: e.target.value })}
              placeholder="Describe what you're working on..."
            />
          </div>
          
          <button
            onClick={startTimeTracking}
            disabled={startingSession}
            className="start-session-btn"
          >
            {startingSession ? 'Starting...' : 'Start Time Tracking'}
          </button>
        </div>
      </div>

      {/* Time Distribution Charts */}
      {timeDistribution && (
        <div className="time-distribution-section">
          <h3>Time Distribution Analysis</h3>
          
          <div className="distribution-stats">
            <div className="total-hours">
              <span className="label">Total Tracked Time:</span>
              <span className="value">{timeDistribution.totalHours.toFixed(1)} hours</span>
            </div>
            <div className="period-info">
              <span className="label">Period:</span>
              <span className="value">{timeDistribution.periodDays} days</span>
            </div>
          </div>

          <div className="charts-grid">
            {/* Category Distribution */}
            <div className="chart-container">
              <h4>Time by Category</h4>
              <ResponsiveContainer width="100%" height={300}>
                <PieChart>
                  <Pie
                    data={timeDistribution.categoryDistribution}
                    cx="50%"
                    cy="50%"
                    innerRadius={60}
                    outerRadius={100}
                    paddingAngle={5}
                    dataKey="value"
                  >
                    {timeDistribution.categoryDistribution.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                    ))}
                  </Pie>
                  <Tooltip formatter={(value: number) => [`${value.toFixed(1)}h`, 'Hours']} />
                  <Legend />
                </PieChart>
              </ResponsiveContainer>
            </div>

            {/* Activity Distribution */}
            <div className="chart-container">
              <h4>Time by Activity Type</h4>
              <ResponsiveContainer width="100%" height={300}>
                <BarChart data={timeDistribution.activityDistribution}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="name" />
                  <YAxis />
                  <Tooltip formatter={(value: number) => [`${value.toFixed(1)}h`, 'Hours']} />
                  <Bar dataKey="value" fill="#00C49F" />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </div>

          {/* Time Distribution Table */}
          <div className="distribution-table">
            <h4>Detailed Breakdown</h4>
            <table>
              <thead>
                <tr>
                  <th>Category</th>
                  <th>Hours</th>
                  <th>Percentage</th>
                </tr>
              </thead>
              <tbody>
                {timeDistribution.categoryDistribution.map((item, index) => (
                  <tr key={index}>
                    <td>{item.name}</td>
                    <td>{item.value.toFixed(1)}h</td>
                    <td>{((item.value / timeDistribution.totalHours) * 100).toFixed(1)}%</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Tips and Recommendations */}
      <div className="time-tracking-tips">
        <h3>Time Tracking Tips</h3>
        <div className="tips-grid">
          <div className="tip-card">
            <div className="tip-icon">⏰</div>
            <div className="tip-content">
              <h4>Track Everything</h4>
              <p>Track all work activities, including meetings, breaks, and administrative tasks for accurate insights.</p>
            </div>
          </div>
          
          <div className="tip-card">
            <div className="tip-icon">🎯</div>
            <div className="tip-content">
              <h4>Set Focus Goals</h4>
              <p>Aim for 4-6 hours of focused work per day. Track your focus score to improve concentration.</p>
            </div>
          </div>
          
          <div className="tip-card">
            <div className="tip-icon">📊</div>
            <div className="tip-content">
              <h4>Review Weekly</h4>
              <p>Review your time distribution weekly to identify patterns and optimization opportunities.</p>
            </div>
          </div>
          
          <div className="tip-card">
            <div className="tip-icon">⚡</div>
            <div className="tip-content">
              <h4>Use Time Blocks</h4>
              <p>Block specific times for different types of work to maintain better focus and productivity.</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

// Active Session Card Component
const ActiveSessionCard: React.FC<{
  session: TimeTrackingSession;
  onEnd: (focusScore?: number) => void;
  formatDuration: (seconds: number) => string;
}> = ({ session, onEnd, formatDuration }) => {
  const [focusScore, setFocusScore] = useState<number>(75);
  const [showEndForm, setShowEndForm] = useState(false);

  return (
    <div className="active-session-card">
      <div className="session-info">
        <div className="session-header">
          <span className="activity-type">{session.activityType}</span>
          <span className="category-badge">{session.category}</span>
        </div>
        
        <div className="session-description">
          {session.description || 'No description'}
        </div>
        
        <div className="session-meta">
          <span>Started: {new Date(session.startTime).toLocaleTimeString()}</span>
          {session.workspaceId && <span>Workspace: {session.workspaceId}</span>}
          {session.taskId && <span>Task: {session.taskId}</span>}
        </div>
      </div>
      
      <div className="session-duration">
        <div className="duration-display">
          {formatDuration(session.currentDurationSeconds)}
        </div>
        <div className="duration-label">Duration</div>
      </div>
      
      <div className="session-actions">
        {!showEndForm ? (
          <button
            onClick={() => setShowEndForm(true)}
            className="end-session-btn"
          >
            End Session
          </button>
        ) : (
          <div className="end-session-form">
            <div className="focus-score-input">
              <label>Focus Score (0-100):</label>
              <input
                type="range"
                min="0"
                max="100"
                value={focusScore}
                onChange={(e) => setFocusScore(parseInt(e.target.value))}
              />
              <span>{focusScore}</span>
            </div>
            <div className="form-actions">
              <button
                onClick={() => onEnd(focusScore)}
                className="confirm-end-btn"
              >
                End
              </button>
              <button
                onClick={() => setShowEndForm(false)}
                className="cancel-btn"
              >
                Cancel
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default TimeTrackingDashboard;