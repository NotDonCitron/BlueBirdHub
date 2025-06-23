// API Configuration
export const API_CONFIG = {
  // In container/production: use relative URLs (nginx proxies to backend)
  // In development: use direct backend URL
  BASE_URL: process.env.NODE_ENV === 'production' 
    ? '' // Relative URLs in production (nginx handles routing)
    : (process.env.REACT_APP_API_URL || 'http://127.0.0.1:8000'),
  
  // Fallback for development only
  MOCK_URL: 'http://127.0.0.1:8000',
  
  // Timeout settings
  TIMEOUT: 10000,
  
  // Retry settings
  MAX_RETRIES: 3,
  RETRY_DELAY: 1000,
};

// API endpoints
export const ENDPOINTS = {
  HEALTH: '/health',
  TASKS: '/tasks',
  WORKSPACES: '/workspaces',
  COLLABORATION: '/collaboration',
  AI: '/ai',
  DASHBOARD: '/dashboard',
  FILES: '/files',
  PROGRESS_STATS: '/api/progress/stats',
  SEARCHABLE_DATA: '/api/searchable-data',
};

// Helper function to get full URL
export const getApiUrl = (endpoint: string, useMock = false): string => {
  const baseUrl = useMock ? API_CONFIG.MOCK_URL : API_CONFIG.BASE_URL;
  return `${baseUrl}${endpoint}`;
};

// Connection test function
export const testConnection = async (): Promise<{success: boolean, backend: 'primary' | 'mock' | 'none'}> => {
  try {
    // Test primary backend first
    const response = await fetch(getApiUrl(ENDPOINTS.HEALTH), {
      method: 'GET',
      timeout: 5000,
    });
    
    if (response.ok) {
      return { success: true, backend: 'primary' };
    }
  } catch (error) {
    console.warn('Primary backend unavailable, trying mock backend');
  }
  
  try {
    // Test mock backend
    const response = await fetch(getApiUrl(ENDPOINTS.HEALTH, true), {
      method: 'GET',
      timeout: 5000,
    });
    
    if (response.ok) {
      return { success: true, backend: 'mock' };
    }
  } catch (error) {
    console.error('Both backends unavailable');
  }
  
  return { success: false, backend: 'none' };
};
