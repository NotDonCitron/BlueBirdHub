/**
 * Conflict Resolution System for Offline Sync
 * Handles data conflicts when changes occur both online and offline
 */

import { EntityType, ConflictResolution, OfflineEntity } from '../OfflineStorage';

export interface ConflictData {
  id: string;
  entityType: EntityType;
  entityId: string | number;
  localData: any;
  remoteData: any;
  conflictFields: string[];
  timestamp: number;
  syncAction: 'create' | 'update' | 'delete';
}

export interface ResolutionStrategy {
  strategy: ConflictResolution;
  mergedData?: any;
  userChoice?: 'local' | 'remote' | 'merge';
  fieldResolutions?: Record<string, 'local' | 'remote' | any>;
}

export interface ConflictResolutionResult {
  resolved: boolean;
  resolvedData?: any;
  error?: string;
}

/**
 * Main conflict resolver class
 */
export class ConflictResolver {
  private autoResolutionRules: Map<string, ConflictResolution> = new Map();
  private fieldPriorityRules: Map<string, (local: any, remote: any) => any> = new Map();

  constructor() {
    this.initializeDefaultRules();
  }

  /**
   * Initialize default auto-resolution rules
   */
  private initializeDefaultRules(): void {
    // Default rules for different entity types
    this.autoResolutionRules.set('user_description', ConflictResolution.LAST_WRITE_WINS);
    this.autoResolutionRules.set('is_favorite', ConflictResolution.MERGE);
    this.autoResolutionRules.set('is_archived', ConflictResolution.MERGE);
    this.autoResolutionRules.set('tags', ConflictResolution.MERGE);

    // Field priority rules
    this.fieldPriorityRules.set('last_accessed_at', (local, remote) => Math.max(local, remote));
    this.fieldPriorityRules.set('completed_at', (local, remote) => remote || local);
    this.fieldPriorityRules.set('version', (local, remote) => Math.max(local, remote));
  }

  /**
   * Resolve conflict automatically if possible
   */
  async resolveConflictAutomatically(conflict: ConflictData): Promise<ConflictResolutionResult> {
    try {
      const { localData, remoteData, conflictFields } = conflict;

      // Check if we can auto-resolve all conflicts
      const canAutoResolve = conflictFields.every(field => 
        this.autoResolutionRules.has(field) || this.fieldPriorityRules.has(field)
      );

      if (!canAutoResolve) {
        return { resolved: false };
      }

      const resolvedData = await this.mergeData(localData, remoteData, conflictFields);
      
      return {
        resolved: true,
        resolvedData
      };

    } catch (error) {
      return {
        resolved: false,
        error: error instanceof Error ? error.message : 'Unknown error'
      };
    }
  }

  /**
   * Resolve conflict with user-provided strategy
   */
  async resolveConflictWithStrategy(
    conflict: ConflictData, 
    strategy: ResolutionStrategy
  ): Promise<ConflictResolutionResult> {
    try {
      const { localData, remoteData } = conflict;
      let resolvedData: any;

      switch (strategy.strategy) {
        case ConflictResolution.LAST_WRITE_WINS:
          resolvedData = this.resolveLastWriteWins(localData, remoteData);
          break;

        case ConflictResolution.MERGE:
          resolvedData = await this.mergeFull(localData, remoteData, strategy.fieldResolutions);
          break;

        case ConflictResolution.USER_CHOICE:
          resolvedData = strategy.userChoice === 'local' ? localData : 
                        strategy.userChoice === 'remote' ? remoteData :
                        strategy.mergedData;
          break;

        case ConflictResolution.KEEP_BOTH:
          resolvedData = await this.keepBoth(localData, remoteData, conflict.entityType);
          break;

        default:
          throw new Error(`Unknown conflict resolution strategy: ${strategy.strategy}`);
      }

      return {
        resolved: true,
        resolvedData
      };

    } catch (error) {
      return {
        resolved: false,
        error: error instanceof Error ? error.message : 'Unknown error'
      };
    }
  }

  /**
   * Detect conflicts between local and remote data
   */
  detectConflicts(local: any, remote: any): string[] {
    const conflicts: string[] = [];
    const excludeFields = ['id', 'sync_status', 'version', 'last_modified', 'created_at'];

    for (const key in local) {
      if (excludeFields.includes(key)) continue;
      
      if (this.hasConflict(local[key], remote[key])) {
        conflicts.push(key);
      }
    }

    return conflicts;
  }

  /**
   * Check if two values represent a conflict
   */
  private hasConflict(localValue: any, remoteValue: any): boolean {
    // Skip if values are the same
    if (localValue === remoteValue) return false;

    // Handle null/undefined cases
    if ((localValue == null) !== (remoteValue == null)) return true;
    if (localValue == null && remoteValue == null) return false;

    // Handle arrays
    if (Array.isArray(localValue) && Array.isArray(remoteValue)) {
      return JSON.stringify(localValue.sort()) !== JSON.stringify(remoteValue.sort());
    }

    // Handle objects
    if (typeof localValue === 'object' && typeof remoteValue === 'object') {
      return JSON.stringify(localValue) !== JSON.stringify(remoteValue);
    }

    // Handle dates
    if (localValue instanceof Date && remoteValue instanceof Date) {
      return localValue.getTime() !== remoteValue.getTime();
    }

    // Handle timestamps
    if (typeof localValue === 'number' && typeof remoteValue === 'number') {
      // Allow small timestamp differences (within 1 second)
      return Math.abs(localValue - remoteValue) > 1000;
    }

    return true;
  }

  /**
   * Resolve using last-write-wins strategy
   */
  private resolveLastWriteWins(local: any, remote: any): any {
    const localTime = local.last_modified || local.updated_at || 0;
    const remoteTime = remote.last_modified || remote.updated_at || 0;

    return localTime > remoteTime ? local : remote;
  }

  /**
   * Merge data intelligently
   */
  private async mergeData(local: any, remote: any, conflictFields: string[]): Promise<any> {
    const merged = { ...remote }; // Start with remote as base

    for (const field of conflictFields) {
      const rule = this.autoResolutionRules.get(field);
      const priorityRule = this.fieldPriorityRules.get(field);

      if (priorityRule) {
        merged[field] = priorityRule(local[field], remote[field]);
      } else if (rule) {
        merged[field] = await this.applyResolutionRule(
          rule, 
          local[field], 
          remote[field], 
          field
        );
      } else {
        // Default to last-write-wins for unknown fields
        const localTime = local.last_modified || 0;
        const remoteTime = remote.last_modified || 0;
        merged[field] = localTime > remoteTime ? local[field] : remote[field];
      }
    }

    // Always use the latest timestamp and highest version
    merged.last_modified = Math.max(
      local.last_modified || 0, 
      remote.last_modified || 0
    );
    merged.version = Math.max(local.version || 1, remote.version || 1) + 1;

    return merged;
  }

  /**
   * Full merge with user-specified field resolutions
   */
  private async mergeFull(
    local: any, 
    remote: any, 
    fieldResolutions?: Record<string, 'local' | 'remote' | any>
  ): Promise<any> {
    const merged = { ...remote };

    // Apply user-specified field resolutions
    if (fieldResolutions) {
      for (const [field, resolution] of Object.entries(fieldResolutions)) {
        if (resolution === 'local') {
          merged[field] = local[field];
        } else if (resolution === 'remote') {
          merged[field] = remote[field];
        } else {
          merged[field] = resolution; // Custom value
        }
      }
    }

    // Merge arrays intelligently
    for (const key in local) {
      if (Array.isArray(local[key]) && Array.isArray(remote[key])) {
        merged[key] = this.mergeArrays(local[key], remote[key]);
      }
    }

    // Update metadata
    merged.last_modified = Date.now();
    merged.version = Math.max(local.version || 1, remote.version || 1) + 1;

    return merged;
  }

  /**
   * Keep both versions by creating a duplicate
   */
  private async keepBoth(local: any, remote: any, entityType: EntityType): Promise<any> {
    // For keep-both strategy, we keep the remote version and create a copy of local
    const localCopy = {
      ...local,
      id: `${local.id}_local_copy_${Date.now()}`,
      name: `${local.name || local.title} (Local Copy)`,
      title: local.title ? `${local.title} (Local Copy)` : undefined,
      sync_status: 'pending_create',
      version: 1,
      last_modified: Date.now()
    };

    // Store the local copy (this would need to be handled by the calling code)
    return remote; // Return remote as the resolved version
  }

  /**
   * Apply a resolution rule to a field
   */
  private async applyResolutionRule(
    rule: ConflictResolution,
    localValue: any,
    remoteValue: any,
    fieldName: string
  ): Promise<any> {
    switch (rule) {
      case ConflictResolution.LAST_WRITE_WINS:
        // This would need timestamp context, defaulting to remote
        return remoteValue;

      case ConflictResolution.MERGE:
        if (Array.isArray(localValue) && Array.isArray(remoteValue)) {
          return this.mergeArrays(localValue, remoteValue);
        }
        if (typeof localValue === 'object' && typeof remoteValue === 'object') {
          return { ...remoteValue, ...localValue };
        }
        // For primitive values, prefer local if it's more recent or remote otherwise
        return localValue || remoteValue;

      default:
        return remoteValue;
    }
  }

  /**
   * Merge two arrays intelligently
   */
  private mergeArrays(local: any[], remote: any[]): any[] {
    const merged = [...remote];
    
    for (const localItem of local) {
      // Check if item exists in remote (by id or content)
      const existsInRemote = remote.some(remoteItem => 
        this.itemsEqual(localItem, remoteItem)
      );
      
      if (!existsInRemote) {
        merged.push(localItem);
      }
    }

    return merged;
  }

  /**
   * Check if two array items are equal
   */
  private itemsEqual(item1: any, item2: any): boolean {
    if (item1 === item2) return true;
    
    // Check by id if both have ids
    if (item1.id && item2.id) {
      return item1.id === item2.id;
    }
    
    // Check by content
    if (typeof item1 === 'object' && typeof item2 === 'object') {
      return JSON.stringify(item1) === JSON.stringify(item2);
    }
    
    return false;
  }

  /**
   * Get conflict severity level
   */
  getConflictSeverity(conflict: ConflictData): 'low' | 'medium' | 'high' {
    const { conflictFields, entityType } = conflict;
    
    // Critical fields that indicate high severity
    const criticalFields = ['title', 'name', 'description', 'status', 'priority', 'due_date'];
    const hasCriticalConflicts = conflictFields.some(field => criticalFields.includes(field));
    
    if (hasCriticalConflicts) return 'high';
    if (conflictFields.length > 3) return 'medium';
    return 'low';
  }

  /**
   * Generate conflict summary for user display
   */
  generateConflictSummary(conflict: ConflictData): string {
    const { conflictFields, entityType } = conflict;
    const severity = this.getConflictSeverity(conflict);
    
    let summary = `${severity.toUpperCase()} conflict in ${entityType}: `;
    
    if (conflictFields.length === 1) {
      summary += `"${conflictFields[0]}" field differs`;
    } else {
      summary += `${conflictFields.length} fields differ (${conflictFields.slice(0, 3).join(', ')}`;
      if (conflictFields.length > 3) {
        summary += `, +${conflictFields.length - 3} more`;
      }
      summary += ')';
    }
    
    return summary;
  }

  /**
   * Add custom resolution rule
   */
  addResolutionRule(fieldName: string, rule: ConflictResolution): void {
    this.autoResolutionRules.set(fieldName, rule);
  }

  /**
   * Add custom field priority rule
   */
  addFieldPriorityRule(fieldName: string, rule: (local: any, remote: any) => any): void {
    this.fieldPriorityRules.set(fieldName, rule);
  }

  /**
   * Remove resolution rule
   */
  removeResolutionRule(fieldName: string): void {
    this.autoResolutionRules.delete(fieldName);
    this.fieldPriorityRules.delete(fieldName);
  }

  /**
   * Get all auto-resolution rules
   */
  getResolutionRules(): Record<string, ConflictResolution | 'priority'> {
    const rules: Record<string, ConflictResolution | 'priority'> = {};
    
    for (const [field, rule] of this.autoResolutionRules) {
      rules[field] = rule;
    }
    
    for (const [field] of this.fieldPriorityRules) {
      rules[field] = 'priority';
    }
    
    return rules;
  }
}

// Singleton instance
export const conflictResolver = new ConflictResolver();