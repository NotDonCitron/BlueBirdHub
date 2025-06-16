import React, { useState, useEffect, useRef, useCallback } from 'react';
import { useLocation } from 'react-router-dom';
import { useApi } from '../../contexts/ApiContext';
import './SmartSearch.css';

interface SearchResult {
  id: string;
  name: string;
  type: string;
  size: string;
  modified: string;
  tags: string[];
  category: string;
  priority: string;
  workspace_id: number;
  workspace_name: string;
}

interface SearchQuery {
  text: string;
  category: string;
  workspace: string;
  tags: string;
}

const SmartSearch: React.FC = () => {
  const { makeApiRequest } = useApi();
  const location = useLocation();
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedCategory, setSelectedCategory] = useState('');
  const [selectedWorkspace, setSelectedWorkspace] = useState('');
  const [selectedTags, setSelectedTags] = useState<string[]>([]);
  const [searchResults, setSearchResults] = useState<SearchResult[]>([]);
  const [allTags, setAllTags] = useState<string[]>([]);
  const [allCategories, setAllCategories] = useState<string[]>([]);
  const [isSearching, setIsSearching] = useState(false);
  const [showFilters, setShowFilters] = useState(false);
  const [lastQuery, setLastQuery] = useState<SearchQuery | null>(null);
  
  const searchControllerRef = useRef<AbortController | null>(null);
  const debounceTimeoutRef = useRef<NodeJS.Timeout | null>(null);

  useEffect(() => {
    loadTags();
    loadCategories();
    
    // Check for URL search parameter
    const urlParams = new URLSearchParams(location.search);
    const queryParam = urlParams.get('q');
    if (queryParam) {
      setSearchQuery(queryParam);
      // Auto-perform search when coming from header
      setTimeout(() => {
        performSearchWithQuery(queryParam);
      }, 100);
    }

    return () => {
      if (searchControllerRef.current) {
        searchControllerRef.current.abort();
      }
      if (debounceTimeoutRef.current) {
        clearTimeout(debounceTimeoutRef.current);
      }
    };
  }, [location.search]);

  const loadTags = async () => {
    try {
      const response = await makeApiRequest('/search/tags');
      if (response.success) {
        setAllTags(response.tags);
      }
    } catch (error) {
      console.error('Failed to load tags:', error);
    }
  };

  const loadCategories = async () => {
    try {
      const response = await makeApiRequest('/search/categories');
      if (response.success) {
        setAllCategories(response.categories);
      }
    } catch (error) {
      console.error('Failed to load categories:', error);
    }
  };

  const performSearchWithQuery = useCallback(async (query?: string) => {
    const searchText = query || searchQuery;
    
    if (!searchText.trim() && !selectedCategory && !selectedWorkspace && selectedTags.length === 0) {
      return;
    }

    // Cancel previous search
    if (searchControllerRef.current) {
      searchControllerRef.current.abort();
    }

    // Create new controller for this search
    searchControllerRef.current = new AbortController();

    setIsSearching(true);
    try {
      const params = new URLSearchParams();
      if (searchText.trim()) params.append('q', searchText.trim());
      if (selectedCategory) params.append('category', selectedCategory);
      if (selectedWorkspace) params.append('workspace', selectedWorkspace);
      if (selectedTags.length > 0) params.append('tags', selectedTags.join(','));

      const response = await makeApiRequest(
        `/search/files?${params.toString()}`, 
        'GET', 
        undefined, 
        { 
          signal: searchControllerRef.current.signal,
          timeout: 10000
        }
      );
      
      if (response && response.success) {
        setSearchResults(response.results);
        setLastQuery(response.query);
      }
    } catch (error: any) {
      if (error?.code !== 'CANCELLED') {
        console.error('Search failed:', error);
        setSearchResults([]);
      }
    } finally {
      setIsSearching(false);
    }
  }, [searchQuery, selectedCategory, selectedWorkspace, selectedTags, makeApiRequest]);

  const debouncedSearch = useCallback((query?: string) => {
    if (debounceTimeoutRef.current) {
      clearTimeout(debounceTimeoutRef.current);
    }

    debounceTimeoutRef.current = setTimeout(() => {
      performSearchWithQuery(query);
    }, 300);
  }, [performSearchWithQuery]);

  const performSearch = () => performSearchWithQuery();

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter') {
      performSearch();
    }
  };

  const addTag = (tag: string) => {
    if (!selectedTags.includes(tag)) {
      setSelectedTags([...selectedTags, tag]);
    }
  };

  const removeTag = (tag: string) => {
    setSelectedTags(selectedTags.filter(t => t !== tag));
  };

  const clearAllFilters = () => {
    setSearchQuery('');
    setSelectedCategory('');
    setSelectedWorkspace('');
    setSelectedTags([]);
    setSearchResults([]);
    setLastQuery(null);
  };

  const getFileIcon = (type: string) => {
    switch (type) {
      case 'image': return '🖼️';
      case 'code': return '💻';
      case 'document': return '📄';
      case 'development': return '⚡';
      case 'design': return '🎨';
      case 'business': return '💼';
      case 'marketing': return '📈';
      case 'finance': return '💰';
      default: return '📄';
    }
  };

  const getPriorityColor = (priority: string) => {
    switch (priority) {
      case 'high': return '#ef4444';
      case 'medium': return '#f59e0b';
      case 'low': return '#10b981';
      default: return '#6b7280';
    }
  };

  return (
    <div className="smart-search">
      <div className="search-header">
        <h2>🔍 Smart Search</h2>
        <p>Search files by name, content, tags, or AI-generated categories</p>
      </div>

      <div className="search-main">
        <div className="search-input-container">
          <input
            type="text"
            className="search-input"
            placeholder="Search files... (try: 'web', 'marketing', 'budget')"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            onKeyDown={handleKeyPress}
          />
          <button 
            className="search-button"
            onClick={performSearch}
            disabled={isSearching}
          >
            {isSearching ? '🔄' : '🔍'}
          </button>
          <button 
            className="filter-toggle"
            onClick={() => setShowFilters(!showFilters)}
          >
            🎛️ Filters
          </button>
        </div>

        {showFilters && (
          <div className="search-filters">
            <div className="filter-row">
              <div className="filter-group">
                <label>Category:</label>
                <select 
                  value={selectedCategory} 
                  onChange={(e) => setSelectedCategory(e.target.value)}
                >
                  <option value="">All Categories</option>
                  {allCategories.map(category => (
                    <option key={category} value={category}>
                      {category.charAt(0).toUpperCase() + category.slice(1)}
                    </option>
                  ))}
                </select>
              </div>

              <div className="filter-group">
                <label>Workspace:</label>
                <select 
                  value={selectedWorkspace} 
                  onChange={(e) => setSelectedWorkspace(e.target.value)}
                >
                  <option value="">All Workspaces</option>
                  <option value="Website">Website</option>
                  <option value="Einkauf">Einkauf</option>
                  <option value="Marketing">Marketing</option>
                  <option value="Finanzen">Finanzen</option>
                </select>
              </div>
            </div>

            <div className="filter-group">
              <label>Tags:</label>
              <div className="tags-input">
                <div className="selected-tags">
                  {selectedTags.map(tag => (
                    <span key={tag} className="selected-tag">
                      {tag}
                      <button onClick={() => removeTag(tag)}>×</button>
                    </span>
                  ))}
                </div>
                <select 
                  onChange={(e) => {
                    if (e.target.value) {
                      addTag(e.target.value);
                      e.target.value = '';
                    }
                  }}
                >
                  <option value="">Add tag...</option>
                  {allTags.filter(tag => !selectedTags.includes(tag)).map(tag => (
                    <option key={tag} value={tag}>{tag}</option>
                  ))}
                </select>
              </div>
            </div>

            <div className="filter-actions">
              <button className="clear-filters" onClick={clearAllFilters}>
                Clear All
              </button>
            </div>
          </div>
        )}
      </div>

      {lastQuery && (
        <div className="search-info">
          <p>
            Found <strong>{searchResults.length}</strong> results
            {lastQuery.text && ` for "${lastQuery.text}"`}
            {lastQuery.category && ` in category "${lastQuery.category}"`}
            {lastQuery.workspace && ` in workspace "${lastQuery.workspace}"`}
            {lastQuery.tags && ` with tags "${lastQuery.tags}"`}
          </p>
        </div>
      )}

      <div className="search-results">
        {searchResults.length > 0 ? (
          <div className="results-grid">
            {searchResults.map((file) => (
              <div key={file.id} className="result-item">
                <div className="file-header">
                  <span className="file-icon">{getFileIcon(file.type)}</span>
                  <div className="file-info">
                    <h4 className="file-name">{file.name}</h4>
                    <p className="file-meta">
                      {file.size} • {file.modified} • {file.workspace_name}
                    </p>
                  </div>
                  <div 
                    className="priority-indicator"
                    style={{ backgroundColor: getPriorityColor(file.priority) }}
                    title={`Priority: ${file.priority}`}
                  >
                    {file.priority.charAt(0).toUpperCase()}
                  </div>
                </div>

                <div className="file-category">
                  <span className="category-badge">{file.category}</span>
                </div>

                <div className="file-tags">
                  {file.tags.map((tag, index) => (
                    <span 
                      key={index} 
                      className="tag"
                      onClick={() => addTag(tag)}
                      title="Click to add as filter"
                    >
                      {tag}
                    </span>
                  ))}
                </div>
              </div>
            ))}
          </div>
        ) : lastQuery ? (
          <div className="no-results">
            <p>No files found matching your search criteria.</p>
            <p>Try different keywords or adjust your filters.</p>
          </div>
        ) : (
          <div className="search-suggestions">
            <h3>Try searching for:</h3>
            <div className="suggestion-tags">
              {allTags.slice(0, 10).map(tag => (
                <button 
                  key={tag}
                  className="suggestion-tag"
                  onClick={() => {
                    setSearchQuery(tag);
                    performSearchWithQuery(tag);
                  }}
                >
                  {tag}
                </button>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default SmartSearch;