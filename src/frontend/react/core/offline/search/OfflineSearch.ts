/**
 * Offline Search Engine with Local Indexes
 * Provides fast, full-text search capabilities for offline data
 */

import { offlineStorage, EntityType, SearchIndexItem } from '../OfflineStorage';
import Fuse from 'fuse.js';

export interface SearchQuery {
  query: string;
  entityTypes?: EntityType[];
  filters?: SearchFilters;
  options?: SearchOptions;
}

export interface SearchFilters {
  userId?: number;
  workspaceId?: string;
  status?: string;
  priority?: string;
  dateRange?: {
    start: number;
    end: number;
  };
  tags?: string[];
  category?: string;
  isDeleted?: boolean;
  syncStatus?: string;
}

export interface SearchOptions {
  limit?: number;
  offset?: number;
  sortBy?: 'relevance' | 'date' | 'name' | 'modified';
  sortOrder?: 'asc' | 'desc';
  fuzzy?: boolean;
  threshold?: number; // Fuzzy search threshold (0-1)
  includeHighlights?: boolean;
  includeSnippets?: boolean;
}

export interface SearchResult {
  id: string;
  entityType: EntityType;
  entityId: string | number;
  title: string;
  content: string;
  relevanceScore: number;
  highlights?: string[];
  snippet?: string;
  metadata?: any;
  lastModified: number;
}

export interface SearchResponse {
  results: SearchResult[];
  totalCount: number;
  queryTime: number;
  suggestions?: string[];
  facets?: SearchFacets;
}

export interface SearchFacets {
  entityTypes: Array<{ type: EntityType; count: number }>;
  categories: Array<{ category: string; count: number }>;
  statuses: Array<{ status: string; count: number }>;
  dateRanges: Array<{ range: string; count: number }>;
}

export interface IndexStats {
  totalDocuments: number;
  documentsPerType: Record<EntityType, number>;
  lastIndexed: number;
  indexSize: number;
  searchLatency: number;
}

/**
 * Offline search engine with advanced indexing
 */
export class OfflineSearch {
  private indexes: Map<EntityType, Fuse<any>> = new Map();
  private invertedIndex: Map<string, Set<string>> = new Map();
  private documentStore: Map<string, any> = new Map();
  private lastIndexUpdate = 0;
  private isIndexing = false;
  private searchHistory: string[] = [];
  private popularQueries: Map<string, number> = new Map();

  constructor() {
    this.initializeIndexes();
  }

  /**
   * Initialize search indexes
   */
  async initialize(): Promise<void> {
    try {
      await this.buildIndexes();
      this.scheduleIndexMaintenance();
      console.log('✅ Offline search initialized');
    } catch (error) {
      console.error('Failed to initialize offline search:', error);
    }
  }

  /**
   * Perform search across all or specific entity types
   */
  async search(searchQuery: SearchQuery): Promise<SearchResponse> {
    const startTime = Date.now();
    const { query, entityTypes, filters, options } = searchQuery;

    try {
      // Record search for analytics
      this.recordSearch(query);

      // Get search results
      const results = await this.performSearch(query, entityTypes, filters, options);

      // Calculate facets if needed
      const facets = this.calculateFacets(results);

      // Generate suggestions
      const suggestions = this.generateSuggestions(query);

      const queryTime = Date.now() - startTime;

      return {
        results: results.slice(options?.offset || 0, (options?.offset || 0) + (options?.limit || 50)),
        totalCount: results.length,
        queryTime,
        suggestions,
        facets
      };

    } catch (error) {
      console.error('Search failed:', error);
      return {
        results: [],
        totalCount: 0,
        queryTime: Date.now() - startTime,
        suggestions: []
      };
    }
  }

  /**
   * Perform the actual search operation
   */
  private async performSearch(
    query: string,
    entityTypes?: EntityType[],
    filters?: SearchFilters,
    options?: SearchOptions
  ): Promise<SearchResult[]> {
    const results: SearchResult[] = [];
    const normalizedQuery = this.normalizeQuery(query);

    // Determine which entity types to search
    const typesToSearch = entityTypes || Object.values(EntityType);

    // Search using Fuse.js for fuzzy matching
    if (options?.fuzzy !== false) {
      for (const entityType of typesToSearch) {
        const index = this.indexes.get(entityType);
        if (index) {
          const fuseResults = index.search(normalizedQuery, {
            limit: options?.limit || 100
          });

          for (const fuseResult of fuseResults) {
            const searchResult = await this.createSearchResult(
              fuseResult.item,
              entityType,
              fuseResult.score || 0,
              query,
              options
            );

            if (searchResult && this.matchesFilters(searchResult, filters)) {
              results.push(searchResult);
            }
          }
        }
      }
    }

    // Also search using inverted index for exact matches
    const exactResults = await this.searchInvertedIndex(normalizedQuery, typesToSearch, filters, options);
    
    // Merge results, preferring exact matches
    const mergedResults = this.mergeSearchResults(results, exactResults);

    // Sort results
    return this.sortSearchResults(mergedResults, options?.sortBy, options?.sortOrder);
  }

  /**
   * Search using inverted index for exact term matching
   */
  private async searchInvertedIndex(
    query: string,
    entityTypes: EntityType[],
    filters?: SearchFilters,
    options?: SearchOptions
  ): Promise<SearchResult[]> {
    const results: SearchResult[] = [];
    const queryTerms = this.tokenize(query);

    // Find documents containing query terms
    const matchingDocIds = new Set<string>();
    
    for (const term of queryTerms) {
      const docIds = this.invertedIndex.get(term);
      if (docIds) {
        if (matchingDocIds.size === 0) {
          // First term - add all matching docs
          docIds.forEach(id => matchingDocIds.add(id));
        } else {
          // Subsequent terms - intersection (AND operation)
          const intersection = new Set([...matchingDocIds].filter(id => docIds.has(id)));
          matchingDocIds.clear();
          intersection.forEach(id => matchingDocIds.add(id));
        }
      }
    }

    // Convert document IDs to search results
    for (const docId of matchingDocIds) {
      const doc = this.documentStore.get(docId);
      if (doc && entityTypes.includes(doc.entityType)) {
        const searchResult = await this.createSearchResult(
          doc,
          doc.entityType,
          1.0, // High relevance for exact matches
          query,
          options
        );

        if (searchResult && this.matchesFilters(searchResult, filters)) {
          results.push(searchResult);
        }
      }
    }

    return results;
  }

  /**
   * Create a search result from indexed document
   */
  private async createSearchResult(
    doc: any,
    entityType: EntityType,
    score: number,
    query: string,
    options?: SearchOptions
  ): Promise<SearchResult | null> {
    try {
      // Get the actual entity data
      const entity = await offlineStorage.get(entityType, doc.entityId);
      if (!entity || entity.isDeleted) {
        return null;
      }

      const title = this.extractTitle(entity, entityType);
      const content = this.extractContent(entity, entityType);

      const result: SearchResult = {
        id: `${entityType}_${doc.entityId}`,
        entityType,
        entityId: doc.entityId,
        title,
        content,
        relevanceScore: 1 - score, // Fuse.js returns lower scores for better matches
        lastModified: entity.lastModified
      };

      // Add highlights if requested
      if (options?.includeHighlights) {
        result.highlights = this.generateHighlights(content, query);
      }

      // Add snippet if requested
      if (options?.includeSnippets) {
        result.snippet = this.generateSnippet(content, query);
      }

      // Add metadata
      result.metadata = {
        status: entity.status,
        priority: entity.priority,
        category: entity.category || entity.ai_category,
        tags: entity.tags || [],
        userId: entity.user_id,
        workspaceId: entity.workspace_id
      };

      return result;

    } catch (error) {
      console.error('Failed to create search result:', error);
      return null;
    }
  }

  /**
   * Build or rebuild search indexes
   */
  async buildIndexes(): Promise<void> {
    if (this.isIndexing) return;

    this.isIndexing = true;
    const startTime = Date.now();

    try {
      console.log('🔍 Building search indexes...');

      // Clear existing indexes
      this.indexes.clear();
      this.invertedIndex.clear();
      this.documentStore.clear();

      // Build indexes for each entity type
      for (const entityType of Object.values(EntityType)) {
        await this.buildEntityTypeIndex(entityType);
      }

      this.lastIndexUpdate = Date.now();
      const indexTime = Date.now() - startTime;
      
      console.log(`✅ Search indexes built in ${indexTime}ms`);

    } catch (error) {
      console.error('Failed to build search indexes:', error);
    } finally {
      this.isIndexing = false;
    }
  }

  /**
   * Build index for a specific entity type
   */
  private async buildEntityTypeIndex(entityType: EntityType): Promise<void> {
    try {
      const entities = await offlineStorage.getAll(entityType);
      const searchableEntities = entities.filter(entity => !entity.isDeleted);

      if (searchableEntities.length === 0) return;

      // Configure Fuse.js options based on entity type
      const fuseOptions = this.getFuseOptions(entityType);
      
      // Create searchable documents
      const documents = searchableEntities.map(entity => {
        const doc = this.createSearchableDocument(entity, entityType);
        
        // Store document for retrieval
        const docId = `${entityType}_${entity.id}`;
        this.documentStore.set(docId, {
          ...doc,
          entityType,
          entityId: entity.id
        });

        // Update inverted index
        this.updateInvertedIndex(doc.searchableText, docId);

        return doc;
      });

      // Create Fuse index
      const fuseIndex = new Fuse(documents, fuseOptions);
      this.indexes.set(entityType, fuseIndex);

      console.log(`📄 Indexed ${documents.length} ${entityType} documents`);

    } catch (error) {
      console.error(`Failed to build index for ${entityType}:`, error);
    }
  }

  /**
   * Update inverted index with document terms
   */
  private updateInvertedIndex(text: string, docId: string): void {
    const terms = this.tokenize(text);
    
    for (const term of terms) {
      if (!this.invertedIndex.has(term)) {
        this.invertedIndex.set(term, new Set());
      }
      this.invertedIndex.get(term)!.add(docId);
    }
  }

  /**
   * Create searchable document from entity
   */
  private createSearchableDocument(entity: any, entityType: EntityType): any {
    const title = this.extractTitle(entity, entityType);
    const content = this.extractContent(entity, entityType);
    const keywords = this.extractKeywords(entity, entityType);

    return {
      id: entity.id,
      title,
      content,
      searchableText: `${title} ${content} ${keywords.join(' ')}`.toLowerCase(),
      keywords,
      category: entity.category || entity.ai_category || '',
      status: entity.status || '',
      priority: entity.priority || '',
      lastModified: entity.lastModified,
      userId: entity.user_id,
      workspaceId: entity.workspace_id
    };
  }

  /**
   * Extract title from entity based on type
   */
  private extractTitle(entity: any, entityType: EntityType): string {
    switch (entityType) {
      case EntityType.WORKSPACE:
        return entity.name || '';
      case EntityType.TASK:
        return entity.title || '';
      case EntityType.FILE:
        return entity.file_name || '';
      default:
        return entity.name || entity.title || '';
    }
  }

  /**
   * Extract content from entity based on type
   */
  private extractContent(entity: any, entityType: EntityType): string {
    const content = [];
    
    if (entity.description) content.push(entity.description);
    if (entity.ai_description) content.push(entity.ai_description);
    if (entity.user_description) content.push(entity.user_description);
    if (entity.content) content.push(entity.content);
    
    return content.join(' ');
  }

  /**
   * Extract keywords from entity
   */
  private extractKeywords(entity: any, entityType: EntityType): string[] {
    const keywords = [];
    
    if (entity.tags) keywords.push(...entity.tags);
    if (entity.ai_tags) keywords.push(...entity.ai_tags.split(','));
    if (entity.keywords) keywords.push(...entity.keywords);
    if (entity.category) keywords.push(entity.category);
    if (entity.ai_category) keywords.push(entity.ai_category);
    
    return keywords.filter(k => k && k.length > 0);
  }

  /**
   * Get Fuse.js configuration for entity type
   */
  private getFuseOptions(entityType: EntityType): any {
    const baseOptions = {
      includeScore: true,
      threshold: 0.3,
      ignoreLocation: true,
      minMatchCharLength: 2
    };

    switch (entityType) {
      case EntityType.WORKSPACE:
        return {
          ...baseOptions,
          keys: [
            { name: 'title', weight: 2 },
            { name: 'content', weight: 1 },
            { name: 'keywords', weight: 1.5 }
          ]
        };

      case EntityType.TASK:
        return {
          ...baseOptions,
          keys: [
            { name: 'title', weight: 2 },
            { name: 'content', weight: 1 },
            { name: 'keywords', weight: 1.5 },
            { name: 'status', weight: 0.5 },
            { name: 'priority', weight: 0.5 }
          ]
        };

      case EntityType.FILE:
        return {
          ...baseOptions,
          keys: [
            { name: 'title', weight: 2 },
            { name: 'content', weight: 1 },
            { name: 'keywords', weight: 1.5 },
            { name: 'category', weight: 1 }
          ]
        };

      default:
        return {
          ...baseOptions,
          keys: [
            { name: 'title', weight: 2 },
            { name: 'content', weight: 1 },
            { name: 'searchableText', weight: 0.5 }
          ]
        };
    }
  }

  /**
   * Normalize search query
   */
  private normalizeQuery(query: string): string {
    return query.trim().toLowerCase();
  }

  /**
   * Tokenize text into searchable terms
   */
  private tokenize(text: string): string[] {
    return text
      .toLowerCase()
      .replace(/[^\w\s]/g, ' ')
      .split(/\s+/)
      .filter(term => term.length > 2);
  }

  /**
   * Check if search result matches filters
   */
  private matchesFilters(result: SearchResult, filters?: SearchFilters): boolean {
    if (!filters) return true;

    if (filters.userId && result.metadata?.userId !== filters.userId) return false;
    if (filters.workspaceId && result.metadata?.workspaceId !== filters.workspaceId) return false;
    if (filters.status && result.metadata?.status !== filters.status) return false;
    if (filters.priority && result.metadata?.priority !== filters.priority) return false;
    if (filters.category && result.metadata?.category !== filters.category) return false;
    
    if (filters.dateRange) {
      if (result.lastModified < filters.dateRange.start || 
          result.lastModified > filters.dateRange.end) {
        return false;
      }
    }

    if (filters.tags && filters.tags.length > 0) {
      const resultTags = result.metadata?.tags || [];
      if (!filters.tags.some(tag => resultTags.includes(tag))) {
        return false;
      }
    }

    return true;
  }

  /**
   * Merge and deduplicate search results
   */
  private mergeSearchResults(fuzzyResults: SearchResult[], exactResults: SearchResult[]): SearchResult[] {
    const resultMap = new Map<string, SearchResult>();

    // Add exact results first (higher priority)
    for (const result of exactResults) {
      resultMap.set(result.id, result);
    }

    // Add fuzzy results if not already present
    for (const result of fuzzyResults) {
      if (!resultMap.has(result.id)) {
        resultMap.set(result.id, result);
      }
    }

    return Array.from(resultMap.values());
  }

  /**
   * Sort search results
   */
  private sortSearchResults(
    results: SearchResult[],
    sortBy: string = 'relevance',
    sortOrder: string = 'desc'
  ): SearchResult[] {
    return results.sort((a, b) => {
      let comparison = 0;

      switch (sortBy) {
        case 'relevance':
          comparison = b.relevanceScore - a.relevanceScore;
          break;
        case 'date':
        case 'modified':
          comparison = b.lastModified - a.lastModified;
          break;
        case 'name':
          comparison = a.title.localeCompare(b.title);
          break;
        default:
          comparison = b.relevanceScore - a.relevanceScore;
      }

      return sortOrder === 'asc' ? -comparison : comparison;
    });
  }

  /**
   * Generate search highlights
   */
  private generateHighlights(content: string, query: string): string[] {
    const highlights = [];
    const queryTerms = this.tokenize(query);
    
    for (const term of queryTerms) {
      const regex = new RegExp(`\\b${term}\\b`, 'gi');
      const matches = content.match(regex);
      if (matches) {
        highlights.push(...matches);
      }
    }

    return [...new Set(highlights)]; // Remove duplicates
  }

  /**
   * Generate search snippet
   */
  private generateSnippet(content: string, query: string, maxLength = 200): string {
    const queryTerms = this.tokenize(query);
    const sentences = content.split(/[.!?]+/).filter(s => s.trim().length > 0);
    
    // Find sentence containing query terms
    for (const sentence of sentences) {
      const sentenceLower = sentence.toLowerCase();
      if (queryTerms.some(term => sentenceLower.includes(term))) {
        if (sentence.length <= maxLength) {
          return sentence.trim();
        } else {
          return sentence.substring(0, maxLength - 3).trim() + '...';
        }
      }
    }

    // Fallback to beginning of content
    return content.length <= maxLength ? 
      content : 
      content.substring(0, maxLength - 3) + '...';
  }

  /**
   * Calculate search facets
   */
  private calculateFacets(results: SearchResult[]): SearchFacets {
    const entityTypes = new Map<EntityType, number>();
    const categories = new Map<string, number>();
    const statuses = new Map<string, number>();

    for (const result of results) {
      // Entity types
      entityTypes.set(result.entityType, (entityTypes.get(result.entityType) || 0) + 1);

      // Categories
      if (result.metadata?.category) {
        categories.set(result.metadata.category, (categories.get(result.metadata.category) || 0) + 1);
      }

      // Statuses
      if (result.metadata?.status) {
        statuses.set(result.metadata.status, (statuses.get(result.metadata.status) || 0) + 1);
      }
    }

    return {
      entityTypes: Array.from(entityTypes.entries()).map(([type, count]) => ({ type, count })),
      categories: Array.from(categories.entries()).map(([category, count]) => ({ category, count })),
      statuses: Array.from(statuses.entries()).map(([status, count]) => ({ status, count })),
      dateRanges: [] // Could be implemented based on lastModified dates
    };
  }

  /**
   * Generate search suggestions
   */
  private generateSuggestions(query: string): string[] {
    const suggestions = [];
    const queryLower = query.toLowerCase();

    // Get popular queries that start with the query
    for (const [popularQuery, count] of this.popularQueries.entries()) {
      if (popularQuery.toLowerCase().startsWith(queryLower) && popularQuery !== query) {
        suggestions.push(popularQuery);
      }
    }

    // Limit suggestions
    return suggestions.slice(0, 5);
  }

  /**
   * Record search for analytics and suggestions
   */
  private recordSearch(query: string): void {
    // Add to search history
    this.searchHistory.unshift(query);
    if (this.searchHistory.length > 100) {
      this.searchHistory = this.searchHistory.slice(0, 100);
    }

    // Update popular queries
    const count = this.popularQueries.get(query) || 0;
    this.popularQueries.set(query, count + 1);
  }

  /**
   * Schedule index maintenance
   */
  private scheduleIndexMaintenance(): void {
    // Rebuild indexes daily
    setInterval(() => {
      this.buildIndexes();
    }, 24 * 60 * 60 * 1000);

    // Check for updates every 5 minutes
    setInterval(async () => {
      const stats = await offlineStorage.getStorageStats();
      if (stats.oldestUnsyncedItem && stats.oldestUnsyncedItem > this.lastIndexUpdate) {
        this.buildIndexes();
      }
    }, 5 * 60 * 1000);
  }

  /**
   * Get search statistics
   */
  async getStats(): Promise<IndexStats> {
    let totalDocuments = 0;
    const documentsPerType: Record<EntityType, number> = {} as any;

    for (const [entityType, index] of this.indexes.entries()) {
      const count = index.getIndex().size;
      documentsPerType[entityType] = count;
      totalDocuments += count;
    }

    return {
      totalDocuments,
      documentsPerType,
      lastIndexed: this.lastIndexUpdate,
      indexSize: this.documentStore.size,
      searchLatency: 0 // Would be calculated from recent searches
    };
  }

  /**
   * Clear search history and suggestions
   */
  clearHistory(): void {
    this.searchHistory = [];
    this.popularQueries.clear();
  }
}

// Singleton instance
export const offlineSearch = new OfflineSearch();