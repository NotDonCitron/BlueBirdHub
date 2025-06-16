/**
 * Performance Monitoring System for OrdnungsHub Desktop App
 * Tracks memory usage, render performance, and system resources
 */

interface PerformanceMetrics {
  memory: {
    used: number;
    total: number;
    percentage: number;
  };
  timing: {
    navigationStart: number;
    domContentLoaded: number;
    loadComplete: number;
  };
  renders: {
    componentCount: number;
    reRenderCount: number;
    averageRenderTime: number;
  };
  system: {
    cpu: number;
    platform: string;
    electronVersion: string;
  };
}

interface PerformanceThresholds {
  memoryWarning: number;
  memoryCritical: number;
  renderTimeWarning: number;
  renderTimeCritical: number;
}

class PerformanceMonitor {
  private metrics: PerformanceMetrics;
  private thresholds: PerformanceThresholds;
  private observers: Set<(metrics: PerformanceMetrics) => void>;
  private monitoringInterval: NodeJS.Timeout | null;
  private renderStartTimes: Map<string, number>;
  
  constructor() {
    this.metrics = this.initializeMetrics();
    this.thresholds = {
      memoryWarning: 150 * 1024 * 1024,  // 150MB
      memoryCritical: 250 * 1024 * 1024, // 250MB
      renderTimeWarning: 16,  // 16ms (60fps threshold)
      renderTimeCritical: 33  // 33ms (30fps threshold)
    };
    this.observers = new Set();
    this.monitoringInterval = null;
    this.renderStartTimes = new Map();
    
    this.setupPerformanceObserver();
    this.setupMemoryMonitoring();
  }

  private initializeMetrics(): PerformanceMetrics {
    return {
      memory: { used: 0, total: 0, percentage: 0 },
      timing: { navigationStart: 0, domContentLoaded: 0, loadComplete: 0 },
      renders: { componentCount: 0, reRenderCount: 0, averageRenderTime: 0 },
      system: { 
        cpu: 0, 
        platform: (window as any).electronAPI?.platform || 'unknown',
        electronVersion: process.versions?.electron || 'unknown'
      }
    };
  }

  public startMonitoring(intervalMs: number = 5000): void {
    if (this.monitoringInterval) {
      this.stopMonitoring();
    }

    this.monitoringInterval = setInterval(() => {
      this.updateMetrics();
      this.checkThresholds();
      this.notifyObservers();
    }, intervalMs);

    console.log('🔍 Performance monitoring started');
  }

  public stopMonitoring(): void {
    if (this.monitoringInterval) {
      clearInterval(this.monitoringInterval);
      this.monitoringInterval = null;
      console.log('⏹️ Performance monitoring stopped');
    }
  }

  public addObserver(callback: (metrics: PerformanceMetrics) => void): void {
    this.observers.add(callback);
  }

  public removeObserver(callback: (metrics: PerformanceMetrics) => void): void {
    this.observers.delete(callback);
  }

  public getMetrics(): PerformanceMetrics {
    return { ...this.metrics };
  }

  public trackComponentRender(componentName: string): () => void {
    const startTime = performance.now();
    this.renderStartTimes.set(componentName, startTime);
    this.metrics.renders.componentCount++;

    return () => {
      const endTime = performance.now();
      const renderTime = endTime - startTime;
      
      // Update average render time
      const currentAvg = this.metrics.renders.averageRenderTime;
      const count = this.metrics.renders.reRenderCount + 1;
      this.metrics.renders.averageRenderTime = (currentAvg * (count - 1) + renderTime) / count;
      this.metrics.renders.reRenderCount++;

      if (renderTime > this.thresholds.renderTimeWarning) {
        console.warn(`⚠️ Slow render detected: ${componentName} took ${renderTime.toFixed(2)}ms`);
      }

      this.renderStartTimes.delete(componentName);
    };
  }

  private setupPerformanceObserver(): void {
    if ('PerformanceObserver' in window) {
      const observer = new PerformanceObserver((list) => {
        const entries = list.getEntries();
        
        entries.forEach((entry) => {
          if (entry.entryType === 'navigation') {
            const navEntry = entry as PerformanceNavigationTiming;
            this.metrics.timing = {
              navigationStart: navEntry.navigationStart,
              domContentLoaded: navEntry.domContentLoadedEventEnd,
              loadComplete: navEntry.loadEventEnd
            };
          } else if (entry.entryType === 'measure') {
            // Custom performance measures
            if (entry.name.startsWith('component-render')) {
              const renderTime = entry.duration;
              if (renderTime > this.thresholds.renderTimeWarning) {
                console.warn(`⚠️ Component render took ${renderTime.toFixed(2)}ms: ${entry.name}`);
              }
            }
          }
        });
      });

      try {
        observer.observe({ entryTypes: ['navigation', 'measure', 'paint'] });
      } catch (error) {
        console.warn('Performance Observer not fully supported:', error);
      }
    }
  }

  private setupMemoryMonitoring(): void {
    // Monitor memory warning events from Electron main process
    if ((window as any).electronAPI) {
      // Listen for memory warnings from main process
      window.addEventListener('memory-warning', () => {
        console.warn('⚠️ Memory warning received from system');
        this.triggerMemoryCleanup();
      });
    }
  }

  private updateMetrics(): void {
    // Update memory metrics
    if ('memory' in performance) {
      const memInfo = (performance as any).memory;
      this.metrics.memory = {
        used: memInfo.usedJSHeapSize,
        total: memInfo.totalJSHeapSize,
        percentage: (memInfo.usedJSHeapSize / memInfo.totalJSHeapSize) * 100
      };
    }

    // Update system metrics (if available through Electron API)
    if ((window as any).electronAPI?.getSystemInfo) {
      (window as any).electronAPI.getSystemInfo().then((sysInfo: any) => {
        this.metrics.system.cpu = sysInfo.cpu || 0;
      }).catch((error: any) => {
        console.debug('Could not fetch system info:', error);
      });
    }
  }

  private checkThresholds(): void {
    const { memory } = this.metrics;

    if (memory.used > this.thresholds.memoryCritical) {
      console.error('🚨 Critical memory usage detected:', this.formatBytes(memory.used));
      this.triggerMemoryCleanup();
      this.notifyMemoryIssue('critical', memory.used);
    } else if (memory.used > this.thresholds.memoryWarning) {
      console.warn('⚠️ High memory usage detected:', this.formatBytes(memory.used));
      this.notifyMemoryIssue('warning', memory.used);
    }
  }

  private triggerMemoryCleanup(): void {
    // Trigger garbage collection if available (development only)
    if (typeof window.gc === 'function') {
      window.gc();
      console.log('🧹 Manual garbage collection triggered');
    }

    // Clear performance entries
    if (performance.clearResourceTimings) {
      performance.clearResourceTimings();
    }

    // Emit cleanup event for React components
    window.dispatchEvent(new CustomEvent('performance-cleanup', {
      detail: { reason: 'memory_threshold' }
    }));
  }

  private notifyMemoryIssue(level: 'warning' | 'critical', usage: number): void {
    window.dispatchEvent(new CustomEvent('memory-issue', {
      detail: { level, usage, formatted: this.formatBytes(usage) }
    }));
  }

  private notifyObservers(): void {
    this.observers.forEach(callback => {
      try {
        callback(this.getMetrics());
      } catch (error) {
        console.error('Error in performance observer callback:', error);
      }
    });
  }

  private formatBytes(bytes: number): string {
    if (bytes === 0) return '0 Bytes';
    
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  }

  public generateReport(): string {
    const { memory, timing, renders, system } = this.metrics;
    
    const report = `
📊 Performance Report
====================

💾 Memory Usage:
  Used: ${this.formatBytes(memory.used)} (${memory.percentage.toFixed(1)}%)
  Total: ${this.formatBytes(memory.total)}

⏱️ Timing:
  Page Load: ${(timing.loadComplete - timing.navigationStart).toFixed(2)}ms
  DOM Ready: ${(timing.domContentLoaded - timing.navigationStart).toFixed(2)}ms

🎨 Rendering:
  Components: ${renders.componentCount}
  Re-renders: ${renders.reRenderCount}
  Avg Render Time: ${renders.averageRenderTime.toFixed(2)}ms

🖥️ System:
  Platform: ${system.platform}
  Electron: ${system.electronVersion}
  CPU Usage: ${system.cpu.toFixed(1)}%

Generated: ${new Date().toISOString()}
    `.trim();

    return report;
  }

  public exportMetrics(): any {
    return {
      timestamp: Date.now(),
      metrics: this.getMetrics(),
      thresholds: this.thresholds,
      isMonitoring: this.monitoringInterval !== null
    };
  }
}

// React Hook for Performance Monitoring
export function usePerformanceMonitoring() {
  const [metrics, setMetrics] = React.useState<PerformanceMetrics | null>(null);
  const [isMonitoring, setIsMonitoring] = React.useState(false);
  const monitorRef = React.useRef<PerformanceMonitor | null>(null);

  React.useEffect(() => {
    monitorRef.current = new PerformanceMonitor();
    
    const observer = (newMetrics: PerformanceMetrics) => {
      setMetrics(newMetrics);
    };

    monitorRef.current.addObserver(observer);

    return () => {
      if (monitorRef.current) {
        monitorRef.current.removeObserver(observer);
        monitorRef.current.stopMonitoring();
      }
    };
  }, []);

  const startMonitoring = React.useCallback(() => {
    if (monitorRef.current) {
      monitorRef.current.startMonitoring();
      setIsMonitoring(true);
    }
  }, []);

  const stopMonitoring = React.useCallback(() => {
    if (monitorRef.current) {
      monitorRef.current.stopMonitoring();
      setIsMonitoring(false);
    }
  }, []);

  const trackRender = React.useCallback((componentName: string) => {
    return monitorRef.current?.trackComponentRender(componentName) || (() => {});
  }, []);

  return {
    metrics,
    isMonitoring,
    startMonitoring,
    stopMonitoring,
    trackRender,
    generateReport: () => monitorRef.current?.generateReport() || '',
    exportMetrics: () => monitorRef.current?.exportMetrics() || null
  };
}

// React Component Wrapper for Performance Tracking
export function withPerformanceTracking<P extends object>(
  Component: React.ComponentType<P>,
  componentName?: string
) {
  const WrappedComponent = React.forwardRef<any, P>((props, ref) => {
    const { trackRender } = usePerformanceMonitoring();
    
    React.useEffect(() => {
      const stopTracking = trackRender(componentName || Component.name || 'Unknown');
      return stopTracking;
    });

    return <Component {...props} ref={ref} />;
  });

  WrappedComponent.displayName = `withPerformanceTracking(${componentName || Component.name || 'Component'})`;
  
  return WrappedComponent;
}

// Memory-efficient Virtual List Component
interface VirtualListProps<T> {
  items: T[];
  itemHeight: number;
  containerHeight: number;
  renderItem: (item: T, index: number) => React.ReactNode;
  overscan?: number;
}

export function VirtualList<T>({
  items,
  itemHeight,
  containerHeight,
  renderItem,
  overscan = 5
}: VirtualListProps<T>) {
  const [scrollTop, setScrollTop] = React.useState(0);

  const startIndex = Math.max(0, Math.floor(scrollTop / itemHeight) - overscan);
  const endIndex = Math.min(
    items.length - 1,
    Math.floor((scrollTop + containerHeight) / itemHeight) + overscan
  );

  const visibleItems = items.slice(startIndex, endIndex + 1);
  const totalHeight = items.length * itemHeight;
  const offsetY = startIndex * itemHeight;

  const handleScroll = React.useCallback((e: React.UIEvent<HTMLDivElement>) => {
    setScrollTop(e.currentTarget.scrollTop);
  }, []);

  return (
    <div
      style={{ height: containerHeight, overflow: 'auto' }}
      onScroll={handleScroll}
    >
      <div style={{ height: totalHeight, position: 'relative' }}>
        <div style={{ transform: `translateY(${offsetY}px)` }}>
          {visibleItems.map((item, index) => (
            <div key={startIndex + index} style={{ height: itemHeight }}>
              {renderItem(item, startIndex + index)}
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

// Global Performance Monitor Instance
export const performanceMonitor = new PerformanceMonitor();

// Auto-start monitoring in development
if (process.env.NODE_ENV === 'development') {
  performanceMonitor.startMonitoring();
}

export default PerformanceMonitor;