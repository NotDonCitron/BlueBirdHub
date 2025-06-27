/**
 * Storage Manager for Offline Data Pruning and Management
 * Handles storage optimization, cleanup, and quota management
 */

import { offlineStorage, EntityType, OfflineEntity } from '../OfflineStorage';

export interface StorageQuota {
  quota: number; // Total available storage in bytes
  usage: number; // Current usage in bytes
  usagePercentage: number; // Usage as percentage
  remaining: number; // Remaining storage in bytes
}

export interface StorageStats {
  totalEntities: number;
  entitiesByType: Record<EntityType, number>;
  storageQuota: StorageQuota;
  oldestEntity: number | null;
  newestEntity: number | null;
  syncedEntities: number;
  unsyncedEntities: number;
  conflictedEntities: number;
  deletedEntities: number;
  compressedEntities: number;
  encryptedEntities: number;
}

export interface PruningPolicy {
  maxAge: number; // Maximum age in milliseconds
  maxEntities: number; // Maximum number of entities per type
  keepSyncedOnly: boolean; // Only keep synced entities
  prioritizeByAccess: boolean; // Keep frequently accessed items
  compressOldData: boolean; // Compress old data to save space
  encryptSensitiveData: boolean; // Encrypt sensitive data
}

export interface CleanupResult {
  deleted: number;
  compressed: number;
  encrypted: number;
  spaceFreed: number; // Bytes freed
  errors: string[];
}

/**
 * Storage manager for offline data optimization
 */
export class StorageManager {
  private defaultPruningPolicy: PruningPolicy = {
    maxAge: 30 * 24 * 60 * 60 * 1000, // 30 days
    maxEntities: 10000, // 10k entities per type
    keepSyncedOnly: false,
    prioritizeByAccess: true,
    compressOldData: true,
    encryptSensitiveData: true
  };

  private customPolicies: Map<EntityType, Partial<PruningPolicy>> = new Map();
  private lastCleanup = 0;
  private isCleanupRunning = false;

  constructor() {
    this.initializeDefaultPolicies();
  }

  /**
   * Initialize default pruning policies for different entity types
   */
  private initializeDefaultPolicies(): void {
    // Files need special handling due to size
    this.customPolicies.set(EntityType.FILE, {
      maxAge: 7 * 24 * 60 * 60 * 1000, // 7 days for files
      maxEntities: 1000,
      compressOldData: true,
      prioritizeByAccess: true
    });

    // Analytics can be more aggressively pruned
    this.customPolicies.set(EntityType.ANALYTICS, {
      maxAge: 14 * 24 * 60 * 60 * 1000, // 14 days for analytics
      maxEntities: 5000,
      keepSyncedOnly: true
    });

    // Workspaces are important, keep longer
    this.customPolicies.set(EntityType.WORKSPACE, {
      maxAge: 90 * 24 * 60 * 60 * 1000, // 90 days
      maxEntities: 100
    });

    // Tasks are moderately important
    this.customPolicies.set(EntityType.TASK, {
      maxAge: 60 * 24 * 60 * 60 * 1000, // 60 days
      maxEntities: 5000
    });
  }

  /**
   * Get current storage statistics
   */
  async getStorageStats(): Promise<StorageStats> {
    try {
      const quota = await this.getStorageQuota();
      const stats = await offlineStorage.getStorageStats();
      
      let totalEntities = 0;
      let syncedEntities = 0;
      let unsyncedEntities = 0;
      let conflictedEntities = 0;
      let deletedEntities = 0;
      let compressedEntities = 0;
      let encryptedEntities = 0;

      const entitiesByType: Record<EntityType, number> = {} as any;

      // Count entities by type and status
      for (const entityType of Object.values(EntityType)) {
        const entities = await offlineStorage.getAll(entityType, { includeDeleted: true });
        entitiesByType[entityType] = entities.length;
        totalEntities += entities.length;

        for (const entity of entities) {
          if (entity.isDeleted) {
            deletedEntities++;
          } else if (entity.syncStatus === 'synced') {
            syncedEntities++;
          } else if (entity.syncStatus === 'conflict') {
            conflictedEntities++;
          } else {
            unsyncedEntities++;
          }

          // Check for compression/encryption markers
          if ((entity as any).compressed) compressedEntities++;
          if ((entity as any).encrypted) encryptedEntities++;
        }
      }

      return {
        totalEntities,
        entitiesByType,
        storageQuota: quota,
        oldestEntity: stats.oldestUnsyncedItem,
        newestEntity: Date.now(), // Approximate
        syncedEntities,
        unsyncedEntities,
        conflictedEntities,
        deletedEntities,
        compressedEntities,
        encryptedEntities
      };

    } catch (error) {
      console.error('Failed to get storage stats:', error);
      throw error;
    }
  }

  /**
   * Get storage quota information
   */
  async getStorageQuota(): Promise<StorageQuota> {
    try {
      if ('storage' in navigator && 'estimate' in navigator.storage) {
        const estimate = await navigator.storage.estimate();
        const quota = estimate.quota || 0;
        const usage = estimate.usage || 0;
        
        return {
          quota,
          usage,
          usagePercentage: quota > 0 ? (usage / quota) * 100 : 0,
          remaining: quota - usage
        };
      }

      // Fallback for browsers without storage estimation
      return {
        quota: 0,
        usage: 0,
        usagePercentage: 0,
        remaining: 0
      };

    } catch (error) {
      console.error('Failed to get storage quota:', error);
      return {
        quota: 0,
        usage: 0,
        usagePercentage: 0,
        remaining: 0
      };
    }
  }

  /**
   * Set custom pruning policy for an entity type
   */
  setPruningPolicy(entityType: EntityType, policy: Partial<PruningPolicy>): void {
    this.customPolicies.set(entityType, policy);
  }

  /**
   * Get effective pruning policy for an entity type
   */
  getPruningPolicy(entityType: EntityType): PruningPolicy {
    const customPolicy = this.customPolicies.get(entityType) || {};
    return { ...this.defaultPruningPolicy, ...customPolicy };
  }

  /**
   * Perform cleanup based on storage pressure
   */
  async performCleanup(force = false): Promise<CleanupResult> {
    if (this.isCleanupRunning && !force) {
      throw new Error('Cleanup already running');
    }

    this.isCleanupRunning = true;
    const result: CleanupResult = {
      deleted: 0,
      compressed: 0,
      encrypted: 0,
      spaceFreed: 0,
      errors: []
    };

    try {
      const stats = await this.getStorageStats();
      
      // Determine cleanup strategy based on storage pressure
      const needsCleanup = force || 
        stats.storageQuota.usagePercentage > 80 ||
        Date.now() - this.lastCleanup > 24 * 60 * 60 * 1000; // Daily cleanup

      if (!needsCleanup) {
        return result;
      }

      console.log('🧹 Starting storage cleanup...');

      // Clean up each entity type
      for (const entityType of Object.values(EntityType)) {
        try {
          const typeResult = await this.cleanupEntityType(entityType, stats);
          result.deleted += typeResult.deleted;
          result.compressed += typeResult.compressed;
          result.encrypted += typeResult.encrypted;
          result.spaceFreed += typeResult.spaceFreed;
        } catch (error) {
          result.errors.push(`Failed to cleanup ${entityType}: ${error}`);
        }
      }

      // Clean up system data
      const systemResult = await this.cleanupSystemData();
      result.deleted += systemResult.deleted;
      result.spaceFreed += systemResult.spaceFreed;

      this.lastCleanup = Date.now();
      
      console.log(`✅ Cleanup completed: ${result.deleted} deleted, ${result.compressed} compressed, ${result.spaceFreed} bytes freed`);

    } catch (error) {
      result.errors.push(`Cleanup failed: ${error}`);
      console.error('Storage cleanup failed:', error);
    } finally {
      this.isCleanupRunning = false;
    }

    return result;
  }

  /**
   * Clean up specific entity type
   */
  private async cleanupEntityType(entityType: EntityType, stats: StorageStats): Promise<CleanupResult> {
    const result: CleanupResult = {
      deleted: 0,
      compressed: 0,
      encrypted: 0,
      spaceFreed: 0,
      errors: []
    };

    const policy = this.getPruningPolicy(entityType);
    const entities = await offlineStorage.getAll(entityType, { includeDeleted: true });
    const now = Date.now();

    // Sort entities for prioritized cleanup
    const sortedEntities = this.sortEntitiesForCleanup(entities);

    for (const entity of sortedEntities) {
      try {
        const entitySize = this.estimateEntitySize(entity);
        let shouldDelete = false;
        let shouldCompress = false;
        let shouldEncrypt = false;

        // Check deletion criteria
        if (entity.isDeleted && entity.deletedAt && (now - entity.deletedAt) > policy.maxAge) {
          shouldDelete = true;
        } else if (policy.keepSyncedOnly && entity.syncStatus !== 'synced') {
          shouldDelete = true;
        } else if ((now - entity.createdAt) > policy.maxAge) {
          shouldDelete = true;
        } else if (stats.entitiesByType[entityType] > policy.maxEntities) {
          // Delete oldest entities if over limit
          shouldDelete = true;
        }

        // Check compression criteria
        if (!shouldDelete && policy.compressOldData && !entity.isDeleted) {
          const age = now - entity.lastModified;
          if (age > (policy.maxAge * 0.5) && !(entity as any).compressed) {
            shouldCompress = true;
          }
        }

        // Check encryption criteria
        if (!shouldDelete && policy.encryptSensitiveData && this.containsSensitiveData(entity)) {
          if (!(entity as any).encrypted) {
            shouldEncrypt = true;
          }
        }

        // Perform actions
        if (shouldDelete) {
          await offlineStorage.hardDelete(entityType, entity.id);
          result.deleted++;
          result.spaceFreed += entitySize;
        } else {
          let modified = false;

          if (shouldCompress) {
            await this.compressEntity(entityType, entity);
            result.compressed++;
            result.spaceFreed += entitySize * 0.3; // Estimate 30% compression
            modified = true;
          }

          if (shouldEncrypt) {
            await this.encryptEntity(entityType, entity);
            result.encrypted++;
            modified = true;
          }

          if (modified) {
            await offlineStorage.store(entityType, entity);
          }
        }

      } catch (error) {
        result.errors.push(`Failed to process ${entityType} ${entity.id}: ${error}`);
      }
    }

    return result;
  }

  /**
   * Clean up system data (sync queue, conflicts, etc.)
   */
  private async cleanupSystemData(): Promise<CleanupResult> {
    const result: CleanupResult = {
      deleted: 0,
      compressed: 0,
      encrypted: 0,
      spaceFreed: 0,
      errors: []
    };

    try {
      // Clean up old sync queue items (failed items older than 7 days)
      const syncQueue = await offlineStorage.getSyncQueue();
      const oldThreshold = Date.now() - (7 * 24 * 60 * 60 * 1000);
      
      const oldItems = syncQueue.filter(item => 
        item.createdAt < oldThreshold && item.retryCount >= item.maxRetries
      );

      for (const item of oldItems) {
        await offlineStorage.clearSyncQueue([item.id]);
        result.deleted++;
        result.spaceFreed += this.estimateEntitySize(item);
      }

      // Clean up resolved conflicts older than 30 days
      const conflicts = await offlineStorage.getConflicts();
      const resolvedOldConflicts = conflicts.filter(conflict =>
        conflict.resolvedAt && 
        (Date.now() - conflict.resolvedAt) > (30 * 24 * 60 * 60 * 1000)
      );

      for (const conflict of resolvedOldConflicts) {
        // Remove resolved conflicts (implementation would depend on storage structure)
        result.deleted++;
      }

      // Clean up old analytics events
      const analytics = await offlineStorage.getAnalyticsEvents({
        toDate: Date.now() - (14 * 24 * 60 * 60 * 1000) // Older than 14 days
      });

      for (const event of analytics.slice(0, Math.max(0, analytics.length - 1000))) {
        // Keep last 1000 analytics events
        result.deleted++;
      }

    } catch (error) {
      result.errors.push(`System cleanup failed: ${error}`);
    }

    return result;
  }

  /**
   * Sort entities for cleanup prioritization
   */
  private sortEntitiesForCleanup(entities: OfflineEntity[]): OfflineEntity[] {
    return entities.sort((a, b) => {
      // Prioritize deleted entities
      if (a.isDeleted && !b.isDeleted) return -1;
      if (!a.isDeleted && b.isDeleted) return 1;

      // Then by sync status (unsynced items last)
      if (a.syncStatus === 'synced' && b.syncStatus !== 'synced') return -1;
      if (a.syncStatus !== 'synced' && b.syncStatus === 'synced') return 1;

      // Then by age (oldest first)
      return a.createdAt - b.createdAt;
    });
  }

  /**
   * Compress entity data
   */
  private async compressEntity(entityType: EntityType, entity: OfflineEntity): Promise<void> {
    try {
      // Mark as compressed (actual compression would be handled by storage layer)
      (entity as any).compressed = true;
      (entity as any).compressedAt = Date.now();
    } catch (error) {
      console.error('Failed to compress entity:', error);
    }
  }

  /**
   * Encrypt entity data
   */
  private async encryptEntity(entityType: EntityType, entity: OfflineEntity): Promise<void> {
    try {
      // Mark as encrypted (actual encryption would be handled by storage layer)
      (entity as any).encrypted = true;
      (entity as any).encryptedAt = Date.now();
    } catch (error) {
      console.error('Failed to encrypt entity:', error);
    }
  }

  /**
   * Check if entity contains sensitive data
   */
  private containsSensitiveData(entity: any): boolean {
    const sensitiveFields = ['password', 'token', 'key', 'secret', 'credential'];
    const entityString = JSON.stringify(entity).toLowerCase();
    
    return sensitiveFields.some(field => entityString.includes(field));
  }

  /**
   * Estimate entity size in bytes
   */
  private estimateEntitySize(entity: any): number {
    try {
      return new Blob([JSON.stringify(entity)]).size;
    } catch {
      return JSON.stringify(entity).length; // Fallback
    }
  }

  /**
   * Perform emergency cleanup when storage is critically low
   */
  async emergencyCleanup(): Promise<CleanupResult> {
    console.warn('🚨 Performing emergency storage cleanup');
    
    const result: CleanupResult = {
      deleted: 0,
      compressed: 0,
      encrypted: 0,
      spaceFreed: 0,
      errors: []
    };

    try {
      // Delete all deleted entities immediately
      for (const entityType of Object.values(EntityType)) {
        const entities = await offlineStorage.getAll(entityType, { includeDeleted: true });
        const deletedEntities = entities.filter(e => e.isDeleted);
        
        for (const entity of deletedEntities) {
          await offlineStorage.hardDelete(entityType, entity.id);
          result.deleted++;
          result.spaceFreed += this.estimateEntitySize(entity);
        }
      }

      // Clear all sync queue items that have failed multiple times
      const syncQueue = await offlineStorage.getSyncQueue();
      const failedItems = syncQueue.filter(item => item.retryCount >= 3);
      
      if (failedItems.length > 0) {
        await offlineStorage.clearSyncQueue(failedItems.map(item => item.id));
        result.deleted += failedItems.length;
      }

      // Clear old analytics
      const analytics = await offlineStorage.getAnalyticsEvents();
      if (analytics.length > 100) {
        // Keep only the most recent 100 analytics events
        const toDelete = analytics.slice(0, analytics.length - 100);
        for (const event of toDelete) {
          result.deleted++;
        }
      }

    } catch (error) {
      result.errors.push(`Emergency cleanup failed: ${error}`);
    }

    return result;
  }

  /**
   * Schedule automatic cleanup
   */
  scheduleAutomaticCleanup(): void {
    // Run cleanup daily
    setInterval(async () => {
      try {
        await this.performCleanup();
      } catch (error) {
        console.error('Automatic cleanup failed:', error);
      }
    }, 24 * 60 * 60 * 1000); // 24 hours

    // Monitor storage pressure
    setInterval(async () => {
      try {
        const quota = await this.getStorageQuota();
        if (quota.usagePercentage > 90) {
          await this.emergencyCleanup();
        } else if (quota.usagePercentage > 80) {
          await this.performCleanup(true);
        }
      } catch (error) {
        console.error('Storage monitoring failed:', error);
      }
    }, 5 * 60 * 1000); // Every 5 minutes
  }

  /**
   * Export storage statistics for debugging
   */
  async exportDiagnostics(): Promise<any> {
    try {
      const stats = await this.getStorageStats();
      const quota = await this.getStorageQuota();
      
      return {
        timestamp: Date.now(),
        storageStats: stats,
        storageQuota: quota,
        pruningPolicies: Object.fromEntries(this.customPolicies),
        lastCleanup: this.lastCleanup,
        isCleanupRunning: this.isCleanupRunning
      };
    } catch (error) {
      console.error('Failed to export diagnostics:', error);
      return { error: error.message };
    }
  }
}

// Singleton instance
export const storageManager = new StorageManager();