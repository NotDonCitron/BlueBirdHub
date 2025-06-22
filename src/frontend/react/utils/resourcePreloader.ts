// Resource Preloader for Performance Optimization
interface PreloadOptions {
  priority?: 'high' | 'low';
  crossorigin?: 'anonymous' | 'use-credentials';
  integrity?: string;
  timeout?: number;
}

interface PreloadResult {
  url: string;
  success: boolean;
  error?: string;
  loadTime: number;
}

class ResourcePreloader {
  private preloadedResources = new Set<string>();
  private preloadPromises = new Map<string, Promise<PreloadResult>>();
  private resourceCache = new Map<string, any>();

  // Preload a single resource
  async preload(url: string, type: 'script' | 'style' | 'image' | 'font' | 'fetch', options: PreloadOptions = {}): Promise<PreloadResult> {
    // Check if already preloaded
    if (this.preloadPromises.has(url)) {
      return this.preloadPromises.get(url)!;
    }

    const startTime = performance.now();
    const promise = this.performPreload(url, type, options, startTime);
    
    this.preloadPromises.set(url, promise);
    return promise;
  }

  private async performPreload(url: string, type: string, options: PreloadOptions, startTime: number): Promise<PreloadResult> {
    try {
      let success = false;
      
      switch (type) {
        case 'script':
          success = await this.preloadScript(url, options);
          break;
        case 'style':
          success = await this.preloadStyle(url, options);
          break;
        case 'image':
          success = await this.preloadImage(url, options);
          break;
        case 'font':
          success = await this.preloadFont(url, options);
          break;
        case 'fetch':
          success = await this.preloadFetch(url, options);
          break;
        default:
          throw new Error(`Unsupported preload type: ${type}`);
      }

      const loadTime = performance.now() - startTime;
      
      if (success) {
        this.preloadedResources.add(url);
      }

      return {
        url,
        success,
        loadTime,
      };
    } catch (error) {
      const loadTime = performance.now() - startTime;
      return {
        url,
        success: false,
        error: error instanceof Error ? error.message : 'Unknown error',
        loadTime,
      };
    }
  }

  private preloadScript(url: string, options: PreloadOptions): Promise<boolean> {
    return new Promise((resolve, reject) => {
      // Check if script is already loaded
      const existingScript = document.querySelector(`script[src="${url}"]`);
      if (existingScript) {
        resolve(true);
        return;
      }

      const link = document.createElement('link');
      link.rel = 'preload';
      link.as = 'script';
      link.href = url;
      
      if (options.crossorigin) {
        link.crossOrigin = options.crossorigin;
      }
      
      if (options.integrity) {
        link.integrity = options.integrity;
      }

      const timeoutId = setTimeout(() => {
        reject(new Error(`Script preload timeout: ${url}`));
      }, options.timeout || 10000);

      link.onload = () => {
        clearTimeout(timeoutId);
        resolve(true);
      };

      link.onerror = () => {
        clearTimeout(timeoutId);
        reject(new Error(`Failed to preload script: ${url}`));
      };

      document.head.appendChild(link);
    });
  }

  private preloadStyle(url: string, options: PreloadOptions): Promise<boolean> {
    return new Promise((resolve, reject) => {
      // Check if style is already loaded
      const existingLink = document.querySelector(`link[href="${url}"]`);
      if (existingLink) {
        resolve(true);
        return;
      }

      const link = document.createElement('link');
      link.rel = 'preload';
      link.as = 'style';
      link.href = url;
      
      if (options.crossorigin) {
        link.crossOrigin = options.crossorigin;
      }

      const timeoutId = setTimeout(() => {
        reject(new Error(`Style preload timeout: ${url}`));
      }, options.timeout || 10000);

      link.onload = () => {
        clearTimeout(timeoutId);
        resolve(true);
      };

      link.onerror = () => {
        clearTimeout(timeoutId);
        reject(new Error(`Failed to preload style: ${url}`));
      };

      document.head.appendChild(link);
    });
  }

  private preloadImage(url: string, options: PreloadOptions): Promise<boolean> {
    return new Promise((resolve, reject) => {
      const img = new Image();
      
      if (options.crossorigin) {
        img.crossOrigin = options.crossorigin;
      }

      const timeoutId = setTimeout(() => {
        reject(new Error(`Image preload timeout: ${url}`));
      }, options.timeout || 10000);

      img.onload = () => {
        clearTimeout(timeoutId);
        this.resourceCache.set(url, img);
        resolve(true);
      };

      img.onerror = () => {
        clearTimeout(timeoutId);
        reject(new Error(`Failed to preload image: ${url}`));
      };

      img.src = url;
    });
  }

  private preloadFont(url: string, options: PreloadOptions): Promise<boolean> {
    return new Promise((resolve, reject) => {
      const link = document.createElement('link');
      link.rel = 'preload';
      link.as = 'font';
      link.href = url;
      link.crossOrigin = 'anonymous'; // Fonts typically require CORS

      const timeoutId = setTimeout(() => {
        reject(new Error(`Font preload timeout: ${url}`));
      }, options.timeout || 10000);

      link.onload = () => {
        clearTimeout(timeoutId);
        resolve(true);
      };

      link.onerror = () => {
        clearTimeout(timeoutId);
        reject(new Error(`Failed to preload font: ${url}`));
      };

      document.head.appendChild(link);
    });
  }

  private async preloadFetch(url: string, options: PreloadOptions): Promise<boolean> {
    try {
      const controller = new AbortController();
      const timeoutId = setTimeout(() => {
        controller.abort();
      }, options.timeout || 10000);

      const response = await fetch(url, {
        signal: controller.signal,
        mode: options.crossorigin === 'anonymous' ? 'cors' : 'same-origin',
      });

      clearTimeout(timeoutId);

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }

      // Cache the response
      const data = await response.json();
      this.resourceCache.set(url, data);
      
      return true;
    } catch (error) {
      throw new Error(`Failed to preload fetch: ${url} - ${error}`);
    }
  }

  // Preload multiple resources
  async preloadAll(resources: Array<{ url: string; type: 'script' | 'style' | 'image' | 'font' | 'fetch'; options?: PreloadOptions }>): Promise<PreloadResult[]> {
    const promises = resources.map(({ url, type, options }) => 
      this.preload(url, type, options || {})
    );
    
    return Promise.allSettled(promises).then(results => 
      results.map(result => 
        result.status === 'fulfilled' ? result.value : {
          url: '',
          success: false,
          error: result.reason?.message || 'Unknown error',
          loadTime: 0,
        }
      )
    );
  }

  // Preload critical resources for the application
  async preloadCriticalResources(): Promise<PreloadResult[]> {
    const criticalResources = [
      // Critical fonts
      { url: '/fonts/inter-regular.woff2', type: 'font' as const },
      { url: '/fonts/inter-medium.woff2', type: 'font' as const },
      
      // Critical images
      { url: '/images/logo.svg', type: 'image' as const },
      { url: '/images/dashboard-bg.webp', type: 'image' as const },
      
      // Critical API endpoints
      { url: '/api/auth/me', type: 'fetch' as const },
      { url: '/api/dashboard/stats', type: 'fetch' as const },
    ];

    console.log('🚀 Preloading critical resources...');
    const results = await this.preloadAll(criticalResources);
    
    const successful = results.filter(r => r.success).length;
    const total = results.length;
    
    console.log(`✅ Preloaded ${successful}/${total} critical resources`);
    
    return results;
  }

  // Preload resources based on user interaction hints
  preloadOnHover(componentType: string): void {
    const hoverPreloadMap: Record<string, Array<{ url: string; type: 'script' | 'style' | 'image' | 'font' | 'fetch' }>> = {
      dashboard: [
        { url: '/api/dashboard/analytics', type: 'fetch' },
        { url: '/api/dashboard/recent-activity', type: 'fetch' },
      ],
      tasks: [
        { url: '/api/tasks', type: 'fetch' },
        { url: '/api/tasks/templates', type: 'fetch' },
      ],
      workspace: [
        { url: '/api/workspaces', type: 'fetch' },
        { url: '/api/workspaces/templates', type: 'fetch' },
      ],
      files: [
        { url: '/api/files', type: 'fetch' },
        { url: '/api/files/recent', type: 'fetch' },
      ],
      ai: [
        { url: '/api/ai/models', type: 'fetch' },
        { url: '/api/ai/conversation-history', type: 'fetch' },
      ],
    };

    const resources = hoverPreloadMap[componentType];
    if (resources) {
      this.preloadAll(resources).catch(console.warn);
    }
  }

  // Preload images with WebP fallback
  async preloadImageWithFallback(baseUrl: string, options: PreloadOptions = {}): Promise<PreloadResult> {
    // Try WebP first if supported
    if (this.supportsWebP()) {
      try {
        const webpUrl = baseUrl.replace(/\.(jpg|jpeg|png)$/i, '.webp');
        return await this.preload(webpUrl, 'image', options);
      } catch (error) {
        // Fall back to original format
        console.warn('WebP preload failed, falling back to original format');
      }
    }

    return this.preload(baseUrl, 'image', options);
  }

  // Check WebP support
  private supportsWebP(): boolean {
    if (typeof window === 'undefined') return false;
    
    const canvas = document.createElement('canvas');
    canvas.width = 1;
    canvas.height = 1;
    
    return canvas.toDataURL('image/webp').indexOf('data:image/webp') === 0;
  }

  // Get cached resource
  getCachedResource(url: string): any {
    return this.resourceCache.get(url);
  }

  // Check if resource is preloaded
  isPreloaded(url: string): boolean {
    return this.preloadedResources.has(url);
  }

  // Clear cache
  clearCache(): void {
    this.resourceCache.clear();
    this.preloadedResources.clear();
    this.preloadPromises.clear();
  }

  // Get preload statistics
  getStats(): { preloaded: number; cached: number; pending: number } {
    return {
      preloaded: this.preloadedResources.size,
      cached: this.resourceCache.size,
      pending: this.preloadPromises.size - this.preloadedResources.size,
    };
  }
}

// Singleton instance
export const resourcePreloader = new ResourcePreloader();

// Utility functions for React components
export const useResourcePreloader = () => {
  const [stats, setStats] = React.useState(resourcePreloader.getStats());

  React.useEffect(() => {
    const interval = setInterval(() => {
      setStats(resourcePreloader.getStats());
    }, 1000);

    return () => clearInterval(interval);
  }, []);

  return {
    preload: resourcePreloader.preload.bind(resourcePreloader),
    preloadAll: resourcePreloader.preloadAll.bind(resourcePreloader),
    preloadOnHover: resourcePreloader.preloadOnHover.bind(resourcePreloader),
    isPreloaded: resourcePreloader.isPreloaded.bind(resourcePreloader),
    getCachedResource: resourcePreloader.getCachedResource.bind(resourcePreloader),
    stats,
  };
};

// Hook for preloading on component mount
export const usePreloadOnMount = (resources: Array<{ url: string; type: 'script' | 'style' | 'image' | 'font' | 'fetch'; options?: PreloadOptions }>) => {
  React.useEffect(() => {
    resourcePreloader.preloadAll(resources).catch(console.warn);
  }, []);
};

// HOC for automatic resource preloading
export const withResourcePreloading = <P extends object>(
  Component: React.ComponentType<P>,
  resources: Array<{ url: string; type: 'script' | 'style' | 'image' | 'font' | 'fetch'; options?: PreloadOptions }>
) => {
  const WrappedComponent = (props: P) => {
    usePreloadOnMount(resources);
    return <Component {...props} />;
  };

  WrappedComponent.displayName = `withResourcePreloading(${Component.displayName || Component.name})`;
  return WrappedComponent;
};

export default resourcePreloader;