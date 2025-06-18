interface PerformanceMetric {
  name: string;
  value: number;
  timestamp: number;
  type: 'navigation' | 'resource' | 'paint' | 'custom';
}

class PerformanceMonitor {
  private static instance: PerformanceMonitor;
  private metrics: PerformanceMetric[] = [];
  private observer?: PerformanceObserver;

  private constructor() {
    this.initializeObserver();
    this.collectInitialMetrics();
  }

  public static getInstance(): PerformanceMonitor {
    if (!PerformanceMonitor.instance) {
      PerformanceMonitor.instance = new PerformanceMonitor();
    }
    return PerformanceMonitor.instance;
  }

  private initializeObserver(): void {
    if ('PerformanceObserver' in window) {
      this.observer = new PerformanceObserver((list) => {
        for (const entry of list.getEntries()) {
          this.addMetric({
            name: entry.name,
            value: entry.duration || entry.startTime,
            timestamp: Date.now(),
            type: this.getEntryType(entry.entryType)
          });
        }
      });

      try {
        this.observer.observe({ entryTypes: ['navigation', 'resource', 'paint', 'measure'] });
      } catch (e) {
        console.warn('Performance Observer not fully supported:', e);
      }
    }
  }

  private getEntryType(entryType: string): PerformanceMetric['type'] {
    switch (entryType) {
      case 'navigation': return 'navigation';
      case 'resource': return 'resource';
      case 'paint': return 'paint';
      case 'measure': return 'custom';
      default: return 'custom';
    }
  }

  private collectInitialMetrics(): void {
    // Core Web Vitals
    this.measureCoreWebVitals();
    
    // Bundle size analysis
    this.analyzeBundleSize();
    
    // Memory usage
    this.trackMemoryUsage();
  }

  private measureCoreWebVitals(): void {
    // First Contentful Paint
    const fcpEntry = performance.getEntriesByName('first-contentful-paint')[0];
    if (fcpEntry) {
      this.addMetric({
        name: 'First Contentful Paint',
        value: fcpEntry.startTime,
        timestamp: Date.now(),
        type: 'paint'
      });
    }

    // Largest Contentful Paint
    if ('PerformanceObserver' in window) {
      const lcpObserver = new PerformanceObserver((list) => {
        const entries = list.getEntries();
        const lastEntry = entries[entries.length - 1];
        
        this.addMetric({
          name: 'Largest Contentful Paint',
          value: lastEntry.startTime,
          timestamp: Date.now(),
          type: 'paint'
        });
      });

      try {
        lcpObserver.observe({ entryTypes: ['largest-contentful-paint'] });
      } catch (e) {
        console.warn('LCP observation not supported:', e);
      }
    }

    // Cumulative Layout Shift
    let clsValue = 0;
    if ('PerformanceObserver' in window) {
      const clsObserver = new PerformanceObserver((list) => {
        for (const entry of list.getEntries()) {
          if (!(entry as any).hadRecentInput) {
            clsValue += (entry as any).value;
          }
        }
        
        this.addMetric({
          name: 'Cumulative Layout Shift',
          value: clsValue,
          timestamp: Date.now(),
          type: 'custom'
        });
      });

      try {
        clsObserver.observe({ entryTypes: ['layout-shift'] });
      } catch (e) {
        console.warn('CLS observation not supported:', e);
      }
    }
  }

  private analyzeBundleSize(): void {
    const resourceEntries = performance.getEntriesByType('resource');
    let totalBundleSize = 0;

    resourceEntries.forEach((entry: any) => {
      if (entry.name.includes('.js') || entry.name.includes('.css')) {
        totalBundleSize += entry.encodedBodySize || entry.transferSize || 0;
      }
    });

    this.addMetric({
      name: 'Total Bundle Size',
      value: totalBundleSize,
      timestamp: Date.now(),
      type: 'resource'
    });
  }

  private trackMemoryUsage(): void {
    if ('memory' in performance) {
      const memory = (performance as any).memory;
      
      this.addMetric({
        name: 'JS Heap Used',
        value: memory.usedJSHeapSize,
        timestamp: Date.now(),
        type: 'custom'
      });

      this.addMetric({
        name: 'JS Heap Total',
        value: memory.totalJSHeapSize,
        timestamp: Date.now(),
        type: 'custom'
      });
    }
  }

  private addMetric(metric: PerformanceMetric): void {
    this.metrics.push(metric);
    
    // Keep only last 100 metrics
    if (this.metrics.length > 100) {
      this.metrics = this.metrics.slice(-100);
    }

    // Log critical metrics
    if (this.isCriticalMetric(metric)) {
      console.warn(`Performance Warning: ${metric.name} = ${metric.value.toFixed(2)}ms`);
    }
  }

  private isCriticalMetric(metric: PerformanceMetric): boolean {
    const thresholds = {
      'First Contentful Paint': 1500,
      'Largest Contentful Paint': 2500,
      'Cumulative Layout Shift': 0.1,
      'JS Heap Used': 50 * 1024 * 1024, // 50MB
    };

    return (thresholds[metric.name as keyof typeof thresholds] || Infinity) < metric.value;
  }

  public measureCustom(name: string, fn: () => void | Promise<void>): Promise<number> {
    return new Promise(async (resolve) => {
      const startTime = performance.now();
      
      try {
        await fn();
      } finally {
        const duration = performance.now() - startTime;
        
        this.addMetric({
          name,
          value: duration,
          timestamp: Date.now(),
          type: 'custom'
        });
        
        resolve(duration);
      }
    });
  }

  public getMetrics(): PerformanceMetric[] {
    return [...this.metrics];
  }

  public getCoreWebVitals(): Record<string, number> {
    const vitals: Record<string, number> = {};
    
    this.metrics.forEach(metric => {
      if (['First Contentful Paint', 'Largest Contentful Paint', 'Cumulative Layout Shift'].includes(metric.name)) {
        vitals[metric.name] = metric.value;
      }
    });
    
    return vitals;
  }

  public getPerformanceScore(): number {
    const vitals = this.getCoreWebVitals();
    let score = 100;

    // Deduct points for poor metrics
    if (vitals['First Contentful Paint'] > 1500) score -= 20;
    if (vitals['Largest Contentful Paint'] > 2500) score -= 30;
    if (vitals['Cumulative Layout Shift'] > 0.1) score -= 25;

    // Bundle size penalty
    const bundleSize = this.metrics.find(m => m.name === 'Total Bundle Size')?.value || 0;
    if (bundleSize > 1024 * 1024) score -= 15; // 1MB threshold

    return Math.max(0, score);
  }

  public exportReport(): string {
    const report = {
      timestamp: new Date().toISOString(),
      coreWebVitals: this.getCoreWebVitals(),
      performanceScore: this.getPerformanceScore(),
      metrics: this.metrics,
      recommendations: this.generateRecommendations()
    };

    return JSON.stringify(report, null, 2);
  }

  private generateRecommendations(): string[] {
    const recommendations: string[] = [];
    const vitals = this.getCoreWebVitals();

    if (vitals['First Contentful Paint'] > 1500) {
      recommendations.push('Optimize First Contentful Paint: Consider code splitting and lazy loading');
    }

    if (vitals['Largest Contentful Paint'] > 2500) {
      recommendations.push('Improve Largest Contentful Paint: Optimize images and critical CSS');
    }

    if (vitals['Cumulative Layout Shift'] > 0.1) {
      recommendations.push('Reduce Layout Shift: Set dimensions for images and ads');
    }

    const bundleSize = this.metrics.find(m => m.name === 'Total Bundle Size')?.value || 0;
    if (bundleSize > 1024 * 1024) {
      recommendations.push('Reduce bundle size: Implement tree shaking and remove unused dependencies');
    }

    const memoryUsage = this.metrics.find(m => m.name === 'JS Heap Used')?.value || 0;
    if (memoryUsage > 50 * 1024 * 1024) {
      recommendations.push('High memory usage detected: Check for memory leaks');
    }

    return recommendations;
  }

  public startContinuousMonitoring(): void {
    // Monitor every 30 seconds
    setInterval(() => {
      this.trackMemoryUsage();
    }, 30000);
  }

  public dispose(): void {
    if (this.observer) {
      this.observer.disconnect();
    }
  }
}

// Export singleton instance
export const performanceMonitor = PerformanceMonitor.getInstance();

// Global access for debugging
if (typeof window !== 'undefined') {
  (window as any).performanceMonitor = performanceMonitor;
}