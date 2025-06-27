/**
 * KPI Dashboard - Component for tracking Key Performance Indicators and goals
 */

import React, { useState, useEffect, useCallback } from 'react';
import {
  LineChart, Line, AreaChart, Area, BarChart, Bar, RadialBarChart, RadialBar,
  ResponsiveContainer, XAxis, YAxis, CartesianGrid, Tooltip, Legend, PieChart, Pie, Cell
} from 'recharts';
import './KPIDashboard.css';

interface KPI {
  id: number;
  name: string;
  description?: string;
  category: string;
  metricType: string;
  targetValue: number;
  currentValue: number;
  unit?: string;
  progressPercentage: number;
  status: string;
  isAchieved: boolean;
  startDate: string;
  endDate: string;
  lastMeasuredAt?: string;
}

interface KPICreate {
  name: string;
  description?: string;
  category: string;
  metricType: string;
  targetValue: number;
  unit?: string;
  startDate: string;
  endDate: string;
  measurementFrequency: string;
  alertThreshold?: number;
}

interface GoalCategory {
  name: string;
  count: number;
  achieved: number;
  averageProgress: number;
}

const KPIDashboard: React.FC<{ userId: number }> = ({ userId }) => {
  const [kpis, setKpis] = useState<KPI[]>([]);
  const [categories, setCategories] = useState<GoalCategory[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showCreateForm, setShowCreateForm] = useState(false);
  const [selectedKPI, setSelectedKPI] = useState<KPI | null>(null);
  
  // Form state
  const [newKPI, setNewKPI] = useState<KPICreate>({
    name: '',
    description: '',
    category: 'productivity',
    metricType: 'count',
    targetValue: 100,
    unit: '',
    startDate: new Date().toISOString().split('T')[0],
    endDate: new Date(Date.now() + 30 * 24 * 60 * 60 * 1000).toISOString().split('T')[0],
    measurementFrequency: 'daily',
    alertThreshold: undefined
  });

  // Fetch KPIs
  const fetchKPIs = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      
      // This would be implemented as a real API endpoint
      // For now, we'll simulate with sample data
      const sampleKPIs: KPI[] = [
        {
          id: 1,
          name: 'Daily Task Completion',
          description: 'Complete at least 5 tasks per day',
          category: 'productivity',
          metricType: 'count',
          targetValue: 150,
          currentValue: 127,
          unit: 'tasks',
          progressPercentage: 84.7,
          status: 'active',
          isAchieved: false,
          startDate: '2024-01-01',
          endDate: '2024-01-31',
          lastMeasuredAt: '2024-01-25T10:00:00Z'
        },
        {
          id: 2,
          name: 'Focus Time',
          description: 'Maintain 6+ hours of focused work daily',
          category: 'productivity',
          metricType: 'time',
          targetValue: 180,
          currentValue: 164,
          unit: 'hours',
          progressPercentage: 91.1,
          status: 'active',
          isAchieved: false,
          startDate: '2024-01-01',
          endDate: '2024-01-31',
          lastMeasuredAt: '2024-01-25T18:00:00Z'
        },
        {
          id: 3,
          name: 'Team Collaboration',
          description: 'Participate in team discussions regularly',
          category: 'collaboration',
          metricType: 'count',
          targetValue: 50,
          currentValue: 53,
          unit: 'comments',
          progressPercentage: 106.0,
          status: 'active',
          isAchieved: true,
          startDate: '2024-01-01',
          endDate: '2024-01-31',
          lastMeasuredAt: '2024-01-25T16:30:00Z'
        },
        {
          id: 4,
          name: 'Learning Goals',
          description: 'Complete learning sessions weekly',
          category: 'development',
          metricType: 'count',
          targetValue: 20,
          currentValue: 12,
          unit: 'sessions',
          progressPercentage: 60.0,
          status: 'active',
          isAchieved: false,
          startDate: '2024-01-01',
          endDate: '2024-01-31',
          lastMeasuredAt: '2024-01-23T14:00:00Z'
        }
      ];
      
      setKpis(sampleKPIs);
      
      // Calculate categories
      const categoryMap = new Map<string, { count: number; achieved: number; totalProgress: number }>();
      
      sampleKPIs.forEach(kpi => {
        const existing = categoryMap.get(kpi.category) || { count: 0, achieved: 0, totalProgress: 0 };
        categoryMap.set(kpi.category, {
          count: existing.count + 1,
          achieved: existing.achieved + (kpi.isAchieved ? 1 : 0),
          totalProgress: existing.totalProgress + kpi.progressPercentage
        });
      });
      
      const categoryStats: GoalCategory[] = Array.from(categoryMap.entries()).map(([name, stats]) => ({
        name,
        count: stats.count,
        achieved: stats.achieved,
        averageProgress: stats.totalProgress / stats.count
      }));
      
      setCategories(categoryStats);
      
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch KPIs');
    } finally {
      setLoading(false);
    }
  }, [userId]);

  useEffect(() => {
    fetchKPIs();
  }, [fetchKPIs]);

  // Create KPI
  const createKPI = async () => {
    try {
      // This would make a real API call
      console.log('Creating KPI:', newKPI);
      
      // Reset form and close
      setNewKPI({
        name: '',
        description: '',
        category: 'productivity',
        metricType: 'count',
        targetValue: 100,
        unit: '',
        startDate: new Date().toISOString().split('T')[0],
        endDate: new Date(Date.now() + 30 * 24 * 60 * 60 * 1000).toISOString().split('T')[0],
        measurementFrequency: 'daily',
        alertThreshold: undefined
      });
      setShowCreateForm(false);
      
      // Refresh KPIs
      await fetchKPIs();
      
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to create KPI');
    }
  };

  // Update KPI progress (simulate)
  const updateKPIProgress = async (kpiId: number, newValue: number) => {
    try {
      setKpis(prevKpis => prevKpis.map(kpi => {
        if (kpi.id === kpiId) {
          const progressPercentage = (newValue / kpi.targetValue) * 100;
          return {
            ...kpi,
            currentValue: newValue,
            progressPercentage,
            isAchieved: progressPercentage >= 100,
            lastMeasuredAt: new Date().toISOString()
          };
        }
        return kpi;
      }));
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to update KPI');
    }
  };

  // Calculate overall progress
  const overallProgress = kpis.length > 0 
    ? kpis.reduce((sum, kpi) => sum + kpi.progressPercentage, 0) / kpis.length 
    : 0;
  
  const achievedGoals = kpis.filter(kpi => kpi.isAchieved).length;

  // Colors for charts
  const COLORS = ['#00C49F', '#0088FE', '#FFBB28', '#FF8042', '#8884d8'];

  if (loading) {
    return (
      <div className="kpi-dashboard loading">
        <div className="loading-spinner"></div>
        <p>Loading KPI dashboard...</p>
      </div>
    );
  }

  return (
    <div className="kpi-dashboard">
      <div className="dashboard-header">
        <div className="header-content">
          <h2>KPI & Goals Dashboard</h2>
          <p>Track your key performance indicators and achieve your goals</p>
        </div>
        <button
          onClick={() => setShowCreateForm(true)}
          className="create-kpi-btn"
        >
          + Create KPI
        </button>
      </div>

      {error && (
        <div className="error-banner">
          <span>⚠️ {error}</span>
          <button onClick={fetchKPIs} className="retry-btn">Retry</button>
        </div>
      )}

      {/* Overview Cards */}
      <div className="overview-cards">
        <div className="overview-card">
          <div className="card-content">
            <div className="card-header">
              <h3>Total KPIs</h3>
              <div className="card-icon">🎯</div>
            </div>
            <div className="card-value">{kpis.length}</div>
            <div className="card-subtitle">Active goals</div>
          </div>
        </div>

        <div className="overview-card">
          <div className="card-content">
            <div className="card-header">
              <h3>Achieved</h3>
              <div className="card-icon">✅</div>
            </div>
            <div className="card-value">{achievedGoals}</div>
            <div className="card-subtitle">Goals completed</div>
          </div>
        </div>

        <div className="overview-card">
          <div className="card-content">
            <div className="card-header">
              <h3>Overall Progress</h3>
              <div className="card-icon">📊</div>
            </div>
            <div className="card-value">{overallProgress.toFixed(1)}%</div>
            <div className="card-subtitle">Average completion</div>
          </div>
        </div>

        <div className="overview-card">
          <div className="card-content">
            <div className="card-header">
              <h3>Categories</h3>
              <div className="card-icon">📂</div>
            </div>
            <div className="card-value">{categories.length}</div>
            <div className="card-subtitle">Goal categories</div>
          </div>
        </div>
      </div>

      {/* Progress Charts */}
      <div className="charts-section">
        <div className="chart-container">
          <h3>Progress by Category</h3>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={categories}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="name" />
              <YAxis />
              <Tooltip />
              <Legend />
              <Bar dataKey="averageProgress" fill="#00C49F" name="Average Progress %" />
            </BarChart>
          </ResponsiveContainer>
        </div>

        <div className="chart-container">
          <h3>Goal Achievement Distribution</h3>
          <ResponsiveContainer width="100%" height={300}>
            <PieChart>
              <Pie
                data={[
                  { name: 'Achieved', value: achievedGoals },
                  { name: 'In Progress', value: kpis.length - achievedGoals }
                ]}
                cx="50%"
                cy="50%"
                innerRadius={60}
                outerRadius={100}
                paddingAngle={5}
                dataKey="value"
              >
                <Cell fill="#00C49F" />
                <Cell fill="#E5E7EB" />
              </Pie>
              <Tooltip />
              <Legend />
            </PieChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* KPI List */}
      <div className="kpi-list-section">
        <h3>Your KPIs</h3>
        <div className="kpi-grid">
          {kpis.map(kpi => (
            <KPICard
              key={kpi.id}
              kpi={kpi}
              onUpdate={(newValue) => updateKPIProgress(kpi.id, newValue)}
              onView={() => setSelectedKPI(kpi)}
            />
          ))}
        </div>
      </div>

      {/* Create KPI Modal */}
      {showCreateForm && (
        <div className="modal-overlay" onClick={() => setShowCreateForm(false)}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h3>Create New KPI</h3>
              <button
                onClick={() => setShowCreateForm(false)}
                className="close-btn"
              >
                ×
              </button>
            </div>

            <div className="modal-body">
              <div className="form-grid">
                <div className="form-group">
                  <label>KPI Name *</label>
                  <input
                    type="text"
                    value={newKPI.name}
                    onChange={(e) => setNewKPI({ ...newKPI, name: e.target.value })}
                    placeholder="e.g., Daily Task Completion"
                    required
                  />
                </div>

                <div className="form-group">
                  <label>Category</label>
                  <select
                    value={newKPI.category}
                    onChange={(e) => setNewKPI({ ...newKPI, category: e.target.value })}
                  >
                    <option value="productivity">Productivity</option>
                    <option value="collaboration">Collaboration</option>
                    <option value="development">Development</option>
                    <option value="quality">Quality</option>
                    <option value="custom">Custom</option>
                  </select>
                </div>

                <div className="form-group">
                  <label>Metric Type</label>
                  <select
                    value={newKPI.metricType}
                    onChange={(e) => setNewKPI({ ...newKPI, metricType: e.target.value })}
                  >
                    <option value="count">Count</option>
                    <option value="percentage">Percentage</option>
                    <option value="ratio">Ratio</option>
                    <option value="score">Score</option>
                    <option value="time">Time</option>
                  </select>
                </div>

                <div className="form-group">
                  <label>Target Value *</label>
                  <input
                    type="number"
                    value={newKPI.targetValue}
                    onChange={(e) => setNewKPI({ ...newKPI, targetValue: parseFloat(e.target.value) })}
                    min="0"
                    step="0.1"
                    required
                  />
                </div>

                <div className="form-group">
                  <label>Unit</label>
                  <input
                    type="text"
                    value={newKPI.unit}
                    onChange={(e) => setNewKPI({ ...newKPI, unit: e.target.value })}
                    placeholder="e.g., tasks, hours, %"
                  />
                </div>

                <div className="form-group">
                  <label>Measurement Frequency</label>
                  <select
                    value={newKPI.measurementFrequency}
                    onChange={(e) => setNewKPI({ ...newKPI, measurementFrequency: e.target.value })}
                  >
                    <option value="daily">Daily</option>
                    <option value="weekly">Weekly</option>
                    <option value="monthly">Monthly</option>
                  </select>
                </div>

                <div className="form-group">
                  <label>Start Date *</label>
                  <input
                    type="date"
                    value={newKPI.startDate}
                    onChange={(e) => setNewKPI({ ...newKPI, startDate: e.target.value })}
                    required
                  />
                </div>

                <div className="form-group">
                  <label>End Date *</label>
                  <input
                    type="date"
                    value={newKPI.endDate}
                    onChange={(e) => setNewKPI({ ...newKPI, endDate: e.target.value })}
                    required
                  />
                </div>

                <div className="form-group full-width">
                  <label>Description</label>
                  <textarea
                    value={newKPI.description}
                    onChange={(e) => setNewKPI({ ...newKPI, description: e.target.value })}
                    placeholder="Describe this KPI and how it will be measured..."
                    rows={3}
                  />
                </div>

                <div className="form-group">
                  <label>Alert Threshold</label>
                  <input
                    type="number"
                    value={newKPI.alertThreshold || ''}
                    onChange={(e) => setNewKPI({ 
                      ...newKPI, 
                      alertThreshold: e.target.value ? parseFloat(e.target.value) : undefined 
                    })}
                    placeholder="Alert when below this value"
                    min="0"
                    step="0.1"
                  />
                </div>
              </div>
            </div>

            <div className="modal-footer">
              <button
                onClick={() => setShowCreateForm(false)}
                className="cancel-btn"
              >
                Cancel
              </button>
              <button
                onClick={createKPI}
                className="create-btn"
                disabled={!newKPI.name || !newKPI.targetValue}
              >
                Create KPI
              </button>
            </div>
          </div>
        </div>
      )}

      {/* KPI Detail Modal */}
      {selectedKPI && (
        <div className="modal-overlay" onClick={() => setSelectedKPI(null)}>
          <div className="modal-content kpi-detail" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h3>{selectedKPI.name}</h3>
              <button
                onClick={() => setSelectedKPI(null)}
                className="close-btn"
              >
                ×
              </button>
            </div>

            <div className="modal-body">
              <KPIDetailView kpi={selectedKPI} />
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

// KPI Card Component
const KPICard: React.FC<{
  kpi: KPI;
  onUpdate: (newValue: number) => void;
  onView: () => void;
}> = ({ kpi, onUpdate, onView }) => {
  const [showUpdateForm, setShowUpdateForm] = useState(false);
  const [newValue, setNewValue] = useState(kpi.currentValue);

  const handleUpdate = () => {
    onUpdate(newValue);
    setShowUpdateForm(false);
  };

  const getStatusColor = (status: string, isAchieved: boolean) => {
    if (isAchieved) return '#00C49F';
    if (status === 'active') return '#0088FE';
    return '#6B7280';
  };

  const progressColor = kpi.isAchieved ? '#00C49F' : 
                      kpi.progressPercentage >= 75 ? '#FFBB28' : 
                      kpi.progressPercentage >= 50 ? '#0088FE' : '#FF8042';

  return (
    <div className={`kpi-card ${kpi.isAchieved ? 'achieved' : ''}`}>
      <div className="kpi-header">
        <div className="kpi-category">{kpi.category}</div>
        <div className={`kpi-status ${kpi.isAchieved ? 'achieved' : 'active'}`}>
          {kpi.isAchieved ? '✅' : '🎯'}
        </div>
      </div>

      <div className="kpi-title">{kpi.name}</div>
      
      {kpi.description && (
        <div className="kpi-description">{kpi.description}</div>
      )}

      <div className="kpi-progress">
        <div className="progress-header">
          <span className="current-value">
            {kpi.currentValue} {kpi.unit}
          </span>
          <span className="target-value">
            / {kpi.targetValue} {kpi.unit}
          </span>
        </div>
        
        <div className="progress-bar">
          <div 
            className="progress-fill"
            style={{ 
              width: `${Math.min(kpi.progressPercentage, 100)}%`,
              backgroundColor: progressColor
            }}
          />
        </div>
        
        <div className="progress-percentage">
          {kpi.progressPercentage.toFixed(1)}%
        </div>
      </div>

      <div className="kpi-dates">
        <span>{new Date(kpi.startDate).toLocaleDateString()}</span>
        <span>→</span>
        <span>{new Date(kpi.endDate).toLocaleDateString()}</span>
      </div>

      <div className="kpi-actions">
        <button onClick={onView} className="view-btn">
          View Details
        </button>
        <button 
          onClick={() => setShowUpdateForm(true)} 
          className="update-btn"
        >
          Update Progress
        </button>
      </div>

      {showUpdateForm && (
        <div className="update-form">
          <div className="form-header">
            <span>Update Progress</span>
            <button onClick={() => setShowUpdateForm(false)}>×</button>
          </div>
          <div className="form-content">
            <input
              type="number"
              value={newValue}
              onChange={(e) => setNewValue(parseFloat(e.target.value))}
              min="0"
              step="0.1"
            />
            <span>{kpi.unit}</span>
          </div>
          <div className="form-actions">
            <button onClick={handleUpdate} className="save-btn">Save</button>
            <button onClick={() => setShowUpdateForm(false)} className="cancel-btn">Cancel</button>
          </div>
        </div>
      )}
    </div>
  );
};

// KPI Detail View Component
const KPIDetailView: React.FC<{ kpi: KPI }> = ({ kpi }) => {
  // Sample progress data - in real app, this would come from API
  const progressData = Array.from({ length: 10 }, (_, i) => ({
    date: new Date(Date.now() - (9 - i) * 24 * 60 * 60 * 1000).toLocaleDateString(),
    value: kpi.currentValue * (0.6 + (i / 9) * 0.4),
    target: kpi.targetValue
  }));

  return (
    <div className="kpi-detail-view">
      <div className="detail-header">
        <div className="detail-meta">
          <span className="category-badge">{kpi.category}</span>
          <span className="metric-type-badge">{kpi.metricType}</span>
          <span className={`status-badge ${kpi.isAchieved ? 'achieved' : 'active'}`}>
            {kpi.isAchieved ? 'Achieved' : 'Active'}
          </span>
        </div>
        
        <div className="detail-progress">
          <div className="big-progress-circle">
            <div className="progress-text">
              <div className="progress-value">{kpi.progressPercentage.toFixed(0)}%</div>
              <div className="progress-label">Complete</div>
            </div>
          </div>
        </div>
      </div>

      <div className="detail-stats">
        <div className="stat-item">
          <div className="stat-label">Current</div>
          <div className="stat-value">{kpi.currentValue} {kpi.unit}</div>
        </div>
        <div className="stat-item">
          <div className="stat-label">Target</div>
          <div className="stat-value">{kpi.targetValue} {kpi.unit}</div>
        </div>
        <div className="stat-item">
          <div className="stat-label">Remaining</div>
          <div className="stat-value">
            {Math.max(0, kpi.targetValue - kpi.currentValue)} {kpi.unit}
          </div>
        </div>
      </div>

      <div className="progress-chart">
        <h4>Progress Over Time</h4>
        <ResponsiveContainer width="100%" height={200}>
          <LineChart data={progressData}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="date" />
            <YAxis />
            <Tooltip />
            <Legend />
            <Line type="monotone" dataKey="value" stroke="#00C49F" strokeWidth={2} name="Current" />
            <Line type="monotone" dataKey="target" stroke="#E5E7EB" strokeDasharray="5 5" name="Target" />
          </LineChart>
        </ResponsiveContainer>
      </div>

      {kpi.lastMeasuredAt && (
        <div className="last-updated">
          Last updated: {new Date(kpi.lastMeasuredAt).toLocaleString()}
        </div>
      )}
    </div>
  );
};

export default KPIDashboard;