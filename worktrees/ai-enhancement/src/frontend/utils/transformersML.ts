/**
 * Transformers.js Integration for OrdnungsHub
 * Local Machine Learning Pipeline for privacy-focused AI processing
 */

// Note: Since @xenova/transformers is not yet available, we'll create a framework-ready implementation
// that can be easily swapped when the library becomes available

interface MLModel {
  name: string;
  task: string;
  loaded: boolean;
  modelUrl?: string;
}

interface EmbeddingResult {
  embedding: number[];
  dimensions: number;
  processingTime: number;
}

interface ClassificationResult {
  label: string;
  confidence: number;
  allScores: Array<{ label: string; score: number }>;
}

interface SimilarityResult {
  similarity: number;
  distance: number;
  method: 'cosine' | 'euclidean' | 'manhattan';
}

class TransformersMLPipeline {
  private models: Map<string, MLModel> = new Map();
  private embeddings_cache: Map<string, EmbeddingResult> = new Map();
  private isInitialized = false;
  private worker: Worker | null = null;

  constructor() {
    this.setupAvailableModels();
  }

  private setupAvailableModels() {
    // Framework for models - will be implemented when Transformers.js is available
    const availableModels: MLModel[] = [
      {
        name: 'sentence-transformer',
        task: 'feature-extraction',
        loaded: false,
        modelUrl: 'Xenova/all-MiniLM-L6-v2'
      },
      {
        name: 'text-classifier',
        task: 'text-classification',
        loaded: false,
        modelUrl: 'Xenova/distilbert-base-uncased-finetuned-sst-2-english'
      },
      {
        name: 'document-classifier',
        task: 'zero-shot-classification',
        loaded: false,
        modelUrl: 'Xenova/distilbert-base-uncased-mnli'
      }
    ];

    availableModels.forEach(model => {
      this.models.set(model.name, model);
    });
  }

  async initialize(): Promise<boolean> {
    if (this.isInitialized) {
      return true;
    }

    try {
      // Initialize Web Worker for ML processing (prevents UI blocking)
      this.worker = new Worker(
        new URL('./transformersWorker.ts', import.meta.url),
        { type: 'module' }
      );

      // Setup worker communication
      this.setupWorkerCommunication();

      console.log('🤖 TransformersML Pipeline initialized');
      this.isInitialized = true;
      return true;

    } catch (error) {
      console.error('Failed to initialize TransformersML:', error);
      return false;
    }
  }

  private setupWorkerCommunication() {
    if (!this.worker) return;

    this.worker.onmessage = (event) => {
      const { type, data, error, requestId } = event.data;

      if (error) {
        console.error('ML Worker Error:', error);
        return;
      }

      // Handle different response types
      switch (type) {
        case 'model-loaded':
          this.handleModelLoaded(data);
          break;
        case 'embedding-result':
          this.handleEmbeddingResult(data, requestId);
          break;
        case 'classification-result':
          this.handleClassificationResult(data, requestId);
          break;
      }
    };
  }

  private handleModelLoaded(data: { modelName: string }) {
    const model = this.models.get(data.modelName);
    if (model) {
      model.loaded = true;
      console.log(`✅ Model loaded: ${data.modelName}`);
    }
  }

  private handleEmbeddingResult(data: EmbeddingResult, requestId: string) {
    // Cache the result
    this.embeddings_cache.set(requestId, data);
    
    // Resolve pending promise (would be implemented with Promise resolution)
    console.log(`📊 Embedding computed: ${data.dimensions}D vector in ${data.processingTime}ms`);
  }

  private handleClassificationResult(data: ClassificationResult, requestId: string) {
    console.log(`🏷️ Classification: ${data.label} (${(data.confidence * 100).toFixed(1)}%)`);
  }

  async loadModel(modelName: string): Promise<boolean> {
    if (!this.isInitialized) {
      await this.initialize();
    }

    const model = this.models.get(modelName);
    if (!model) {
      throw new Error(`Model not found: ${modelName}`);
    }

    if (model.loaded) {
      return true;
    }

    try {
      // Send load request to worker
      this.worker?.postMessage({
        type: 'load-model',
        modelName: modelName,
        modelUrl: model.modelUrl,
        task: model.task
      });

      // In real implementation, this would return a Promise that resolves when model is loaded
      return true;

    } catch (error) {
      console.error(`Failed to load model ${modelName}:`, error);
      return false;
    }
  }

  async generateEmbedding(text: string, useCache: boolean = true): Promise<EmbeddingResult> {
    // Check cache first
    if (useCache) {
      const cacheKey = this.hashText(text);
      const cached = this.embeddings_cache.get(cacheKey);
      if (cached) {
        return cached;
      }
    }

    if (!this.isInitialized) {
      await this.initialize();
    }

    // Ensure sentence transformer is loaded
    await this.loadModel('sentence-transformer');

    const startTime = performance.now();

    try {
      // For now, create a mock embedding (will be replaced with real Transformers.js)
      const mockEmbedding = this.generateMockEmbedding(text);
      
      const result: EmbeddingResult = {
        embedding: mockEmbedding,
        dimensions: mockEmbedding.length,
        processingTime: performance.now() - startTime
      };

      // Cache the result
      if (useCache) {
        const cacheKey = this.hashText(text);
        this.embeddings_cache.set(cacheKey, result);
      }

      return result;

    } catch (error) {
      console.error('Embedding generation failed:', error);
      throw error;
    }
  }

  async classifyText(text: string, labels: string[]): Promise<ClassificationResult> {
    if (!this.isInitialized) {
      await this.initialize();
    }

    // Ensure classifier is loaded
    await this.loadModel('document-classifier');

    try {
      // For now, create a mock classification (will be replaced with real Transformers.js)
      const mockResult = this.generateMockClassification(text, labels);
      
      return mockResult;

    } catch (error) {
      console.error('Text classification failed:', error);
      throw error;
    }
  }

  async calculateSimilarity(
    embedding1: number[], 
    embedding2: number[], 
    method: 'cosine' | 'euclidean' | 'manhattan' = 'cosine'
  ): Promise<SimilarityResult> {
    
    if (embedding1.length !== embedding2.length) {
      throw new Error('Embeddings must have the same dimensions');
    }

    let similarity: number;
    let distance: number;

    switch (method) {
      case 'cosine':
        similarity = this.cosineSimilarity(embedding1, embedding2);
        distance = 1 - similarity;
        break;
      
      case 'euclidean':
        distance = this.euclideanDistance(embedding1, embedding2);
        similarity = 1 / (1 + distance);
        break;
      
      case 'manhattan':
        distance = this.manhattanDistance(embedding1, embedding2);
        similarity = 1 / (1 + distance);
        break;
      
      default:
        throw new Error(`Unknown similarity method: ${method}`);
    }

    return { similarity, distance, method };
  }

  async findSimilarTexts(
    queryEmbedding: number[], 
    documentEmbeddings: Array<{ id: string; embedding: number[]; metadata?: any }>,
    topK: number = 5
  ): Promise<Array<{ id: string; similarity: number; metadata?: any }>> {
    
    const similarities = await Promise.all(
      documentEmbeddings.map(async (doc) => {
        const simResult = await this.calculateSimilarity(queryEmbedding, doc.embedding);
        return {
          id: doc.id,
          similarity: simResult.similarity,
          metadata: doc.metadata
        };
      })
    );

    // Sort by similarity (descending) and return top K
    return similarities
      .sort((a, b) => b.similarity - a.similarity)
      .slice(0, topK);
  }

  async categorizeDocument(
    content: string, 
    categories: string[] = ['work', 'personal', 'finance', 'education', 'creative']
  ): Promise<ClassificationResult> {
    
    return await this.classifyText(content, categories);
  }

  async extractKeyTopics(
    content: string, 
    numTopics: number = 5
  ): Promise<Array<{ topic: string; confidence: number }>> {
    
    // This would use topic modeling in real implementation
    // For now, return mock topics based on content analysis
    const words = content.toLowerCase().split(/\s+/);
    const wordFreq = new Map<string, number>();
    
    // Count word frequencies
    words.forEach(word => {
      if (word.length > 3) {
        wordFreq.set(word, (wordFreq.get(word) || 0) + 1);
      }
    });

    // Get top words as topics
    const sortedWords = Array.from(wordFreq.entries())
      .sort((a, b) => b[1] - a[1])
      .slice(0, numTopics);

    return sortedWords.map(([word, freq]) => ({
      topic: word,
      confidence: Math.min(freq / words.length * 10, 1.0)
    }));
  }

  // Utility methods

  private hashText(text: string): string {
    // Simple hash function for caching
    let hash = 0;
    for (let i = 0; i < text.length; i++) {
      const char = text.charCodeAt(i);
      hash = ((hash << 5) - hash) + char;
      hash = hash & hash;
    }
    return hash.toString();
  }

  private generateMockEmbedding(text: string): number[] {
    // Generate a deterministic mock embedding based on text content
    const dimensions = 384; // Common embedding size
    const embedding = new Array(dimensions);
    
    // Use text hash to generate consistent values
    const hash = this.hashText(text);
    const seed = parseInt(hash, 10);
    
    // Simple pseudo-random number generator
    let random = seed;
    for (let i = 0; i < dimensions; i++) {
      random = (random * 9301 + 49297) % 233280;
      embedding[i] = (random / 233280) * 2 - 1; // Range: -1 to 1
    }
    
    // Normalize the vector
    const magnitude = Math.sqrt(embedding.reduce((sum, val) => sum + val * val, 0));
    return embedding.map(val => val / magnitude);
  }

  private generateMockClassification(text: string, labels: string[]): ClassificationResult {
    // Generate mock classification scores based on keyword matching
    const textLower = text.toLowerCase();
    const scores = labels.map(label => {
      const labelLower = label.toLowerCase();
      const matches = (textLower.match(new RegExp(labelLower, 'g')) || []).length;
      const score = Math.min(matches / 10 + Math.random() * 0.3, 1.0);
      return { label, score };
    });

    // Sort by score
    scores.sort((a, b) => b.score - a.score);
    
    // Normalize scores
    const totalScore = scores.reduce((sum, s) => sum + s.score, 0);
    const normalizedScores = scores.map(s => ({
      label: s.label,
      score: totalScore > 0 ? s.score / totalScore : 1 / scores.length
    }));

    return {
      label: normalizedScores[0].label,
      confidence: normalizedScores[0].score,
      allScores: normalizedScores
    };
  }

  private cosineSimilarity(a: number[], b: number[]): number {
    const dotProduct = a.reduce((sum, val, i) => sum + val * b[i], 0);
    const magnitudeA = Math.sqrt(a.reduce((sum, val) => sum + val * val, 0));
    const magnitudeB = Math.sqrt(b.reduce((sum, val) => sum + val * val, 0));
    
    return dotProduct / (magnitudeA * magnitudeB);
  }

  private euclideanDistance(a: number[], b: number[]): number {
    return Math.sqrt(a.reduce((sum, val, i) => sum + Math.pow(val - b[i], 2), 0));
  }

  private manhattanDistance(a: number[], b: number[]): number {
    return a.reduce((sum, val, i) => sum + Math.abs(val - b[i]), 0);
  }

  getStatus() {
    return {
      initialized: this.isInitialized,
      modelsLoaded: Array.from(this.models.values()).filter(m => m.loaded).length,
      totalModels: this.models.size,
      cacheSize: this.embeddings_cache.size,
      workerActive: this.worker !== null
    };
  }

  clearCache() {
    this.embeddings_cache.clear();
    console.log('🗑️ ML embeddings cache cleared');
  }

  async cleanup() {
    if (this.worker) {
      this.worker.terminate();
      this.worker = null;
    }
    this.clearCache();
    this.isInitialized = false;
    console.log('🧹 TransformersML Pipeline cleaned up');
  }
}

// Global ML pipeline instance
export const mlPipeline = new TransformersMLPipeline();

// React hook for ML operations
export function useTransformersML() {
  const [isReady, setIsReady] = React.useState(false);
  const [status, setStatus] = React.useState<any>(null);

  React.useEffect(() => {
    const initializePipeline = async () => {
      try {
        const success = await mlPipeline.initialize();
        setIsReady(success);
        setStatus(mlPipeline.getStatus());
      } catch (error) {
        console.error('Failed to initialize ML pipeline:', error);
        setIsReady(false);
      }
    };

    initializePipeline();

    return () => {
      mlPipeline.cleanup();
    };
  }, []);

  const generateEmbedding = React.useCallback(async (text: string) => {
    if (!isReady) throw new Error('ML pipeline not ready');
    return await mlPipeline.generateEmbedding(text);
  }, [isReady]);

  const classifyText = React.useCallback(async (text: string, labels: string[]) => {
    if (!isReady) throw new Error('ML pipeline not ready');
    return await mlPipeline.classifyText(text, labels);
  }, [isReady]);

  const findSimilarTexts = React.useCallback(async (
    queryEmbedding: number[],
    documents: Array<{ id: string; embedding: number[]; metadata?: any }>,
    topK: number = 5
  ) => {
    if (!isReady) throw new Error('ML pipeline not ready');
    return await mlPipeline.findSimilarTexts(queryEmbedding, documents, topK);
  }, [isReady]);

  return {
    isReady,
    status,
    generateEmbedding,
    classifyText,
    findSimilarTexts,
    categorizeDocument: mlPipeline.categorizeDocument.bind(mlPipeline),
    extractKeyTopics: mlPipeline.extractKeyTopics.bind(mlPipeline),
    clearCache: mlPipeline.clearCache.bind(mlPipeline)
  };
}

export default TransformersMLPipeline;