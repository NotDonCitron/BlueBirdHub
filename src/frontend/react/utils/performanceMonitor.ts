import React from 'react';

// Core Web Vitals and Performance Monitoring
interface PerformanceMetrics {
  // Core Web Vitals
  LCP?: number; // Largest Contentful Paint
  FID?: number; // First Input Delay
  CLS?: number; // Cumulative Layout Shift
  
  // Additional metrics
  FCP?: number; // First Contentful Paint
  TTFB?: number; // Time to First Byte
  TTI?: number; // Time to Interactive
  
  // Bundle metrics
  bundleSize?: number;
  loadTime?: number;
  
  // Memory usage
  usedJSHeapSize?: number;
  totalJSHeapSize?: number;
  jsHeapSizeLimit?: number;
  
  // Network
  connectionType?: string;
  effectiveType?: string;
  downlink?: number;
}

interface PerformanceBudget {
  LCP: number; // Target: < 2500ms
  FID: number; // Target: < 100ms
  CLS: number; // Target: < 0.1
  FCP: number; // Target: < 1800ms
  TTFB: number; // Target: < 600ms
  bundleSize: number; // Target: < 400KB
  loadTime: number; // Target: < 1500ms
}

class PerformanceMonitor {
  private metrics: PerformanceMetrics = {};
  private budget: PerformanceBudget = {
    LCP: 2500,
    FID: 100,
    CLS: 0.1,
    FCP: 1800,
    TTFB: 600,
    bundleSize: 400 * 1024, // 400KB
    loadTime: 1500
  };
  
  private observers: PerformanceObserver[] = [];
  private isMonitoring = false;

  constructor() {
    this.initializeWebVitals();
  }

  private initializeWebVitals() {
    // Only run in browser environment
    if (typeof window === 'undefined') return;

    // Largest Contentful Paint (LCP)
    this.observeMetric('largest-contentful-paint', (entries) => {
      const lcpEntry = entries[entries.length - 1] as PerformanceEntry & { renderTime: number; loadTime: number };
      this.metrics.LCP = lcpEntry.renderTime || lcpEntry.loadTime;
      this.reportMetric('LCP', this.metrics.LCP);
    });

    // First Input Delay (FID)
    this.observeMetric('first-input', (entries) => {
      const fidEntry = entries[0] as PerformanceEntry & { processingStart: number; startTime: number };
      this.metrics.FID = fidEntry.processingStart - fidEntry.startTime;
      this.reportMetric('FID', this.metrics.FID);
    });

    // Cumulative Layout Shift (CLS)
    let clsValue = 0;
    this.observeMetric('layout-shift', (entries) => {
      for (const entry of entries) {
        const layoutShiftEntry = entry as PerformanceEntry & { value: number; hadRecentInput: boolean };
        if (!layoutShiftEntry.hadRecentInput) {
          clsValue += layoutShiftEntry.value;
        }
      }
      this.metrics.CLS = clsValue;
      this.reportMetric('CLS', this.metrics.CLS);
    });

    // First Contentful Paint (FCP)
    this.observeMetric('paint', (entries) => {
      for (const entry of entries) {
        if (entry.name === 'first-contentful-paint') {
          this.metrics.FCP = entry.startTime;
          this.reportMetric('FCP', this.metrics.FCP);
        }
      }
    });

    // Navigation timing for TTFB
    if ('navigation' in performance) {
      const navEntry = performance.getEntriesByType('navigation')[0] as PerformanceNavigationTiming;
      if (navEntry) {
        this.metrics.TTFB = navEntry.responseStart - navEntry.requestStart;
        this.reportMetric('TTFB', this.metrics.TTFB);
      }
    }
  }

  private observeMetric(type: string, callback: (entries: PerformanceEntry[]) => void) {
    try {
      const observer = new PerformanceObserver((list) => {
        callback(list.getEntries());
      });
      
      observer.observe({ type, buffered: true });
      this.observers.push(observer);
    } catch (error) {
      console.warn(`Failed to observe ${type}:`, error);
    }
  }

  private reportMetric(name: string, value: number) {
    const budget = this.budget[name as keyof PerformanceBudget];
    const isOverBudget = budget && value > budget;
    
    if (isOverBudget) {
      console.warn(`⚠️ Performance Budget Exceeded: ${name} = ${value}ms (budget: ${budget}ms)`);
    } else {
      console.log(`✅ Performance Metric: ${name} = ${value}ms`);
    }

    // Send to analytics if available
    if (typeof gtag !== 'undefined') {
      gtag('event', 'web_vitals', {
        metric_name: name,
        metric_value: Math.round(value),
        custom_parameter: isOverBudget ? 'over_budget' : 'within_budget'
      });
    }
  }

  public startContinuousMonitoring() {
    if (this.isMonitoring || typeof window === 'undefined') return;
    
    this.isMonitoring = true;
    
    // Monitor memory usage
    this.monitorMemoryUsage();
    
    // Monitor network information
    this.monitorNetworkInformation();
    
    // Monitor bundle size
    this.monitorBundleSize();
    
    // Start load time monitoring
    this.monitorLoadTime();
    
    console.log('🚀 Performance monitoring started');
  }

  private monitorMemoryUsage() {
    if (!('memory' in performance)) return;
    
    const updateMemoryMetrics = () => {
      const memory = (performance as any).memory;
      this.metrics.usedJSHeapSize = memory.usedJSHeapSize;
      this.metrics.totalJSHeapSize = memory.totalJSHeapSize;
      this.metrics.jsHeapSizeLimit = memory.jsHeapSizeLimit;
      
      // Warn if memory usage is high
      const usagePercent = (memory.usedJSHeapSize / memory.jsHeapSizeLimit) * 100;
      if (usagePercent > 80) {
        console.warn(`⚠️ High memory usage: ${usagePercent.toFixed(1)}%`);
      }
    };
    
    updateMemoryMetrics();
    setInterval(updateMemoryMetrics, 30000); // Every 30 seconds
  }

  private monitorNetworkInformation() {
    if (!('connection' in navigator)) return;
    
    const connection = (navigator as any).connection;
    this.metrics.connectionType = connection.type;
    this.metrics.effectiveType = connection.effectiveType;
    this.metrics.downlink = connection.downlink;
    
    connection.addEventListener('change', () => {
      this.metrics.connectionType = connection.type;
      this.metrics.effectiveType = connection.effectiveType;
      this.metrics.downlink = connection.downlink;
      
      console.log(`📶 Network changed: ${connection.effectiveType}, ${connection.downlink}Mbps`);
    });
  }

  private monitorBundleSize() {
    // Get resource timing for scripts
    const scriptEntries = performance.getEntriesByType('resource')
      .filter(entry => entry.name.includes('.js'));
    
    let totalSize = 0;
    scriptEntries.forEach(entry => {
      const resourceEntry = entry as PerformanceResourceTiming;
      if (resourceEntry.transferSize) {
        totalSize += resourceEntry.transferSize;
      }
    });
    
    this.metrics.bundleSize = totalSize;
    
    if (totalSize > this.budget.bundleSize) {
      console.warn(`⚠️ Bundle size over budget: ${(totalSize / 1024).toFixed(1)}KB (budget: ${(this.budget.bundleSize / 1024).toFixed(1)}KB)`);
    } else {
      console.log(`📦 Bundle size: ${(totalSize / 1024).toFixed(1)}KB`);
    }
  }

  private monitorLoadTime() {
    window.addEventListener('load', () => {
      const loadTime = performance.now();
      this.metrics.loadTime = loadTime;
      
      if (loadTime > this.budget.loadTime) {
        console.warn(`⚠️ Load time over budget: ${loadTime.toFixed(0)}ms (budget: ${this.budget.loadTime}ms)`);
      } else {
        console.log(`⏱️ Load time: ${loadTime.toFixed(0)}ms`);
      }
    });
  }

  public getMetrics(): PerformanceMetrics {
    return { ...this.metrics };
  }

  public getBudget(): PerformanceBudget {
    return { ...this.budget };
  }

  public setBudget(newBudget: Partial<PerformanceBudget>) {
    this.budget = { ...this.budget, ...newBudget };
  }

  public generateReport(): string {
    const metrics = this.getMetrics();
    const budget = this.getBudget();
    
    let report = '📊 Performance Report\n';
    report += '========================\n\n';
    
    // Core Web Vitals
    report += '🎯 Core Web Vitals:\n';
    if (metrics.LCP) {
      const status = metrics.LCP <= budget.LCP ? '✅' : '❌';
      report += `  ${status} LCP: ${metrics.LCP.toFixed(0)}ms (budget: ${budget.LCP}ms)\n`;
    }
    if (metrics.FID) {
      const status = metrics.FID <= budget.FID ? '✅' : '❌';
      report += `  ${status} FID: ${metrics.FID.toFixed(0)}ms (budget: ${budget.FID}ms)\n`;
    }
    if (metrics.CLS !== undefined) {
      const status = metrics.CLS <= budget.CLS ? '✅' : '❌';
      report += `  ${status} CLS: ${metrics.CLS.toFixed(3)} (budget: ${budget.CLS})\n`;
    }
    
    // Additional metrics
    report += '\n📈 Additional Metrics:\n';
    if (metrics.FCP) {
      const status = metrics.FCP <= budget.FCP ? '✅' : '❌';
      report += `  ${status} FCP: ${metrics.FCP.toFixed(0)}ms (budget: ${budget.FCP}ms)\n`;
    }
    if (metrics.TTFB) {
      const status = metrics.TTFB <= budget.TTFB ? '✅' : '❌';
      report += `  ${status} TTFB: ${metrics.TTFB.toFixed(0)}ms (budget: ${budget.TTFB}ms)\n`;
    }
    if (metrics.bundleSize) {
      const status = metrics.bundleSize <= budget.bundleSize ? '✅' : '❌';
      report += `  ${status} Bundle Size: ${(metrics.bundleSize / 1024).toFixed(1)}KB (budget: ${(budget.bundleSize / 1024).toFixed(1)}KB)\n`;
    }
    if (metrics.loadTime) {
      const status = metrics.loadTime <= budget.loadTime ? '✅' : '❌';
      report += `  ${status} Load Time: ${metrics.loadTime.toFixed(0)}ms (budget: ${budget.loadTime}ms)\n`;
    }
    
    // Memory usage
    if (metrics.usedJSHeapSize) {
      report += '\n🧠 Memory Usage:\n';
      report += `  Used: ${(metrics.usedJSHeapSize / 1024 / 1024).toFixed(1)}MB\n`;
      report += `  Total: ${(metrics.totalJSHeapSize! / 1024 / 1024).toFixed(1)}MB\n`;
      report += `  Limit: ${(metrics.jsHeapSizeLimit! / 1024 / 1024).toFixed(1)}MB\n`;
    }
    
    // Network info
    if (metrics.effectiveType) {
      report += '\n📶 Network:\n';
      report += `  Type: ${metrics.effectiveType}\n`;
      if (metrics.downlink) {
        report += `  Speed: ${metrics.downlink}Mbps\n`;
      }
    }
    
    return report;
  }

  public dispose() {
    this.observers.forEach(observer => observer.disconnect());
    this.observers = [];
    this.isMonitoring = false;
    console.log('🛑 Performance monitoring stopped');
  }
}

// Singleton instance
export const performanceMonitor = new PerformanceMonitor();

// Utility functions for React components
export const usePerformanceMetric = (metricName: string) => {
  const startTime = performance.now();
  
  return {
    end: () => {
      const endTime = performance.now();
      const duration = endTime - startTime;
      console.log(`⏱️ ${metricName}: ${duration.toFixed(2)}ms`);
      return duration;
    }
  };
};

// React hook for component render time
export const useRenderTime = (componentName: string) => {
  const renderStart = performance.now();
  
  React.useEffect(() => {
    const renderTime = performance.now() - renderStart;
    if (renderTime > 16) { // Flag renders > 16ms (60fps threshold)
      console.warn(`⚠️ Slow render: ${componentName} took ${renderTime.toFixed(2)}ms`);
    }
  });
};

export default performanceMonitor;