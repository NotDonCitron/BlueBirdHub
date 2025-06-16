/**
 * Memory Management Utilities for Electron Renderer Process
 * Implements garbage collection helpers, memory monitoring, and leak detection
 */

interface MemoryInfo {
  usedJSHeapSize: number;
  totalJSHeapSize: number;
  jsHeapSizeLimit: number;
}

interface MemorySnapshot {
  timestamp: number;
  memory: MemoryInfo;
  url: string;
  userAgent: string;
}

interface MemoryLeak {
  detected: boolean;
  growthRate: number; // MB per minute
  snapshots: MemorySnapshot[];
  recommendation: string;
}

class MemoryManager {
  private snapshots: MemorySnapshot[] = [];
  private maxSnapshots = 100;
  private leakDetectionThreshold = 10; // MB per minute
  private cleanupInterval: number | null = null;
  private monitoringInterval: number | null = null;
  
  constructor() {
    this.initialize();
  }

  private initialize() {
    // Start memory monitoring
    this.startMonitoring();
    
    // Setup cleanup interval
    this.startPeriodicCleanup();
    
    // Listen for page visibility changes
    this.setupVisibilityHandling();
    
    // Setup low memory warnings
    this.setupLowMemoryWarnings();
  }

  /**
   * Start continuous memory monitoring
   */
  startMonitoring(intervalMs: number = 30000): void {
    if (this.monitoringInterval) {
      clearInterval(this.monitoringInterval);
    }

    this.monitoringInterval = window.setInterval(() => {
      this.takeSnapshot();
      this.detectMemoryLeaks();
    }, intervalMs);

    console.log(`Memory monitoring started (interval: ${intervalMs}ms)`);
  }

  /**
   * Stop memory monitoring
   */
  stopMonitoring(): void {
    if (this.monitoringInterval) {
      clearInterval(this.monitoringInterval);
      this.monitoringInterval = null;
    }
  }

  /**
   * Take a memory snapshot
   */
  takeSnapshot(): MemorySnapshot | null {
    if (!('memory' in performance)) {
      console.warn('Performance.memory API not available');
      return null;
    }

    const memory = (performance as any).memory as MemoryInfo;
    const snapshot: MemorySnapshot = {
      timestamp: Date.now(),
      memory: {
        usedJSHeapSize: memory.usedJSHeapSize,
        totalJSHeapSize: memory.totalJSHeapSize,
        jsHeapSizeLimit: memory.jsHeapSizeLimit
      },
      url: window.location.href,
      userAgent: navigator.userAgent
    };

    this.snapshots.push(snapshot);

    // Keep only recent snapshots
    if (this.snapshots.length > this.maxSnapshots) {
      this.snapshots.shift();
    }

    return snapshot;
  }

  /**
   * Get current memory usage
   */
  getCurrentMemoryUsage(): MemoryInfo | null {
    if (!('memory' in performance)) {
      return null;
    }

    return (performance as any).memory as MemoryInfo;
  }

  /**
   * Format memory size in human readable format
   */
  formatMemorySize(bytes: number): string {
    const mb = bytes / (1024 * 1024);
    return `${mb.toFixed(2)} MB`;
  }

  /**
   * Get memory usage statistics
   */
  getMemoryStats(): {
    current: MemoryInfo | null;
    usage_percentage: number;
    trend: 'increasing' | 'decreasing' | 'stable';
    leak_detected: boolean;
  } {
    const current = this.getCurrentMemoryUsage();
    
    if (!current) {
      return {
        current: null,
        usage_percentage: 0,
        trend: 'stable',
        leak_detected: false
      };
    }

    const usagePercentage = (current.usedJSHeapSize / current.jsHeapSizeLimit) * 100;
    const trend = this.calculateMemoryTrend();
    const leakInfo = this.detectMemoryLeaks();

    return {
      current,
      usage_percentage: usagePercentage,
      trend,
      leak_detected: leakInfo.detected
    };
  }

  /**
   * Detect memory leaks based on growth patterns
   */
  detectMemoryLeaks(): MemoryLeak {
    if (this.snapshots.length < 5) {
      return {
        detected: false,
        growthRate: 0,
        snapshots: this.snapshots,
        recommendation: 'Insufficient data for leak detection'
      };
    }

    // Calculate memory growth rate over the last 5 minutes
    const recentSnapshots = this.snapshots.slice(-10);
    const timeSpan = recentSnapshots[recentSnapshots.length - 1].timestamp - recentSnapshots[0].timestamp;
    const timeSpanMinutes = timeSpan / (1000 * 60);
    
    const memoryGrowth = recentSnapshots[recentSnapshots.length - 1].memory.usedJSHeapSize - 
                        recentSnapshots[0].memory.usedJSHeapSize;
    const growthRateMB = (memoryGrowth / (1024 * 1024)) / timeSpanMinutes;

    const detected = growthRateMB > this.leakDetectionThreshold;
    
    let recommendation = 'Memory usage is normal';
    if (detected) {
      if (growthRateMB > 50) {
        recommendation = 'Critical memory leak detected! Check for unclosed intervals, event listeners, or large object accumulation.';
      } else if (growthRateMB > 20) {
        recommendation = 'Significant memory growth detected. Review recent code changes and check for memory-intensive operations.';
      } else {
        recommendation = 'Moderate memory growth detected. Monitor for continued growth patterns.';
      }
    }

    return {
      detected,
      growthRate: growthRateMB,
      snapshots: recentSnapshots,
      recommendation
    };
  }

  /**
   * Force garbage collection (if available)
   */
  forceGarbageCollection(): boolean {
    if ('gc' in window && typeof (window as any).gc === 'function') {
      try {
        (window as any).gc();
        console.log('Manual garbage collection triggered');
        return true;
      } catch (error) {
        console.warn('Failed to trigger garbage collection:', error);
        return false;
      }
    }
    
    console.warn('Garbage collection not available');
    return false;
  }

  /**
   * Optimize memory usage
   */
  optimizeMemory(): {
    actions_taken: string[];
    memory_before: MemoryInfo | null;
    memory_after: MemoryInfo | null;
  } {
    const memoryBefore = this.getCurrentMemoryUsage();
    const actionsTaken: string[] = [];

    // Clear old snapshots
    if (this.snapshots.length > 50) {
      this.snapshots = this.snapshots.slice(-50);
      actionsTaken.push('Cleared old memory snapshots');
    }

    // Clear browser caches (if in Electron)
    if ((window as any).electronAPI?.clearCache) {
      (window as any).electronAPI.clearCache();
      actionsTaken.push('Cleared Electron cache');
    }

    // Force garbage collection
    if (this.forceGarbageCollection()) {
      actionsTaken.push('Triggered garbage collection');
    }

    // Clear any global references (application-specific)
    this.clearApplicationCache();
    actionsTaken.push('Cleared application cache');

    const memoryAfter = this.getCurrentMemoryUsage();

    return {
      actions_taken: actionsTaken,
      memory_before: memoryBefore,
      memory_after: memoryAfter
    };
  }

  /**
   * Setup periodic cleanup
   */
  private startPeriodicCleanup(intervalMs: number = 300000): void { // 5 minutes
    if (this.cleanupInterval) {
      clearInterval(this.cleanupInterval);
    }

    this.cleanupInterval = window.setInterval(() => {
      this.periodicCleanup();
    }, intervalMs);
  }

  /**
   * Perform periodic cleanup
   */
  private periodicCleanup(): void {
    const memoryStats = this.getMemoryStats();
    
    // If memory usage is high, perform optimization
    if (memoryStats.usage_percentage > 80) {
      console.warn(`High memory usage detected (${memoryStats.usage_percentage.toFixed(1)}%)`);
      this.optimizeMemory();
    }

    // Clear old DOM nodes that might be hanging around
    this.clearOrphanedDOMNodes();
  }

  /**
   * Calculate memory trend
   */
  private calculateMemoryTrend(): 'increasing' | 'decreasing' | 'stable' {
    if (this.snapshots.length < 3) {
      return 'stable';
    }

    const recent = this.snapshots.slice(-3);
    const trend = recent[2].memory.usedJSHeapSize - recent[0].memory.usedJSHeapSize;
    const threshold = 1024 * 1024; // 1MB

    if (trend > threshold) {
      return 'increasing';
    } else if (trend < -threshold) {
      return 'decreasing';
    } else {
      return 'stable';
    }
  }

  /**
   * Setup page visibility handling
   */
  private setupVisibilityHandling(): void {
    document.addEventListener('visibilitychange', () => {
      if (document.hidden) {
        // Page is hidden, reduce memory usage
        this.optimizeMemory();
      }
    });
  }

  /**
   * Setup low memory warnings
   */
  private setupLowMemoryWarnings(): void {
    // Check for low memory conditions
    const checkMemory = () => {
      const stats = this.getMemoryStats();
      if (stats.usage_percentage > 90) {
        this.handleLowMemory();
      }
    };

    setInterval(checkMemory, 10000); // Check every 10 seconds
  }

  /**
   * Handle low memory situations
   */
  private handleLowMemory(): void {
    console.warn('Low memory condition detected');
    
    // Emit custom event for application to handle
    window.dispatchEvent(new CustomEvent('lowMemory', {
      detail: this.getMemoryStats()
    }));

    // Perform aggressive cleanup
    this.optimizeMemory();
  }

  /**
   * Clear application-specific cache
   */
  private clearApplicationCache(): void {
    // Clear any global caches or large objects
    // This should be customized based on your application
    
    // Clear image caches
    if ('caches' in window) {
      caches.keys().then(names => {
        names.forEach(name => {
          caches.delete(name);
        });
      });
    }

    // Clear any global app state that can be rebuilt
    // Example: clearApplicationState();
  }

  /**
   * Clear orphaned DOM nodes
   */
  private clearOrphanedDOMNodes(): void {
    // Remove any DOM nodes that are no longer needed
    const orphanedElements = document.querySelectorAll('[data-cleanup="true"]');
    orphanedElements.forEach(element => {
      element.remove();
    });
  }

  /**
   * Get detailed memory report
   */
  getDetailedReport(): {
    current_usage: MemoryInfo | null;
    statistics: ReturnType<typeof this.getMemoryStats>;
    leak_analysis: MemoryLeak;
    recommendations: string[];
    snapshots_count: number;
  } {
    const current = this.getCurrentMemoryUsage();
    const stats = this.getMemoryStats();
    const leakAnalysis = this.detectMemoryLeaks();
    
    const recommendations: string[] = [];
    
    if (stats.usage_percentage > 80) {
      recommendations.push('High memory usage - consider implementing lazy loading');
    }
    
    if (stats.leak_detected) {
      recommendations.push('Memory leak detected - review event listeners and intervals');
    }
    
    if (this.snapshots.length < 10) {
      recommendations.push('Insufficient monitoring data - let application run longer for better analysis');
    }

    return {
      current_usage: current,
      statistics: stats,
      leak_analysis: leakAnalysis,
      recommendations,
      snapshots_count: this.snapshots.length
    };
  }

  /**
   * Cleanup when destroying the manager
   */
  destroy(): void {
    this.stopMonitoring();
    
    if (this.cleanupInterval) {
      clearInterval(this.cleanupInterval);
      this.cleanupInterval = null;
    }
    
    this.snapshots = [];
  }
}

// Create global memory manager instance
export const memoryManager = new MemoryManager();

// Export types for use in components
export type { MemoryInfo, MemorySnapshot, MemoryLeak };