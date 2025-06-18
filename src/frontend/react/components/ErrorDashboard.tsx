import React, { useState, useEffect } from 'react';
import { CircuitBreakerFactory } from '../../../utils/circuitBreaker';
import { errorLogger } from '../utils/errorLogger';

interface ErrorMetric {
  timestamp: string;
  type: string;
  message: string;
  component?: string;
  count: number;
}

interface ErrorStats {
  totalErrors: number;
  criticalErrors: number;
  recentErrors: number;
  errorRate: number;
}

const ErrorDashboard: React.FC = () => {
  const [errors, setErrors] = useState<ErrorMetric[]>([]);
  const [stats, setStats] = useState<ErrorStats>({
    totalErrors: 0,
    criticalErrors: 0,
    recentErrors: 0,
    errorRate: 0
  });
  const [circuitBreakerMetrics, setCircuitBreakerMetrics] = useState<any>({});
  const [isVisible, setIsVisible] = useState(false);

  useEffect(() => {
    loadErrorData();
    const interval = setInterval(loadErrorData, 5000); // Update every 5 seconds
    return () => clearInterval(interval);
  }, []);

  const loadErrorData = () => {
    // Get errors from error logger
    const recentErrors = errorLogger.getErrors();
    
    // Group errors by type and count
    const errorGroups = groupErrorsByType(recentErrors);
    setErrors(errorGroups);
    
    // Calculate stats
    const now = Date.now();
    const oneHourAgo = now - 3600000;
    
    const recentErrorsCount = recentErrors.filter(
      error => new Date(error.timestamp).getTime() > oneHourAgo
    ).length;
    
    const criticalErrorsCount = recentErrors.filter(
      error => isCriticalError(error)
    ).length;
    
    setStats({
      totalErrors: recentErrors.length,
      criticalErrors: criticalErrorsCount,
      recentErrors: recentErrorsCount,
      errorRate: recentErrorsCount / 60 // Errors per minute
    });
    
    // Get circuit breaker metrics
    setCircuitBreakerMetrics(CircuitBreakerFactory.getMetrics());
  };

  const groupErrorsByType = (errors: any[]): ErrorMetric[] => {
    const groups = new Map<string, ErrorMetric>();
    
    errors.forEach(error => {
      const type = error.type || 'Unknown';
      const key = `${type}-${error.message}`;
      
      if (groups.has(key)) {
        const existing = groups.get(key)!;
        existing.count++;
      } else {
        groups.set(key, {
          timestamp: error.timestamp,
          type,
          message: error.message,
          component: error.component,
          count: 1
        });
      }
    });
    
    return Array.from(groups.values()).sort((a, b) => b.count - a.count);
  };

  const isCriticalError = (error: any): boolean => {
    return error.type === 'error' || 
           error.message.includes('500') ||
           error.message.includes('critical') ||
           error.message.includes('crash');
  };

  const clearErrors = () => {
    errorLogger.clearErrors();
    loadErrorData();
  };

  const exportErrors = () => {
    const data = {
      timestamp: new Date().toISOString(),
      stats,
      errors,
      circuitBreakers: circuitBreakerMetrics
    };
    
    const blob = new Blob([JSON.stringify(data, null, 2)], {
      type: 'application/json'
    });
    
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `error-report-${Date.now()}.json`;
    a.click();
    URL.revokeObjectURL(url);
  };

  const getStatusColor = (isHealthy: boolean) => {
    return isHealthy ? '#10b981' : '#ef4444';
  };

  if (!isVisible) {
    return (
      <button
        onClick={() => setIsVisible(true)}
        style={{
          position: 'fixed',
          bottom: '20px',
          right: '20px',
          zIndex: 9999,
          padding: '10px 15px',
          backgroundColor: stats.criticalErrors > 0 ? '#ef4444' : '#3b82f6',
          color: 'white',
          border: 'none',
          borderRadius: '50px',
          cursor: 'pointer',
          fontSize: '12px',
          boxShadow: '0 4px 12px rgba(0,0,0,0.15)'
        }}
      >
        🔍 Errors: {stats.totalErrors}
      </button>
    );
  }

  return (
    <div style={{
      position: 'fixed',
      top: '20px',
      right: '20px',
      width: '400px',
      maxHeight: '600px',
      backgroundColor: 'white',
      border: '1px solid #e5e7eb',
      borderRadius: '8px',
      boxShadow: '0 10px 25px rgba(0,0,0,0.15)',
      zIndex: 9999,
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
          Error Dashboard
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

      {/* Stats */}
      <div style={{
        padding: '15px',
        display: 'grid',
        gridTemplateColumns: '1fr 1fr',
        gap: '10px'
      }}>
        <div style={{
          padding: '10px',
          backgroundColor: '#fef3c7',
          borderRadius: '6px',
          textAlign: 'center'
        }}>
          <div style={{ fontSize: '20px', fontWeight: 'bold', color: '#d97706' }}>
            {stats.totalErrors}
          </div>
          <div style={{ fontSize: '12px', color: '#92400e' }}>
            Total Errors
          </div>
        </div>
        
        <div style={{
          padding: '10px',
          backgroundColor: stats.criticalErrors > 0 ? '#fecaca' : '#dcfce7',
          borderRadius: '6px',
          textAlign: 'center'
        }}>
          <div style={{
            fontSize: '20px',
            fontWeight: 'bold',
            color: stats.criticalErrors > 0 ? '#dc2626' : '#16a34a'
          }}>
            {stats.criticalErrors}
          </div>
          <div style={{
            fontSize: '12px',
            color: stats.criticalErrors > 0 ? '#991b1b' : '#15803d'
          }}>
            Critical
          </div>
        </div>
        
        <div style={{
          padding: '10px',
          backgroundColor: '#dbeafe',
          borderRadius: '6px',
          textAlign: 'center'
        }}>
          <div style={{ fontSize: '20px', fontWeight: 'bold', color: '#2563eb' }}>
            {stats.recentErrors}
          </div>
          <div style={{ fontSize: '12px', color: '#1d4ed8' }}>
            Last Hour
          </div>
        </div>
        
        <div style={{
          padding: '10px',
          backgroundColor: '#f3e8ff',
          borderRadius: '6px',
          textAlign: 'center'
        }}>
          <div style={{ fontSize: '20px', fontWeight: 'bold', color: '#7c3aed' }}>
            {stats.errorRate.toFixed(1)}
          </div>
          <div style={{ fontSize: '12px', color: '#6d28d9' }}>
            /min
          </div>
        </div>
      </div>

      {/* Circuit Breakers */}
      <div style={{ padding: '0 15px' }}>
        <h4 style={{ margin: '10px 0', fontSize: '14px', color: '#374151' }}>
          Circuit Breakers
        </h4>
        {Object.entries(circuitBreakerMetrics).map(([name, metrics]: [string, any]) => (
          <div key={name} style={{
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
            padding: '5px 0',
            fontSize: '12px'
          }}>
            <span>{name}</span>
            <span style={{
              padding: '2px 8px',
              borderRadius: '12px',
              backgroundColor: getStatusColor(metrics.isHealthy),
              color: 'white',
              fontSize: '10px'
            }}>
              {metrics.state}
            </span>
          </div>
        ))}
      </div>

      {/* Recent Errors */}
      <div style={{
        maxHeight: '250px',
        overflowY: 'auto',
        margin: '15px'
      }}>
        <h4 style={{ margin: '0 0 10px 0', fontSize: '14px', color: '#374151' }}>
          Recent Errors
        </h4>
        {errors.length === 0 ? (
          <div style={{
            textAlign: 'center',
            color: '#6b7280',
            fontSize: '12px',
            padding: '20px'
          }}>
            No errors detected 🎉
          </div>
        ) : (
          errors.slice(0, 10).map((error, index) => (
            <div key={index} style={{
              padding: '8px',
              backgroundColor: '#f9fafb',
              borderRadius: '4px',
              marginBottom: '5px',
              fontSize: '11px'
            }}>
              <div style={{
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'center',
                marginBottom: '3px'
              }}>
                <span style={{ fontWeight: 'bold', color: '#ef4444' }}>
                  {error.type}
                </span>
                <span style={{
                  backgroundColor: '#3b82f6',
                  color: 'white',
                  padding: '1px 6px',
                  borderRadius: '10px',
                  fontSize: '10px'
                }}>
                  {error.count}
                </span>
              </div>
              <div style={{ color: '#6b7280' }}>
                {error.message.substring(0, 50)}...
              </div>
              {error.component && (
                <div style={{ color: '#9ca3af', fontSize: '10px' }}>
                  {error.component}
                </div>
              )}
            </div>
          ))
        )}
      </div>

      {/* Actions */}
      <div style={{
        padding: '15px',
        borderTop: '1px solid #e5e7eb',
        display: 'flex',
        gap: '10px'
      }}>
        <button
          onClick={clearErrors}
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
          Clear
        </button>
        <button
          onClick={exportErrors}
          style={{
            flex: 1,
            padding: '8px',
            backgroundColor: '#3b82f6',
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
    </div>
  );
};

export default ErrorDashboard;