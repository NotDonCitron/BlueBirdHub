/**
 * Comprehensive Offline Manager - Main Orchestrator
 * Coordinates all offline functionality and provides unified interface
 */

import { offlineStorage, EntityType } from './OfflineStorage';
import { electronOfflineStorage } from './ElectronOfflineStorage';
import { syncManager, SyncEvent } from './sync/SyncManager';
import { backgroundSync } from './sync/BackgroundSync';
import { conflictResolver } from './conflict/ConflictResolver';
import { storageManager } from './storage/StorageManager';
import { offlineSearch } from './search/OfflineSearch';
import { encryptionManager } from './encryption/EncryptionManager';
import { deltaSync } from './sync/DeltaSync';

export interface OfflineConfig {
  enableEncryption: boolean;
  enableCompression: boolean;
  enableBackgroundSync: boolean;
  enableOfflineSearch: boolean;
  enableAnalytics: boolean;
  syncInterval: number;
  storageQuotaWarning: number; // Percentage
  maxRetries: number;
  userPassword?: string;
  platform: 'web' | 'electron';
}

export interface OfflineStatus {
  isInitialized: boolean;
  isOnline: boolean;
  storageUsage: number;
  storageQuota: number;
  syncQueueSize: number;
  conflictCount: number;
  lastSync: number | null;
  encryptionEnabled: boolean;
  searchIndexSize: number;
  backgroundSyncActive: boolean;
}

export interface OfflineStats {
  storage: any;
  sync: any;
  search: any;
  encryption: any;
  conflicts: number;
  performance: {
    avgSyncTime: number;
    avgSearchTime: number;
    cacheHitRate: number;
  };
}

/**
 * Main offline manager that orchestrates all offline functionality
 */
export class OfflineManager {
  private config: OfflineConfig = {
    enableEncryption: true,
    enableCompression: true,
    enableBackgroundSync: true,
    enableOfflineSearch: true,
    enableAnalytics: true,
    syncInterval: 30000,
    storageQuotaWarning: 80,
    maxRetries: 5,
    platform: 'web'
  };

  private isInitialized = false;
  private currentStorage: typeof offlineStorage | typeof electronOfflineStorage;
  private eventListeners: Set<(event: OfflineEvent) => void> = new Set();
  private performanceMetrics: Map<string, number[]> = new Map();

  constructor() {
    // Detect platform
    this.config.platform = this.detectPlatform();
    this.currentStorage = this.config.platform === 'electron' ? electronOfflineStorage : offlineStorage;
  }

  /**
   * Initialize the entire offline system
   */
  async initialize(config?: Partial<OfflineConfig>): Promise<void> {
    if (this.isInitialized) {
      console.warn('Offline manager already initialized');
      return;
    }

    const startTime = Date.now();

    try {
      // Update configuration
      if (config) {
        this.config = { ...this.config, ...config };
      }

      this.emitEvent({ type: 'initialization_start' });

      // Initialize storage layer
      console.log('🚀 Initializing offline storage...');
      await this.currentStorage.initialize();

      // Initialize encryption if enabled
      if (this.config.enableEncryption) {
        console.log('🔐 Initializing encryption...');
        await encryptionManager.initialize(this.config.userPassword);
      }

      // Initialize sync manager
      console.log('🔄 Initializing sync manager...');
      await syncManager.initialize();

      // Initialize background sync if enabled
      if (this.config.enableBackgroundSync) {
        console.log('⏰ Initializing background sync...');
        await backgroundSync.initialize();
        backgroundSync.updateConfig({
          enabled: true,
          syncInterval: this.config.syncInterval,
          maxRetries: this.config.maxRetries
        });
        backgroundSync.start();
      }

      // Initialize search if enabled
      if (this.config.enableOfflineSearch) {
        console.log('🔍 Initializing offline search...');
        await offlineSearch.initialize();
      }

      // Initialize delta sync
      console.log('📊 Initializing delta sync...');
      await deltaSync.initialize();

      // Initialize storage manager
      console.log('💾 Initializing storage manager...');
      storageManager.scheduleAutomaticCleanup();

      // Set up event listeners
      this.setupEventListeners();

      // Set up service worker communication
      this.setupServiceWorkerCommunication();

      // Schedule periodic tasks
      this.schedulePeriodicTasks();

      this.isInitialized = true;
      const initTime = Date.now() - startTime;

      this.emitEvent({ 
        type: 'initialization_complete', 
        data: { initTime, config: this.config }
      });

      console.log(`✅ Offline manager initialized in ${initTime}ms`);

    } catch (error) {
      this.emitEvent({ 
        type: 'initialization_error', 
        error: error instanceof Error ? error.message : 'Unknown error'
      });

      console.error('❌ Failed to initialize offline manager:', error);
      throw error;
    }
  }

  /**
   * Create offline entity with automatic encryption and indexing
   */
  async createEntity<T>(
    entityType: EntityType,
    data: Omit<T, 'id' | 'createdAt' | 'lastModified' | 'syncStatus'>
  ): Promise<T> {
    await this.ensureInitialized();

    const startTime = Date.now();

    try {
      // Generate entity with metadata
      const entity: any = {
        ...data,
        id: this.generateEntityId(),
        createdAt: Date.now(),
        lastModified: Date.now(),
        syncStatus: 'pending_create',
        version: 1
      };

      // Encrypt sensitive data if enabled
      let processedEntity = entity;
      if (this.config.enableEncryption) {
        processedEntity = await encryptionManager.encryptEntity(entityType, entity);
      }

      // Store entity
      await this.currentStorage.store(entityType, processedEntity, {
        encrypt: this.config.enableEncryption,
        compress: this.config.enableCompression
      });

      // Add to search index if enabled
      if (this.config.enableOfflineSearch && !entity.isDeleted) {
        const searchableText = this.createSearchableText(entity, entityType);
        await this.currentStorage.updateSearchIndex(entityType, entity.id, searchableText);
      }

      // Queue for sync
      await syncManager.queueOfflineAction(
        entityType,
        entity.id,
        'create',
        entity,
        { priority: 1 }
      );

      // Record performance
      const duration = Date.now() - startTime;
      this.recordPerformance('create_entity', duration);

      this.emitEvent({
        type: 'entity_created',
        entityType,
        entityId: entity.id,
        data: entity
      });

      return entity;

    } catch (error) {
      this.emitEvent({
        type: 'entity_error',
        entityType,
        error: error instanceof Error ? error.message : 'Unknown error'
      });

      throw error;
    }
  }

  /**
   * Update offline entity
   */
  async updateEntity<T>(
    entityType: EntityType,
    id: string | number,
    updates: Partial<T>
  ): Promise<T> {
    await this.ensureInitialized();

    const startTime = Date.now();

    try {
      // Get current entity
      let currentEntity = await this.currentStorage.get(entityType, id);
      if (!currentEntity) {
        throw new Error('Entity not found');
      }

      // Decrypt if needed
      if (this.config.enableEncryption) {
        currentEntity = await encryptionManager.decryptEntity(entityType, currentEntity);
      }

      // Merge updates
      const updatedEntity = {
        ...currentEntity,
        ...updates,
        lastModified: Date.now(),
        syncStatus: 'pending_update',
        version: (currentEntity.version || 1) + 1
      };

      // Encrypt if enabled
      let processedEntity = updatedEntity;
      if (this.config.enableEncryption) {
        processedEntity = await encryptionManager.encryptEntity(entityType, updatedEntity);
      }

      // Store updated entity
      await this.currentStorage.store(entityType, processedEntity, {
        encrypt: this.config.enableEncryption,
        compress: this.config.enableCompression
      });

      // Update search index
      if (this.config.enableOfflineSearch && !updatedEntity.isDeleted) {
        const searchableText = this.createSearchableText(updatedEntity, entityType);
        await this.currentStorage.updateSearchIndex(entityType, id, searchableText);
      }

      // Queue for sync
      await syncManager.queueOfflineAction(
        entityType,
        id,
        'update',
        updatedEntity,
        { priority: 1 }
      );

      // Record performance
      const duration = Date.now() - startTime;
      this.recordPerformance('update_entity', duration);

      this.emitEvent({
        type: 'entity_updated',
        entityType,
        entityId: id,
        data: updatedEntity
      });

      return updatedEntity;

    } catch (error) {
      this.emitEvent({
        type: 'entity_error',
        entityType,
        entityId: id,
        error: error instanceof Error ? error.message : 'Unknown error'
      });

      throw error;
    }
  }

  /**
   * Delete offline entity
   */
  async deleteEntity(entityType: EntityType, id: string | number): Promise<void> {
    await this.ensureInitialized();

    try {
      // Soft delete
      await this.currentStorage.delete(entityType, id);

      // Queue for sync
      await syncManager.queueOfflineAction(
        entityType,
        id,
        'delete',
        null,
        { priority: 1 }
      );

      this.emitEvent({
        type: 'entity_deleted',
        entityType,
        entityId: id
      });

    } catch (error) {
      this.emitEvent({
        type: 'entity_error',
        entityType,
        entityId: id,
        error: error instanceof Error ? error.message : 'Unknown error'
      });

      throw error;
    }
  }

  /**
   * Get entity with automatic decryption
   */
  async getEntity<T>(entityType: EntityType, id: string | number): Promise<T | null> {
    await this.ensureInitialized();

    try {
      let entity = await this.currentStorage.get(entityType, id);
      if (!entity) return null;

      // Decrypt if needed
      if (this.config.enableEncryption) {
        entity = await encryptionManager.decryptEntity(entityType, entity);
      }

      return entity;

    } catch (error) {
      console.error('Failed to get entity:', error);
      return null;
    }
  }

  /**
   * Get all entities with filtering and decryption
   */
  async getEntities<T>(
    entityType: EntityType,
    filter?: any
  ): Promise<T[]> {
    await this.ensureInitialized();

    try {
      const entities = await this.currentStorage.getAll(entityType, filter);
      
      // Decrypt if needed
      if (this.config.enableEncryption) {
        const decryptedEntities = await Promise.all(
          entities.map(entity => encryptionManager.decryptEntity(entityType, entity))
        );
        return decryptedEntities;
      }

      return entities;

    } catch (error) {
      console.error('Failed to get entities:', error);
      return [];
    }
  }

  /**
   * Search entities using offline search
   */
  async searchEntities(query: string, options?: any): Promise<any> {
    await this.ensureInitialized();

    if (!this.config.enableOfflineSearch) {
      throw new Error('Offline search not enabled');
    }

    const startTime = Date.now();

    try {
      const results = await offlineSearch.search({ query, ...options });
      
      const duration = Date.now() - startTime;
      this.recordPerformance('search', duration);

      return results;

    } catch (error) {
      console.error('Search failed:', error);
      throw error;
    }
  }

  /**
   * Force synchronization
   */
  async sync(): Promise<any> {
    await this.ensureInitialized();
    return await syncManager.sync();
  }

  /**
   * Get offline status
   */
  async getStatus(): Promise<OfflineStatus> {
    await this.ensureInitialized();

    const [syncStatus, storageStats, searchStats, encryptionStats] = await Promise.all([
      syncManager.getStatus(),
      this.currentStorage.getStorageStats(),
      this.config.enableOfflineSearch ? offlineSearch.getStats() : null,
      this.config.enableEncryption ? encryptionManager.getEncryptionStats() : null
    ]);

    return {
      isInitialized: this.isInitialized,
      isOnline: navigator.onLine,
      storageUsage: storageStats.totalSize || 0,
      storageQuota: 0, // Would need quota API
      syncQueueSize: syncStatus.queueSize,
      conflictCount: syncStatus.conflictCount,
      lastSync: syncStatus.lastSync,
      encryptionEnabled: this.config.enableEncryption,
      searchIndexSize: searchStats?.totalDocuments || 0,
      backgroundSyncActive: this.config.enableBackgroundSync
    };
  }

  /**
   * Get comprehensive statistics
   */
  async getStats(): Promise<OfflineStats> {
    await this.ensureInitialized();

    const [storageStats, encryptionStats, searchStats] = await Promise.all([
      this.currentStorage.getStorageStats(),
      this.config.enableEncryption ? encryptionManager.getEncryptionStats() : null,
      this.config.enableOfflineSearch ? offlineSearch.getStats() : null
    ]);

    const performanceStats = this.calculatePerformanceStats();

    return {
      storage: storageStats,
      sync: await syncManager.getStatus(),
      search: searchStats,
      encryption: encryptionStats,
      conflicts: (await this.currentStorage.getConflicts()).length,
      performance: performanceStats
    };
  }

  /**
   * Clean up storage
   */
  async cleanup(): Promise<any> {
    await this.ensureInitialized();
    return await storageManager.performCleanup(true);
  }

  /**
   * Export all offline data
   */
  async exportData(): Promise<any> {
    await this.ensureInitialized();
    return await this.currentStorage.exportData();
  }

  /**
   * Import offline data
   */
  async importData(data: any): Promise<void> {
    await this.ensureInitialized();
    await this.currentStorage.importData(data);
  }

  /**
   * Add event listener
   */
  addEventListener(listener: (event: OfflineEvent) => void): void {
    this.eventListeners.add(listener);
  }

  /**
   * Remove event listener
   */
  removeEventListener(listener: (event: OfflineEvent) => void): void {
    this.eventListeners.delete(listener);
  }

  // Private methods

  private async ensureInitialized(): Promise<void> {
    if (!this.isInitialized) {
      throw new Error('Offline manager not initialized. Call initialize() first.');
    }
  }

  private detectPlatform(): 'web' | 'electron' {
    return typeof window !== 'undefined' && (window as any).electronAPI ? 'electron' : 'web';
  }

  private generateEntityId(): string {
    return `${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
  }

  private createSearchableText(entity: any, entityType: EntityType): string {
    const searchable = [];
    
    // Add common searchable fields
    if (entity.name) searchable.push(entity.name);
    if (entity.title) searchable.push(entity.title);
    if (entity.description) searchable.push(entity.description);
    if (entity.content) searchable.push(entity.content);
    
    // Add entity-specific fields
    switch (entityType) {
      case EntityType.TASK:
        if (entity.status) searchable.push(entity.status);
        if (entity.priority) searchable.push(entity.priority);
        break;
      case EntityType.FILE:
        if (entity.file_name) searchable.push(entity.file_name);
        if (entity.file_extension) searchable.push(entity.file_extension);
        break;
    }

    return searchable.join(' ');
  }

  private setupEventListeners(): void {
    // Listen to sync events
    syncManager.addEventListener((event: SyncEvent) => {
      this.emitEvent({
        type: 'sync_event',
        data: event
      });
    });

    // Listen to network changes
    window.addEventListener('online', () => {
      this.emitEvent({ type: 'network_online' });
    });

    window.addEventListener('offline', () => {
      this.emitEvent({ type: 'network_offline' });
    });
  }

  private setupServiceWorkerCommunication(): void {
    if ('serviceWorker' in navigator) {
      navigator.serviceWorker.addEventListener('message', (event) => {
        this.emitEvent({
          type: 'service_worker_message',
          data: event.data
        });
      });
    }
  }

  private schedulePeriodicTasks(): void {
    // Storage monitoring
    setInterval(async () => {
      try {
        const stats = await this.currentStorage.getStorageStats();
        // Check storage quota warning
        // Implementation would depend on quota API
        
        this.emitEvent({
          type: 'storage_stats',
          data: stats
        });

      } catch (error) {
        console.error('Storage monitoring failed:', error);
      }
    }, 60000); // Every minute

    // Performance metrics cleanup
    setInterval(() => {
      this.cleanupPerformanceMetrics();
    }, 300000); // Every 5 minutes
  }

  private recordPerformance(operation: string, duration: number): void {
    if (!this.performanceMetrics.has(operation)) {
      this.performanceMetrics.set(operation, []);
    }
    
    const metrics = this.performanceMetrics.get(operation)!;
    metrics.push(duration);
    
    // Keep only recent metrics
    if (metrics.length > 100) {
      metrics.splice(0, metrics.length - 100);
    }
  }

  private calculatePerformanceStats(): {
    avgSyncTime: number;
    avgSearchTime: number;
    cacheHitRate: number;
  } {
    const syncMetrics = this.performanceMetrics.get('sync') || [];
    const searchMetrics = this.performanceMetrics.get('search') || [];

    return {
      avgSyncTime: syncMetrics.length > 0 ? syncMetrics.reduce((a, b) => a + b, 0) / syncMetrics.length : 0,
      avgSearchTime: searchMetrics.length > 0 ? searchMetrics.reduce((a, b) => a + b, 0) / searchMetrics.length : 0,
      cacheHitRate: 0 // Would be calculated from cache statistics
    };
  }

  private cleanupPerformanceMetrics(): void {
    for (const [operation, metrics] of this.performanceMetrics.entries()) {
      if (metrics.length > 50) {
        this.performanceMetrics.set(operation, metrics.slice(-50));
      }
    }
  }

  private emitEvent(event: OfflineEvent): void {
    this.eventListeners.forEach(listener => {
      try {
        listener(event);
      } catch (error) {
        console.error('Event listener error:', error);
      }
    });
  }
}

interface OfflineEvent {
  type: string;
  entityType?: EntityType;
  entityId?: string | number;
  data?: any;
  error?: string;
}

// Singleton instance
export const offlineManager = new OfflineManager();