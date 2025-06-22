import { API_CONFIG, ENDPOINTS, getApiUrl, testConnection } from './api';

// Custom error classes
export class APIError extends Error {
  constructor(public status: number, message: string, public endpoint: string) {
    super(message);
    this.name = 'APIError';
  }
}

export class ConnectionError extends Error {
  constructor(message: string) {
    super(message);
    this.name = 'ConnectionError';
  }
}

// API Client class with automatic fallback
export class ApiClient {
  private currentBackend: 'primary' | 'mock' | 'none' = 'primary';
  private isTestingConnection = false;

  async request<T>(
    endpoint: string, 
    options: RequestInit = {},
    retryCount = 0
  ): Promise<T> {
    const url = getApiUrl(endpoint, this.currentBackend === 'mock');
    
    try {
      const response = await fetch(url, {
        ...options,
        headers: {
          'Content-Type': 'application/json',
          ...options.headers,
        },
        signal: AbortSignal.timeout(API_CONFIG.TIMEOUT),
      });

      if (!response.ok) {
        // If primary backend fails, try mock backend
        if (this.currentBackend === 'primary' && response.status >= 500) {
          console.warn(`Primary backend error (${response.status}), switching to mock`);
          this.currentBackend = 'mock';
          return this.request<T>(endpoint, options, retryCount);
        }
        
        throw new APIError(response.status, `HTTP ${response.status}`, endpoint);
      }

      return await response.json();
    } catch (error) {
      if (error instanceof APIError) {
        throw error;
      }

      // Connection failed - try alternative backend or retry
      if (retryCount < API_CONFIG.MAX_RETRIES) {
        if (this.currentBackend === 'primary') {
          console.warn('Primary backend connection failed, trying mock backend');
          this.currentBackend = 'mock';
          return this.request<T>(endpoint, options, retryCount);
        } else {
          // Retry with delay
          await new Promise(resolve => setTimeout(resolve, API_CONFIG.RETRY_DELAY));
          return this.request<T>(endpoint, options, retryCount + 1);
        }
      }

      throw new ConnectionError(`Failed to connect to backend after ${retryCount + 1} attempts`);
    }
  }

  async get<T>(endpoint: string): Promise<T> {
    return this.request<T>(endpoint, { method: 'GET' });
  }

  async post<T>(endpoint: string, data?: any): Promise<T> {
    return this.request<T>(endpoint, {
      method: 'POST',
      body: data ? JSON.stringify(data) : undefined,
    });
  }

  async put<T>(endpoint: string, data?: any): Promise<T> {
    return this.request<T>(endpoint, {
      method: 'PUT',
      body: data ? JSON.stringify(data) : undefined,
    });
  }

  async delete<T>(endpoint: string): Promise<T> {
    return this.request<T>(endpoint, { method: 'DELETE' });
  }

  // Method to get progress stats
  async getProgressStats<T>(): Promise<T> {
    return this.get<T>(ENDPOINTS.PROGRESS_STATS);
  }

  // Method to get all searchable data
  async getSearchableData<T>(): Promise<T> {
    return this.get<T>(ENDPOINTS.SEARCHABLE_DATA);
  }

  // Test and set optimal backend
  async initializeConnection(): Promise<void> {
    if (this.isTestingConnection) return;
    
    this.isTestingConnection = true;
    try {
      const result = await testConnection();
      this.currentBackend = result.backend === 'none' ? 'primary' : result.backend;
      console.log(`✅ Connected to ${this.currentBackend} backend`);
    } catch (error) {
      console.warn('Connection test failed, using primary backend as default');
      this.currentBackend = 'primary';
    } finally {
      this.isTestingConnection = false;
    }
  }

  getCurrentBackend(): string {
    return this.currentBackend;
  }
}

// Singleton instance
export const apiClient = new ApiClient();
