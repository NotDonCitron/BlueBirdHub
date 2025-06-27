/**
 * Background Synchronization with Intelligent Retry Logic
 * Handles automatic sync operations with exponential backoff and smart scheduling
 */

import { syncManager, SyncEvent } from './SyncManager';
import { offlineStorage, EntityType, SyncQueueItem } from '../OfflineStorage';

export interface BackgroundSyncConfig {
  enabled: boolean;
  syncInterval: number; // milliseconds
  retryDelayBase: number; // base delay for exponential backoff
  maxRetryDelay: number; // maximum retry delay
  maxRetries: number; // maximum retry attempts
  batchSize: number; // items to sync in one batch
  lowPowerMode: boolean; // reduce sync frequency on low battery
  wifiOnlyMode: boolean; // sync only on WiFi
}

export interface SyncSchedule {
  immediate: boolean;
  delayed: number; // delay in milliseconds
  condition?: 'online' | 'wifi' | 'charging' | 'idle';
}

export interface NetworkInfo {
  isOnline: boolean;
  connectionType: string;
  effectiveType: string;
  downlink: number;
  rtt: number;
  saveData: boolean;
}

export interface BatteryInfo {
  level: number;
  charging: boolean;
  chargingTime: number;
  dischargingTime: number;
}

/**
 * Background sync manager with intelligent scheduling
 */
export class BackgroundSync {
  private config: BackgroundSyncConfig = {
    enabled: true,
    syncInterval: 30000, // 30 seconds
    retryDelayBase: 1000, // 1 second
    maxRetryDelay: 300000, // 5 minutes
    maxRetries: 5,
    batchSize: 10,
    lowPowerMode: false,
    wifiOnlyMode: false
  };

  private syncTimer: number | null = null;
  private retryTimers: Map<string, number> = new Map();
  private isActive = false;
  private lastSyncAttempt = 0;
  private consecutiveFailures = 0;
  private networkInfo: NetworkInfo | null = null;
  private batteryInfo: BatteryInfo | null = null;
  private visibilityState: 'visible' | 'hidden' = 'visible';

  constructor() {
    this.initializeMonitoring();
  }

  /**
   * Initialize background sync and monitoring
   */
  async initialize(): Promise<void> {
    try {
      // Update network and battery info
      await this.updateNetworkInfo();
      await this.updateBatteryInfo();
      
      // Set up event listeners
      this.setupEventListeners();
      
      // Register service worker background sync if available
      if ('serviceWorker' in navigator && 'sync' in window.ServiceWorkerRegistration.prototype) {
        await this.registerServiceWorkerSync();
      }
      
      this.isActive = true;
      this.scheduleNextSync();
      
      console.log('✅ Background sync initialized');
    } catch (error) {
      console.error('Failed to initialize background sync:', error);
    }
  }

  /**
   * Update configuration
   */
  updateConfig(newConfig: Partial<BackgroundSyncConfig>): void {
    this.config = { ...this.config, ...newConfig };
    
    if (this.isActive) {
      this.rescheduleSync();
    }
  }

  /**
   * Start background sync
   */
  start(): void {
    if (!this.isActive) {
      this.isActive = true;
      this.scheduleNextSync();
      console.log('🚀 Background sync started');
    }
  }

  /**
   * Stop background sync
   */
  stop(): void {
    this.isActive = false;
    this.clearAllTimers();
    console.log('⏹️ Background sync stopped');
  }

  /**
   * Force immediate sync
   */
  async forcSync(): Promise<void> {
    if (!this.shouldSync()) {
      console.log('⏸️ Sync conditions not met, skipping force sync');
      return;
    }

    try {
      await this.performSync();
    } catch (error) {
      console.error('Force sync failed:', error);
    }
  }

  /**
   * Schedule sync based on current conditions
   */
  private scheduleNextSync(): void {
    if (!this.isActive || !this.config.enabled) return;

    const schedule = this.calculateSyncSchedule();
    
    if (schedule.immediate) {
      this.performSync();
    } else if (schedule.delayed > 0) {
      this.setSyncTimer(schedule.delayed);
    }
  }

  /**
   * Calculate when the next sync should occur
   */
  private calculateSyncSchedule(): SyncSchedule {
    const now = Date.now();
    
    // Check if we should sync immediately
    if (this.shouldSyncImmediately()) {
      return { immediate: true, delayed: 0 };
    }

    // Calculate base delay
    let delay = this.config.syncInterval;

    // Adjust delay based on network conditions
    if (this.networkInfo) {
      if (this.networkInfo.effectiveType === 'slow-2g' || this.networkInfo.effectiveType === '2g') {
        delay *= 3; // Longer delays on slow connections
      } else if (this.networkInfo.saveData) {
        delay *= 2; // Respect data saver mode
      }
    }

    // Adjust delay based on battery
    if (this.batteryInfo && this.config.lowPowerMode) {
      if (!this.batteryInfo.charging && this.batteryInfo.level < 0.2) {
        delay *= 4; // Much longer delays on low battery
      } else if (!this.batteryInfo.charging && this.batteryInfo.level < 0.5) {
        delay *= 2; // Longer delays on medium battery
      }
    }

    // Adjust delay based on visibility
    if (this.visibilityState === 'hidden') {
      delay *= 2; // Less frequent sync when app is hidden
    }

    // Exponential backoff for consecutive failures
    if (this.consecutiveFailures > 0) {
      const backoffMultiplier = Math.pow(2, this.consecutiveFailures);
      delay = Math.min(delay * backoffMultiplier, this.config.maxRetryDelay);
    }

    // Ensure minimum time between sync attempts
    const timeSinceLastAttempt = now - this.lastSyncAttempt;
    const minDelay = 5000; // Minimum 5 seconds between attempts
    
    if (timeSinceLastAttempt < minDelay) {
      delay = Math.max(delay, minDelay - timeSinceLastAttempt);
    }

    return { immediate: false, delayed: delay };
  }

  /**
   * Check if sync should happen immediately
   */
  private shouldSyncImmediately(): boolean {
    // Sync immediately if network just came back online
    if (this.networkInfo?.isOnline && this.consecutiveFailures > 0) {
      return true;
    }

    // Sync immediately if there are high-priority items
    // This would need to check the sync queue for high priority items
    return false;
  }

  /**
   * Check if sync conditions are met
   */
  private shouldSync(): boolean {
    // Don't sync if disabled
    if (!this.config.enabled) return false;

    // Don't sync if offline
    if (!this.networkInfo?.isOnline) return false;

    // Check WiFi only mode
    if (this.config.wifiOnlyMode && this.networkInfo.connectionType !== 'wifi') {
      return false;
    }

    // Check low power mode
    if (this.config.lowPowerMode && this.batteryInfo) {
      if (!this.batteryInfo.charging && this.batteryInfo.level < 0.1) {
        return false;
      }
    }

    return true;
  }

  /**
   * Perform the actual sync operation
   */
  private async performSync(): Promise<void> {
    if (!this.shouldSync()) {
      this.scheduleNextSync();
      return;
    }

    this.lastSyncAttempt = Date.now();

    try {
      console.log('🔄 Starting background sync...');
      
      // Get sync queue and prioritize items
      const syncQueue = await offlineStorage.getSyncQueue();
      const prioritizedQueue = this.prioritizeQueue(syncQueue);
      
      if (prioritizedQueue.length === 0) {
        this.consecutiveFailures = 0;
        this.scheduleNextSync();
        return;
      }

      // Sync in batches
      const batch = prioritizedQueue.slice(0, this.config.batchSize);
      const result = await syncManager.sync({
        batchSize: this.config.batchSize,
        timeout: this.calculateTimeout()
      });

      if (result.success) {
        this.consecutiveFailures = 0;
        console.log(`✅ Background sync completed: ${result.synced} items synced`);
      } else {
        this.consecutiveFailures++;
        console.warn(`⚠️ Background sync partially failed: ${result.failed} items failed`);
      }

      // Schedule retry for failed items
      if (result.failed > 0) {
        await this.scheduleRetries(batch.slice(result.synced));
      }

    } catch (error) {
      this.consecutiveFailures++;
      console.error('❌ Background sync failed:', error);
      
      // Schedule retry with exponential backoff
      await this.scheduleRetryForError();
    }

    this.scheduleNextSync();
  }

  /**
   * Prioritize sync queue items
   */
  private prioritizeQueue(queue: SyncQueueItem[]): SyncQueueItem[] {
    return queue.sort((a, b) => {
      // Sort by priority (higher first)
      if (a.priority !== b.priority) {
        return (b.priority || 0) - (a.priority || 0);
      }

      // Then by retry count (fewer retries first)
      if (a.retryCount !== b.retryCount) {
        return a.retryCount - b.retryCount;
      }

      // Then by age (older first)
      return a.createdAt - b.createdAt;
    });
  }

  /**
   * Calculate timeout based on network conditions
   */
  private calculateTimeout(): number {
    if (!this.networkInfo) return 30000; // Default 30 seconds

    const { effectiveType, rtt } = this.networkInfo;
    
    switch (effectiveType) {
      case 'slow-2g':
        return 60000; // 60 seconds for very slow connections
      case '2g':
        return 45000; // 45 seconds for slow connections
      case '3g':
        return 30000; // 30 seconds for medium connections
      case '4g':
      default:
        return 20000; // 20 seconds for fast connections
    }
  }

  /**
   * Schedule retries for failed items
   */
  private async scheduleRetries(failedItems: SyncQueueItem[]): Promise<void> {
    for (const item of failedItems) {
      const retryDelay = this.calculateRetryDelay(item.retryCount);
      const timerId = window.setTimeout(async () => {
        try {
          await this.retryItem(item);
        } catch (error) {
          console.error(`Retry failed for item ${item.id}:`, error);
        } finally {
          this.retryTimers.delete(item.id);
        }
      }, retryDelay);

      this.retryTimers.set(item.id, timerId);
    }
  }

  /**
   * Schedule retry after a general error
   */
  private async scheduleRetryForError(): Promise<void> {
    const delay = this.calculateRetryDelay(this.consecutiveFailures);
    this.setSyncTimer(delay);
  }

  /**
   * Calculate retry delay with exponential backoff
   */
  private calculateRetryDelay(retryCount: number): number {
    const delay = this.config.retryDelayBase * Math.pow(2, retryCount);
    const jitter = Math.random() * 1000; // Add jitter to avoid thundering herd
    return Math.min(delay + jitter, this.config.maxRetryDelay);
  }

  /**
   * Retry a single item
   */
  private async retryItem(item: SyncQueueItem): Promise<void> {
    if (item.retryCount >= this.config.maxRetries) {
      console.warn(`Max retries reached for item ${item.id}, giving up`);
      return;
    }

    if (!this.shouldSync()) {
      // Reschedule for later
      this.scheduleRetries([item]);
      return;
    }

    // The actual retry will be handled by the sync manager
    // We just trigger a sync here
    await this.performSync();
  }

  /**
   * Set sync timer
   */
  private setSyncTimer(delay: number): void {
    this.clearSyncTimer();
    this.syncTimer = window.setTimeout(() => {
      this.performSync();
    }, delay);
  }

  /**
   * Clear sync timer
   */
  private clearSyncTimer(): void {
    if (this.syncTimer) {
      clearTimeout(this.syncTimer);
      this.syncTimer = null;
    }
  }

  /**
   * Clear all timers
   */
  private clearAllTimers(): void {
    this.clearSyncTimer();
    
    for (const timerId of this.retryTimers.values()) {
      clearTimeout(timerId);
    }
    this.retryTimers.clear();
  }

  /**
   * Reschedule sync with new config
   */
  private rescheduleSync(): void {
    this.clearAllTimers();
    this.scheduleNextSync();
  }

  /**
   * Set up event listeners for environmental changes
   */
  private setupEventListeners(): void {
    // Network state changes
    window.addEventListener('online', () => {
      this.updateNetworkInfo().then(() => {
        this.consecutiveFailures = 0; // Reset on network restore
        this.scheduleNextSync();
      });
    });

    window.addEventListener('offline', () => {
      this.updateNetworkInfo();
      this.clearAllTimers(); // Stop sync when offline
    });

    // Visibility changes
    document.addEventListener('visibilitychange', () => {
      this.visibilityState = document.visibilityState as 'visible' | 'hidden';
      this.rescheduleSync();
    });

    // Page focus/blur
    window.addEventListener('focus', () => {
      this.scheduleNextSync();
    });

    // Battery changes
    if ('getBattery' in navigator) {
      (navigator as any).getBattery().then((battery: any) => {
        battery.addEventListener('chargingchange', () => {
          this.updateBatteryInfo().then(() => this.rescheduleSync());
        });
        
        battery.addEventListener('levelchange', () => {
          this.updateBatteryInfo().then(() => this.rescheduleSync());
        });
      });
    }

    // Connection changes
    if ('connection' in navigator) {
      (navigator as any).connection.addEventListener('change', () => {
        this.updateNetworkInfo().then(() => this.rescheduleSync());
      });
    }
  }

  /**
   * Initialize monitoring of system resources
   */
  private initializeMonitoring(): void {
    // Update info periodically
    setInterval(() => {
      this.updateNetworkInfo();
      this.updateBatteryInfo();
    }, 60000); // Update every minute
  }

  /**
   * Update network information
   */
  private async updateNetworkInfo(): Promise<void> {
    try {
      const connection = (navigator as any).connection;
      
      this.networkInfo = {
        isOnline: navigator.onLine,
        connectionType: connection?.type || 'unknown',
        effectiveType: connection?.effectiveType || '4g',
        downlink: connection?.downlink || 0,
        rtt: connection?.rtt || 0,
        saveData: connection?.saveData || false
      };
    } catch (error) {
      this.networkInfo = {
        isOnline: navigator.onLine,
        connectionType: 'unknown',
        effectiveType: '4g',
        downlink: 0,
        rtt: 0,
        saveData: false
      };
    }
  }

  /**
   * Update battery information
   */
  private async updateBatteryInfo(): Promise<void> {
    try {
      if ('getBattery' in navigator) {
        const battery = await (navigator as any).getBattery();
        this.batteryInfo = {
          level: battery.level,
          charging: battery.charging,
          chargingTime: battery.chargingTime,
          dischargingTime: battery.dischargingTime
        };
      }
    } catch (error) {
      this.batteryInfo = null;
    }
  }

  /**
   * Register service worker background sync
   */
  private async registerServiceWorkerSync(): Promise<void> {
    try {
      const registration = await navigator.serviceWorker.ready;
      
      // Register different sync tags for different entity types
      const syncTags = ['workspace-sync', 'task-sync', 'file-sync', 'full-sync'];
      
      for (const tag of syncTags) {
        try {
          await registration.sync.register(tag);
        } catch (error) {
          console.warn(`Failed to register sync tag ${tag}:`, error);
        }
      }
      
      console.log('✅ Service worker background sync registered');
    } catch (error) {
      console.warn('Service worker background sync not available:', error);
    }
  }

  /**
   * Get current sync status
   */
  getStatus(): {
    isActive: boolean;
    nextSyncIn: number | null;
    consecutiveFailures: number;
    networkInfo: NetworkInfo | null;
    batteryInfo: BatteryInfo | null;
  } {
    const nextSyncIn = this.syncTimer ? 
      this.lastSyncAttempt + this.config.syncInterval - Date.now() : null;

    return {
      isActive: this.isActive,
      nextSyncIn: nextSyncIn && nextSyncIn > 0 ? nextSyncIn : null,
      consecutiveFailures: this.consecutiveFailures,
      networkInfo: this.networkInfo,
      batteryInfo: this.batteryInfo
    };
  }
}

// Singleton instance
export const backgroundSync = new BackgroundSync();