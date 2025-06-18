interface ErrorInfo {
  message: string;
  stack?: string;
  source: string;
  timestamp: string;
  userAgent: string;
  url: string;
}

class ErrorLogger {
  private static instance: ErrorLogger;
  private errors: ErrorInfo[] = [];
  private maxErrors = 100;

  private constructor() {
    this.setupGlobalErrorHandlers();
  }

  public static getInstance(): ErrorLogger {
    if (!ErrorLogger.instance) {
      ErrorLogger.instance = new ErrorLogger();
    }
    return ErrorLogger.instance;
  }

  private setupGlobalErrorHandlers(): void {
    // Handle JavaScript errors
    window.addEventListener('error', (event) => {
      this.logError({
        message: event.message,
        stack: event.error?.stack,
        source: 'JavaScript Error',
        timestamp: new Date().toISOString(),
        userAgent: navigator.userAgent,
        url: window.location.href
      });
    });

    // Handle unhandled promise rejections
    window.addEventListener('unhandledrejection', (event) => {
      this.logError({
        message: event.reason?.message || String(event.reason),
        stack: event.reason?.stack,
        source: 'Unhandled Promise Rejection',
        timestamp: new Date().toISOString(),
        userAgent: navigator.userAgent,
        url: window.location.href
      });
    });

    // Override console.error to capture logged errors
    const originalConsoleError = console.error;
    console.error = (...args: any[]) => {
      this.logError({
        message: args.join(' '),
        source: 'Console Error',
        timestamp: new Date().toISOString(),
        userAgent: navigator.userAgent,
        url: window.location.href
      });
      originalConsoleError.apply(console, args);
    };

    // Override console.warn for warnings
    const originalConsoleWarn = console.warn;
    console.warn = (...args: any[]) => {
      this.logError({
        message: args.join(' '),
        source: 'Console Warning',
        timestamp: new Date().toISOString(),
        userAgent: navigator.userAgent,
        url: window.location.href
      });
      originalConsoleWarn.apply(console, args);
    };
  }

  public logError(errorInfo: ErrorInfo): void {
    this.errors.push(errorInfo);
    
    // Keep only the last maxErrors entries
    if (this.errors.length > this.maxErrors) {
      this.errors = this.errors.slice(-this.maxErrors);
    }

    // Log to console with timestamp and color coding
    const timestamp = new Date().toLocaleTimeString();
    console.group(`%c🚨 Error Logged [${timestamp}]`, 'color: red; font-weight: bold;');
    console.log(`%cSource: ${errorInfo.source}`, 'color: orange;');
    console.log(`%cMessage: ${errorInfo.message}`, 'color: red;');
    if (errorInfo.stack) {
      console.log(`%cStack:`, 'color: gray;');
      console.log(errorInfo.stack);
    }
    console.log(`%cURL: ${errorInfo.url}`, 'color: blue;');
    console.groupEnd();

    // Send to backend if available
    this.sendToBackend(errorInfo);
  }

  private async sendToBackend(errorInfo: ErrorInfo): Promise<void> {
    try {
      await fetch('http://localhost:8001/api/logs/frontend-error', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(errorInfo),
      });
    } catch (error) {
      // Silently fail if backend is not available
      console.debug('Could not send error to backend:', error);
    }
  }

  public getErrors(): ErrorInfo[] {
    return [...this.errors];
  }

  public clearErrors(): void {
    this.errors = [];
    console.log('%c✅ Error log cleared', 'color: green; font-weight: bold;');
  }

  public exportErrors(): string {
    return JSON.stringify(this.errors, null, 2);
  }

  public logCustomError(message: string, details?: any): void {
    this.logError({
      message: `${message}${details ? ` - Details: ${JSON.stringify(details)}` : ''}`,
      source: 'Custom Error',
      timestamp: new Date().toISOString(),
      userAgent: navigator.userAgent,
      url: window.location.href
    });
  }
}

// Export singleton instance
export const errorLogger = ErrorLogger.getInstance();

// Export for manual error logging
export const logError = (message: string, details?: any) => {
  errorLogger.logCustomError(message, details);
};

// Export function to get all errors (useful for debugging)
export const getErrorLog = () => errorLogger.getErrors();

// Export function to clear errors
export const clearErrorLog = () => errorLogger.clearErrors();

// Make it available globally for debugging
(window as any).errorLogger = {
  getErrors: getErrorLog,
  clearErrors: clearErrorLog,
  exportErrors: () => errorLogger.exportErrors(),
  logError: logError
};