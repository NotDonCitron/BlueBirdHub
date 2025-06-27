import React, { useState, useEffect } from 'react';
import { useApi } from '../../contexts/ApiContext';
import './VoiceAnalytics.css';

interface VoiceAnalytics {
  total_commands: number;
  command_types: Record<string, number>;
  success_rate: number;
  average_confidence: number;
  most_used_command: string;
  languages_used: string[];
}

interface VoiceAnalyticsProps {
  onClose: () => void;
}

const VoiceAnalytics: React.FC<VoiceAnalyticsProps> = ({ onClose }) => {
  const api = useApi();
  const [analytics, setAnalytics] = useState<VoiceAnalytics | null>(null);
  const [loading, setLoading] = useState(true);
  const [timeRange, setTimeRange] = useState<'week' | 'month' | 'all'>('week');

  useEffect(() => {
    loadAnalytics();
  }, [timeRange]);

  const loadAnalytics = async () => {
    try {
      setLoading(true);
      const response = await api.get(`/api/voice/analytics?range=${timeRange}`);
      setAnalytics(response);
    } catch (error) {
      console.error('Failed to load voice analytics:', error);
    } finally {
      setLoading(false);
    }
  };

  const formatPercentage = (value: number) => `${(value * 100).toFixed(1)}%`;

  const getTopCommands = () => {
    if (!analytics?.command_types) return [];
    return Object.entries(analytics.command_types)
      .sort(([, a], [, b]) => b - a)
      .slice(0, 5);
  };

  const getCommandTypeIcon = (type: string) => {
    const icons: Record<string, string> = {
      create_task: 'fa-plus',
      update_task: 'fa-edit',
      delete_task: 'fa-trash',
      search_task: 'fa-search',
      navigate: 'fa-compass',
      set_priority: 'fa-flag',
      set_deadline: 'fa-calendar',
      help: 'fa-question-circle'
    };
    return icons[type] || 'fa-microphone';
  };

  const getCommandTypeColor = (type: string) => {
    const colors: Record<string, string> = {
      create_task: '#10b981',
      update_task: '#3b82f6',
      delete_task: '#ef4444',
      search_task: '#8b5cf6',
      navigate: '#f59e0b',
      set_priority: '#ec4899',
      set_deadline: '#06b6d4',
      help: '#6b7280'
    };
    return colors[type] || '#6b7280';
  };

  const exportAnalytics = () => {
    if (!analytics) return;

    const data = {
      exported_at: new Date().toISOString(),
      time_range: timeRange,
      analytics: analytics,
      summary: {
        total_voice_interactions: analytics.total_commands,
        success_rate_percentage: formatPercentage(analytics.success_rate),
        average_confidence_percentage: formatPercentage(analytics.average_confidence),
        top_commands: getTopCommands(),
        languages_used: analytics.languages_used
      }
    };

    const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `voice-analytics-${timeRange}-${new Date().toISOString().split('T')[0]}.json`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  if (loading) {
    return (
      <div className="voice-analytics-overlay">
        <div className="voice-analytics-modal">
          <div className="loading-state">
            <i className="fas fa-spinner fa-spin" />
            <p>Loading voice analytics...</p>
          </div>
        </div>
      </div>
    );
  }

  if (!analytics) {
    return (
      <div className="voice-analytics-overlay">
        <div className="voice-analytics-modal">
          <div className="error-state">
            <i className="fas fa-exclamation-triangle" />
            <p>Failed to load voice analytics</p>
            <button onClick={loadAnalytics}>Retry</button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="voice-analytics-overlay">
      <div className="voice-analytics-modal">
        <div className="voice-analytics-header">
          <h2>Voice Command Analytics</h2>
          <div className="header-controls">
            <select
              value={timeRange}
              onChange={(e) => setTimeRange(e.target.value as 'week' | 'month' | 'all')}
              className="time-range-select"
            >
              <option value="week">Past Week</option>
              <option value="month">Past Month</option>
              <option value="all">All Time</option>
            </select>
            <button className="export-btn" onClick={exportAnalytics}>
              <i className="fas fa-download" /> Export
            </button>
            <button className="close-btn" onClick={onClose}>
              <i className="fas fa-times" />
            </button>
          </div>
        </div>

        <div className="voice-analytics-content">
          {/* Overview Stats */}
          <div className="analytics-overview">
            <div className="stat-card">
              <div className="stat-icon">
                <i className="fas fa-microphone" style={{ color: '#3b82f6' }} />
              </div>
              <div className="stat-info">
                <span className="stat-value">{analytics.total_commands}</span>
                <span className="stat-label">Total Commands</span>
              </div>
            </div>

            <div className="stat-card">
              <div className="stat-icon">
                <i className="fas fa-check-circle" style={{ color: '#10b981' }} />
              </div>
              <div className="stat-info">
                <span className="stat-value">{formatPercentage(analytics.success_rate)}</span>
                <span className="stat-label">Success Rate</span>
              </div>
            </div>

            <div className="stat-card">
              <div className="stat-icon">
                <i className="fas fa-brain" style={{ color: '#8b5cf6' }} />
              </div>
              <div className="stat-info">
                <span className="stat-value">{formatPercentage(analytics.average_confidence)}</span>
                <span className="stat-label">Avg Confidence</span>
              </div>
            </div>

            <div className="stat-card">
              <div className="stat-icon">
                <i className="fas fa-language" style={{ color: '#f59e0b' }} />
              </div>
              <div className="stat-info">
                <span className="stat-value">{analytics.languages_used.length}</span>
                <span className="stat-label">Languages</span>
              </div>
            </div>
          </div>

          {/* Command Types Distribution */}
          <div className="analytics-section">
            <h3>Command Types Distribution</h3>
            <div className="command-types-chart">
              {getTopCommands().map(([type, count]) => {
                const percentage = (count / analytics.total_commands) * 100;
                return (
                  <div key={type} className="command-type-bar">
                    <div className="command-type-info">
                      <i 
                        className={`fas ${getCommandTypeIcon(type)}`}
                        style={{ color: getCommandTypeColor(type) }}
                      />
                      <span className="command-type-name">
                        {type.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}
                      </span>
                      <span className="command-type-count">{count}</span>
                    </div>
                    <div className="command-type-progress">
                      <div 
                        className="command-type-progress-bar"
                        style={{ 
                          width: `${percentage}%`,
                          backgroundColor: getCommandTypeColor(type)
                        }}
                      />
                    </div>
                    <span className="command-type-percentage">
                      {percentage.toFixed(1)}%
                    </span>
                  </div>
                );
              })}
            </div>
          </div>

          {/* Usage Patterns */}
          <div className="analytics-section">
            <h3>Usage Patterns</h3>
            <div className="usage-patterns">
              <div className="pattern-card">
                <h4>Most Used Command</h4>
                <div className="pattern-content">
                  <i 
                    className={`fas ${getCommandTypeIcon(analytics.most_used_command)}`}
                    style={{ color: getCommandTypeColor(analytics.most_used_command) }}
                  />
                  <span>
                    {analytics.most_used_command.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}
                  </span>
                </div>
              </div>

              <div className="pattern-card">
                <h4>Languages Used</h4>
                <div className="pattern-content">
                  <div className="language-list">
                    {analytics.languages_used.map(lang => (
                      <span key={lang} className="language-tag">
                        {lang.toUpperCase()}
                      </span>
                    ))}
                  </div>
                </div>
              </div>

              <div className="pattern-card">
                <h4>Recognition Quality</h4>
                <div className="pattern-content">
                  <div className="quality-indicator">
                    <div className="quality-bar">
                      <div 
                        className="quality-fill"
                        style={{ 
                          width: `${analytics.average_confidence * 100}%`,
                          backgroundColor: analytics.average_confidence > 0.8 ? '#10b981' :
                                         analytics.average_confidence > 0.6 ? '#f59e0b' : '#ef4444'
                        }}
                      />
                    </div>
                    <span className="quality-label">
                      {analytics.average_confidence > 0.8 ? 'Excellent' :
                       analytics.average_confidence > 0.6 ? 'Good' : 'Needs Improvement'}
                    </span>
                  </div>
                </div>
              </div>
            </div>
          </div>

          {/* Insights and Recommendations */}
          <div className="analytics-section">
            <h3>Insights & Recommendations</h3>
            <div className="insights-list">
              {analytics.success_rate < 0.8 && (
                <div className="insight-item warning">
                  <i className="fas fa-exclamation-triangle" />
                  <div className="insight-content">
                    <h4>Low Success Rate</h4>
                    <p>Your voice command success rate is below 80%. Try speaking more clearly or adjusting your microphone settings.</p>
                  </div>
                </div>
              )}

              {analytics.average_confidence < 0.7 && (
                <div className="insight-item info">
                  <i className="fas fa-info-circle" />
                  <div className="insight-content">
                    <h4>Recognition Confidence</h4>
                    <p>Voice recognition confidence could be improved. Consider training your voice profile or using a better microphone.</p>
                  </div>
                </div>
              )}

              {analytics.total_commands > 50 && (
                <div className="insight-item success">
                  <i className="fas fa-star" />
                  <div className="insight-content">
                    <h4>Active Voice User</h4>
                    <p>Great job! You're actively using voice commands. Consider creating custom shortcuts for your most frequent actions.</p>
                  </div>
                </div>
              )}

              {analytics.languages_used.length > 1 && (
                <div className="insight-item info">
                  <i className="fas fa-globe" />
                  <div className="insight-content">
                    <h4>Multilingual Usage</h4>
                    <p>You're using voice commands in multiple languages. Make sure each language is properly configured for best results.</p>
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default VoiceAnalytics;