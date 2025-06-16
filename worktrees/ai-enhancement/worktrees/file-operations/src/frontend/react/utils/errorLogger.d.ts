interface ErrorInfo {
    message: string;
    stack?: string;
    source: string;
    timestamp: string;
    userAgent: string;
    url: string;
}
declare class ErrorLogger {
    private static instance;
    private errors;
    private maxErrors;
    private constructor();
    static getInstance(): ErrorLogger;
    private setupGlobalErrorHandlers;
    logError(errorInfo: ErrorInfo): void;
    private sendToBackend;
    getErrors(): ErrorInfo[];
    clearErrors(): void;
    exportErrors(): string;
    logCustomError(message: string, details?: any): void;
}
export declare const errorLogger: ErrorLogger;
export declare const logError: (message: string, details?: any) => void;
export declare const getErrorLog: () => ErrorInfo[];
export declare const clearErrorLog: () => void;
export {};
