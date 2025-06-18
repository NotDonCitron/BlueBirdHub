export enum CircuitState {
  CLOSED = 'CLOSED',
  OPEN = 'OPEN',
  HALF_OPEN = 'HALF_OPEN'
}

export interface CircuitBreakerOptions {
  failureThreshold?: number;
  resetTimeout?: number;
  monitoringPeriod?: number;
  halfOpenMaxAttempts?: number;
  onStateChange?: (state: CircuitState) => void;
}

export class CircuitBreaker<T = any> {
  private state: CircuitState = CircuitState.CLOSED;
  private failureCount = 0;
  private successCount = 0;
  private lastFailureTime?: number;
  private halfOpenAttempts = 0;
  
  private readonly failureThreshold: number;
  private readonly resetTimeout: number;
  private readonly monitoringPeriod: number;
  private readonly halfOpenMaxAttempts: number;
  private readonly onStateChange?: (state: CircuitState) => void;

  constructor(options: CircuitBreakerOptions = {}) {
    this.failureThreshold = options.failureThreshold || 5;
    this.resetTimeout = options.resetTimeout || 60000; // 60 seconds
    this.monitoringPeriod = options.monitoringPeriod || 300000; // 5 minutes
    this.halfOpenMaxAttempts = options.halfOpenMaxAttempts || 3;
    this.onStateChange = options.onStateChange;
  }

  async execute<R>(
    operation: () => Promise<R>,
    fallback?: () => R | Promise<R>
  ): Promise<R> {
    if (this.state === CircuitState.OPEN) {
      if (this.canAttemptReset()) {
        this.transitionTo(CircuitState.HALF_OPEN);
      } else {
        if (fallback) {
          return fallback();
        }
        throw new Error(`Circuit breaker is OPEN. Service unavailable.`);
      }
    }

    try {
      const result = await operation();
      this.onSuccess();
      return result;
    } catch (error) {
      this.onFailure();
      
      if (fallback && this.state === CircuitState.OPEN) {
        return fallback();
      }
      
      throw error;
    }
  }

  private onSuccess(): void {
    this.failureCount = 0;
    
    if (this.state === CircuitState.HALF_OPEN) {
      this.successCount++;
      
      if (this.successCount >= this.halfOpenMaxAttempts) {
        this.transitionTo(CircuitState.CLOSED);
      }
    }
  }

  private onFailure(): void {
    this.failureCount++;
    this.lastFailureTime = Date.now();
    
    if (this.state === CircuitState.HALF_OPEN) {
      this.transitionTo(CircuitState.OPEN);
      return;
    }
    
    if (this.failureCount >= this.failureThreshold) {
      this.transitionTo(CircuitState.OPEN);
    }
  }

  private canAttemptReset(): boolean {
    return (
      this.lastFailureTime !== undefined &&
      Date.now() - this.lastFailureTime >= this.resetTimeout
    );
  }

  private transitionTo(newState: CircuitState): void {
    if (this.state !== newState) {
      console.log(`Circuit breaker state transition: ${this.state} -> ${newState}`);
      this.state = newState;
      
      if (newState === CircuitState.HALF_OPEN) {
        this.halfOpenAttempts = 0;
        this.successCount = 0;
      }
      
      if (this.onStateChange) {
        this.onStateChange(newState);
      }
    }
  }

  getState(): CircuitState {
    return this.state;
  }

  getMetrics() {
    return {
      state: this.state,
      failureCount: this.failureCount,
      successCount: this.successCount,
      lastFailureTime: this.lastFailureTime,
      isHealthy: this.state === CircuitState.CLOSED
    };
  }

  reset(): void {
    this.failureCount = 0;
    this.successCount = 0;
    this.halfOpenAttempts = 0;
    this.lastFailureTime = undefined;
    this.transitionTo(CircuitState.CLOSED);
  }
}

// Factory for creating circuit breakers for different services
export class CircuitBreakerFactory {
  private static breakers = new Map<string, CircuitBreaker>();

  static getBreaker(
    name: string,
    options?: CircuitBreakerOptions
  ): CircuitBreaker {
    if (!this.breakers.has(name)) {
      this.breakers.set(name, new CircuitBreaker(options));
    }
    return this.breakers.get(name)!;
  }

  static getMetrics() {
    const metrics: Record<string, any> = {};
    
    this.breakers.forEach((breaker, name) => {
      metrics[name] = breaker.getMetrics();
    });
    
    return metrics;
  }

  static resetAll(): void {
    this.breakers.forEach(breaker => breaker.reset());
  }
}

// Usage example:
// const apiBreaker = CircuitBreakerFactory.getBreaker('api', {
//   failureThreshold: 3,
//   resetTimeout: 30000,
//   onStateChange: (state) => console.log(`API Circuit is now ${state}`)
// });
//
// try {
//   const result = await apiBreaker.execute(
//     () => fetch('/api/data'),
//     () => ({ data: 'cached data' }) // fallback
//   );
// } catch (error) {
//   console.error('Service unavailable');
// }