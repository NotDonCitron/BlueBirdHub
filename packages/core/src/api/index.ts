// API client and types
export interface ApiConfig {
  baseUrl: string;
  timeout?: number;
  retries?: number;
}

export interface RequestOptions {
  timeout?: number;
  signal?: AbortSignal;
  retries?: number;
}

export class ApiRequestError extends Error {
  constructor(
    message: string,
    public status?: number,
    public code?: string
  ) {
    super(message);
    this.name = 'ApiRequestError';
  }
}

export class ApiClient {
  private baseUrl: string;
  private timeout: number;
  private retries: number;

  constructor(config: ApiConfig) {
    this.baseUrl = config.baseUrl;
    this.timeout = config.timeout || 10000;
    this.retries = config.retries || 3;
  }

  private async makeRequest(
    endpoint: string,
    options: RequestInit & RequestOptions = {}
  ): Promise<Response> {
    const { timeout = this.timeout, signal, retries = this.retries, ...fetchOptions } = options;
    
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), timeout);
    
    const combinedSignal = signal ? 
      this.combineAbortSignals(signal, controller.signal) : 
      controller.signal;

    let lastError: Error | undefined;
    
    for (let attempt = 0; attempt <= retries; attempt++) {
      try {
        const response = await fetch(`${this.baseUrl}${endpoint}`, {
          ...fetchOptions,
          signal: combinedSignal,
        });

        clearTimeout(timeoutId);

        if (!response.ok) {
          const errorText = await response.text().catch(() => 'Unknown error');
          throw new ApiRequestError(
            `HTTP ${response.status}: ${response.statusText} - ${errorText}`,
            response.status
          );
        }

        return response;
      } catch (error) {
        clearTimeout(timeoutId);
        
        if (error instanceof Error && error.name === 'AbortError') {
          if (signal?.aborted) {
            throw new ApiRequestError('Request was cancelled', undefined, 'CANCELLED');
          } else {
            throw new ApiRequestError(`Request timeout after ${timeout}ms`, undefined, 'TIMEOUT');
          }
        }

        lastError = error instanceof Error ? error : new Error(String(error));
        
        if (attempt === retries) {
          break;
        }

        await this.delay(Math.pow(2, attempt) * 1000);
      }
    }

    throw new ApiRequestError(
      `Request failed after ${retries + 1} attempts: ${lastError?.message || 'Unknown error'}`,
      undefined,
      'RETRY_EXHAUSTED'
    );
  }

  private combineAbortSignals(signal1: AbortSignal, signal2: AbortSignal): AbortSignal {
    const controller = new AbortController();
    
    const abort = () => controller.abort();
    
    if (signal1.aborted || signal2.aborted) {
      abort();
    } else {
      signal1.addEventListener('abort', abort, { once: true });
      signal2.addEventListener('abort', abort, { once: true });
    }
    
    return controller.signal;
  }

  private delay(ms: number): Promise<void> {
    return new Promise(resolve => setTimeout(resolve, ms));
  }

  async get(endpoint: string, options: RequestOptions = {}): Promise<any> {
    const response = await this.makeRequest(endpoint, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
      },
      ...options,
    });

    return response.json();
  }

  async post(endpoint: string, data: any, options: RequestOptions = {}): Promise<any> {
    const response = await this.makeRequest(endpoint, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(data),
      ...options,
    });

    return response.json();
  }

  async put(endpoint: string, data: any, options: RequestOptions = {}): Promise<any> {
    const response = await this.makeRequest(endpoint, {
      method: 'PUT',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(data),
      ...options,
    });

    return response.json();
  }

  async delete(endpoint: string, options: RequestOptions = {}): Promise<any> {
    const response = await this.makeRequest(endpoint, {
      method: 'DELETE',
      headers: {
        'Content-Type': 'application/json',
      },
      ...options,
    });

    return response.json();
  }
}

export const defaultApiClient = new ApiClient({
  baseUrl: 'http://localhost:8001',
});