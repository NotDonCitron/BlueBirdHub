/**
 * Performance Monitor Component
 * Displays real-time performance metrics for the application
 */
import React, { useState, useEffect, memo } from 'react';
import { useFPSMonitor, useMemoryMonitor, useRenderCount } from '../../hooks/usePerformance';
import './PerformanceMonitor.css';

interface PerformanceMonitorProps {
  position?: 'top-left' | 'top-right' | 'bottom-left' | 'bottom-right';
  visible?: boolean;
}

export const PerformanceMonitor: React.FC<PerformanceMonitorProps> = memo(({
  position = 'bottom-right',
  visible = true
}) => {
  const fps = useFPSMonitor();
  const memoryInfo = useMemoryMonitor(2000);
  const renderCount = useRenderCount('PerformanceMonitor');
  const [cpuUsage, setCpuUsage] = useState<number>(0);

  // Get CPU usage from Electron (if available)
  useEffect(() => {
    if ((window as any).electronAPI?.getCPUUsage) {
      const interval = setInterval(async () => {
        try {
          const usage = await (window as any).electronAPI.getCPUUsage();
          setCpuUsage(usage);
        } catch (error) {
          console.error('Failed to get CPU usage:', error);
        }
      }, 2000);

      return () => clearInterval(interval);
    }
  }, []);

  if (!visible || process.env.NODE_ENV !== 'development') {
    return null;
  }

  const formatBytes = (bytes: number) => {
    const mb = bytes / (1024 * 1024);
    return `${mb.toFixed(1)} MB`;
  };

  const getFPSColor = (fps: number) => {
    if (fps >= 55) return '#4CAF50';
    if (fps >= 30) return '#FFC107';
    return '#F44336';
  };

  const getMemoryPercentage = () => {
    if (!memoryInfo) return 0;
    return (memoryInfo.usedJSHeapSize / memoryInfo.jsHeapSizeLimit) * 100;
  };

  const getMemoryColor = (percentage: number) => {
    if (percentage < 70) return '#4CAF50';
    if (percentage < 85) return '#FFC107';
    return '#F44336';
  };

  return (
    <div className={`performance-monitor performance-monitor--${position}`}>
      <div className="performance-monitor__header">
        Performance Monitor
      </div>
      
      <div className="performance-monitor__metric">
        <span className="performance-monitor__label">FPS:</span>
        <span 
          className="performance-monitor__value"
          style={{ color: getFPSColor(fps) }}
        >
          {fps}
        </span>
      </div>

      {memoryInfo && (
        <>
          <div className="performance-monitor__metric">
            <span className="performance-monitor__label">Memory:</span>
            <span 
              className="performance-monitor__value"
              style={{ color: getMemoryColor(getMemoryPercentage()) }}
            >
              {formatBytes(memoryInfo.usedJSHeapSize)}
            </span>
          </div>
          
          <div className="performance-monitor__metric">
            <span className="performance-monitor__label">Heap:</span>
            <span className="performance-monitor__value">
              {getMemoryPercentage().toFixed(1)}%
            </span>
          </div>

          <div className="performance-monitor__progress">
            <div 
              className="performance-monitor__progress-bar"
              style={{ 
                width: `${getMemoryPercentage()}%`,
                backgroundColor: getMemoryColor(getMemoryPercentage())
              }}
            />
          </div>
        </>
      )}

      {cpuUsage > 0 && (
        <div className="performance-monitor__metric">
          <span className="performance-monitor__label">CPU:</span>
          <span className="performance-monitor__value">
            {cpuUsage.toFixed(1)}%
          </span>
        </div>
      )}

      <div className="performance-monitor__metric">
        <span className="performance-monitor__label">Renders:</span>
        <span className="performance-monitor__value">
          {renderCount}
        </span>
      </div>
    </div>
  );
});

PerformanceMonitor.displayName = 'PerformanceMonitor';