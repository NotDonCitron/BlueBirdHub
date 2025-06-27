/**
 * Report Generator - Component for creating custom analytics reports
 */

import React, { useState, useEffect, useCallback } from 'react';
import './ReportGenerator.css';

interface ReportTemplate {
  id: string;
  name: string;
  description: string;
  category: string;
  defaultMetrics: string[];
  recommendedFor: string[];
}

interface ReportConfig {
  name: string;
  reportType: string;
  format: 'pdf' | 'csv' | 'xlsx' | 'json';
  dateRangeStart: string;
  dateRangeEnd: string;
  metricsIncluded: string[];
  filters: {
    userIds?: number[];
    workspaceIds?: number[];
    teamIds?: number[];
    categories?: string[];
  };
}

interface GeneratedReport {
  id: string;
  name: string;
  status: 'pending' | 'generating' | 'completed' | 'failed';
  format: string;
  createdAt: string;
  downloadUrl?: string;
  fileSizeBytes?: number;
  error?: string;
}

const ReportGenerator: React.FC<{ userId: number }> = ({ userId }) => {
  const [templates, setTemplates] = useState<ReportTemplate[]>([]);
  const [reports, setReports] = useState<GeneratedReport[]>([]);
  const [selectedTemplate, setSelectedTemplate] = useState<ReportTemplate | null>(null);
  const [reportConfig, setReportConfig] = useState<ReportConfig>({
    name: '',
    reportType: 'productivity',
    format: 'pdf',
    dateRangeStart: new Date(Date.now() - 30 * 24 * 60 * 60 * 1000).toISOString().split('T')[0],
    dateRangeEnd: new Date().toISOString().split('T')[0],
    metricsIncluded: [],
    filters: {}
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [showAdvanced, setShowAdvanced] = useState(false);

  // Available metrics
  const availableMetrics = [
    { id: 'task_completion_rate', name: 'Task Completion Rate', category: 'productivity' },
    { id: 'time_tracking', name: 'Time Tracking Data', category: 'productivity' },
    { id: 'focus_scores', name: 'Focus Scores', category: 'productivity' },
    { id: 'collaboration_activity', name: 'Collaboration Activity', category: 'collaboration' },
    { id: 'meeting_attendance', name: 'Meeting Attendance', category: 'collaboration' },
    { id: 'file_sharing', name: 'File Sharing Activity', category: 'collaboration' },
    { id: 'team_performance', name: 'Team Performance', category: 'team' },
    { id: 'workload_distribution', name: 'Workload Distribution', category: 'team' },
    { id: 'goal_achievement', name: 'Goal Achievement', category: 'goals' },
    { id: 'kpi_progress', name: 'KPI Progress', category: 'goals' },
    { id: 'productivity_trends', name: 'Productivity Trends', category: 'analytics' },
    { id: 'activity_patterns', name: 'Activity Patterns', category: 'analytics' },
    { id: 'insights_summary', name: 'AI Insights Summary', category: 'analytics' }
  ];

  // Load templates and reports
  useEffect(() => {
    loadTemplates();
    loadReports();
  }, []);

  const loadTemplates = () => {
    const sampleTemplates: ReportTemplate[] = [
      {
        id: 'individual_productivity',
        name: 'Individual Productivity Report',
        description: 'Comprehensive personal productivity analysis including tasks, time tracking, and goal progress',
        category: 'productivity',
        defaultMetrics: ['task_completion_rate', 'time_tracking', 'focus_scores', 'goal_achievement'],
        recommendedFor: ['individual_users', 'managers']
      },
      {
        id: 'team_performance',
        name: 'Team Performance Report',
        description: 'Team-wide analytics including collaboration, workload distribution, and collective achievements',
        category: 'team',
        defaultMetrics: ['team_performance', 'workload_distribution', 'collaboration_activity', 'meeting_attendance'],
        recommendedFor: ['team_leaders', 'managers', 'hr']
      },
      {
        id: 'executive_summary',
        name: 'Executive Summary',
        description: 'High-level overview of organizational productivity and key metrics',
        category: 'executive',
        defaultMetrics: ['productivity_trends', 'team_performance', 'goal_achievement', 'insights_summary'],
        recommendedFor: ['executives', 'directors']
      },
      {
        id: 'weekly_digest',
        name: 'Weekly Digest',
        description: 'Weekly summary of activities, achievements, and areas for improvement',
        category: 'digest',
        defaultMetrics: ['task_completion_rate', 'collaboration_activity', 'focus_scores', 'activity_patterns'],
        recommendedFor: ['all_users']
      },
      {
        id: 'goal_tracking',
        name: 'Goal Tracking Report',
        description: 'Detailed analysis of goal progress, KPI achievements, and recommended actions',
        category: 'goals',
        defaultMetrics: ['goal_achievement', 'kpi_progress', 'productivity_trends'],
        recommendedFor: ['goal_oriented_users', 'managers']
      }
    ];
    
    setTemplates(sampleTemplates);
  };

  const loadReports = useCallback(async () => {
    try {
      // This would fetch from API
      const sampleReports: GeneratedReport[] = [
        {
          id: 'report_001',
          name: 'January Productivity Report',
          status: 'completed',
          format: 'pdf',
          createdAt: '2024-01-25T10:00:00Z',
          downloadUrl: '/api/reports/download/report_001',
          fileSizeBytes: 2048576
        },
        {
          id: 'report_002',
          name: 'Team Performance Q1',
          status: 'completed',
          format: 'xlsx',
          createdAt: '2024-01-20T15:30:00Z',
          downloadUrl: '/api/reports/download/report_002',
          fileSizeBytes: 1024000
        },
        {
          id: 'report_003',
          name: 'Weekly Digest',
          status: 'generating',
          format: 'pdf',
          createdAt: '2024-01-25T14:00:00Z'
        }
      ];
      
      setReports(sampleReports);
    } catch (err) {
      console.error('Failed to load reports:', err);
    }
  }, []);

  // Select template and configure
  const selectTemplate = (template: ReportTemplate) => {
    setSelectedTemplate(template);
    setReportConfig(prev => ({
      ...prev,
      name: template.name,
      reportType: template.category,
      metricsIncluded: template.defaultMetrics
    }));
  };

  // Generate report
  const generateReport = async () => {
    try {
      setLoading(true);
      setError(null);

      const response = await fetch('/api/analytics/export/report', {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
        },
        // In real implementation, this would be a POST with the config
      });

      if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);

      const result = await response.json();
      
      // Add to reports list
      const newReport: GeneratedReport = {
        id: result.report_id,
        name: reportConfig.name,
        status: 'generating',
        format: reportConfig.format,
        createdAt: new Date().toISOString()
      };
      
      setReports(prev => [newReport, ...prev]);
      
      // Reset form
      setReportConfig({
        name: '',
        reportType: 'productivity',
        format: 'pdf',
        dateRangeStart: new Date(Date.now() - 30 * 24 * 60 * 60 * 1000).toISOString().split('T')[0],
        dateRangeEnd: new Date().toISOString().split('T')[0],
        metricsIncluded: [],
        filters: {}
      });
      setSelectedTemplate(null);

    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to generate report');
    } finally {
      setLoading(false);
    }
  };

  // Download report
  const downloadReport = (report: GeneratedReport) => {
    if (report.downloadUrl) {
      const link = document.createElement('a');
      link.href = report.downloadUrl;
      link.download = `${report.name}.${report.format}`;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
    }
  };

  // Format file size
  const formatFileSize = (bytes: number): string => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  return (
    <div className="report-generator">
      <div className="generator-header">
        <h2>Report Generator</h2>
        <p>Create custom analytics reports with your data</p>
      </div>

      {error && (
        <div className="error-banner">
          <span>⚠️ {error}</span>
          <button onClick={() => setError(null)} className="close-btn">×</button>
        </div>
      )}

      <div className="generator-content">
        {/* Templates Section */}
        <div className="templates-section">
          <h3>Choose a Template</h3>
          <div className="templates-grid">
            {templates.map(template => (
              <div
                key={template.id}
                className={`template-card ${selectedTemplate?.id === template.id ? 'selected' : ''}`}
                onClick={() => selectTemplate(template)}
              >
                <div className="template-header">
                  <h4>{template.name}</h4>
                  <div className="template-category">{template.category}</div>
                </div>
                <p className="template-description">{template.description}</p>
                <div className="template-metrics">
                  <span className="metrics-label">Includes:</span>
                  <div className="metrics-list">
                    {template.defaultMetrics.slice(0, 3).map(metric => (
                      <span key={metric} className="metric-tag">
                        {availableMetrics.find(m => m.id === metric)?.name}
                      </span>
                    ))}
                    {template.defaultMetrics.length > 3 && (
                      <span className="more-metrics">+{template.defaultMetrics.length - 3} more</span>
                    )}
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Configuration Section */}
        {selectedTemplate && (
          <div className="config-section">
            <h3>Configure Report</h3>
            <div className="config-form">
              <div className="form-grid">
                <div className="form-group">
                  <label>Report Name</label>
                  <input
                    type="text"
                    value={reportConfig.name}
                    onChange={(e) => setReportConfig(prev => ({ ...prev, name: e.target.value }))}
                    placeholder="Enter report name"
                  />
                </div>

                <div className="form-group">
                  <label>Format</label>
                  <select
                    value={reportConfig.format}
                    onChange={(e) => setReportConfig(prev => ({ 
                      ...prev, 
                      format: e.target.value as 'pdf' | 'csv' | 'xlsx' | 'json' 
                    }))}
                  >
                    <option value="pdf">PDF Document</option>
                    <option value="xlsx">Excel Spreadsheet</option>
                    <option value="csv">CSV File</option>
                    <option value="json">JSON Data</option>
                  </select>
                </div>

                <div className="form-group">
                  <label>Start Date</label>
                  <input
                    type="date"
                    value={reportConfig.dateRangeStart}
                    onChange={(e) => setReportConfig(prev => ({ ...prev, dateRangeStart: e.target.value }))}
                  />
                </div>

                <div className="form-group">
                  <label>End Date</label>
                  <input
                    type="date"
                    value={reportConfig.dateRangeEnd}
                    onChange={(e) => setReportConfig(prev => ({ ...prev, dateRangeEnd: e.target.value }))}
                  />
                </div>
              </div>

              {/* Metrics Selection */}
              <div className="metrics-section">
                <h4>Included Metrics</h4>
                <div className="metrics-grid">
                  {availableMetrics.map(metric => (
                    <label key={metric.id} className="metric-checkbox">
                      <input
                        type="checkbox"
                        checked={reportConfig.metricsIncluded.includes(metric.id)}
                        onChange={(e) => {
                          const { checked } = e.target;
                          setReportConfig(prev => ({
                            ...prev,
                            metricsIncluded: checked
                              ? [...prev.metricsIncluded, metric.id]
                              : prev.metricsIncluded.filter(m => m !== metric.id)
                          }));
                        }}
                      />
                      <span className="metric-name">{metric.name}</span>
                      <span className="metric-category">{metric.category}</span>
                    </label>
                  ))}
                </div>
              </div>

              {/* Advanced Filters */}
              <div className="advanced-section">
                <button
                  onClick={() => setShowAdvanced(!showAdvanced)}
                  className="advanced-toggle"
                >
                  {showAdvanced ? '▼' : '▶'} Advanced Filters
                </button>

                {showAdvanced && (
                  <div className="advanced-filters">
                    <div className="filter-group">
                      <label>User IDs (comma-separated)</label>
                      <input
                        type="text"
                        placeholder="e.g., 1,2,3"
                        onChange={(e) => {
                          const ids = e.target.value.split(',').map(id => parseInt(id.trim())).filter(id => !isNaN(id));
                          setReportConfig(prev => ({
                            ...prev,
                            filters: { ...prev.filters, userIds: ids.length > 0 ? ids : undefined }
                          }));
                        }}
                      />
                    </div>

                    <div className="filter-group">
                      <label>Workspace IDs (comma-separated)</label>
                      <input
                        type="text"
                        placeholder="e.g., 1,2,3"
                        onChange={(e) => {
                          const ids = e.target.value.split(',').map(id => parseInt(id.trim())).filter(id => !isNaN(id));
                          setReportConfig(prev => ({
                            ...prev,
                            filters: { ...prev.filters, workspaceIds: ids.length > 0 ? ids : undefined }
                          }));
                        }}
                      />
                    </div>

                    <div className="filter-group">
                      <label>Categories</label>
                      <select
                        multiple
                        onChange={(e) => {
                          const categories = Array.from(e.target.selectedOptions, option => option.value);
                          setReportConfig(prev => ({
                            ...prev,
                            filters: { ...prev.filters, categories: categories.length > 0 ? categories : undefined }
                          }));
                        }}
                      >
                        <option value="productivity">Productivity</option>
                        <option value="collaboration">Collaboration</option>
                        <option value="system">System</option>
                        <option value="other">Other</option>
                      </select>
                    </div>
                  </div>
                )}
              </div>

              <div className="generate-section">
                <button
                  onClick={generateReport}
                  disabled={loading || !reportConfig.name || reportConfig.metricsIncluded.length === 0}
                  className="generate-btn"
                >
                  {loading ? 'Generating...' : 'Generate Report'}
                </button>
              </div>
            </div>
          </div>
        )}

        {/* Generated Reports */}
        <div className="reports-section">
          <h3>Generated Reports</h3>
          {reports.length === 0 ? (
            <div className="no-reports">
              <p>No reports generated yet. Create your first report using the templates above.</p>
            </div>
          ) : (
            <div className="reports-list">
              {reports.map(report => (
                <div key={report.id} className={`report-card ${report.status}`}>
                  <div className="report-info">
                    <div className="report-header">
                      <h4>{report.name}</h4>
                      <div className={`status-badge ${report.status}`}>
                        {report.status === 'generating' && '⏳'}
                        {report.status === 'completed' && '✅'}
                        {report.status === 'failed' && '❌'}
                        {report.status === 'pending' && '⏸️'}
                        {report.status}
                      </div>
                    </div>
                    
                    <div className="report-meta">
                      <span>Format: {report.format.toUpperCase()}</span>
                      <span>Created: {new Date(report.createdAt).toLocaleDateString()}</span>
                      {report.fileSizeBytes && (
                        <span>Size: {formatFileSize(report.fileSizeBytes)}</span>
                      )}
                    </div>

                    {report.error && (
                      <div className="report-error">
                        Error: {report.error}
                      </div>
                    )}
                  </div>

                  <div className="report-actions">
                    {report.status === 'completed' && report.downloadUrl && (
                      <button
                        onClick={() => downloadReport(report)}
                        className="download-btn"
                      >
                        Download
                      </button>
                    )}
                    {report.status === 'generating' && (
                      <div className="progress-indicator">
                        <div className="progress-bar">
                          <div className="progress-fill"></div>
                        </div>
                      </div>
                    )}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default ReportGenerator;