/**
 * Enhanced Encryption Manager for Offline Data Security
 * Provides comprehensive encryption for sensitive offline data
 */

import { AESGCMEncryption, EncryptedData } from './AESGCMEncryption';
import { EntityType, OfflineEntity } from '../OfflineStorage';

export interface EncryptionConfig {
  enabled: boolean;
  algorithm: 'AES-GCM' | 'AES-CBC';
  keySize: 128 | 192 | 256;
  autoEncryptSensitive: boolean;
  encryptUserData: boolean;
  encryptFileContent: boolean;
  encryptAnalytics: boolean;
  compressionBeforeEncryption: boolean;
}

export interface EncryptionKey {
  id: string;
  key: CryptoKey;
  derivedFrom: 'password' | 'biometric' | 'device' | 'random';
  createdAt: number;
  expiresAt?: number;
  usage: string[]; // What this key can be used for
}

export interface EncryptionMetadata {
  encrypted: boolean;
  algorithm: string;
  keyId: string;
  iv: string;
  authTag?: string;
  encryptedAt: number;
  encryptedFields?: string[];
}

export interface SecurityAuditLog {
  id: string;
  action: 'encrypt' | 'decrypt' | 'key_generate' | 'key_derive' | 'access_denied';
  entityType?: EntityType;
  entityId?: string | number;
  keyId?: string;
  success: boolean;
  error?: string;
  timestamp: number;
  userAgent: string;
  ipAddress?: string;
}

/**
 * Comprehensive encryption manager for offline data
 */
export class EncryptionManager {
  private config: EncryptionConfig = {
    enabled: true,
    algorithm: 'AES-GCM',
    keySize: 256,
    autoEncryptSensitive: true,
    encryptUserData: true,
    encryptFileContent: false, // Large files handled separately
    encryptAnalytics: false,
    compressionBeforeEncryption: true
  };

  private keys: Map<string, EncryptionKey> = new Map();
  private masterKey: CryptoKey | null = null;
  private deviceKey: CryptoKey | null = null;
  private securityLogs: SecurityAuditLog[] = [];
  private sensitiveFields = new Set([
    'password', 'token', 'secret', 'key', 'credential', 
    'auth', 'session', 'cookie', 'bearer', 'api_key',
    'personal_info', 'email', 'phone', 'address',
    'payment', 'credit_card', 'bank_account'
  ]);

  private encryptionRules: Map<EntityType, EncryptionRule> = new Map();

  constructor() {
    this.initializeEncryptionRules();
  }

  /**
   * Initialize encryption rules for different entity types
   */
  private initializeEncryptionRules(): void {
    // Workspace encryption rules
    this.encryptionRules.set(EntityType.WORKSPACE, {
      alwaysEncrypt: ['layout_config', 'ambient_sound'],
      neverEncrypt: ['id', 'name', 'theme', 'is_active', 'created_at', 'updated_at'],
      conditionalEncrypt: ['description'], // Encrypt if contains sensitive data
      encryptionLevel: 'medium'
    });

    // Task encryption rules
    this.encryptionRules.set(EntityType.TASK, {
      alwaysEncrypt: [],
      neverEncrypt: ['id', 'status', 'priority', 'created_at', 'updated_at', 'due_date'],
      conditionalEncrypt: ['title', 'description'], // Encrypt if contains sensitive keywords
      encryptionLevel: 'low'
    });

    // File encryption rules
    this.encryptionRules.set(EntityType.FILE, {
      alwaysEncrypt: ['cached_data'], // File content
      neverEncrypt: ['id', 'file_name', 'file_extension', 'file_size', 'mime_type', 'created_at'],
      conditionalEncrypt: ['user_description', 'ai_description'],
      encryptionLevel: 'high'
    });

    // Analytics encryption rules
    this.encryptionRules.set(EntityType.ANALYTICS, {
      alwaysEncrypt: ['data'], // Event data
      neverEncrypt: ['id', 'event_type', 'timestamp'],
      conditionalEncrypt: [],
      encryptionLevel: 'medium'
    });
  }

  /**
   * Initialize encryption system
   */
  async initialize(userPassword?: string): Promise<void> {
    try {
      // Generate or derive master key
      if (userPassword) {
        this.masterKey = await this.deriveKeyFromPassword(userPassword);
      } else {
        this.masterKey = await this.generateDeviceKey();
      }

      // Generate device-specific key
      this.deviceKey = await this.generateDeviceKey();

      // Initialize default encryption keys
      await this.initializeDefaultKeys();

      console.log('✅ Encryption manager initialized');
    } catch (error) {
      console.error('Failed to initialize encryption manager:', error);
      throw error;
    }
  }

  /**
   * Encrypt entity based on rules and configuration
   */
  async encryptEntity<T extends OfflineEntity>(
    entityType: EntityType, 
    entity: T,
    options: { forceEncrypt?: boolean; keyId?: string } = {}
  ): Promise<T> {
    if (!this.config.enabled && !options.forceEncrypt) {
      return entity;
    }

    try {
      const rule = this.encryptionRules.get(entityType);
      if (!rule && !options.forceEncrypt) {
        return entity;
      }

      const keyId = options.keyId || this.getDefaultKeyId(entityType);
      const encryptionKey = this.keys.get(keyId);
      
      if (!encryptionKey) {
        throw new Error(`Encryption key not found: ${keyId}`);
      }

      const aesEncryption = new AESGCMEncryption(await this.exportKey(encryptionKey.key));
      const encryptedEntity = { ...entity };
      const encryptedFields: string[] = [];

      // Determine fields to encrypt
      const fieldsToEncrypt = this.determineFieldsToEncrypt(entity, rule, options.forceEncrypt);

      // Encrypt individual fields
      for (const field of fieldsToEncrypt) {
        if (entity[field] !== undefined && entity[field] !== null) {
          const encrypted = await aesEncryption.encrypt(entity[field]);
          encryptedEntity[field] = encrypted;
          encryptedFields.push(field);
        }
      }

      // Add encryption metadata
      if (encryptedFields.length > 0) {
        (encryptedEntity as any).__encryption__ = {
          encrypted: true,
          algorithm: this.config.algorithm,
          keyId,
          encryptedAt: Date.now(),
          encryptedFields
        } as EncryptionMetadata;

        // Log encryption event
        await this.logSecurityEvent({
          action: 'encrypt',
          entityType,
          entityId: entity.id,
          keyId,
          success: true
        });
      }

      return encryptedEntity;

    } catch (error) {
      // Log encryption failure
      await this.logSecurityEvent({
        action: 'encrypt',
        entityType,
        entityId: entity.id,
        success: false,
        error: error instanceof Error ? error.message : 'Unknown error'
      });

      console.error('Failed to encrypt entity:', error);
      throw error;
    }
  }

  /**
   * Decrypt entity
   */
  async decryptEntity<T extends OfflineEntity>(
    entityType: EntityType,
    entity: T
  ): Promise<T> {
    const metadata = (entity as any).__encryption__ as EncryptionMetadata;
    
    if (!metadata || !metadata.encrypted) {
      return entity; // Not encrypted
    }

    try {
      const encryptionKey = this.keys.get(metadata.keyId);
      if (!encryptionKey) {
        throw new Error(`Decryption key not found: ${metadata.keyId}`);
      }

      const aesEncryption = new AESGCMEncryption(await this.exportKey(encryptionKey.key));
      const decryptedEntity = { ...entity };

      // Decrypt encrypted fields
      for (const field of metadata.encryptedFields || []) {
        if (entity[field] && (entity[field] as any).encrypted) {
          const decrypted = await aesEncryption.decrypt(entity[field] as EncryptedData);
          decryptedEntity[field] = decrypted;
        }
      }

      // Remove encryption metadata
      delete (decryptedEntity as any).__encryption__;

      // Log decryption event
      await this.logSecurityEvent({
        action: 'decrypt',
        entityType,
        entityId: entity.id,
        keyId: metadata.keyId,
        success: true
      });

      return decryptedEntity;

    } catch (error) {
      // Log decryption failure
      await this.logSecurityEvent({
        action: 'decrypt',
        entityType,
        entityId: entity.id,
        keyId: metadata.keyId,
        success: false,
        error: error instanceof Error ? error.message : 'Unknown error'
      });

      console.error('Failed to decrypt entity:', error);
      throw error;
    }
  }

  /**
   * Encrypt file content
   */
  async encryptFileContent(content: ArrayBuffer, keyId?: string): Promise<EncryptedData> {
    const key = keyId ? this.keys.get(keyId) : this.keys.get(this.getDefaultKeyId(EntityType.FILE));
    if (!key) {
      throw new Error('File encryption key not found');
    }

    const aesEncryption = new AESGCMEncryption(await this.exportKey(key.key));
    
    // Convert ArrayBuffer to base64 for encryption
    const base64Content = btoa(String.fromCharCode(...new Uint8Array(content)));
    return await aesEncryption.encrypt({ content: base64Content, type: 'file' });
  }

  /**
   * Decrypt file content
   */
  async decryptFileContent(encryptedContent: EncryptedData, keyId?: string): Promise<ArrayBuffer> {
    const key = keyId ? this.keys.get(keyId) : this.keys.get(this.getDefaultKeyId(EntityType.FILE));
    if (!key) {
      throw new Error('File decryption key not found');
    }

    const aesEncryption = new AESGCMEncryption(await this.exportKey(key.key));
    const decrypted = await aesEncryption.decrypt(encryptedContent);
    
    // Convert base64 back to ArrayBuffer
    const binaryString = atob(decrypted.content);
    const bytes = new Uint8Array(binaryString.length);
    for (let i = 0; i < binaryString.length; i++) {
      bytes[i] = binaryString.charCodeAt(i);
    }
    return bytes.buffer;
  }

  /**
   * Generate new encryption key
   */
  async generateKey(
    usage: string[] = ['encrypt', 'decrypt'],
    algorithm = 'AES-GCM'
  ): Promise<EncryptionKey> {
    try {
      const cryptoKey = await crypto.subtle.generateKey(
        {
          name: algorithm,
          length: this.config.keySize
        },
        true, // extractable
        usage as KeyUsage[]
      );

      const keyId = await this.generateKeyId();
      const encryptionKey: EncryptionKey = {
        id: keyId,
        key: cryptoKey,
        derivedFrom: 'random',
        createdAt: Date.now(),
        usage
      };

      this.keys.set(keyId, encryptionKey);

      await this.logSecurityEvent({
        action: 'key_generate',
        keyId,
        success: true
      });

      return encryptionKey;

    } catch (error) {
      await this.logSecurityEvent({
        action: 'key_generate',
        success: false,
        error: error instanceof Error ? error.message : 'Unknown error'
      });

      throw error;
    }
  }

  /**
   * Derive key from password
   */
  async deriveKeyFromPassword(
    password: string,
    salt?: string,
    iterations = 100000
  ): Promise<CryptoKey> {
    try {
      const encoder = new TextEncoder();
      const passwordBuffer = encoder.encode(password);
      const saltBuffer = encoder.encode(salt || 'BlueBirdHub-Salt-v2');

      // Import password as key material
      const keyMaterial = await crypto.subtle.importKey(
        'raw',
        passwordBuffer,
        'PBKDF2',
        false,
        ['deriveKey']
      );

      // Derive AES key
      const derivedKey = await crypto.subtle.deriveKey(
        {
          name: 'PBKDF2',
          salt: saltBuffer,
          iterations,
          hash: 'SHA-256'
        },
        keyMaterial,
        {
          name: 'AES-GCM',
          length: this.config.keySize
        },
        true,
        ['encrypt', 'decrypt']
      );

      await this.logSecurityEvent({
        action: 'key_derive',
        success: true
      });

      return derivedKey;

    } catch (error) {
      await this.logSecurityEvent({
        action: 'key_derive',
        success: false,
        error: error instanceof Error ? error.message : 'Unknown error'
      });

      throw error;
    }
  }

  /**
   * Generate device-specific key
   */
  private async generateDeviceKey(): Promise<CryptoKey> {
    // Create device-specific entropy
    const deviceInfo = {
      userAgent: navigator.userAgent,
      language: navigator.language,
      platform: navigator.platform,
      timestamp: Date.now(),
      random: crypto.getRandomValues(new Uint8Array(32))
    };

    const deviceString = JSON.stringify(deviceInfo);
    const encoder = new TextEncoder();
    const deviceBuffer = encoder.encode(deviceString);

    // Hash device info to create deterministic but unique key material
    const hashBuffer = await crypto.subtle.digest('SHA-256', deviceBuffer);

    // Import as key material
    const keyMaterial = await crypto.subtle.importKey(
      'raw',
      hashBuffer,
      'HKDF',
      false,
      ['deriveKey']
    );

    // Derive device key
    return await crypto.subtle.deriveKey(
      {
        name: 'HKDF',
        hash: 'SHA-256',
        salt: new Uint8Array([]), // No salt for device key
        info: encoder.encode('BlueBirdHub-Device-Key-v1')
      },
      keyMaterial,
      {
        name: 'AES-GCM',
        length: this.config.keySize
      },
      true,
      ['encrypt', 'decrypt']
    );
  }

  /**
   * Initialize default encryption keys
   */
  private async initializeDefaultKeys(): Promise<void> {
    // Create default keys for each entity type
    for (const entityType of Object.values(EntityType)) {
      const keyId = `default_${entityType}`;
      
      if (!this.keys.has(keyId)) {
        const encryptionKey: EncryptionKey = {
          id: keyId,
          key: this.deviceKey!,
          derivedFrom: 'device',
          createdAt: Date.now(),
          usage: ['encrypt', 'decrypt']
        };

        this.keys.set(keyId, encryptionKey);
      }
    }

    // Create master encryption key
    if (!this.keys.has('master')) {
      const encryptionKey: EncryptionKey = {
        id: 'master',
        key: this.masterKey!,
        derivedFrom: 'password',
        createdAt: Date.now(),
        usage: ['encrypt', 'decrypt']
      };

      this.keys.set('master', encryptionKey);
    }
  }

  /**
   * Determine which fields to encrypt based on rules
   */
  private determineFieldsToEncrypt(
    entity: any,
    rule?: EncryptionRule,
    forceEncrypt = false
  ): string[] {
    const fieldsToEncrypt = new Set<string>();

    if (forceEncrypt) {
      // Encrypt all fields except metadata
      for (const key of Object.keys(entity)) {
        if (!key.startsWith('__') && !['id', 'created_at', 'updated_at'].includes(key)) {
          fieldsToEncrypt.add(key);
        }
      }
      return Array.from(fieldsToEncrypt);
    }

    if (!rule) return [];

    // Always encrypt specified fields
    for (const field of rule.alwaysEncrypt) {
      if (entity[field] !== undefined) {
        fieldsToEncrypt.add(field);
      }
    }

    // Conditionally encrypt fields
    for (const field of rule.conditionalEncrypt) {
      if (entity[field] !== undefined && this.containsSensitiveData(entity[field])) {
        fieldsToEncrypt.add(field);
      }
    }

    // Auto-encrypt sensitive fields if enabled
    if (this.config.autoEncryptSensitive) {
      for (const key of Object.keys(entity)) {
        if (!rule.neverEncrypt.includes(key) && this.isSensitiveField(key)) {
          fieldsToEncrypt.add(key);
        }
      }
    }

    return Array.from(fieldsToEncrypt);
  }

  /**
   * Check if field name indicates sensitive data
   */
  private isSensitiveField(fieldName: string): boolean {
    const lowerField = fieldName.toLowerCase();
    return Array.from(this.sensitiveFields).some(sensitive => 
      lowerField.includes(sensitive)
    );
  }

  /**
   * Check if data contains sensitive information
   */
  private containsSensitiveData(data: any): boolean {
    if (typeof data !== 'string') {
      data = JSON.stringify(data);
    }

    const lowerData = data.toLowerCase();
    return Array.from(this.sensitiveFields).some(sensitive => 
      lowerData.includes(sensitive)
    );
  }

  /**
   * Get default key ID for entity type
   */
  private getDefaultKeyId(entityType: EntityType): string {
    return `default_${entityType}`;
  }

  /**
   * Generate unique key ID
   */
  private async generateKeyId(): Promise<string> {
    const randomBytes = crypto.getRandomValues(new Uint8Array(16));
    return Array.from(randomBytes, byte => byte.toString(16).padStart(2, '0')).join('');
  }

  /**
   * Export CryptoKey as raw key material
   */
  private async exportKey(key: CryptoKey): Promise<string> {
    const exported = await crypto.subtle.exportKey('raw', key);
    const exportedArray = new Uint8Array(exported);
    return Array.from(exportedArray, byte => byte.toString(16).padStart(2, '0')).join('');
  }

  /**
   * Log security events
   */
  private async logSecurityEvent(
    event: Omit<SecurityAuditLog, 'id' | 'timestamp' | 'userAgent'>
  ): Promise<void> {
    const logEntry: SecurityAuditLog = {
      ...event,
      id: crypto.randomUUID(),
      timestamp: Date.now(),
      userAgent: navigator.userAgent
    };

    this.securityLogs.push(logEntry);

    // Keep only recent logs (last 1000)
    if (this.securityLogs.length > 1000) {
      this.securityLogs = this.securityLogs.slice(-1000);
    }
  }

  /**
   * Get security audit logs
   */
  getSecurityLogs(filter?: {
    action?: string;
    entityType?: EntityType;
    success?: boolean;
    fromDate?: number;
    toDate?: number;
  }): SecurityAuditLog[] {
    let logs = this.securityLogs;

    if (filter) {
      logs = logs.filter(log => {
        if (filter.action && log.action !== filter.action) return false;
        if (filter.entityType && log.entityType !== filter.entityType) return false;
        if (filter.success !== undefined && log.success !== filter.success) return false;
        if (filter.fromDate && log.timestamp < filter.fromDate) return false;
        if (filter.toDate && log.timestamp > filter.toDate) return false;
        return true;
      });
    }

    return logs.sort((a, b) => b.timestamp - a.timestamp);
  }

  /**
   * Update encryption configuration
   */
  updateConfig(newConfig: Partial<EncryptionConfig>): void {
    this.config = { ...this.config, ...newConfig };
  }

  /**
   * Get encryption status for entity
   */
  getEncryptionStatus(entity: any): {
    encrypted: boolean;
    algorithm?: string;
    keyId?: string;
    encryptedFields?: string[];
    encryptedAt?: number;
  } {
    const metadata = entity.__encryption__ as EncryptionMetadata;
    
    if (!metadata) {
      return { encrypted: false };
    }

    return {
      encrypted: metadata.encrypted,
      algorithm: metadata.algorithm,
      keyId: metadata.keyId,
      encryptedFields: metadata.encryptedFields,
      encryptedAt: metadata.encryptedAt
    };
  }

  /**
   * Get encryption statistics
   */
  getEncryptionStats(): {
    totalKeys: number;
    keysByType: Record<string, number>;
    encryptionEvents: number;
    decryptionEvents: number;
    failedEvents: number;
    lastActivity: number | null;
  } {
    const keysByType: Record<string, number> = {};
    
    for (const key of this.keys.values()) {
      keysByType[key.derivedFrom] = (keysByType[key.derivedFrom] || 0) + 1;
    }

    const encryptionEvents = this.securityLogs.filter(log => log.action === 'encrypt' && log.success).length;
    const decryptionEvents = this.securityLogs.filter(log => log.action === 'decrypt' && log.success).length;
    const failedEvents = this.securityLogs.filter(log => !log.success).length;
    const lastActivity = this.securityLogs.length > 0 ? 
      Math.max(...this.securityLogs.map(log => log.timestamp)) : null;

    return {
      totalKeys: this.keys.size,
      keysByType,
      encryptionEvents,
      decryptionEvents,
      failedEvents,
      lastActivity
    };
  }
}

interface EncryptionRule {
  alwaysEncrypt: string[];
  neverEncrypt: string[];
  conditionalEncrypt: string[];
  encryptionLevel: 'low' | 'medium' | 'high';
}

// Singleton instance
export const encryptionManager = new EncryptionManager();