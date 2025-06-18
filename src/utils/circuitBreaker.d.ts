export declare enum CircuitState {
    CLOSED = "CLOSED",
    OPEN = "OPEN",
    HALF_OPEN = "HALF_OPEN"
}
export interface CircuitBreakerOptions {
    failureThreshold?: number;
    resetTimeout?: number;
    monitoringPeriod?: number;
    halfOpenMaxAttempts?: number;
    onStateChange?: (state: CircuitState) => void;
}
export declare class CircuitBreaker<T = any> {
    private state;
    private failureCount;
    private successCount;
    private lastFailureTime?;
    private halfOpenAttempts;
    private readonly failureThreshold;
    private readonly resetTimeout;
    private readonly monitoringPeriod;
    private readonly halfOpenMaxAttempts;
    private readonly onStateChange?;
    constructor(options?: CircuitBreakerOptions);
    execute<R>(operation: () => Promise<R>, fallback?: () => R | Promise<R>): Promise<R>;
    private onSuccess;
    private onFailure;
    private canAttemptReset;
    private transitionTo;
    getState(): CircuitState;
    getMetrics(): {
        state: CircuitState;
        failureCount: number;
        successCount: number;
        lastFailureTime: number | undefined;
        isHealthy: boolean;
    };
    reset(): void;
}
export declare class CircuitBreakerFactory {
    private static breakers;
    static getBreaker(name: string, options?: CircuitBreakerOptions): CircuitBreaker;
    static getMetrics(): Record<string, any>;
    static resetAll(): void;
}
