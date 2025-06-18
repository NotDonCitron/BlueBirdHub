interface ErrorInfo {
    message: string;
    stack?: string;
    source: string;
    timestamp: string;
    userAgent: string;
    url: string;
    type?: string;
    component?: string;
    context?: any;
}
declare class ErrorLogger {
    private static instance;
    private errors;
    private maxErrors;
    private constructor();
    static getInstance(): ErrorLogger;
    private setupGlobalErrorHandlers;
    logErrorInfo(errorInfo: ErrorInfo): void;
    private sendToBackend;
    logError(error: Error, context?: any): void;
    getErrors(): ErrorInfo[];
    private logErrorInternal;
    clearErrors(): void;
    exportErrors(): string;
    logCustomError(message: string, details?: any): void;
}
export declare const errorLogger: ErrorLogger;
export declare const logError: (message: string, details?: any) => void;
export declare const getErrorLog: () => ErrorInfo[];
export declare const clearErrorLog: () => void;
export {};
