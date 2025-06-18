/**
 * Development Request Interceptor
 * Verhindert gefährliche API-Calls zur Entwicklungszeit
 */

// Verbotene Patterns für Frontend-Self-Calls
const FORBIDDEN_PATTERNS = [
  /localhost:300[01]/,
  /127\.0\.0\.1:300[01]/,
  /^\/automation$/,  // Absolute paths to frontend
  /^\/dashboard$/,
  /^\/tasks$/,
  /^\/workspaces$/
];

// Korrekte Backend-Patterns
const BACKEND_PATTERNS = [
  /localhost:800[01]/,
  /127\.0\.0\.1:800[01]/,
  /^http:\/\/localhost:800[01]/,
  /^https:\/\/.*\.com/
];

interface InterceptedRequest {
  url: string;
  method: string;
  timestamp: Date;
  blocked: boolean;
  reason?: string;
}

class RequestInterceptor {
  private static instance: RequestInterceptor;
  private interceptedRequests: InterceptedRequest[] = [];
  private originalFetch: typeof fetch;
  private isEnabled: boolean = false;

  private constructor() {
    this.originalFetch = window.fetch;
    
    // Only enable in development
    if (process.env.NODE_ENV === 'development') {
      this.enable();
    }
  }

  public static getInstance(): RequestInterceptor {
    if (!RequestInterceptor.instance) {
      RequestInterceptor.instance = new RequestInterceptor();
    }
    return RequestInterceptor.instance;
  }

  private enable(): void {
    if (this.isEnabled) return;

    console.log('🛡️ Request Interceptor enabled - Protecting against frontend self-calls');

    // Override fetch
    window.fetch = async (input: RequestInfo | URL, init?: RequestInit): Promise<Response> => {
      const url = typeof input === 'string' ? input : input.toString();
      const method = init?.method || 'GET';

      const intercepted: InterceptedRequest = {
        url,
        method,
        timestamp: new Date(),
        blocked: false
      };

      // Check for forbidden patterns
      const isForbidden = FORBIDDEN_PATTERNS.some(pattern => pattern.test(url));
      
      if (isForbidden) {
        intercepted.blocked = true;
        intercepted.reason = 'Frontend self-call detected';
        
        this.interceptedRequests.push(intercepted);
        
        // Alert developer
        this.alertDeveloper(url, method);
        
        // Block the request
        throw new Error(
          `🚨 BLOCKED: Frontend self-call prevented!\n` +
          `URL: ${url}\n` +
          `This would cause routing errors. Use backend URLs (port 8000/8001) instead.`
        );
      }

      // Check if URL looks like a backend call
      const isBackendCall = BACKEND_PATTERNS.some(pattern => pattern.test(url));
      
      if (!isBackendCall && !url.startsWith('data:') && !url.startsWith('blob:')) {
        console.warn(`⚠️ Suspicious API call: ${url}`);
        console.warn('Consider using ApiManager for all backend calls');
      }

      this.interceptedRequests.push(intercepted);
      
      // Log API calls in development
      console.log(`🌐 API Call: ${method} ${url}`);
      
      // Proceed with original fetch
      return this.originalFetch(input, init);
    };

    this.isEnabled = true;
  }

  private alertDeveloper(url: string, method: string): void {
    console.error(
      `%c🚨 CRITICAL: Frontend Self-Call Blocked!`,
      'color: red; font-size: 16px; font-weight: bold;'
    );
    console.error(`Method: ${method}`);
    console.error(`URL: ${url}`);
    console.error(`Fix: Use ApiManager with backend URLs (8000/8001)`);
    
    // Desktop notification if supported
    if ('Notification' in window && Notification.permission === 'granted') {
      new Notification('OrdnungsHub Dev Alert', {
        body: `Blocked frontend self-call: ${method} ${url}`,
        icon: '/favicon.ico'
      });
    }
  }

  public disable(): void {
    if (!this.isEnabled) return;
    
    window.fetch = this.originalFetch;
    this.isEnabled = false;
    console.log('🛡️ Request Interceptor disabled');
  }

  public getInterceptedRequests(): InterceptedRequest[] {
    return [...this.interceptedRequests];
  }

  public getBlockedRequests(): InterceptedRequest[] {
    return this.interceptedRequests.filter(req => req.blocked);
  }

  public clearHistory(): void {
    this.interceptedRequests = [];
    console.log('🧹 Request history cleared');
  }

  public generateReport(): string {
    const total = this.interceptedRequests.length;
    const blocked = this.getBlockedRequests().length;
    const success = total - blocked;

    const report = [
      '📊 Request Interceptor Report',
      '=' * 40,
      `Total Requests: ${total}`,
      `Successful: ${success}`,
      `Blocked: ${blocked}`,
      '',
      'Blocked Requests:',
      ...this.getBlockedRequests().map(req => 
        `  - ${req.method} ${req.url} (${req.reason})`
      ),
      '',
      'Recent Requests:',
      ...this.interceptedRequests.slice(-10).map(req => 
        `  - ${req.method} ${req.url} ${req.blocked ? '❌' : '✅'}`
      )
    ].join('\n');

    return report;
  }
}

// Initialize interceptor in development
if (process.env.NODE_ENV === 'development') {
  const interceptor = RequestInterceptor.getInstance();
  
  // Make available for debugging
  (window as any).requestInterceptor = interceptor;
  (window as any).debugRequests = {
    getHistory: () => interceptor.getInterceptedRequests(),
    getBlocked: () => interceptor.getBlockedRequests(),
    generateReport: () => {
      console.log(interceptor.generateReport());
      return interceptor.generateReport();
    },
    clear: () => interceptor.clearHistory()
  };

  // Request notification permission
  if ('Notification' in window && Notification.permission === 'default') {
    Notification.requestPermission();
  }
}

export default RequestInterceptor;
export { RequestInterceptor };
