/**
 * Zentraler API Manager - Verhindert Frontend-API-Routing-Probleme
 * Single Source of Truth für alle API-Konfigurationen
 */

import { CircuitBreaker, CircuitBreakerFactory } from '../../../utils/circuitBreaker';

// Verbotene URLs (Frontend-Ports)
const FORBIDDEN_URLS = [
  'localhost:3000',
  'localhost:3001', 
  '127.0.0.1:3000',
  '127.0.0.1:3001'
];

// Erlaubte Backend-URLs
type BackendPort = 8000 | 8001 | 8080;
type ApiUrl = `http://localhost:${BackendPort}` | `https://${string}`;

interface ApiConfig {
  baseUrl: ApiUrl;
  fallbackUrl: ApiUrl;
  timeout: number;
  maxRetries: number;
}

interface BackendHealth {
  url: string;
  healthy: boolean;
  responseTime: number;
  lastChecked: Date;
}

class ApiManager {
  private static instance: ApiManager;
  private config: ApiConfig;
  private currentBackend: string;
  private healthStatus: Map<string, BackendHealth> = new Map();
  private isInitialized = false;

  private constructor() {
    this.config = {
      baseUrl: this.getFromEnv('REACT_APP_API_URL') || 'http://localhost:8000',
      fallbackUrl: this.getFromEnv('REACT_APP_FALLBACK_API_URL') || 'http://localhost:8000',
      timeout: parseInt(this.getFromEnv('REACT_APP_API_TIMEOUT') || '10000'),
      maxRetries: 3
    };
    
    this.currentBackend = this.config.baseUrl;
    this.validateConfiguration();
  }

  public static getInstance(): ApiManager {
    if (!ApiManager.instance) {
      ApiManager.instance = new ApiManager();
    }
    return ApiManager.instance;
  }

  private getFromEnv(key: string): string | undefined {
    return process.env[key];
  }

  private validateConfiguration(): void {
    const urlsToCheck = [this.config.baseUrl, this.config.fallbackUrl];
    
    for (const url of urlsToCheck) {
      if (this.containsForbiddenUrl(url)) {
        throw new Error(
          `CRITICAL: Frontend self-call detected!\n` +
          `Forbidden URL: ${url}\n` +
          `This would cause infinite loops. Check your environment configuration.`
        );
      }
    }
    
    console.log('API Configuration validated - No frontend self-calls detected');
  }

  private containsForbiddenUrl(url: string): boolean {
    return FORBIDDEN_URLS.some(forbidden => url.includes(forbidden));
  }

  private async testConnection(url: string): Promise<BackendHealth> {
    const startTime = performance.now();
    
    try {
      const response = await fetch(`${url}/health`, {
        method: 'GET',
        signal: AbortSignal.timeout(this.config.timeout),
        headers: {
          'Content-Type': 'application/json'
        }
      });

      const endTime = performance.now();
      const responseTime = endTime - startTime;

      const health: BackendHealth = {
        url,
        healthy: response.ok,
        responseTime,
        lastChecked: new Date()
      };

      this.healthStatus.set(url, health);
      return health;
    } catch (error) {
      const endTime = performance.now();
      const health: BackendHealth = {
        url,
        healthy: false,
        responseTime: endTime - startTime,
        lastChecked: new Date()
      };

      this.healthStatus.set(url, health);
      return health;
    }
  }

  public async initializeConnection(): Promise<void> {
    if (this.isInitialized) return;

    console.log('Initializing API connection...');
    
    // Test primary backend
    const primaryHealth = await this.testConnection(this.config.baseUrl);
    
    if (primaryHealth.healthy) {
      this.currentBackend = this.config.baseUrl;
      console.log(`Connected to primary backend: ${this.config.baseUrl}`);
    } else {
      console.warn(`Primary backend unavailable: ${this.config.baseUrl}`);
      
      // Test fallback backend
      const fallbackHealth = await this.testConnection(this.config.fallbackUrl);
      
      if (fallbackHealth.healthy) {
        this.currentBackend = this.config.fallbackUrl;
        console.log(`Connected to fallback backend: ${this.config.fallbackUrl}`);
      } else {
        console.error('All backends unavailable!');
        throw new Error('No backend available');
      }
    }

    this.isInitialized = true;
  }

  public async makeRequest<T>(
    endpoint: string, 
    options: RequestInit = {}
  ): Promise<T> {
    if (!this.isInitialized) {
      await this.initializeConnection();
    }

    // Security check: Prevent frontend self-calls
    if (this.containsForbiddenUrl(endpoint)) {
      throw new Error(
        `BLOCKED: Attempted frontend self-call to ${endpoint}\n` +
        `This would cause routing errors. Use backend endpoints only.`
      );
    }

    const url = `${this.currentBackend}${endpoint}`;
    
    // Log API calls in development
    if (process.env.NODE_ENV === 'development') {
      console.log(`API Request: ${options.method || 'GET'} ${url}`);
    }

    try {
      const response = await fetch(url, {
        ...options,
        headers: {
          'Content-Type': 'application/json',
          ...options.headers,
        },
        signal: AbortSignal.timeout(this.config.timeout),
      });

      if (!response.ok) {
        // If primary backend fails, try fallback
        if (this.currentBackend === this.config.baseUrl && url.includes(this.config.baseUrl)) {
          console.warn(`Primary backend error (${response.status}), trying fallback...`);
          this.currentBackend = this.config.fallbackUrl;
          return this.makeRequest<T>(endpoint, options);
        }
        
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      return await response.json();
    } catch (error) {
      if (error instanceof Error) {
        console.error(`API request failed: ${error.message}`);
        
        // Log for debugging
        console.error(`Failed endpoint: ${endpoint}`);
        console.error(`Current backend: ${this.currentBackend}`);
      }
      
      throw error;
    }
  }

  public async get<T>(endpoint: string): Promise<T> {
    return this.makeRequest<T>(endpoint, { method: 'GET' });
  }

  public async post<T>(endpoint: string, data?: any): Promise<T> {
    return this.makeRequest<T>(endpoint, {
      method: 'POST',
      body: data ? JSON.stringify(data) : undefined,
    });
  }

  public async put<T>(endpoint: string, data?: any): Promise<T> {
    return this.makeRequest<T>(endpoint, {
      method: 'PUT',
      body: data ? JSON.stringify(data) : undefined,
    });
  }

  public async delete<T>(endpoint: string): Promise<T> {
    return this.makeRequest<T>(endpoint, { method: 'DELETE' });
  }

  public getHealthStatus(): Map<string, BackendHealth> {
    return this.healthStatus;
  }

  public getCurrentBackend(): string {
    return this.currentBackend;
  }

  public getConfig(): ApiConfig {
    return { ...this.config };
  }
}

// Development-only debugging tools
if (process.env.NODE_ENV === 'development') {
  (window as any).apiManager = ApiManager.getInstance();
  (window as any).debugApi = {
    getHealth: () => ApiManager.getInstance().getHealthStatus(),
    getCurrentBackend: () => ApiManager.getInstance().getCurrentBackend(),
    getConfig: () => ApiManager.getInstance().getConfig(),
  };
}

export default ApiManager;
export { ApiManager };
