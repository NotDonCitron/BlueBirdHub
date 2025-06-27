/**
 * AES-GCM Encryption for Offline Data Security
 * Provides client-side encryption for sensitive offline data
 */

export interface EncryptedData {
  data: string; // Base64 encoded encrypted data
  iv: string; // Base64 encoded initialization vector
  authTag?: string; // Base64 encoded authentication tag (for AES-GCM)
  encrypted: true;
}

export class AESGCMEncryption {
  private readonly keyMaterial: string;
  private cryptoKey: CryptoKey | null = null;

  constructor(keyMaterial: string) {
    this.keyMaterial = keyMaterial;
  }

  /**
   * Initialize the crypto key from key material
   */
  private async getCryptoKey(): Promise<CryptoKey> {
    if (this.cryptoKey) {
      return this.cryptoKey;
    }

    // Derive key from key material using PBKDF2
    const encoder = new TextEncoder();
    const keyMaterialBuffer = encoder.encode(this.keyMaterial);
    
    // Import key material
    const importedKey = await crypto.subtle.importKey(
      'raw',
      keyMaterialBuffer,
      'PBKDF2',
      false,
      ['deriveKey']
    );

    // Salt for key derivation (in production, this should be user-specific)
    const salt = encoder.encode('BlueBirdHub-Salt-v1');

    // Derive AES-GCM key
    this.cryptoKey = await crypto.subtle.deriveKey(
      {
        name: 'PBKDF2',
        salt: salt,
        iterations: 100000,
        hash: 'SHA-256'
      },
      importedKey,
      {
        name: 'AES-GCM',
        length: 256
      },
      false,
      ['encrypt', 'decrypt']
    );

    return this.cryptoKey;
  }

  /**
   * Encrypt data using AES-GCM
   */
  async encrypt(data: any): Promise<EncryptedData> {
    try {
      const key = await this.getCryptoKey();
      const encoder = new TextEncoder();
      
      // Convert data to JSON string
      const jsonString = JSON.stringify(data);
      const dataBuffer = encoder.encode(jsonString);

      // Generate random IV
      const iv = crypto.getRandomValues(new Uint8Array(12)); // 12 bytes for AES-GCM

      // Encrypt the data
      const encryptedBuffer = await crypto.subtle.encrypt(
        {
          name: 'AES-GCM',
          iv: iv
        },
        key,
        dataBuffer
      );

      // Convert to base64 for storage
      const encryptedArray = new Uint8Array(encryptedBuffer);
      const encryptedBase64 = this.arrayBufferToBase64(encryptedArray);
      const ivBase64 = this.arrayBufferToBase64(iv);

      return {
        data: encryptedBase64,
        iv: ivBase64,
        encrypted: true
      };
    } catch (error) {
      console.error('Encryption failed:', error);
      throw new Error('Failed to encrypt data');
    }
  }

  /**
   * Decrypt data using AES-GCM
   */
  async decrypt(encryptedData: EncryptedData | any): Promise<any> {
    // Check if data is actually encrypted
    if (!encryptedData.encrypted) {
      return encryptedData;
    }

    try {
      const key = await this.getCryptoKey();
      
      // Convert base64 back to arrays
      const encryptedArray = this.base64ToArrayBuffer(encryptedData.data);
      const iv = this.base64ToArrayBuffer(encryptedData.iv);

      // Decrypt the data
      const decryptedBuffer = await crypto.subtle.decrypt(
        {
          name: 'AES-GCM',
          iv: iv
        },
        key,
        encryptedArray
      );

      // Convert back to string and parse JSON
      const decoder = new TextDecoder();
      const jsonString = decoder.decode(decryptedBuffer);
      return JSON.parse(jsonString);
    } catch (error) {
      console.error('Decryption failed:', error);
      throw new Error('Failed to decrypt data');
    }
  }

  /**
   * Encrypt only sensitive fields in an object
   */
  async encryptSensitiveFields(data: any, sensitiveFields: string[]): Promise<any> {
    const result = { ...data };

    for (const field of sensitiveFields) {
      if (result[field] !== undefined) {
        result[field] = await this.encrypt(result[field]);
      }
    }

    return result;
  }

  /**
   * Decrypt only sensitive fields in an object
   */
  async decryptSensitiveFields(data: any, sensitiveFields: string[]): Promise<any> {
    const result = { ...data };

    for (const field of sensitiveFields) {
      if (result[field] && result[field].encrypted) {
        result[field] = await this.decrypt(result[field]);
      }
    }

    return result;
  }

  /**
   * Generate a secure random key for encryption
   */
  static generateKey(): string {
    const array = new Uint8Array(32);
    crypto.getRandomValues(array);
    return Array.from(array, byte => byte.toString(16).padStart(2, '0')).join('');
  }

  /**
   * Hash a password using PBKDF2
   */
  static async hashPassword(password: string, salt?: string): Promise<string> {
    const encoder = new TextEncoder();
    const passwordBuffer = encoder.encode(password);
    const saltBuffer = encoder.encode(salt || 'BlueBirdHub-Default-Salt');

    const importedKey = await crypto.subtle.importKey(
      'raw',
      passwordBuffer,
      'PBKDF2',
      false,
      ['deriveBits']
    );

    const derivedBits = await crypto.subtle.deriveBits(
      {
        name: 'PBKDF2',
        salt: saltBuffer,
        iterations: 100000,
        hash: 'SHA-256'
      },
      importedKey,
      256
    );

    const hashArray = new Uint8Array(derivedBits);
    return Array.from(hashArray, byte => byte.toString(16).padStart(2, '0')).join('');
  }

  /**
   * Verify a password against a hash
   */
  static async verifyPassword(password: string, hash: string, salt?: string): Promise<boolean> {
    const computedHash = await this.hashPassword(password, salt);
    return computedHash === hash;
  }

  // Utility methods for base64 encoding/decoding

  private arrayBufferToBase64(buffer: ArrayBuffer | Uint8Array): string {
    const bytes = buffer instanceof ArrayBuffer ? new Uint8Array(buffer) : buffer;
    let binary = '';
    for (let i = 0; i < bytes.byteLength; i++) {
      binary += String.fromCharCode(bytes[i]);
    }
    return btoa(binary);
  }

  private base64ToArrayBuffer(base64: string): Uint8Array {
    const binaryString = atob(base64);
    const bytes = new Uint8Array(binaryString.length);
    for (let i = 0; i < binaryString.length; i++) {
      bytes[i] = binaryString.charCodeAt(i);
    }
    return bytes;
  }
}

// Encryption utility functions for common use cases

/**
 * Encrypt user credentials
 */
export const encryptCredentials = async (credentials: any, key: string): Promise<EncryptedData> => {
  const encryption = new AESGCMEncryption(key);
  return await encryption.encrypt(credentials);
};

/**
 * Decrypt user credentials
 */
export const decryptCredentials = async (encryptedCredentials: EncryptedData, key: string): Promise<any> => {
  const encryption = new AESGCMEncryption(key);
  return await encryption.decrypt(encryptedCredentials);
};

/**
 * Encrypt file content
 */
export const encryptFileContent = async (content: ArrayBuffer, key: string): Promise<EncryptedData> => {
  const encryption = new AESGCMEncryption(key);
  // Convert ArrayBuffer to base64 for JSON serialization
  const base64Content = btoa(String.fromCharCode(...new Uint8Array(content)));
  return await encryption.encrypt({ content: base64Content, type: 'file' });
};

/**
 * Decrypt file content
 */
export const decryptFileContent = async (encryptedContent: EncryptedData, key: string): Promise<ArrayBuffer> => {
  const encryption = new AESGCMEncryption(key);
  const decrypted = await encryption.decrypt(encryptedContent);
  // Convert base64 back to ArrayBuffer
  const binaryString = atob(decrypted.content);
  const bytes = new Uint8Array(binaryString.length);
  for (let i = 0; i < binaryString.length; i++) {
    bytes[i] = binaryString.charCodeAt(i);
  }
  return bytes.buffer;
};