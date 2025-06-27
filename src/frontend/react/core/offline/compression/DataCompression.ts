/**
 * Data Compression for Offline Storage Optimization
 * Provides compression/decompression for offline data to save storage space
 */

export interface CompressedData {
  data: string; // Base64 encoded compressed data
  originalSize: number;
  compressedSize: number;
  algorithm: 'gzip' | 'deflate' | 'json-pack';
  compressed: true;
}

export class DataCompression {
  private readonly compressionLevel = 6; // Default compression level

  /**
   * Compress data using the best available algorithm
   */
  async compress(data: any): Promise<CompressedData> {
    const originalJson = JSON.stringify(data);
    const originalSize = new Blob([originalJson]).size;

    // Try different compression methods and pick the best one
    const methods = [
      () => this.compressWithGzip(originalJson),
      () => this.compressWithDeflate(originalJson),
      () => this.compressWithJsonPack(data)
    ];

    let bestResult: CompressedData | null = null;
    let bestRatio = 1;

    for (const method of methods) {
      try {
        const result = await method();
        const ratio = result.compressedSize / originalSize;
        
        if (ratio < bestRatio) {
          bestRatio = ratio;
          bestResult = result;
        }
      } catch (error) {
        console.warn('Compression method failed:', error);
      }
    }

    // If no compression provides benefit, return original data with minimal overhead
    if (!bestResult || bestRatio > 0.95) {
      return {
        data: btoa(originalJson),
        originalSize,
        compressedSize: originalSize,
        algorithm: 'json-pack',
        compressed: true
      };
    }

    return bestResult;
  }

  /**
   * Decompress data based on the algorithm used
   */
  async decompress(compressedData: CompressedData | any): Promise<any> {
    // Check if data is actually compressed
    if (!compressedData.compressed) {
      return compressedData;
    }

    try {
      switch (compressedData.algorithm) {
        case 'gzip':
          return await this.decompressGzip(compressedData);
        case 'deflate':
          return await this.decompressDeflate(compressedData);
        case 'json-pack':
          return this.decompressJsonPack(compressedData);
        default:
          throw new Error(`Unknown compression algorithm: ${compressedData.algorithm}`);
      }
    } catch (error) {
      console.error('Decompression failed:', error);
      throw new Error('Failed to decompress data');
    }
  }

  /**
   * Compress using GZIP (if available in browser)
   */
  private async compressWithGzip(jsonString: string): Promise<CompressedData> {
    if (!('CompressionStream' in window)) {
      throw new Error('CompressionStream not supported');
    }

    const encoder = new TextEncoder();
    const inputBuffer = encoder.encode(jsonString);
    
    const stream = new CompressionStream('gzip');
    const writer = stream.writable.getWriter();
    const reader = stream.readable.getReader();
    
    // Write data to compression stream
    writer.write(inputBuffer);
    writer.close();
    
    // Read compressed data
    const chunks: Uint8Array[] = [];
    let totalSize = 0;
    
    while (true) {
      const { done, value } = await reader.read();
      if (done) break;
      chunks.push(value);
      totalSize += value.length;
    }
    
    // Combine chunks
    const compressedArray = new Uint8Array(totalSize);
    let offset = 0;
    for (const chunk of chunks) {
      compressedArray.set(chunk, offset);
      offset += chunk.length;
    }
    
    return {
      data: this.arrayBufferToBase64(compressedArray),
      originalSize: inputBuffer.length,
      compressedSize: totalSize,
      algorithm: 'gzip',
      compressed: true
    };
  }

  /**
   * Compress using Deflate (if available in browser)
   */
  private async compressWithDeflate(jsonString: string): Promise<CompressedData> {
    if (!('CompressionStream' in window)) {
      throw new Error('CompressionStream not supported');
    }

    const encoder = new TextEncoder();
    const inputBuffer = encoder.encode(jsonString);
    
    const stream = new CompressionStream('deflate');
    const writer = stream.writable.getWriter();
    const reader = stream.readable.getReader();
    
    writer.write(inputBuffer);
    writer.close();
    
    const chunks: Uint8Array[] = [];
    let totalSize = 0;
    
    while (true) {
      const { done, value } = await reader.read();
      if (done) break;
      chunks.push(value);
      totalSize += value.length;
    }
    
    const compressedArray = new Uint8Array(totalSize);
    let offset = 0;
    for (const chunk of chunks) {
      compressedArray.set(chunk, offset);
      offset += chunk.length;
    }
    
    return {
      data: this.arrayBufferToBase64(compressedArray),
      originalSize: inputBuffer.length,
      compressedSize: totalSize,
      algorithm: 'deflate',
      compressed: true
    };
  }

  /**
   * Compress using JSON packing (manual compression technique)
   */
  private compressWithJsonPack(data: any): CompressedData {
    const packed = this.packJson(data);
    const packedString = JSON.stringify(packed);
    const originalSize = JSON.stringify(data).length;
    const compressedSize = packedString.length;
    
    return {
      data: btoa(packedString),
      originalSize,
      compressedSize,
      algorithm: 'json-pack',
      compressed: true
    };
  }

  /**
   * Decompress GZIP data
   */
  private async decompressGzip(compressedData: CompressedData): Promise<any> {
    if (!('DecompressionStream' in window)) {
      throw new Error('DecompressionStream not supported');
    }

    const compressedArray = this.base64ToArrayBuffer(compressedData.data);
    
    const stream = new DecompressionStream('gzip');
    const writer = stream.writable.getWriter();
    const reader = stream.readable.getReader();
    
    writer.write(compressedArray);
    writer.close();
    
    const chunks: Uint8Array[] = [];
    let totalSize = 0;
    
    while (true) {
      const { done, value } = await reader.read();
      if (done) break;
      chunks.push(value);
      totalSize += value.length;
    }
    
    const decompressedArray = new Uint8Array(totalSize);
    let offset = 0;
    for (const chunk of chunks) {
      decompressedArray.set(chunk, offset);
      offset += chunk.length;
    }
    
    const decoder = new TextDecoder();
    const jsonString = decoder.decode(decompressedArray);
    return JSON.parse(jsonString);
  }

  /**
   * Decompress Deflate data
   */
  private async decompressDeflate(compressedData: CompressedData): Promise<any> {
    if (!('DecompressionStream' in window)) {
      throw new Error('DecompressionStream not supported');
    }

    const compressedArray = this.base64ToArrayBuffer(compressedData.data);
    
    const stream = new DecompressionStream('deflate');
    const writer = stream.writable.getWriter();
    const reader = stream.readable.getReader();
    
    writer.write(compressedArray);
    writer.close();
    
    const chunks: Uint8Array[] = [];
    let totalSize = 0;
    
    while (true) {
      const { done, value } = await reader.read();
      if (done) break;
      chunks.push(value);
      totalSize += value.length;
    }
    
    const decompressedArray = new Uint8Array(totalSize);
    let offset = 0;
    for (const chunk of chunks) {
      decompressedArray.set(chunk, offset);
      offset += chunk.length;
    }
    
    const decoder = new TextDecoder();
    const jsonString = decoder.decode(decompressedArray);
    return JSON.parse(jsonString);
  }

  /**
   * Decompress JSON pack data
   */
  private decompressJsonPack(compressedData: CompressedData): any {
    const packedString = atob(compressedData.data);
    const packed = JSON.parse(packedString);
    return this.unpackJson(packed);
  }

  /**
   * Manual JSON compression by removing redundancy
   */
  private packJson(obj: any): any {
    if (Array.isArray(obj)) {
      return obj.map(item => this.packJson(item));
    }
    
    if (obj && typeof obj === 'object') {
      const packed: any = {};
      
      // Common key abbreviations
      const keyMap: Record<string, string> = {
        'id': 'i',
        'name': 'n',
        'title': 't',
        'description': 'd',
        'created_at': 'c',
        'updated_at': 'u',
        'user_id': 'ui',
        'workspace_id': 'wi',
        'status': 's',
        'priority': 'p',
        'is_active': 'a',
        'is_deleted': 'dl',
        'last_modified': 'lm',
        'sync_status': 'ss'
      };
      
      for (const [key, value] of Object.entries(obj)) {
        const shortKey = keyMap[key] || key;
        packed[shortKey] = this.packJson(value);
      }
      
      return packed;
    }
    
    return obj;
  }

  /**
   * Unpack manually compressed JSON
   */
  private unpackJson(packed: any): any {
    if (Array.isArray(packed)) {
      return packed.map(item => this.unpackJson(item));
    }
    
    if (packed && typeof packed === 'object') {
      const unpacked: any = {};
      
      // Reverse key mapping
      const reverseKeyMap: Record<string, string> = {
        'i': 'id',
        'n': 'name',
        't': 'title',
        'd': 'description',
        'c': 'created_at',
        'u': 'updated_at',
        'ui': 'user_id',
        'wi': 'workspace_id',
        's': 'status',
        'p': 'priority',
        'a': 'is_active',
        'dl': 'is_deleted',
        'lm': 'last_modified',
        'ss': 'sync_status'
      };
      
      for (const [shortKey, value] of Object.entries(packed)) {
        const fullKey = reverseKeyMap[shortKey] || shortKey;
        unpacked[fullKey] = this.unpackJson(value);
      }
      
      return unpacked;
    }
    
    return packed;
  }

  /**
   * Estimate compression ratio for data
   */
  estimateCompressionRatio(data: any): number {
    const jsonString = JSON.stringify(data);
    const originalSize = new Blob([jsonString]).size;
    
    // Simple heuristic based on data characteristics
    let estimatedRatio = 0.7; // Default 30% compression
    
    // Text-heavy data compresses better
    const textFields = ['description', 'content', 'notes', 'title'];
    const hasTextFields = textFields.some(field => 
      jsonString.includes(`"${field}"`) && 
      jsonString.includes('":')
    );
    
    if (hasTextFields) {
      estimatedRatio = 0.5; // 50% compression for text-heavy data
    }
    
    // Repetitive data compresses very well
    const uniqueChars = new Set(jsonString).size;
    const repetitionRatio = uniqueChars / jsonString.length;
    
    if (repetitionRatio < 0.1) {
      estimatedRatio = 0.3; // 70% compression for highly repetitive data
    }
    
    return estimatedRatio;
  }

  /**
   * Check if compression is worthwhile for given data
   */
  shouldCompress(data: any): boolean {
    const jsonString = JSON.stringify(data);
    const size = new Blob([jsonString]).size;
    
    // Don't compress small data (< 1KB)
    if (size < 1024) {
      return false;
    }
    
    // Always compress large data (> 10KB)
    if (size > 10240) {
      return true;
    }
    
    // For medium-sized data, check if it's likely to compress well
    const estimatedRatio = this.estimateCompressionRatio(data);
    return estimatedRatio < 0.8; // Compress if we expect >20% savings
  }

  // Utility methods

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

// Utility functions for common compression tasks

/**
 * Compress file content for offline storage
 */
export const compressFileContent = async (content: ArrayBuffer): Promise<CompressedData> => {
  const compression = new DataCompression();
  // Convert ArrayBuffer to base64 for JSON serialization
  const base64Content = btoa(String.fromCharCode(...new Uint8Array(content)));
  return await compression.compress({ content: base64Content, type: 'file' });
};

/**
 * Decompress file content
 */
export const decompressFileContent = async (compressedContent: CompressedData): Promise<ArrayBuffer> => {
  const compression = new DataCompression();
  const decompressed = await compression.decompress(compressedContent);
  // Convert base64 back to ArrayBuffer
  const binaryString = atob(decompressed.content);
  const bytes = new Uint8Array(binaryString.length);
  for (let i = 0; i < binaryString.length; i++) {
    bytes[i] = binaryString.charCodeAt(i);
  }
  return bytes.buffer;
};