import React, { useState, useEffect } from 'react';
import { performanceMonitor } from '../utils/performanceMonitor';

const PerformanceDashboard: React.FC = () => {
  const [metrics, setMetrics] = useState<any[]>([]);
  const [coreWebVitals, setCoreWebVitals] = useState<Record<string, number>>({});
  const [performanceScore, setPerformanceScore] = useState<number>(0);
  const [isVisible, setIsVisible] = useState(false);

  useEffect(() => {
    loadPerformanceData();
    const interval = setInterval(loadPerformanceData, 5000);
    return () => clearInterval(interval);
  }, []);

  const loadPerformanceData = () => {
    setMetrics(performanceMonitor.getMetrics());
    setCoreWebVitals(performanceMonitor.getCoreWebVitals());
    setPerformanceScore(performanceMonitor.getPerformanceScore());
  };

  const getScoreColor = (score: number) => {
    if (score >= 90) return '#10b981'; // Green
    if (score >= 70) return '#f59e0b'; // Yellow
    return '#ef4444'; // Red
  };

  const getVitalStatus = (name: string, value: number) => {
    const thresholds = {
      'First Contentful Paint': { good: 1500, poor: 2500 },
      'Largest Contentful Paint': { good: 2500, poor: 4000 },
      'Cumulative Layout Shift': { good: 0.1, poor: 0.25 }
    };

    const threshold = thresholds[name as keyof typeof thresholds];
    if (!threshold) return 'unknown';

    if (name === 'Cumulative Layout Shift') {
      if (value <= threshold.good) return 'good';
      if (value <= threshold.poor) return 'needs-improvement';
      return 'poor';
    } else {
      if (value <= threshold.good) return 'good';
      if (value <= threshold.poor) return 'needs-improvement';
      return 'poor';
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'good': return '#10b981';
      case 'needs-improvement': return '#f59e0b';
      case 'poor': return '#ef4444';
      default: return '#6b7280';
    }
  };

  const formatValue = (name: string, value: number) => {
    if (name === 'Cumulative Layout Shift') {
      return value.toFixed(3);
    }
    if (name.includes('Size') || name.includes('Heap')) {
      return `${(value / 1024 / 1024).toFixed(1)} MB`;
    }
    return `${value.toFixed(0)}ms`;
  };

  const exportReport = () => {
    const report = performanceMonitor.exportReport();
    const blob = new Blob([report], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `performance-report-${Date.now()}.json`;
    a.click();
    URL.revokeObjectURL(url);
  };

  if (!isVisible) {
    return (
      <button
        onClick={() => setIsVisible(true)}
        style={{
          position: 'fixed',
          bottom: '80px',
          right: '20px',
          zIndex: 9998,
          padding: '10px 15px',
          backgroundColor: getScoreColor(performanceScore),
          color: 'white',
          border: 'none',
          borderRadius: '50px',
          cursor: 'pointer',
          fontSize: '12px',
          boxShadow: '0 4px 12px rgba(0,0,0,0.15)'
        }}
      >
        ⚡ Score: {performanceScore}
      </button>
    );
  }

  return (
    <div style={{
      position: 'fixed',
      top: '20px',
      left: '20px',
      width: '400px',
      maxHeight: '600px',
      backgroundColor: 'white',
      border: '1px solid #e5e7eb',
      borderRadius: '8px',
      boxShadow: '0 10px 25px rgba(0,0,0,0.15)',
      zIndex: 9998,
      overflow: 'hidden'
    }}>
      {/* Header */}
      <div style={{
        padding: '15px',
        backgroundColor: '#f8fafc',
        borderBottom: '1px solid #e5e7eb',
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center'
      }}>
        <h3 style={{ margin: 0, fontSize: '16px', color: '#1f2937' }}>
          Performance Dashboard
        </h3>
        <button
          onClick={() => setIsVisible(false)}
          style={{
            background: 'none',
            border: 'none',
            fontSize: '20px',
            cursor: 'pointer',
            color: '#6b7280'
          }}
        >
          ×
        </button>
      </div>

      {/* Performance Score */}
      <div style={{
        padding: '20px',
        textAlign: 'center',
        borderBottom: '1px solid #e5e7eb'
      }}>
        <div style={{
          fontSize: '48px',
          fontWeight: 'bold',
          color: getScoreColor(performanceScore),
          marginBottom: '5px'
        }}>
          {performanceScore}
        </div>
        <div style={{ fontSize: '14px', color: '#6b7280' }}>
          Performance Score
        </div>
      </div>

      {/* Core Web Vitals */}
      <div style={{ padding: '15px' }}>
        <h4 style={{ margin: '0 0 15px 0', fontSize: '14px', color: '#374151' }}>
          Core Web Vitals
        </h4>
        
        {Object.entries(coreWebVitals).map(([name, value]) => {
          const status = getVitalStatus(name, value);
          return (
            <div key={name} style={{
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'center',
              padding: '8px 0',
              borderBottom: '1px solid #f3f4f6'
            }}>
              <div style={{ fontSize: '12px', color: '#374151' }}>
                {name.replace(/([A-Z])/g, ' $1').trim()}
              </div>
              <div style={{
                display: 'flex',
                alignItems: 'center',
                gap: '8px'
              }}>
                <span style={{ fontSize: '12px', fontWeight: 'bold' }}>
                  {formatValue(name, value)}
                </span>
                <div style={{
                  width: '8px',
                  height: '8px',
                  borderRadius: '50%',
                  backgroundColor: getStatusColor(status)
                }} />
              </div>
            </div>
          );
        })}
      </div>

      {/* Recent Metrics */}
      <div style={{
        maxHeight: '200px',
        overflowY: 'auto',
        margin: '0 15px'
      }}>
        <h4 style={{ margin: '10px 0', fontSize: '14px', color: '#374151' }}>
          Recent Metrics
        </h4>
        {metrics.slice(-8).reverse().map((metric, index) => (
          <div key={index} style={{
            padding: '6px 0',
            fontSize: '11px',
            display: 'flex',
            justifyContent: 'space-between',
            borderBottom: '1px solid #f9fafb'
          }}>
            <span style={{ color: '#6b7280', flex: 1 }}>
              {metric.name}
            </span>
            <span style={{ fontWeight: 'bold', color: '#374151' }}>
              {formatValue(metric.name, metric.value)}
            </span>
          </div>
        ))}
      </div>

      {/* Actions */}
      <div style={{
        padding: '15px',
        borderTop: '1px solid #e5e7eb',
        display: 'flex',
        gap: '10px'
      }}>
        <button
          onClick={loadPerformanceData}
          style={{
            flex: 1,
            padding: '8px',
            backgroundColor: '#f3f4f6',
            color: '#374151',
            border: '1px solid #d1d5db',
            borderRadius: '4px',
            fontSize: '12px',
            cursor: 'pointer'
          }}
        >
          Refresh
        </button>
        <button
          onClick={exportReport}
          style={{
            flex: 1,
            padding: '8px',
            backgroundColor: '#10b981',
            color: 'white',
            border: 'none',
            borderRadius: '4px',
            fontSize: '12px',
            cursor: 'pointer'
          }}
        >
          Export
        </button>
      </div>

      {/* Performance Tips */}
      {performanceScore < 70 && (
        <div style={{
          margin: '15px',
          padding: '10px',
          backgroundColor: '#fef3c7',
          borderRadius: '6px',
          fontSize: '11px'
        }}>
          <strong style={{ color: '#92400e' }}>Tips:</strong>
          <ul style={{ margin: '5px 0', paddingLeft: '15px', color: '#92400e' }}>
            <li>Enable lazy loading for components</li>
            <li>Optimize images and fonts</li>
            <li>Reduce bundle size with code splitting</li>
            <li>Use React.memo for expensive components</li>
          </ul>
        </div>
      )}
    </div>
  );
};

export default PerformanceDashboard;