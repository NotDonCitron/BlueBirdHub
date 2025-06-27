/**
 * Comprehensive Sync Manager for Offline Operations
 * Coordinates sync operations, handles conflicts, and manages offline state
 */

import { offlineStorage, EntityType, SyncStatus, OfflineEntity, SyncQueueItem } from '../OfflineStorage';
import { conflictResolver, ConflictData, ResolutionStrategy } from '../conflict/ConflictResolver';
import { apiClient } from '../../config/apiClient';

export interface SyncOptions {
  entityTypes?: EntityType[];
  priority?: number;
  batchSize?: number;
  timeout?: number;
  retryOnFailure?: boolean;
}

export interface SyncResult {
  success: boolean;
  synced: number;
  failed: number;
  conflicts: number;
  errors: string[];
  duration: number;
}

export interface SyncStatus {
  isOnline: boolean;
  isSyncing: boolean;
  syncProgress: number;
  queueSize: number;
  conflictCount: number;
  lastSync: number | null;
  nextSync: number | null;
}

export interface SyncEvent {
  type: 'start' | 'progress' | 'complete' | 'error' | 'conflict';
  entityType?: EntityType;
  entityId?: string | number;
  progress?: number;
  error?: string;
  conflict?: ConflictData;
}

/**
 * Main sync manager class
 */
export class SyncManager {
  private isInitialized = false;
  private isSyncing = false;
  private syncListeners: Set<(event: SyncEvent) => void> = new Set();
  private autoSyncEnabled = true;
  private autoSyncInterval = 30000; // 30 seconds
  private autoSyncTimer: number | null = null;
  private networkStatus = navigator.onLine;
  private serviceWorkerRegistration: ServiceWorkerRegistration | null = null;

  constructor() {
    this.initializeNetworkListeners();
  }

  /**
   * Initialize the sync manager
   */
  async initialize(): Promise<void> {
    if (this.isInitialized) return;

    try {
      // Initialize offline storage
      await offlineStorage.initialize();

      // Register service worker if not already registered
      if ('serviceWorker' in navigator) {
        this.serviceWorkerRegistration = await navigator.serviceWorker.register('/service-worker.js');
        this.setupServiceWorkerListeners();
      }

      // Start auto-sync if enabled
      if (this.autoSyncEnabled) {
        this.startAutoSync();
      }

      this.isInitialized = true;
      console.log('✅ Sync manager initialized');

    } catch (error) {
      console.error('Failed to initialize sync manager:', error);
      throw error;
    }
  }

  /**
   * Queue an offline action for later sync
   */
  async queueOfflineAction(
    entityType: EntityType,
    entityId: string | number,
    action: 'create' | 'update' | 'delete',
    data: any,
    options: { priority?: number; url?: string; method?: string } = {}
  ): Promise<void> {
    await this.ensureInitialized();

    const queueItem: Omit<SyncQueueItem, 'id' | 'createdAt'> = {
      entityType,
      entityId,
      action,
      data,
      url: options.url || this.buildApiUrl(entityType, entityId, action),
      method: options.method || this.getHttpMethod(action),
      priority: options.priority || 1,
      retryCount: 0,
      maxRetries: 5
    };

    await offlineStorage.addToSyncQueue(queueItem);

    // Update entity sync status
    if (data) {
      data.syncStatus = action === 'create' ? SyncStatus.PENDING_CREATE :
                       action === 'update' ? SyncStatus.PENDING_UPDATE :
                       SyncStatus.PENDING_DELETE;
      
      await offlineStorage.store(entityType, data);
    }

    // Try to sync immediately if online
    if (this.networkStatus && !this.isSyncing) {
      this.scheduleSync();
    }

    console.log(`[SyncManager] Queued ${action} for ${entityType} ${entityId}`);
  }

  /**
   * Perform immediate sync
   */
  async sync(options: SyncOptions = {}): Promise<SyncResult> {
    await this.ensureInitialized();

    if (this.isSyncing) {
      throw new Error('Sync already in progress');
    }

    if (!this.networkStatus) {
      throw new Error('Cannot sync while offline');
    }

    this.isSyncing = true;
    const startTime = Date.now();
    const result: SyncResult = {
      success: false,
      synced: 0,
      failed: 0,
      conflicts: 0,
      errors: [],
      duration: 0
    };

    try {
      this.emitSyncEvent({ type: 'start' });

      // Get sync queue
      const syncQueue = await offlineStorage.getSyncQueue();
      const filteredQueue = options.entityTypes 
        ? syncQueue.filter(item => options.entityTypes!.includes(item.entityType))
        : syncQueue;

      if (filteredQueue.length === 0) {
        result.success = true;
        return result;
      }

      const batchSize = options.batchSize || 10;
      const batches = this.createBatches(filteredQueue, batchSize);

      for (let i = 0; i < batches.length; i++) {
        const batch = batches[i];
        const batchResults = await this.syncBatch(batch, options.timeout);

        result.synced += batchResults.synced;
        result.failed += batchResults.failed;
        result.conflicts += batchResults.conflicts;
        result.errors.push(...batchResults.errors);

        // Emit progress
        const progress = ((i + 1) / batches.length) * 100;
        this.emitSyncEvent({ type: 'progress', progress });

        // Small delay between batches to avoid overwhelming the server
        if (i < batches.length - 1) {
          await this.delay(100);
        }
      }

      result.success = result.failed === 0;
      result.duration = Date.now() - startTime;

      // Update last sync time
      await this.updateLastSyncTime();

      this.emitSyncEvent({ type: 'complete' });
      console.log(`[SyncManager] Sync completed: ${result.synced} synced, ${result.failed} failed, ${result.conflicts} conflicts`);

    } catch (error) {
      result.errors.push(error instanceof Error ? error.message : 'Unknown error');
      result.duration = Date.now() - startTime;
      
      this.emitSyncEvent({ 
        type: 'error', 
        error: error instanceof Error ? error.message : 'Unknown error' 
      });
      
      console.error('[SyncManager] Sync failed:', error);
    } finally {
      this.isSyncing = false;
    }

    return result;
  }

  /**
   * Sync a batch of items
   */
  private async syncBatch(
    batch: SyncQueueItem[], 
    timeout?: number
  ): Promise<{ synced: number; failed: number; conflicts: number; errors: string[] }> {
    const result = { synced: 0, failed: 0, conflicts: 0, errors: [] };
    const processedIds: string[] = [];

    for (const item of batch) {
      try {
        const syncResult = await this.syncSingleItem(item, timeout);
        
        if (syncResult.success) {
          result.synced++;
          processedIds.push(item.id);
          
          // Update entity sync status
          await this.updateEntitySyncStatus(item.entityType, item.entityId, SyncStatus.SYNCED);
        } else if (syncResult.conflict) {
          result.conflicts++;
          // Keep item in queue for user resolution
        } else {
          result.failed++;
          result.errors.push(syncResult.error || 'Unknown sync error');
        }

      } catch (error) {
        result.failed++;
        result.errors.push(error instanceof Error ? error.message : 'Unknown error');
        console.error(`[SyncManager] Error syncing item ${item.id}:`, error);
      }
    }

    // Remove successfully synced items from queue
    if (processedIds.length > 0) {
      await offlineStorage.clearSyncQueue(processedIds);
    }

    return result;
  }

  /**
   * Sync a single item
   */
  private async syncSingleItem(
    item: SyncQueueItem, 
    timeout?: number
  ): Promise<{ success: boolean; conflict?: boolean; error?: string }> {
    try {
      // Prepare request
      const requestOptions: RequestInit = {
        method: item.method,
        headers: {
          'Content-Type': 'application/json',
          ...item.headers
        },
        signal: timeout ? AbortSignal.timeout(timeout) : undefined
      };

      if (item.data && item.method !== 'DELETE') {
        requestOptions.body = JSON.stringify(item.data);
      }

      // Make API request
      const response = await fetch(item.url, requestOptions);

      if (response.ok) {
        // Handle successful response
        const responseData = response.status !== 204 ? await response.json() : null;
        
        if (responseData && (item.action === 'create' || item.action === 'update')) {
          // Update local entity with server response
          await this.updateLocalEntity(item.entityType, item.entityId, responseData);
        }

        return { success: true };

      } else if (response.status === 409) {
        // Handle conflict
        const serverData = await response.json();
        await this.handleSyncConflict(item, serverData);
        return { success: false, conflict: true };

      } else if (response.status === 404 && item.action === 'delete') {
        // Item already deleted on server
        return { success: true };

      } else {
        return { 
          success: false, 
          error: `HTTP ${response.status}: ${response.statusText}` 
        };
      }

    } catch (error) {
      if (error instanceof Error && error.name === 'AbortError') {
        return { success: false, error: 'Request timeout' };
      }
      
      return { 
        success: false, 
        error: error instanceof Error ? error.message : 'Unknown error' 
      };
    }
  }

  /**
   * Handle sync conflict
   */
  private async handleSyncConflict(item: SyncQueueItem, serverData: any): Promise<void> {
    const localData = item.data;
    const conflictFields = conflictResolver.detectConflicts(localData, serverData);

    const conflict: ConflictData = {
      id: `conflict_${item.entityType}_${item.entityId}_${Date.now()}`,
      entityType: item.entityType,
      entityId: item.entityId,
      localData,
      remoteData: serverData,
      conflictFields,
      timestamp: Date.now(),
      syncAction: item.action
    };

    // Try automatic resolution first
    const autoResolution = await conflictResolver.resolveConflictAutomatically(conflict);
    
    if (autoResolution.resolved && autoResolution.resolvedData) {
      // Auto-resolution successful
      await this.updateLocalEntity(item.entityType, item.entityId, autoResolution.resolvedData);
      console.log(`[SyncManager] Auto-resolved conflict for ${item.entityType} ${item.entityId}`);
    } else {
      // Store conflict for user resolution
      await offlineStorage.storeConflict(conflict);
      this.emitSyncEvent({ type: 'conflict', conflict });
      console.log(`[SyncManager] Conflict stored for user resolution: ${item.entityType} ${item.entityId}`);
    }
  }

  /**
   * Resolve a conflict with user input
   */
  async resolveConflict(conflictId: string, strategy: ResolutionStrategy): Promise<boolean> {
    try {
      const conflicts = await offlineStorage.getConflicts();
      const conflict = conflicts.find(c => c.id === conflictId);

      if (!conflict) {
        throw new Error('Conflict not found');
      }

      const resolution = await conflictResolver.resolveConflictWithStrategy(conflict, strategy);
      
      if (resolution.resolved && resolution.resolvedData) {
        // Update local entity
        await this.updateLocalEntity(conflict.entityType, conflict.entityId, resolution.resolvedData);
        
        // Mark conflict as resolved
        await offlineStorage.resolveConflict(conflictId, resolution.resolvedData);
        
        // Queue for sync
        await this.queueOfflineAction(
          conflict.entityType,
          conflict.entityId,
          'update',
          resolution.resolvedData,
          { priority: 2 } // High priority for resolved conflicts
        );

        console.log(`[SyncManager] Conflict ${conflictId} resolved`);
        return true;
      }

      return false;

    } catch (error) {
      console.error('[SyncManager] Error resolving conflict:', error);
      return false;
    }
  }

  /**
   * Get current sync status
   */
  async getStatus(): Promise<SyncStatus> {
    await this.ensureInitialized();

    const syncQueue = await offlineStorage.getSyncQueue();
    const conflicts = await offlineStorage.getConflicts();
    const stats = await offlineStorage.getStorageStats();

    return {
      isOnline: this.networkStatus,
      isSyncing: this.isSyncing,
      syncProgress: 0, // Would be updated during sync
      queueSize: syncQueue.length,
      conflictCount: conflicts.length,
      lastSync: stats.oldestUnsyncedItem,
      nextSync: this.autoSyncTimer ? Date.now() + this.autoSyncInterval : null
    };
  }

  /**
   * Add sync event listener
   */
  addEventListener(listener: (event: SyncEvent) => void): void {
    this.syncListeners.add(listener);
  }

  /**
   * Remove sync event listener
   */
  removeEventListener(listener: (event: SyncEvent) => void): void {
    this.syncListeners.delete(listener);
  }

  /**
   * Enable/disable auto-sync
   */
  setAutoSync(enabled: boolean, interval?: number): void {
    this.autoSyncEnabled = enabled;
    if (interval) {
      this.autoSyncInterval = interval;
    }

    if (enabled) {
      this.startAutoSync();
    } else {
      this.stopAutoSync();
    }
  }

  /**
   * Force full sync of all data
   */
  async fullSync(): Promise<SyncResult> {
    return this.sync({
      entityTypes: [EntityType.WORKSPACE, EntityType.TASK, EntityType.FILE],
      batchSize: 5 // Smaller batches for full sync
    });
  }

  // Private helper methods

  private async ensureInitialized(): Promise<void> {
    if (!this.isInitialized) {
      await this.initialize();
    }
  }

  private initializeNetworkListeners(): void {
    const updateNetworkStatus = () => {
      const wasOnline = this.networkStatus;
      this.networkStatus = navigator.onLine;

      if (!wasOnline && this.networkStatus) {
        // Just came back online
        console.log('[SyncManager] Network restored, scheduling sync');
        this.scheduleSync(1000); // Sync after 1 second delay
      }
    };

    window.addEventListener('online', updateNetworkStatus);
    window.addEventListener('offline', updateNetworkStatus);
  }

  private setupServiceWorkerListeners(): void {
    if (!this.serviceWorkerRegistration) return;

    navigator.serviceWorker.addEventListener('message', (event) => {
      const { type } = event.data;

      switch (type) {
        case 'SYNC_SUCCESS':
          this.handleServiceWorkerSyncSuccess(event.data);
          break;
        case 'SYNC_CONFLICT':
          this.handleServiceWorkerSyncConflict(event.data);
          break;
        case 'SYNC_FAILURE':
          this.handleServiceWorkerSyncFailure(event.data);
          break;
      }
    });
  }

  private handleServiceWorkerSyncSuccess(data: any): void {
    console.log(`[SyncManager] Service worker synced ${data.entityType} ${data.entityId}`);
  }

  private handleServiceWorkerSyncConflict(data: any): void {
    this.emitSyncEvent({ type: 'conflict', conflict: data.conflict });
  }

  private handleServiceWorkerSyncFailure(data: any): void {
    console.error(`[SyncManager] Service worker sync failed for ${data.entityType} ${data.entityId}:`, data.error);
  }

  private startAutoSync(): void {
    if (this.autoSyncTimer) {
      clearInterval(this.autoSyncTimer);
    }

    this.autoSyncTimer = window.setInterval(() => {
      if (this.networkStatus && !this.isSyncing) {
        this.sync().catch(error => {
          console.error('[SyncManager] Auto-sync failed:', error);
        });
      }
    }, this.autoSyncInterval);
  }

  private stopAutoSync(): void {
    if (this.autoSyncTimer) {
      clearInterval(this.autoSyncTimer);
      this.autoSyncTimer = null;
    }
  }

  private scheduleSync(delay = 0): void {
    setTimeout(() => {
      if (this.networkStatus && !this.isSyncing) {
        this.sync().catch(error => {
          console.error('[SyncManager] Scheduled sync failed:', error);
        });
      }
    }, delay);
  }

  private emitSyncEvent(event: SyncEvent): void {
    this.syncListeners.forEach(listener => {
      try {
        listener(event);
      } catch (error) {
        console.error('[SyncManager] Error in sync event listener:', error);
      }
    });
  }

  private createBatches<T>(items: T[], batchSize: number): T[][] {
    const batches: T[][] = [];
    for (let i = 0; i < items.length; i += batchSize) {
      batches.push(items.slice(i, i + batchSize));
    }
    return batches;
  }

  private buildApiUrl(entityType: EntityType, entityId: string | number, action: string): string {
    const baseUrl = '/api';
    const entityPath = entityType === EntityType.WORKSPACE ? 'workspaces' :
                      entityType === EntityType.TASK ? 'tasks' :
                      entityType === EntityType.FILE ? 'files' : entityType;

    if (action === 'create') {
      return `${baseUrl}/${entityPath}`;
    } else {
      return `${baseUrl}/${entityPath}/${entityId}`;
    }
  }

  private getHttpMethod(action: string): string {
    switch (action) {
      case 'create': return 'POST';
      case 'update': return 'PUT';
      case 'delete': return 'DELETE';
      default: return 'GET';
    }
  }

  private async updateLocalEntity(entityType: EntityType, entityId: string | number, data: any): Promise<void> {
    data.syncStatus = SyncStatus.SYNCED;
    data.lastModified = Date.now();
    await offlineStorage.store(entityType, data);
  }

  private async updateEntitySyncStatus(entityType: EntityType, entityId: string | number, status: SyncStatus): Promise<void> {
    const entity = await offlineStorage.get(entityType, entityId);
    if (entity) {
      entity.syncStatus = status;
      entity.lastModified = Date.now();
      await offlineStorage.store(entityType, entity);
    }
  }

  private async updateLastSyncTime(): Promise<void> {
    // This would be stored in the metadata store
    const timestamp = Date.now();
    // Implementation depends on how metadata is stored
  }

  private delay(ms: number): Promise<void> {
    return new Promise(resolve => setTimeout(resolve, ms));
  }
}

// Singleton instance
export const syncManager = new SyncManager();