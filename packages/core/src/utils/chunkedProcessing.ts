export interface ChunkProcessingOptions {
  chunkSize?: number;
  delayBetweenChunks?: number;
  maxConcurrent?: number;
  onProgress?: (completed: number, total: number) => void;
  onError?: (error: Error, item: any, index: number) => void;
  signal?: AbortSignal;
}

export interface ChunkResult<T, R> {
  results: R[];
  errors: Array<{ error: Error; item: T; index: number }>;
  cancelled: boolean;
}

export class ChunkedProcessor {
  static async processArray<T, R>(
    items: T[],
    processor: (item: T, index: number) => Promise<R>,
    options: ChunkProcessingOptions = {}
  ): Promise<ChunkResult<T, R>> {
    const {
      chunkSize = 50,
      delayBetweenChunks = 0,
      maxConcurrent = 5,
      onProgress,
      onError,
      signal
    } = options;

    const results: R[] = [];
    const errors: Array<{ error: Error; item: T; index: number }> = [];
    let completed = 0;

    if (signal?.aborted) {
      return { results: [], errors: [], cancelled: true };
    }

    for (let i = 0; i < items.length; i += chunkSize) {
      if (signal?.aborted) {
        return { results, errors, cancelled: true };
      }

      const chunk = items.slice(i, i + chunkSize);
      const chunkPromises = chunk.map(async (item, chunkIndex) => {
        const actualIndex = i + chunkIndex;
        try {
          const result = await processor(item, actualIndex);
          completed++;
          onProgress?.(completed, items.length);
          return { success: true, result, index: actualIndex };
        } catch (error) {
          const err = error instanceof Error ? error : new Error(String(error));
          errors.push({ error: err, item, index: actualIndex });
          onError?.(err, item, actualIndex);
          completed++;
          onProgress?.(completed, items.length);
          return { success: false, error: err, index: actualIndex };
        }
      });

      const chunkResults = await this.limitConcurrency(chunkPromises, maxConcurrent);
      
      chunkResults.forEach(result => {
        if (result.success && result.result !== undefined) {
          results[result.index] = result.result;
        }
      });

      if (delayBetweenChunks > 0 && i + chunkSize < items.length) {
        await this.delay(delayBetweenChunks);
      }
    }

    return { results: results.filter(r => r !== undefined), errors, cancelled: false };
  }

  static async processArraySync<T, R>(
    items: T[],
    processor: (item: T, index: number) => R,
    options: Omit<ChunkProcessingOptions, 'maxConcurrent'> = {}
  ): Promise<ChunkResult<T, R>> {
    const {
      chunkSize = 100,
      delayBetweenChunks = 0,
      onProgress,
      onError,
      signal
    } = options;

    const results: R[] = [];
    const errors: Array<{ error: Error; item: T; index: number }> = [];
    let completed = 0;

    if (signal?.aborted) {
      return { results: [], errors: [], cancelled: true };
    }

    for (let i = 0; i < items.length; i += chunkSize) {
      if (signal?.aborted) {
        return { results, errors, cancelled: true };
      }

      const chunk = items.slice(i, i + chunkSize);
      
      for (let j = 0; j < chunk.length; j++) {
        const item = chunk[j];
        const actualIndex = i + j;
        
        try {
          const result = processor(item, actualIndex);
          results[actualIndex] = result;
          completed++;
          onProgress?.(completed, items.length);
        } catch (error) {
          const err = error instanceof Error ? error : new Error(String(error));
          errors.push({ error: err, item, index: actualIndex });
          onError?.(err, item, actualIndex);
          completed++;
          onProgress?.(completed, items.length);
        }
      }

      if (delayBetweenChunks > 0 && i + chunkSize < items.length) {
        await this.delay(delayBetweenChunks);
      }
    }

    return { results: results.filter(r => r !== undefined), errors, cancelled: false };
  }

  static async groupItemsChunked<T>(
    items: T[],
    groupBy: (item: T) => string,
    options: Omit<ChunkProcessingOptions, 'maxConcurrent'> = {}
  ): Promise<{ [key: string]: T[] }> {
    const grouped: { [key: string]: T[] } = {};
    
    const result = await this.processArraySync(
      items,
      (item) => {
        const key = groupBy(item);
        if (!grouped[key]) {
          grouped[key] = [];
        }
        grouped[key].push(item);
        return item;
      },
      options
    );

    if (result.cancelled) {
      return {};
    }

    return grouped;
  }

  static async sortItemsChunked<T>(
    items: T[],
    compareFn: (a: T, b: T) => number,
    options: Omit<ChunkProcessingOptions, 'maxConcurrent'> = {}
  ): Promise<T[]> {
    const { chunkSize = 1000, signal } = options;

    if (signal?.aborted) {
      return [];
    }

    // For small arrays, use native sort
    if (items.length <= chunkSize) {
      return [...items].sort(compareFn);
    }

    // For large arrays, use merge sort approach
    const chunks: T[][] = [];
    
    for (let i = 0; i < items.length; i += chunkSize) {
      if (signal?.aborted) {
        return [];
      }
      
      const chunk = items.slice(i, i + chunkSize);
      chunks.push([...chunk].sort(compareFn));
      
      await this.delay(0); // Yield to event loop
    }

    // Merge sorted chunks
    return this.mergeSortedChunks(chunks, compareFn, signal);
  }

  private static async mergeSortedChunks<T>(
    chunks: T[][],
    compareFn: (a: T, b: T) => number,
    signal?: AbortSignal
  ): Promise<T[]> {
    while (chunks.length > 1) {
      if (signal?.aborted) {
        return [];
      }

      const newChunks: T[][] = [];
      
      for (let i = 0; i < chunks.length; i += 2) {
        if (i + 1 < chunks.length) {
          newChunks.push(this.mergeSorted(chunks[i], chunks[i + 1], compareFn));
        } else {
          newChunks.push(chunks[i]);
        }
      }
      
      chunks = newChunks;
      await this.delay(0); // Yield to event loop
    }

    return chunks[0] || [];
  }

  private static mergeSorted<T>(
    arr1: T[],
    arr2: T[],
    compareFn: (a: T, b: T) => number
  ): T[] {
    const result: T[] = [];
    let i = 0, j = 0;

    while (i < arr1.length && j < arr2.length) {
      if (compareFn(arr1[i], arr2[j]) <= 0) {
        result.push(arr1[i]);
        i++;
      } else {
        result.push(arr2[j]);
        j++;
      }
    }

    while (i < arr1.length) {
      result.push(arr1[i]);
      i++;
    }

    while (j < arr2.length) {
      result.push(arr2[j]);
      j++;
    }

    return result;
  }

  private static async limitConcurrency<T>(
    promises: Promise<T>[],
    maxConcurrent: number
  ): Promise<T[]> {
    const results: T[] = [];
    
    for (let i = 0; i < promises.length; i += maxConcurrent) {
      const batch = promises.slice(i, i + maxConcurrent);
      const batchResults = await Promise.all(batch);
      results.push(...batchResults);
    }
    
    return results;
  }

  private static delay(ms: number): Promise<void> {
    return new Promise(resolve => setTimeout(resolve, ms));
  }
}

export default ChunkedProcessor;