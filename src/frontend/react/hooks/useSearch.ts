import { useState, useEffect, useMemo } from 'react';
import Fuse from 'fuse.js';
import { apiClient } from '../config/apiClient';

// Define a generic searchable item type
interface SearchableItem {
  id: string | number;
  title: string;
  type: 'task' | 'workspace' | 'file';
  [key: string]: any;
}

const fuseOptions = {
  keys: ['title', 'description', 'tags', 'name'],
  includeScore: true,
  threshold: 0.4,
};

export const useSearch = () => {
  const [query, setQuery] = useState('');
  const [data, setData] = useState<SearchableItem[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Fetch all searchable data on mount
  useEffect(() => {
    const fetchSearchableData = async () => {
      try {
        setIsLoading(true);
        const response = await apiClient.getSearchableData<SearchableItem[]>();
        setData(response);
      } catch (e) {
        setError('Failed to load search data');
        console.error(e);
      } finally {
        setIsLoading(false);
      }
    };
    fetchSearchableData();
  }, []);

  const fuse = useMemo(() => new Fuse(data, fuseOptions), [data]);

  const results = useMemo(() => {
    if (!query) return [];
    return fuse.search(query).map(result => result.item);
  }, [query, fuse]);

  return { 
    setQuery, 
    results, 
    isLoading, 
    error 
  };
}; 