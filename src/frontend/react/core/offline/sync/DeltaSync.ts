/**
 * Delta Sync System for Efficient Data Synchronization
 * Provides efficient synchronization by only transferring changed data
 */

import { offlineStorage, EntityType, OfflineEntity } from '../OfflineStorage';
import { DataCompression } from '../compression/DataCompression';

export interface DeltaOperation {
  type: 'insert' | 'update' | 'delete' | 'move';
  path: string;
  value?: any;
  oldValue?: any;
  index?: number;
  newIndex?: number;
}

export interface DeltaPatch {
  entityType: EntityType;
  entityId: string | number;
  baseVersion: number;
  targetVersion: number;
  operations: DeltaOperation[];
  checksum: string;
  timestamp: number;
  compressed?: boolean;
}

export interface SyncDelta {
  lastSyncTimestamp: number;
  entities: {
    [entityType: string]: {
      created: Array<{ id: string | number; data: any; version: number }>;
      updated: Array<{ id: string | number; patch: DeltaPatch; version: number }>;
      deleted: Array<{ id: string | number; version: number; deletedAt: number }>;
    };
  };
  totalSize: number;
  compressedSize?: number;
}

export interface SyncManifest {
  version: number;
  timestamp: number;
  entities: {
    [entityType: string]: {
      [entityId: string]: {
        version: number;
        lastModified: number;
        checksum: string;
      };
    };
  };
}

/**
 * Delta sync manager for efficient data synchronization
 */
export class DeltaSync {
  private compression = new DataCompression();
  private lastSyncTimestamp: number = 0;
  private syncManifest: SyncManifest | null = null;

  /**
   * Initialize delta sync
   */
  async initialize(): Promise<void> {
    try {
      // Load last sync timestamp and manifest
      await this.loadSyncState();
      console.log('✅ Delta sync initialized');
    } catch (error) {
      console.error('Failed to initialize delta sync:', error);
    }
  }

  /**
   * Generate delta for outgoing sync (local changes to server)
   */
  async generateOutgoingDelta(
    entityTypes: EntityType[] = [EntityType.WORKSPACE, EntityType.TASK, EntityType.FILE]
  ): Promise<SyncDelta> {
    const delta: SyncDelta = {
      lastSyncTimestamp: this.lastSyncTimestamp,
      entities: {},
      totalSize: 0
    };

    for (const entityType of entityTypes) {
      delta.entities[entityType] = {
        created: [],
        updated: [],
        deleted: []
      };

      // Get all entities of this type
      const entities = await offlineStorage.getAll(entityType, { includeDeleted: true });
      
      for (const entity of entities) {
        const size = this.calculateEntitySize(entity);
        delta.totalSize += size;

        if (entity.isDeleted && entity.deletedAt && entity.deletedAt > this.lastSyncTimestamp) {
          // Entity was deleted since last sync
          delta.entities[entityType].deleted.push({
            id: entity.id,
            version: entity.version,
            deletedAt: entity.deletedAt
          });
        } else if (entity.createdAt > this.lastSyncTimestamp) {
          // Entity was created since last sync
          delta.entities[entityType].created.push({
            id: entity.id,
            data: this.sanitizeEntityForSync(entity),
            version: entity.version
          });
        } else if (entity.lastModified > this.lastSyncTimestamp) {
          // Entity was updated since last sync - generate patch
          const patch = await this.generateEntityPatch(entityType, entity);
          if (patch) {
            delta.entities[entityType].updated.push({
              id: entity.id,
              patch,
              version: entity.version
            });
          }
        }
      }
    }

    // Compress delta if beneficial
    if (delta.totalSize > 10240) { // Compress if larger than 10KB
      const compressed = await this.compression.compress(delta);
      if (compressed.compressedSize < delta.totalSize * 0.8) {
        delta.compressedSize = compressed.compressedSize;
        return compressed as any; // Return compressed version
      }
    }

    return delta;
  }

  /**
   * Apply incoming delta from server
   */
  async applyIncomingDelta(delta: SyncDelta): Promise<{
    applied: number;
    conflicts: number;
    errors: string[];
  }> {
    const result = {
      applied: 0,
      conflicts: 0,
      errors: []
    };

    try {
      // Decompress if needed
      let actualDelta = delta;
      if (delta.compressedSize) {
        actualDelta = await this.compression.decompress(delta as any);
      }

      // Apply changes for each entity type
      for (const [entityType, changes] of Object.entries(actualDelta.entities)) {
        try {
          // Apply deletions first
          for (const deletion of changes.deleted) {
            try {
              await offlineStorage.hardDelete(entityType as EntityType, deletion.id);
              result.applied++;
            } catch (error) {
              result.errors.push(`Failed to delete ${entityType} ${deletion.id}: ${error}`);
            }
          }

          // Apply creations
          for (const creation of changes.created) {
            try {
              const entity = {
                ...creation.data,
                syncStatus: 'synced',
                version: creation.version,
                lastModified: Date.now()
              };
              await offlineStorage.store(entityType as EntityType, entity);
              result.applied++;
            } catch (error) {
              result.errors.push(`Failed to create ${entityType} ${creation.id}: ${error}`);
            }
          }

          // Apply updates
          for (const update of changes.updated) {
            try {
              const applied = await this.applyEntityPatch(entityType as EntityType, update.patch);
              if (applied) {
                result.applied++;
              } else {
                result.conflicts++;
              }
            } catch (error) {
              result.errors.push(`Failed to update ${entityType} ${update.id}: ${error}`);
            }
          }

        } catch (error) {
          result.errors.push(`Failed to process ${entityType}: ${error}`);
        }
      }

      // Update sync timestamp
      this.lastSyncTimestamp = Math.max(this.lastSyncTimestamp, actualDelta.lastSyncTimestamp);
      await this.saveSyncState();

    } catch (error) {
      result.errors.push(`Failed to apply delta: ${error}`);
    }

    return result;
  }

  /**
   * Generate entity patch between versions
   */
  private async generateEntityPatch(entityType: EntityType, currentEntity: OfflineEntity): Promise<DeltaPatch | null> {
    try {
      // Get the base version from manifest
      const baseEntity = await this.getBaseEntityVersion(entityType, currentEntity.id);
      if (!baseEntity) {
        // No base version, treat as creation
        return null;
      }

      const operations = this.diffObjects(baseEntity, currentEntity);
      if (operations.length === 0) {
        return null; // No changes
      }

      const patch: DeltaPatch = {
        entityType,
        entityId: currentEntity.id,
        baseVersion: baseEntity.version,
        targetVersion: currentEntity.version,
        operations,
        checksum: await this.calculateChecksum(currentEntity),
        timestamp: currentEntity.lastModified
      };

      // Compress patch if beneficial
      const patchSize = JSON.stringify(patch).length;
      if (patchSize > 1024) { // Compress patches larger than 1KB
        const compressed = await this.compression.compress(patch);
        if (compressed.compressedSize < patchSize * 0.8) {
          patch.compressed = true;
          return compressed as any;
        }
      }

      return patch;

    } catch (error) {
      console.error('Failed to generate entity patch:', error);
      return null;
    }
  }

  /**
   * Apply entity patch
   */
  private async applyEntityPatch(entityType: EntityType, patch: DeltaPatch): Promise<boolean> {
    try {
      // Decompress if needed
      let actualPatch = patch;
      if (patch.compressed) {
        actualPatch = await this.compression.decompress(patch as any);
      }

      // Get current entity
      const currentEntity = await offlineStorage.get(entityType, actualPatch.entityId);
      if (!currentEntity) {
        throw new Error('Entity not found');
      }

      // Check version compatibility
      if (currentEntity.version !== actualPatch.baseVersion) {
        // Version mismatch - conflict detected
        console.warn(`Version conflict for ${entityType} ${actualPatch.entityId}: expected ${actualPatch.baseVersion}, got ${currentEntity.version}`);
        return false;
      }

      // Apply operations
      const patchedEntity = this.applyOperations(currentEntity, actualPatch.operations);
      
      // Verify checksum
      const calculatedChecksum = await this.calculateChecksum(patchedEntity);
      if (calculatedChecksum !== actualPatch.checksum) {
        throw new Error('Checksum mismatch after applying patch');
      }

      // Update entity
      patchedEntity.version = actualPatch.targetVersion;
      patchedEntity.lastModified = actualPatch.timestamp;
      patchedEntity.syncStatus = 'synced';

      await offlineStorage.store(entityType, patchedEntity);
      return true;

    } catch (error) {
      console.error('Failed to apply entity patch:', error);
      return false;
    }
  }

  /**
   * Generate diff operations between two objects
   */
  private diffObjects(oldObj: any, newObj: any, path = ''): DeltaOperation[] {
    const operations: DeltaOperation[] = [];

    // Handle null/undefined cases
    if (oldObj === null || oldObj === undefined) {
      if (newObj !== null && newObj !== undefined) {
        operations.push({
          type: 'insert',
          path,
          value: newObj
        });
      }
      return operations;
    }

    if (newObj === null || newObj === undefined) {
      operations.push({
        type: 'delete',
        path,
        oldValue: oldObj
      });
      return operations;
    }

    // Handle primitive values
    if (typeof oldObj !== 'object' || typeof newObj !== 'object') {
      if (oldObj !== newObj) {
        operations.push({
          type: 'update',
          path,
          value: newObj,
          oldValue: oldObj
        });
      }
      return operations;
    }

    // Handle arrays
    if (Array.isArray(oldObj) && Array.isArray(newObj)) {
      return this.diffArrays(oldObj, newObj, path);
    }

    // Handle objects
    const allKeys = new Set([...Object.keys(oldObj), ...Object.keys(newObj)]);
    
    for (const key of allKeys) {
      const currentPath = path ? `${path}.${key}` : key;
      const oldValue = oldObj[key];
      const newValue = newObj[key];

      if (!(key in oldObj)) {
        // Property added
        operations.push({
          type: 'insert',
          path: currentPath,
          value: newValue
        });
      } else if (!(key in newObj)) {
        // Property removed
        operations.push({
          type: 'delete',
          path: currentPath,
          oldValue: oldValue
        });
      } else {
        // Property potentially changed
        operations.push(...this.diffObjects(oldValue, newValue, currentPath));
      }
    }

    return operations;
  }

  /**
   * Generate diff operations for arrays
   */
  private diffArrays(oldArray: any[], newArray: any[], path: string): DeltaOperation[] {
    const operations: DeltaOperation[] = [];

    // Simple approach: treat array changes as replacements
    // For more sophisticated diff, we could implement LCS algorithm
    if (JSON.stringify(oldArray) !== JSON.stringify(newArray)) {
      operations.push({
        type: 'update',
        path,
        value: newArray,
        oldValue: oldArray
      });
    }

    return operations;
  }

  /**
   * Apply operations to an object
   */
  private applyOperations(obj: any, operations: DeltaOperation[]): any {
    const result = JSON.parse(JSON.stringify(obj)); // Deep clone

    for (const operation of operations) {
      this.applyOperation(result, operation);
    }

    return result;
  }

  /**
   * Apply a single operation to an object
   */
  private applyOperation(obj: any, operation: DeltaOperation): void {
    const pathParts = operation.path.split('.');
    let current = obj;

    // Navigate to parent object
    for (let i = 0; i < pathParts.length - 1; i++) {
      const part = pathParts[i];
      if (!(part in current)) {
        current[part] = {};
      }
      current = current[part];
    }

    const lastPart = pathParts[pathParts.length - 1];

    switch (operation.type) {
      case 'insert':
      case 'update':
        current[lastPart] = operation.value;
        break;

      case 'delete':
        delete current[lastPart];
        break;

      case 'move':
        // Handle array moves if needed
        if (Array.isArray(current) && operation.index !== undefined && operation.newIndex !== undefined) {
          const item = current.splice(operation.index, 1)[0];
          current.splice(operation.newIndex, 0, item);
        }
        break;
    }
  }

  /**
   * Get sync manifest from server
   */
  async fetchSyncManifest(): Promise<SyncManifest> {
    try {
      const response = await fetch('/api/sync/manifest');
      if (!response.ok) {
        throw new Error(`Failed to fetch sync manifest: ${response.statusText}`);
      }
      
      const manifest = await response.json();
      this.syncManifest = manifest;
      return manifest;
    } catch (error) {
      console.error('Failed to fetch sync manifest:', error);
      throw error;
    }
  }

  /**
   * Generate local sync manifest
   */
  async generateLocalManifest(): Promise<SyncManifest> {
    const manifest: SyncManifest = {
      version: Date.now(),
      timestamp: Date.now(),
      entities: {}
    };

    const entityTypes = [EntityType.WORKSPACE, EntityType.TASK, EntityType.FILE];
    
    for (const entityType of entityTypes) {
      manifest.entities[entityType] = {};
      const entities = await offlineStorage.getAll(entityType);
      
      for (const entity of entities) {
        if (!entity.isDeleted) {
          manifest.entities[entityType][entity.id] = {
            version: entity.version,
            lastModified: entity.lastModified,
            checksum: entity.checksum || await this.calculateChecksum(entity)
          };
        }
      }
    }

    return manifest;
  }

  /**
   * Compare manifests to find differences
   */
  compareManifests(local: SyncManifest, remote: SyncManifest): {
    localOnly: Array<{ entityType: string; entityId: string; info: any }>;
    remoteOnly: Array<{ entityType: string; entityId: string; info: any }>;
    conflicts: Array<{ entityType: string; entityId: string; local: any; remote: any }>;
    outdated: Array<{ entityType: string; entityId: string; local: any; remote: any }>;
  } {
    const result = {
      localOnly: [] as Array<{ entityType: string; entityId: string; info: any }>,
      remoteOnly: [] as Array<{ entityType: string; entityId: string; info: any }>,
      conflicts: [] as Array<{ entityType: string; entityId: string; local: any; remote: any }>,
      outdated: [] as Array<{ entityType: string; entityId: string; local: any; remote: any }>
    };

    // Get all entity types from both manifests
    const allEntityTypes = new Set([
      ...Object.keys(local.entities),
      ...Object.keys(remote.entities)
    ]);

    for (const entityType of allEntityTypes) {
      const localEntities = local.entities[entityType] || {};
      const remoteEntities = remote.entities[entityType] || {};

      const allEntityIds = new Set([
        ...Object.keys(localEntities),
        ...Object.keys(remoteEntities)
      ]);

      for (const entityId of allEntityIds) {
        const localInfo = localEntities[entityId];
        const remoteInfo = remoteEntities[entityId];

        if (!localInfo && remoteInfo) {
          // Entity exists only on remote
          result.remoteOnly.push({ entityType, entityId, info: remoteInfo });
        } else if (localInfo && !remoteInfo) {
          // Entity exists only locally
          result.localOnly.push({ entityType, entityId, info: localInfo });
        } else if (localInfo && remoteInfo) {
          // Entity exists on both sides
          if (localInfo.checksum !== remoteInfo.checksum) {
            if (localInfo.lastModified > remoteInfo.lastModified) {
              // Local is newer
              result.outdated.push({ entityType, entityId, local: localInfo, remote: remoteInfo });
            } else if (localInfo.lastModified < remoteInfo.lastModified) {
              // Remote is newer
              result.outdated.push({ entityType, entityId, local: localInfo, remote: remoteInfo });
            } else {
              // Same timestamp but different checksum - conflict
              result.conflicts.push({ entityType, entityId, local: localInfo, remote: remoteInfo });
            }
          }
        }
      }
    }

    return result;
  }

  // Utility methods

  private async getBaseEntityVersion(entityType: EntityType, entityId: string | number): Promise<any | null> {
    // In a real implementation, this would get the entity version from the last sync
    // For now, we'll return null to indicate no base version
    return null;
  }

  private sanitizeEntityForSync(entity: any): any {
    // Remove sync-specific fields
    const { syncStatus, localId, ...syncEntity } = entity;
    return syncEntity;
  }

  private calculateEntitySize(entity: any): number {
    return JSON.stringify(entity).length;
  }

  private async calculateChecksum(data: any): Promise<string> {
    const jsonString = JSON.stringify(data, Object.keys(data).sort());
    const encoder = new TextEncoder();
    const dataBuffer = encoder.encode(jsonString);
    const hashBuffer = await crypto.subtle.digest('SHA-256', dataBuffer);
    const hashArray = Array.from(new Uint8Array(hashBuffer));
    return hashArray.map(b => b.toString(16).padStart(2, '0')).join('');
  }

  private async loadSyncState(): Promise<void> {
    try {
      // Load from metadata store
      // Implementation would depend on storage mechanism
      this.lastSyncTimestamp = 0; // Default
    } catch (error) {
      console.warn('Failed to load sync state:', error);
    }
  }

  private async saveSyncState(): Promise<void> {
    try {
      // Save to metadata store
      // Implementation would depend on storage mechanism
    } catch (error) {
      console.warn('Failed to save sync state:', error);
    }
  }
}

// Singleton instance
export const deltaSync = new DeltaSync();