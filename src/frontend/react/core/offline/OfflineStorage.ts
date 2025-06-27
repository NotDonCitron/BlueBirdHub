/**
 * Comprehensive Offline Storage System for BlueBirdHub
 * Provides IndexedDB-based offline storage with encryption, compression, and conflict resolution
 */

import { AESGCMEncryption } from './encryption/AESGCMEncryption';
import { DataCompression } from './compression/DataCompression';

// Database schema version for migrations
export const OFFLINE_DB_VERSION = 1;
export const OFFLINE_DB_NAME = 'BlueBirdHubOffline';

// Entity types for offline storage
export enum EntityType {
  WORKSPACE = 'workspace',
  TASK = 'task',
  FILE = 'file',
  USER = 'user',
  PROJECT = 'project',
  SYNC_QUEUE = 'sync_queue',
  CONFLICT = 'conflict',
  SEARCH_INDEX = 'search_index',
  ANALYTICS = 'analytics',
  METADATA = 'metadata'
}

// Sync status for entities
export enum SyncStatus {
  SYNCED = 'synced',
  PENDING_CREATE = 'pending_create',
  PENDING_UPDATE = 'pending_update',
  PENDING_DELETE = 'pending_delete',
  CONFLICT = 'conflict',
  ERROR = 'error'
}

// Conflict resolution strategies
export enum ConflictResolution {
  LAST_WRITE_WINS = 'last_write_wins',
  MERGE = 'merge',
  USER_CHOICE = 'user_choice',
  KEEP_BOTH = 'keep_both'
}

// Base interface for offline entities
export interface OfflineEntity {
  id: string | number;
  localId?: string; // UUID for offline-created entities
  syncStatus: SyncStatus;
  version: number;
  lastModified: number;
  createdAt: number;
  deletedAt?: number;
  isDeleted?: boolean;
  etag?: string; // For HTTP caching
  checksum?: string; // For data integrity
}

// Workspace offline entity
export interface OfflineWorkspace extends OfflineEntity {
  user_id: number;
  name: string;
  description?: string;
  theme: string;
  is_active: boolean;
  is_default: boolean;
  icon?: string;
  color?: string;
  layout_config?: any;
  ambient_sound?: string;
  last_accessed_at?: number;
}

// Task offline entity
export interface OfflineTask extends OfflineEntity {
  user_id: number;
  workspace_id?: number;
  project_id?: number;
  title: string;
  description?: string;
  status: string;
  priority: string;
  due_date?: number;
  completed_at?: number;
  estimated_hours?: number;
  actual_hours?: number;
  is_recurring: boolean;
  recurrence_pattern?: string;
  ai_suggested_priority?: number;
}

// File offline entity
export interface OfflineFile extends OfflineEntity {
  user_id: number;
  workspace_id?: number;
  file_path: string;
  file_name: string;
  file_extension?: string;
  file_size?: number;
  mime_type?: string;
  checksum: string;
  ai_category?: string;
  ai_description?: string;
  ai_tags?: string;
  importance_score?: number;
  user_category?: string;
  user_description?: string;
  is_favorite: boolean;
  is_archived: boolean;
  file_created_at?: number;
  file_modified_at?: number;
  last_accessed_at?: number;
  cached_data?: ArrayBuffer; // Cached file content
}

// Sync queue item
export interface SyncQueueItem {
  id: string;
  entityType: EntityType;
  entityId: string | number;
  action: 'create' | 'update' | 'delete';
  data: any;
  url: string;
  method: string;
  headers?: Record<string, string>;
  priority: number; // Higher = more priority
  retryCount: number;
  maxRetries: number;
  lastAttempt?: number;
  nextAttempt?: number;
  error?: string;
  createdAt: number;
}

// Conflict item
export interface ConflictItem {
  id: string;
  entityType: EntityType;
  entityId: string | number;
  localData: any;
  remoteData: any;
  conflictFields: string[];
  resolutionStrategy?: ConflictResolution;
  resolvedData?: any;
  createdAt: number;
  resolvedAt?: number;
}

// Search index item
export interface SearchIndexItem {
  id: string;
  entityType: EntityType;
  entityId: string | number;
  searchableText: string;
  keywords: string[];
  category: string;
  lastIndexed: number;
}

// Analytics event
export interface AnalyticsEvent {
  id: string;
  eventType: string;
  entityType?: EntityType;
  entityId?: string | number;
  data: any;
  timestamp: number;
  sessionId: string;
  userId?: number;
  isOffline: boolean;
}

/**
 * Main Offline Storage Manager
 */
export class OfflineStorage {
  private db: IDBDatabase | null = null;
  private encryption: AESGCMEncryption;
  private compression: DataCompression;
  private isInitialized = false;
  private readonly encryptionKey: string;

  constructor(encryptionKey?: string) {
    this.encryptionKey = encryptionKey || this.generateEncryptionKey();
    this.encryption = new AESGCMEncryption(this.encryptionKey);
    this.compression = new DataCompression();
  }

  /**
   * Initialize the offline storage database
   */
  async initialize(): Promise<void> {
    if (this.isInitialized) return;

    return new Promise((resolve, reject) => {
      const request = indexedDB.open(OFFLINE_DB_NAME, OFFLINE_DB_VERSION);

      request.onerror = () => {
        reject(new Error('Failed to open IndexedDB'));
      };

      request.onsuccess = (event) => {
        this.db = (event.target as IDBOpenDBRequest).result;
        this.isInitialized = true;
        console.log('✅ Offline storage initialized');
        resolve();
      };

      request.onupgradeneeded = (event) => {
        const db = (event.target as IDBOpenDBRequest).result;
        this.createObjectStores(db);
      };
    });
  }

  /**
   * Create IndexedDB object stores
   */
  private createObjectStores(db: IDBDatabase): void {
    // Workspaces store
    if (!db.objectStoreNames.contains('workspaces')) {
      const workspaceStore = db.createObjectStore('workspaces', { keyPath: 'id' });
      workspaceStore.createIndex('userId', 'user_id', { unique: false });
      workspaceStore.createIndex('syncStatus', 'syncStatus', { unique: false });
      workspaceStore.createIndex('lastModified', 'lastModified', { unique: false });
    }

    // Tasks store
    if (!db.objectStoreNames.contains('tasks')) {
      const taskStore = db.createObjectStore('tasks', { keyPath: 'id' });
      taskStore.createIndex('userId', 'user_id', { unique: false });
      taskStore.createIndex('workspaceId', 'workspace_id', { unique: false });
      taskStore.createIndex('status', 'status', { unique: false });
      taskStore.createIndex('priority', 'priority', { unique: false });
      taskStore.createIndex('syncStatus', 'syncStatus', { unique: false });
      taskStore.createIndex('dueDate', 'due_date', { unique: false });
    }

    // Files store
    if (!db.objectStoreNames.contains('files')) {
      const fileStore = db.createObjectStore('files', { keyPath: 'id' });
      fileStore.createIndex('userId', 'user_id', { unique: false });
      fileStore.createIndex('workspaceId', 'workspace_id', { unique: false });
      fileStore.createIndex('fileName', 'file_name', { unique: false });
      fileStore.createIndex('syncStatus', 'syncStatus', { unique: false });
      fileStore.createIndex('checksum', 'checksum', { unique: false });
    }

    // Sync queue store
    if (!db.objectStoreNames.contains('sync_queue')) {
      const syncStore = db.createObjectStore('sync_queue', { keyPath: 'id' });
      syncStore.createIndex('entityType', 'entityType', { unique: false });
      syncStore.createIndex('priority', 'priority', { unique: false });
      syncStore.createIndex('nextAttempt', 'nextAttempt', { unique: false });
      syncStore.createIndex('createdAt', 'createdAt', { unique: false });
    }

    // Conflicts store
    if (!db.objectStoreNames.contains('conflicts')) {
      const conflictStore = db.createObjectStore('conflicts', { keyPath: 'id' });
      conflictStore.createIndex('entityType', 'entityType', { unique: false });
      conflictStore.createIndex('entityId', 'entityId', { unique: false });
      conflictStore.createIndex('createdAt', 'createdAt', { unique: false });
    }

    // Search index store
    if (!db.objectStoreNames.contains('search_index')) {
      const searchStore = db.createObjectStore('search_index', { keyPath: 'id' });
      searchStore.createIndex('entityType', 'entityType', { unique: false });
      searchStore.createIndex('entityId', 'entityId', { unique: false });
      searchStore.createIndex('keywords', 'keywords', { unique: false, multiEntry: true });
    }

    // Analytics store
    if (!db.objectStoreNames.contains('analytics')) {
      const analyticsStore = db.createObjectStore('analytics', { keyPath: 'id' });
      analyticsStore.createIndex('eventType', 'eventType', { unique: false });
      analyticsStore.createIndex('timestamp', 'timestamp', { unique: false });
      analyticsStore.createIndex('userId', 'userId', { unique: false });
    }

    // Metadata store for app configuration
    if (!db.objectStoreNames.contains('metadata')) {
      db.createObjectStore('metadata', { keyPath: 'key' });
    }
  }

  /**
   * Store entity with encryption and compression
   */
  async store<T extends OfflineEntity>(
    entityType: EntityType,
    entity: T,
    options: { encrypt?: boolean; compress?: boolean } = {}
  ): Promise<void> {
    await this.ensureInitialized();

    const storeName = this.getStoreName(entityType);
    const transaction = this.db!.transaction([storeName], 'readwrite');
    const store = transaction.objectStore(storeName);

    // Add sync metadata
    const entityWithSync: T = {
      ...entity,
      syncStatus: entity.syncStatus || SyncStatus.PENDING_CREATE,
      version: entity.version || 1,
      lastModified: Date.now(),
      checksum: await this.calculateChecksum(entity)
    };

    // Apply compression if requested
    let dataToStore = entityWithSync;
    if (options.compress) {
      dataToStore = await this.compression.compress(entityWithSync) as T;
    }

    // Apply encryption if requested
    if (options.encrypt) {
      dataToStore = await this.encryption.encrypt(dataToStore) as T;
    }

    return new Promise((resolve, reject) => {
      const request = store.put(dataToStore);
      request.onsuccess = () => resolve();
      request.onerror = () => reject(request.error);
    });
  }

  /**
   * Retrieve entity with decryption and decompression
   */
  async get<T extends OfflineEntity>(
    entityType: EntityType,
    id: string | number,
    options: { decrypt?: boolean; decompress?: boolean } = {}
  ): Promise<T | null> {
    await this.ensureInitialized();

    const storeName = this.getStoreName(entityType);
    const transaction = this.db!.transaction([storeName], 'readonly');
    const store = transaction.objectStore(storeName);

    return new Promise((resolve, reject) => {
      const request = store.get(id);
      request.onsuccess = async () => {
        let result = request.result as T;
        if (!result) {
          resolve(null);
          return;
        }

        // Apply decryption if needed
        if (options.decrypt) {
          result = await this.encryption.decrypt(result) as T;
        }

        // Apply decompression if needed
        if (options.decompress) {
          result = await this.compression.decompress(result) as T;
        }

        resolve(result);
      };
      request.onerror = () => reject(request.error);
    });
  }

  /**
   * Get all entities of a type with filtering
   */
  async getAll<T extends OfflineEntity>(
    entityType: EntityType,
    filter?: {
      userId?: number;
      syncStatus?: SyncStatus;
      workspaceId?: number;
      includeDeleted?: boolean;
    },
    options: { decrypt?: boolean; decompress?: boolean } = {}
  ): Promise<T[]> {
    await this.ensureInitialized();

    const storeName = this.getStoreName(entityType);
    const transaction = this.db!.transaction([storeName], 'readonly');
    const store = transaction.objectStore(storeName);

    return new Promise((resolve, reject) => {
      const request = store.getAll();
      request.onsuccess = async () => {
        let results = request.result as T[];

        // Apply filters
        if (filter) {
          results = results.filter(item => {
            if (!filter.includeDeleted && item.isDeleted) return false;
            if (filter.userId && (item as any).user_id !== filter.userId) return false;
            if (filter.syncStatus && item.syncStatus !== filter.syncStatus) return false;
            if (filter.workspaceId && (item as any).workspace_id !== filter.workspaceId) return false;
            return true;
          });
        }

        // Apply decryption/decompression if needed
        if (options.decrypt || options.decompress) {
          const processedResults = await Promise.all(
            results.map(async (item) => {
              let processed = item;
              if (options.decrypt) {
                processed = await this.encryption.decrypt(processed) as T;
              }
              if (options.decompress) {
                processed = await this.compression.decompress(processed) as T;
              }
              return processed;
            })
          );
          resolve(processedResults);
        } else {
          resolve(results);
        }
      };
      request.onerror = () => reject(request.error);
    });
  }

  /**
   * Delete entity (soft delete)
   */
  async delete(entityType: EntityType, id: string | number): Promise<void> {
    const entity = await this.get(entityType, id);
    if (entity) {
      entity.isDeleted = true;
      entity.deletedAt = Date.now();
      entity.syncStatus = SyncStatus.PENDING_DELETE;
      entity.lastModified = Date.now();
      await this.store(entityType, entity);
    }
  }

  /**
   * Hard delete entity from storage
   */
  async hardDelete(entityType: EntityType, id: string | number): Promise<void> {
    await this.ensureInitialized();

    const storeName = this.getStoreName(entityType);
    const transaction = this.db!.transaction([storeName], 'readwrite');
    const store = transaction.objectStore(storeName);

    return new Promise((resolve, reject) => {
      const request = store.delete(id);
      request.onsuccess = () => resolve();
      request.onerror = () => reject(request.error);
    });
  }

  /**
   * Add item to sync queue
   */
  async addToSyncQueue(item: Omit<SyncQueueItem, 'id' | 'createdAt'>): Promise<void> {
    const queueItem: SyncQueueItem = {
      ...item,
      id: this.generateUUID(),
      createdAt: Date.now()
    };

    await this.store(EntityType.SYNC_QUEUE, queueItem as any);
  }

  /**
   * Get sync queue items
   */
  async getSyncQueue(): Promise<SyncQueueItem[]> {
    const items = await this.getAll<any>(EntityType.SYNC_QUEUE);
    return items.sort((a, b) => b.priority - a.priority || a.nextAttempt! - b.nextAttempt!);
  }

  /**
   * Clear processed sync queue items
   */
  async clearSyncQueue(processedIds: string[]): Promise<void> {
    await this.ensureInitialized();

    const transaction = this.db!.transaction(['sync_queue'], 'readwrite');
    const store = transaction.objectStore('sync_queue');

    for (const id of processedIds) {
      store.delete(id);
    }
  }

  /**
   * Store conflict for resolution
   */
  async storeConflict(conflict: Omit<ConflictItem, 'id' | 'createdAt'>): Promise<void> {
    const conflictItem: ConflictItem = {
      ...conflict,
      id: this.generateUUID(),
      createdAt: Date.now()
    };

    await this.store(EntityType.CONFLICT, conflictItem as any);
  }

  /**
   * Get all unresolved conflicts
   */
  async getConflicts(): Promise<ConflictItem[]> {
    const conflicts = await this.getAll<any>(EntityType.CONFLICT);
    return conflicts.filter(c => !c.resolvedAt);
  }

  /**
   * Resolve conflict
   */
  async resolveConflict(conflictId: string, resolvedData: any): Promise<void> {
    const conflict = await this.get<any>(EntityType.CONFLICT, conflictId);
    if (conflict) {
      conflict.resolvedData = resolvedData;
      conflict.resolvedAt = Date.now();
      await this.store(EntityType.CONFLICT, conflict);

      // Update the original entity
      await this.store(conflict.entityType, {
        ...resolvedData,
        syncStatus: SyncStatus.PENDING_UPDATE
      });
    }
  }

  /**
   * Update search index
   */
  async updateSearchIndex(entityType: EntityType, entityId: string | number, searchableText: string): Promise<void> {
    const keywords = this.extractKeywords(searchableText);
    const indexItem: SearchIndexItem = {
      id: `${entityType}_${entityId}`,
      entityType,
      entityId,
      searchableText: searchableText.toLowerCase(),
      keywords,
      category: entityType,
      lastIndexed: Date.now()
    };

    await this.store(EntityType.SEARCH_INDEX, indexItem as any);
  }

  /**
   * Search entities
   */
  async search(query: string, entityTypes?: EntityType[]): Promise<SearchIndexItem[]> {
    const searchIndex = await this.getAll<any>(EntityType.SEARCH_INDEX);
    const queryLower = query.toLowerCase();
    const queryWords = queryLower.split(/\s+/).filter(word => word.length > 0);

    return searchIndex.filter(item => {
      if (entityTypes && !entityTypes.includes(item.entityType)) return false;

      // Check if query matches searchable text or keywords
      const textMatch = item.searchableText.includes(queryLower);
      const keywordMatch = queryWords.some(word => 
        item.keywords.some(keyword => keyword.includes(word))
      );

      return textMatch || keywordMatch;
    });
  }

  /**
   * Store analytics event
   */
  async storeAnalyticsEvent(event: Omit<AnalyticsEvent, 'id'>): Promise<void> {
    const analyticsEvent: AnalyticsEvent = {
      ...event,
      id: this.generateUUID()
    };

    await this.store(EntityType.ANALYTICS, analyticsEvent as any);
  }

  /**
   * Get analytics events
   */
  async getAnalyticsEvents(filter?: {
    eventType?: string;
    fromDate?: number;
    toDate?: number;
    userId?: number;
  }): Promise<AnalyticsEvent[]> {
    const events = await this.getAll<any>(EntityType.ANALYTICS);
    
    if (!filter) return events;

    return events.filter(event => {
      if (filter.eventType && event.eventType !== filter.eventType) return false;
      if (filter.fromDate && event.timestamp < filter.fromDate) return false;
      if (filter.toDate && event.timestamp > filter.toDate) return false;
      if (filter.userId && event.userId !== filter.userId) return false;
      return true;
    });
  }

  /**
   * Get storage statistics
   */
  async getStorageStats(): Promise<{
    totalSize: number;
    entityCounts: Record<EntityType, number>;
    syncQueueSize: number;
    conflictCount: number;
    oldestUnsyncedItem: number | null;
  }> {
    const stats = {
      totalSize: 0,
      entityCounts: {} as Record<EntityType, number>,
      syncQueueSize: 0,
      conflictCount: 0,
      oldestUnsyncedItem: null as number | null
    };

    for (const entityType of Object.values(EntityType)) {
      const items = await this.getAll(entityType);
      stats.entityCounts[entityType] = items.length;

      if (entityType === EntityType.SYNC_QUEUE) {
        stats.syncQueueSize = items.length;
      } else if (entityType === EntityType.CONFLICT) {
        stats.conflictCount = items.filter(item => !(item as any).resolvedAt).length;
      }

      // Find oldest unsynced item
      const unsyncedItems = items.filter(item => item.syncStatus !== SyncStatus.SYNCED);
      if (unsyncedItems.length > 0) {
        const oldest = Math.min(...unsyncedItems.map(item => item.lastModified));
        if (!stats.oldestUnsyncedItem || oldest < stats.oldestUnsyncedItem) {
          stats.oldestUnsyncedItem = oldest;
        }
      }
    }

    // Estimate storage size (rough calculation)
    if ('storage' in navigator && 'estimate' in navigator.storage) {
      try {
        const estimate = await navigator.storage.estimate();
        stats.totalSize = estimate.usage || 0;
      } catch (error) {
        console.warn('Could not estimate storage usage:', error);
      }
    }

    return stats;
  }

  /**
   * Clean up old data
   */
  async cleanup(options: {
    deleteOlderThan?: number; // timestamp
    maxAnalyticsEvents?: number;
    maxResolvedConflicts?: number;
  } = {}): Promise<void> {
    const defaultOlderThan = Date.now() - (30 * 24 * 60 * 60 * 1000); // 30 days
    const olderThan = options.deleteOlderThan || defaultOlderThan;

    // Clean up old analytics events
    if (options.maxAnalyticsEvents) {
      const events = await this.getAll<any>(EntityType.ANALYTICS);
      events.sort((a, b) => b.timestamp - a.timestamp);
      
      if (events.length > options.maxAnalyticsEvents) {
        const toDelete = events.slice(options.maxAnalyticsEvents);
        for (const event of toDelete) {
          await this.hardDelete(EntityType.ANALYTICS, event.id);
        }
      }
    }

    // Clean up resolved conflicts
    if (options.maxResolvedConflicts) {
      const conflicts = await this.getAll<any>(EntityType.CONFLICT);
      const resolved = conflicts.filter(c => c.resolvedAt).sort((a, b) => b.resolvedAt - a.resolvedAt);
      
      if (resolved.length > options.maxResolvedConflicts) {
        const toDelete = resolved.slice(options.maxResolvedConflicts);
        for (const conflict of toDelete) {
          await this.hardDelete(EntityType.CONFLICT, conflict.id);
        }
      }
    }

    // Clean up old deleted entities
    for (const entityType of [EntityType.WORKSPACE, EntityType.TASK, EntityType.FILE]) {
      const entities = await this.getAll(entityType, { includeDeleted: true });
      const oldDeleted = entities.filter(e => e.isDeleted && e.deletedAt && e.deletedAt < olderThan);
      
      for (const entity of oldDeleted) {
        await this.hardDelete(entityType, entity.id);
      }
    }
  }

  /**
   * Export data for backup
   */
  async exportData(): Promise<any> {
    const data: any = {};

    for (const entityType of Object.values(EntityType)) {
      data[entityType] = await this.getAll(entityType, { includeDeleted: true });
    }

    return {
      version: OFFLINE_DB_VERSION,
      exportedAt: Date.now(),
      data
    };
  }

  /**
   * Import data from backup
   */
  async importData(backupData: any): Promise<void> {
    if (backupData.version !== OFFLINE_DB_VERSION) {
      throw new Error('Incompatible backup version');
    }

    for (const [entityType, entities] of Object.entries(backupData.data)) {
      for (const entity of entities as any[]) {
        await this.store(entityType as EntityType, entity);
      }
    }
  }

  // Utility methods

  private async ensureInitialized(): Promise<void> {
    if (!this.isInitialized) {
      await this.initialize();
    }
  }

  private getStoreName(entityType: EntityType): string {
    switch (entityType) {
      case EntityType.WORKSPACE: return 'workspaces';
      case EntityType.TASK: return 'tasks';
      case EntityType.FILE: return 'files';
      case EntityType.SYNC_QUEUE: return 'sync_queue';
      case EntityType.CONFLICT: return 'conflicts';
      case EntityType.SEARCH_INDEX: return 'search_index';
      case EntityType.ANALYTICS: return 'analytics';
      case EntityType.METADATA: return 'metadata';
      default: throw new Error(`Unknown entity type: ${entityType}`);
    }
  }

  private generateUUID(): string {
    return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function(c) {
      const r = Math.random() * 16 | 0;
      const v = c === 'x' ? r : (r & 0x3 | 0x8);
      return v.toString(16);
    });
  }

  private generateEncryptionKey(): string {
    // In production, this should be derived from user credentials or stored securely
    return crypto.randomUUID();
  }

  private async calculateChecksum(data: any): Promise<string> {
    const jsonString = JSON.stringify(data, Object.keys(data).sort());
    const encoder = new TextEncoder();
    const dataBuffer = encoder.encode(jsonString);
    const hashBuffer = await crypto.subtle.digest('SHA-256', dataBuffer);
    const hashArray = Array.from(new Uint8Array(hashBuffer));
    return hashArray.map(b => b.toString(16).padStart(2, '0')).join('');
  }

  private extractKeywords(text: string): string[] {
    return text.toLowerCase()
      .replace(/[^\w\s]/g, ' ')
      .split(/\s+/)
      .filter(word => word.length > 2)
      .slice(0, 20); // Limit to 20 keywords
  }
}

// Singleton instance
export const offlineStorage = new OfflineStorage();