/**
 * SQLite-based Offline Storage for Electron App
 * Provides desktop-specific offline storage with better performance and larger capacity
 */

import { Database } from 'sqlite3';
import { promisify } from 'util';
import { join } from 'path';
import { app } from 'electron';
import { AESGCMEncryption } from './encryption/AESGCMEncryption';
import { DataCompression } from './compression/DataCompression';
import {
  EntityType,
  SyncStatus,
  ConflictResolution,
  OfflineEntity,
  OfflineWorkspace,
  OfflineTask,
  OfflineFile,
  SyncQueueItem,
  ConflictItem,
  SearchIndexItem,
  AnalyticsEvent
} from './OfflineStorage';

// SQLite specific interfaces
interface SQLiteRow {
  [key: string]: any;
}

interface SQLiteRunResult {
  lastID: number;
  changes: number;
}

/**
 * Electron-specific offline storage using SQLite
 */
export class ElectronOfflineStorage {
  private db: Database | null = null;
  private encryption: AESGCMEncryption;
  private compression: DataCompression;
  private isInitialized = false;
  private readonly dbPath: string;
  private readonly encryptionKey: string;

  // Promisified database methods
  private dbRun: ((sql: string, params?: any[]) => Promise<SQLiteRunResult>) | null = null;
  private dbGet: ((sql: string, params?: any[]) => Promise<SQLiteRow | undefined>) | null = null;
  private dbAll: ((sql: string, params?: any[]) => Promise<SQLiteRow[]>) | null = null;

  constructor(encryptionKey?: string) {
    this.encryptionKey = encryptionKey || this.generateEncryptionKey();
    this.encryption = new AESGCMEncryption(this.encryptionKey);
    this.compression = new DataCompression();
    
    // Set database path in user data directory
    const userDataPath = app ? app.getPath('userData') : './data';
    this.dbPath = join(userDataPath, 'bluebirdHub-offline.db');
  }

  /**
   * Initialize SQLite database
   */
  async initialize(): Promise<void> {
    if (this.isInitialized) return;

    return new Promise((resolve, reject) => {
      this.db = new Database(this.dbPath, (err) => {
        if (err) {
          reject(new Error(`Failed to open SQLite database: ${err.message}`));
          return;
        }

        // Promisify database methods
        this.dbRun = promisify(this.db!.run.bind(this.db));
        this.dbGet = promisify(this.db!.get.bind(this.db));
        this.dbAll = promisify(this.db!.all.bind(this.db));

        this.createTables()
          .then(() => {
            this.isInitialized = true;
            console.log('✅ SQLite offline storage initialized');
            resolve();
          })
          .catch(reject);
      });
    });
  }

  /**
   * Create database tables
   */
  private async createTables(): Promise<void> {
    const tables = [
      // Workspaces table
      `CREATE TABLE IF NOT EXISTS workspaces (
        id TEXT PRIMARY KEY,
        user_id INTEGER NOT NULL,
        name TEXT NOT NULL,
        description TEXT,
        theme TEXT DEFAULT 'default',
        is_active BOOLEAN DEFAULT 1,
        is_default BOOLEAN DEFAULT 0,
        icon TEXT,
        color TEXT,
        layout_config TEXT,
        ambient_sound TEXT,
        last_accessed_at INTEGER,
        sync_status TEXT DEFAULT 'pending_create',
        version INTEGER DEFAULT 1,
        last_modified INTEGER NOT NULL,
        created_at INTEGER NOT NULL,
        deleted_at INTEGER,
        is_deleted BOOLEAN DEFAULT 0,
        etag TEXT,
        checksum TEXT,
        encrypted_data TEXT,
        compressed_data TEXT
      )`,

      // Tasks table
      `CREATE TABLE IF NOT EXISTS tasks (
        id TEXT PRIMARY KEY,
        user_id INTEGER NOT NULL,
        workspace_id TEXT,
        project_id TEXT,
        title TEXT NOT NULL,
        description TEXT,
        status TEXT DEFAULT 'PENDING',
        priority TEXT DEFAULT 'MEDIUM',
        due_date INTEGER,
        completed_at INTEGER,
        estimated_hours INTEGER,
        actual_hours INTEGER,
        is_recurring BOOLEAN DEFAULT 0,
        recurrence_pattern TEXT,
        ai_suggested_priority INTEGER,
        sync_status TEXT DEFAULT 'pending_create',
        version INTEGER DEFAULT 1,
        last_modified INTEGER NOT NULL,
        created_at INTEGER NOT NULL,
        deleted_at INTEGER,
        is_deleted BOOLEAN DEFAULT 0,
        etag TEXT,
        checksum TEXT,
        encrypted_data TEXT,
        compressed_data TEXT,
        FOREIGN KEY (workspace_id) REFERENCES workspaces(id)
      )`,

      // Files table
      `CREATE TABLE IF NOT EXISTS files (
        id TEXT PRIMARY KEY,
        user_id INTEGER NOT NULL,
        workspace_id TEXT,
        file_path TEXT NOT NULL,
        file_name TEXT NOT NULL,
        file_extension TEXT,
        file_size INTEGER,
        mime_type TEXT,
        checksum TEXT NOT NULL,
        ai_category TEXT,
        ai_description TEXT,
        ai_tags TEXT,
        importance_score INTEGER,
        user_category TEXT,
        user_description TEXT,
        is_favorite BOOLEAN DEFAULT 0,
        is_archived BOOLEAN DEFAULT 0,
        file_created_at INTEGER,
        file_modified_at INTEGER,
        last_accessed_at INTEGER,
        cached_data BLOB,
        sync_status TEXT DEFAULT 'pending_create',
        version INTEGER DEFAULT 1,
        last_modified INTEGER NOT NULL,
        created_at INTEGER NOT NULL,
        deleted_at INTEGER,
        is_deleted BOOLEAN DEFAULT 0,
        etag TEXT,
        encrypted_data TEXT,
        compressed_data TEXT,
        FOREIGN KEY (workspace_id) REFERENCES workspaces(id)
      )`,

      // Sync queue table
      `CREATE TABLE IF NOT EXISTS sync_queue (
        id TEXT PRIMARY KEY,
        entity_type TEXT NOT NULL,
        entity_id TEXT NOT NULL,
        action TEXT NOT NULL,
        data TEXT NOT NULL,
        url TEXT NOT NULL,
        method TEXT NOT NULL,
        headers TEXT,
        priority INTEGER DEFAULT 0,
        retry_count INTEGER DEFAULT 0,
        max_retries INTEGER DEFAULT 3,
        last_attempt INTEGER,
        next_attempt INTEGER,
        error TEXT,
        created_at INTEGER NOT NULL
      )`,

      // Conflicts table
      `CREATE TABLE IF NOT EXISTS conflicts (
        id TEXT PRIMARY KEY,
        entity_type TEXT NOT NULL,
        entity_id TEXT NOT NULL,
        local_data TEXT NOT NULL,
        remote_data TEXT NOT NULL,
        conflict_fields TEXT NOT NULL,
        resolution_strategy TEXT,
        resolved_data TEXT,
        created_at INTEGER NOT NULL,
        resolved_at INTEGER
      )`,

      // Search index table
      `CREATE TABLE IF NOT EXISTS search_index (
        id TEXT PRIMARY KEY,
        entity_type TEXT NOT NULL,
        entity_id TEXT NOT NULL,
        searchable_text TEXT NOT NULL,
        keywords TEXT NOT NULL,
        category TEXT NOT NULL,
        last_indexed INTEGER NOT NULL
      )`,

      // Analytics table
      `CREATE TABLE IF NOT EXISTS analytics (
        id TEXT PRIMARY KEY,
        event_type TEXT NOT NULL,
        entity_type TEXT,
        entity_id TEXT,
        data TEXT NOT NULL,
        timestamp INTEGER NOT NULL,
        session_id TEXT NOT NULL,
        user_id INTEGER,
        is_offline BOOLEAN DEFAULT 1
      )`,

      // Metadata table
      `CREATE TABLE IF NOT EXISTS metadata (
        key TEXT PRIMARY KEY,
        value TEXT NOT NULL,
        updated_at INTEGER NOT NULL
      )`
    ];

    // Create tables
    for (const sql of tables) {
      await this.dbRun!(sql);
    }

    // Create indexes for better performance
    const indexes = [
      'CREATE INDEX IF NOT EXISTS idx_workspaces_user_id ON workspaces(user_id)',
      'CREATE INDEX IF NOT EXISTS idx_workspaces_sync_status ON workspaces(sync_status)',
      'CREATE INDEX IF NOT EXISTS idx_tasks_user_id ON tasks(user_id)',
      'CREATE INDEX IF NOT EXISTS idx_tasks_workspace_id ON tasks(workspace_id)',
      'CREATE INDEX IF NOT EXISTS idx_tasks_status ON tasks(status)',
      'CREATE INDEX IF NOT EXISTS idx_tasks_priority ON tasks(priority)',
      'CREATE INDEX IF NOT EXISTS idx_tasks_due_date ON tasks(due_date)',
      'CREATE INDEX IF NOT EXISTS idx_files_user_id ON files(user_id)',
      'CREATE INDEX IF NOT EXISTS idx_files_workspace_id ON files(workspace_id)',
      'CREATE INDEX IF NOT EXISTS idx_files_checksum ON files(checksum)',
      'CREATE INDEX IF NOT EXISTS idx_sync_queue_priority ON sync_queue(priority DESC)',
      'CREATE INDEX IF NOT EXISTS idx_sync_queue_next_attempt ON sync_queue(next_attempt)',
      'CREATE INDEX IF NOT EXISTS idx_search_index_entity_type ON search_index(entity_type)',
      'CREATE INDEX IF NOT EXISTS idx_analytics_event_type ON analytics(event_type)',
      'CREATE INDEX IF NOT EXISTS idx_analytics_timestamp ON analytics(timestamp)'
    ];

    for (const sql of indexes) {
      await this.dbRun!(sql);
    }
  }

  /**
   * Store entity with optional encryption and compression
   */
  async store<T extends OfflineEntity>(
    entityType: EntityType,
    entity: T,
    options: { encrypt?: boolean; compress?: boolean } = {}
  ): Promise<void> {
    await this.ensureInitialized();

    const table = this.getTableName(entityType);
    const now = Date.now();

    // Prepare entity with sync metadata
    const entityWithSync: T = {
      ...entity,
      syncStatus: entity.syncStatus || SyncStatus.PENDING_CREATE,
      version: entity.version || 1,
      lastModified: now,
      checksum: await this.calculateChecksum(entity)
    };

    // Handle encryption
    let encryptedData = null;
    if (options.encrypt) {
      encryptedData = JSON.stringify(await this.encryption.encrypt(entityWithSync));
    }

    // Handle compression
    let compressedData = null;
    if (options.compress) {
      compressedData = JSON.stringify(await this.compression.compress(entityWithSync));
    }

    // Prepare SQL based on entity type
    const columns = this.getEntityColumns(entityType);
    const values = this.getEntityValues(entityWithSync, columns);

    // Add encryption/compression data if applicable
    if (encryptedData) {
      columns.push('encrypted_data');
      values.push(encryptedData);
    }
    if (compressedData) {
      columns.push('compressed_data');
      values.push(compressedData);
    }

    const placeholders = columns.map(() => '?').join(', ');
    const sql = `INSERT OR REPLACE INTO ${table} (${columns.join(', ')}) VALUES (${placeholders})`;

    await this.dbRun!(sql, values);
  }

  /**
   * Retrieve entity with optional decryption and decompression
   */
  async get<T extends OfflineEntity>(
    entityType: EntityType,
    id: string | number,
    options: { decrypt?: boolean; decompress?: boolean } = {}
  ): Promise<T | null> {
    await this.ensureInitialized();

    const table = this.getTableName(entityType);
    const row = await this.dbGet!(`SELECT * FROM ${table} WHERE id = ?`, [id]);

    if (!row) return null;

    return this.processRow<T>(row, options);
  }

  /**
   * Get all entities with filtering
   */
  async getAll<T extends OfflineEntity>(
    entityType: EntityType,
    filter?: {
      userId?: number;
      syncStatus?: SyncStatus;
      workspaceId?: string;
      includeDeleted?: boolean;
    },
    options: { decrypt?: boolean; decompress?: boolean } = {}
  ): Promise<T[]> {
    await this.ensureInitialized();

    const table = this.getTableName(entityType);
    let sql = `SELECT * FROM ${table}`;
    const params: any[] = [];
    const conditions: string[] = [];

    // Apply filters
    if (filter) {
      if (!filter.includeDeleted) {
        conditions.push('is_deleted = 0');
      }

      if (filter.userId !== undefined) {
        conditions.push('user_id = ?');
        params.push(filter.userId);
      }

      if (filter.syncStatus) {
        conditions.push('sync_status = ?');
        params.push(filter.syncStatus);
      }

      if (filter.workspaceId) {
        conditions.push('workspace_id = ?');
        params.push(filter.workspaceId);
      }
    }

    if (conditions.length > 0) {
      sql += ' WHERE ' + conditions.join(' AND ');
    }

    sql += ' ORDER BY last_modified DESC';

    const rows = await this.dbAll!(sql, params);
    const results: T[] = [];

    for (const row of rows) {
      const processed = await this.processRow<T>(row, options);
      if (processed) results.push(processed);
    }

    return results;
  }

  /**
   * Soft delete entity
   */
  async delete(entityType: EntityType, id: string | number): Promise<void> {
    await this.ensureInitialized();

    const table = this.getTableName(entityType);
    const now = Date.now();

    await this.dbRun!(
      `UPDATE ${table} SET is_deleted = 1, deleted_at = ?, sync_status = 'pending_delete', last_modified = ? WHERE id = ?`,
      [now, now, id]
    );
  }

  /**
   * Hard delete entity
   */
  async hardDelete(entityType: EntityType, id: string | number): Promise<void> {
    await this.ensureInitialized();

    const table = this.getTableName(entityType);
    await this.dbRun!(`DELETE FROM ${table} WHERE id = ?`, [id]);
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

    await this.dbRun!(
      `INSERT INTO sync_queue (
        id, entity_type, entity_id, action, data, url, method, headers,
        priority, retry_count, max_retries, last_attempt, next_attempt, error, created_at
      ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)`,
      [
        queueItem.id,
        queueItem.entityType,
        queueItem.entityId,
        queueItem.action,
        JSON.stringify(queueItem.data),
        queueItem.url,
        queueItem.method,
        JSON.stringify(queueItem.headers || {}),
        queueItem.priority,
        queueItem.retryCount,
        queueItem.maxRetries,
        queueItem.lastAttempt || null,
        queueItem.nextAttempt || null,
        queueItem.error || null,
        queueItem.createdAt
      ]
    );
  }

  /**
   * Get sync queue items
   */
  async getSyncQueue(): Promise<SyncQueueItem[]> {
    const rows = await this.dbAll!(
      'SELECT * FROM sync_queue ORDER BY priority DESC, next_attempt ASC NULLS FIRST'
    );

    return rows.map(row => ({
      id: row.id,
      entityType: row.entity_type as EntityType,
      entityId: row.entity_id,
      action: row.action as 'create' | 'update' | 'delete',
      data: JSON.parse(row.data),
      url: row.url,
      method: row.method,
      headers: JSON.parse(row.headers || '{}'),
      priority: row.priority,
      retryCount: row.retry_count,
      maxRetries: row.max_retries,
      lastAttempt: row.last_attempt,
      nextAttempt: row.next_attempt,
      error: row.error,
      createdAt: row.created_at
    }));
  }

  /**
   * Clear processed sync queue items
   */
  async clearSyncQueue(processedIds: string[]): Promise<void> {
    if (processedIds.length === 0) return;

    const placeholders = processedIds.map(() => '?').join(', ');
    await this.dbRun!(`DELETE FROM sync_queue WHERE id IN (${placeholders})`, processedIds);
  }

  /**
   * Store conflict
   */
  async storeConflict(conflict: Omit<ConflictItem, 'id' | 'createdAt'>): Promise<void> {
    const conflictItem: ConflictItem = {
      ...conflict,
      id: this.generateUUID(),
      createdAt: Date.now()
    };

    await this.dbRun!(
      `INSERT INTO conflicts (
        id, entity_type, entity_id, local_data, remote_data, conflict_fields,
        resolution_strategy, resolved_data, created_at, resolved_at
      ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)`,
      [
        conflictItem.id,
        conflictItem.entityType,
        conflictItem.entityId,
        JSON.stringify(conflictItem.localData),
        JSON.stringify(conflictItem.remoteData),
        JSON.stringify(conflictItem.conflictFields),
        conflictItem.resolutionStrategy || null,
        conflictItem.resolvedData ? JSON.stringify(conflictItem.resolvedData) : null,
        conflictItem.createdAt,
        conflictItem.resolvedAt || null
      ]
    );
  }

  /**
   * Get unresolved conflicts
   */
  async getConflicts(): Promise<ConflictItem[]> {
    const rows = await this.dbAll!('SELECT * FROM conflicts WHERE resolved_at IS NULL ORDER BY created_at');

    return rows.map(row => ({
      id: row.id,
      entityType: row.entity_type as EntityType,
      entityId: row.entity_id,
      localData: JSON.parse(row.local_data),
      remoteData: JSON.parse(row.remote_data),
      conflictFields: JSON.parse(row.conflict_fields),
      resolutionStrategy: row.resolution_strategy as ConflictResolution,
      resolvedData: row.resolved_data ? JSON.parse(row.resolved_data) : undefined,
      createdAt: row.created_at,
      resolvedAt: row.resolved_at
    }));
  }

  /**
   * Resolve conflict
   */
  async resolveConflict(conflictId: string, resolvedData: any): Promise<void> {
    const now = Date.now();

    await this.dbRun!(
      'UPDATE conflicts SET resolved_data = ?, resolved_at = ? WHERE id = ?',
      [JSON.stringify(resolvedData), now, conflictId]
    );

    // Get the conflict to update the original entity
    const conflict = await this.dbGet!('SELECT * FROM conflicts WHERE id = ?', [conflictId]);
    if (conflict) {
      await this.store(conflict.entity_type as EntityType, {
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

    await this.dbRun!(
      `INSERT OR REPLACE INTO search_index (
        id, entity_type, entity_id, searchable_text, keywords, category, last_indexed
      ) VALUES (?, ?, ?, ?, ?, ?, ?)`,
      [
        indexItem.id,
        indexItem.entityType,
        indexItem.entityId,
        indexItem.searchableText,
        JSON.stringify(indexItem.keywords),
        indexItem.category,
        indexItem.lastIndexed
      ]
    );
  }

  /**
   * Search entities
   */
  async search(query: string, entityTypes?: EntityType[]): Promise<SearchIndexItem[]> {
    const queryLower = query.toLowerCase();
    let sql = `
      SELECT * FROM search_index 
      WHERE searchable_text LIKE ? OR keywords LIKE ?
    `;
    const params = [`%${queryLower}%`, `%${queryLower}%`];

    if (entityTypes && entityTypes.length > 0) {
      const placeholders = entityTypes.map(() => '?').join(', ');
      sql += ` AND entity_type IN (${placeholders})`;
      params.push(...entityTypes);
    }

    sql += ' ORDER BY last_indexed DESC';

    const rows = await this.dbAll!(sql, params);

    return rows.map(row => ({
      id: row.id,
      entityType: row.entity_type as EntityType,
      entityId: row.entity_id,
      searchableText: row.searchable_text,
      keywords: JSON.parse(row.keywords),
      category: row.category,
      lastIndexed: row.last_indexed
    }));
  }

  /**
   * Store analytics event
   */
  async storeAnalyticsEvent(event: Omit<AnalyticsEvent, 'id'>): Promise<void> {
    const analyticsEvent: AnalyticsEvent = {
      ...event,
      id: this.generateUUID()
    };

    await this.dbRun!(
      `INSERT INTO analytics (
        id, event_type, entity_type, entity_id, data, timestamp, session_id, user_id, is_offline
      ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)`,
      [
        analyticsEvent.id,
        analyticsEvent.eventType,
        analyticsEvent.entityType || null,
        analyticsEvent.entityId || null,
        JSON.stringify(analyticsEvent.data),
        analyticsEvent.timestamp,
        analyticsEvent.sessionId,
        analyticsEvent.userId || null,
        analyticsEvent.isOffline ? 1 : 0
      ]
    );
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
    let sql = 'SELECT * FROM analytics';
    const params: any[] = [];
    const conditions: string[] = [];

    if (filter) {
      if (filter.eventType) {
        conditions.push('event_type = ?');
        params.push(filter.eventType);
      }

      if (filter.fromDate) {
        conditions.push('timestamp >= ?');
        params.push(filter.fromDate);
      }

      if (filter.toDate) {
        conditions.push('timestamp <= ?');
        params.push(filter.toDate);
      }

      if (filter.userId) {
        conditions.push('user_id = ?');
        params.push(filter.userId);
      }
    }

    if (conditions.length > 0) {
      sql += ' WHERE ' + conditions.join(' AND ');
    }

    sql += ' ORDER BY timestamp DESC';

    const rows = await this.dbAll!(sql, params);

    return rows.map(row => ({
      id: row.id,
      eventType: row.event_type,
      entityType: row.entity_type as EntityType,
      entityId: row.entity_id,
      data: JSON.parse(row.data),
      timestamp: row.timestamp,
      sessionId: row.session_id,
      userId: row.user_id,
      isOffline: row.is_offline === 1
    }));
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

    // Get entity counts
    const entityTables = {
      [EntityType.WORKSPACE]: 'workspaces',
      [EntityType.TASK]: 'tasks', 
      [EntityType.FILE]: 'files'
    };

    for (const [entityType, table] of Object.entries(entityTables)) {
      const result = await this.dbGet!(`SELECT COUNT(*) as count FROM ${table}`);
      stats.entityCounts[entityType as EntityType] = result?.count || 0;
    }

    // Get sync queue size
    const queueResult = await this.dbGet!('SELECT COUNT(*) as count FROM sync_queue');
    stats.syncQueueSize = queueResult?.count || 0;

    // Get conflict count
    const conflictResult = await this.dbGet!('SELECT COUNT(*) as count FROM conflicts WHERE resolved_at IS NULL');
    stats.conflictCount = conflictResult?.count || 0;

    // Find oldest unsynced item
    const oldestResult = await this.dbGet!(`
      SELECT MIN(last_modified) as oldest FROM (
        SELECT last_modified FROM workspaces WHERE sync_status != 'synced'
        UNION ALL
        SELECT last_modified FROM tasks WHERE sync_status != 'synced'
        UNION ALL
        SELECT last_modified FROM files WHERE sync_status != 'synced'
      )
    `);
    stats.oldestUnsyncedItem = oldestResult?.oldest || null;

    return stats;
  }

  /**
   * Clean up old data
   */
  async cleanup(options: {
    deleteOlderThan?: number;
    maxAnalyticsEvents?: number;
    maxResolvedConflicts?: number;
  } = {}): Promise<void> {
    const defaultOlderThan = Date.now() - (30 * 24 * 60 * 60 * 1000); // 30 days
    const olderThan = options.deleteOlderThan || defaultOlderThan;

    // Clean up old analytics events
    if (options.maxAnalyticsEvents) {
      await this.dbRun!(
        'DELETE FROM analytics WHERE id NOT IN (SELECT id FROM analytics ORDER BY timestamp DESC LIMIT ?)',
        [options.maxAnalyticsEvents]
      );
    }

    // Clean up resolved conflicts
    if (options.maxResolvedConflicts) {
      await this.dbRun!(
        'DELETE FROM conflicts WHERE resolved_at IS NOT NULL AND id NOT IN (SELECT id FROM conflicts WHERE resolved_at IS NOT NULL ORDER BY resolved_at DESC LIMIT ?)',
        [options.maxResolvedConflicts]
      );
    }

    // Clean up old deleted entities
    const tables = ['workspaces', 'tasks', 'files'];
    for (const table of tables) {
      await this.dbRun!(
        `DELETE FROM ${table} WHERE is_deleted = 1 AND deleted_at < ?`,
        [olderThan]
      );
    }
  }

  /**
   * Close database connection
   */
  async close(): Promise<void> {
    if (this.db) {
      return new Promise((resolve, reject) => {
        this.db!.close((err) => {
          if (err) {
            reject(err);
          } else {
            this.db = null;
            this.isInitialized = false;
            resolve();
          }
        });
      });
    }
  }

  // Private utility methods

  private async ensureInitialized(): Promise<void> {
    if (!this.isInitialized) {
      await this.initialize();
    }
  }

  private getTableName(entityType: EntityType): string {
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

  private getEntityColumns(entityType: EntityType): string[] {
    const baseColumns = ['id', 'sync_status', 'version', 'last_modified', 'created_at', 'deleted_at', 'is_deleted', 'etag', 'checksum'];
    
    switch (entityType) {
      case EntityType.WORKSPACE:
        return [...baseColumns, 'user_id', 'name', 'description', 'theme', 'is_active', 'is_default', 'icon', 'color', 'layout_config', 'ambient_sound', 'last_accessed_at'];
      case EntityType.TASK:
        return [...baseColumns, 'user_id', 'workspace_id', 'project_id', 'title', 'description', 'status', 'priority', 'due_date', 'completed_at', 'estimated_hours', 'actual_hours', 'is_recurring', 'recurrence_pattern', 'ai_suggested_priority'];
      case EntityType.FILE:
        return [...baseColumns, 'user_id', 'workspace_id', 'file_path', 'file_name', 'file_extension', 'file_size', 'mime_type', 'checksum', 'ai_category', 'ai_description', 'ai_tags', 'importance_score', 'user_category', 'user_description', 'is_favorite', 'is_archived', 'file_created_at', 'file_modified_at', 'last_accessed_at', 'cached_data'];
      default:
        return baseColumns;
    }
  }

  private getEntityValues(entity: any, columns: string[]): any[] {
    return columns.map(column => {
      const value = entity[this.camelCase(column)];
      if (value === undefined || value === null) return null;
      if (typeof value === 'object') return JSON.stringify(value);
      return value;
    });
  }

  private camelCase(str: string): string {
    return str.replace(/_([a-z])/g, (match, letter) => letter.toUpperCase());
  }

  private async processRow<T>(row: SQLiteRow, options: { decrypt?: boolean; decompress?: boolean }): Promise<T | null> {
    try {
      let entity: any = {};

      // Check for encrypted data
      if (options.decrypt && row.encrypted_data) {
        const encryptedData = JSON.parse(row.encrypted_data);
        entity = await this.encryption.decrypt(encryptedData);
      }
      // Check for compressed data
      else if (options.decompress && row.compressed_data) {
        const compressedData = JSON.parse(row.compressed_data);
        entity = await this.compression.decompress(compressedData);
      }
      // Use regular row data
      else {
        // Convert snake_case to camelCase
        for (const [key, value] of Object.entries(row)) {
          if (key.endsWith('_data')) continue; // Skip encrypted/compressed data fields
          const camelKey = this.camelCase(key);
          
          // Parse JSON fields
          if (typeof value === 'string' && (key.includes('config') || key.includes('headers') || key.includes('data'))) {
            try {
              entity[camelKey] = JSON.parse(value);
            } catch {
              entity[camelKey] = value;
            }
          } else {
            entity[camelKey] = value;
          }
        }
      }

      return entity as T;
    } catch (error) {
      console.error('Failed to process row:', error);
      return null;
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
    // In production, this should be derived from user credentials
    return require('crypto').randomBytes(32).toString('hex');
  }

  private async calculateChecksum(data: any): Promise<string> {
    const jsonString = JSON.stringify(data, Object.keys(data).sort());
    const crypto = require('crypto');
    return crypto.createHash('sha256').update(jsonString).digest('hex');
  }

  private extractKeywords(text: string): string[] {
    return text.toLowerCase()
      .replace(/[^\w\s]/g, ' ')
      .split(/\s+/)
      .filter(word => word.length > 2)
      .slice(0, 20);
  }
}

// Singleton instance for Electron
export const electronOfflineStorage = new ElectronOfflineStorage();