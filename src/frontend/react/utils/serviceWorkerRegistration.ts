/**
 * Service Worker Registration and Management
 * Phase 2 Performance Optimization - PWA Features
 */

interface ServiceWorkerConfig {
  onSuccess?: (registration: ServiceWorkerRegistration) => void;
  onUpdate?: (registration: ServiceWorkerRegistration) => void;
  onOffline?: () => void;
  onOnline?: () => void;
}

const isLocalhost = Boolean(
  window.location.hostname === 'localhost' ||
  window.location.hostname === '[::1]' ||
  window.location.hostname.match(
    /^127(?:\.(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)){3}$/
  )
);

/**
 * Register Service Worker
 */
export function registerServiceWorker(config?: ServiceWorkerConfig): void {
  if ('serviceWorker' in navigator) {
    const publicUrl = new URL(process.env.PUBLIC_URL || '', window.location.href);
    
    if (publicUrl.origin !== window.location.origin) {
      return;
    }

    window.addEventListener('load', () => {
      const swUrl = `${process.env.PUBLIC_URL}/service-worker.js`;

      if (isLocalhost) {
        checkValidServiceWorker(swUrl, config);
        navigator.serviceWorker.ready.then(() => {
          console.log(
            '[SW] This web app is being served cache-first by a service worker. ' +
            'To learn more, visit https://cra.link/PWA'
          );
        });
      } else {
        registerValidServiceWorker(swUrl, config);
      }
    });

    // Setup online/offline event listeners
    setupConnectionListeners(config);
  }
}

/**
 * Register valid service worker
 */
function registerValidServiceWorker(swUrl: string, config?: ServiceWorkerConfig): void {
  navigator.serviceWorker
    .register(swUrl)
    .then((registration) => {
      console.log('[SW] Service Worker registered successfully');
      
      registration.onupdatefound = () => {
        const installingWorker = registration.installing;
        if (installingWorker == null) {
          return;
        }

        installingWorker.onstatechange = () => {
          if (installingWorker.state === 'installed') {
            if (navigator.serviceWorker.controller) {
              console.log(
                '[SW] New content is available and will be used when all ' +
                'tabs for this page are closed. See https://cra.link/PWA.'
              );

              if (config && config.onUpdate) {
                config.onUpdate(registration);
              }
            } else {
              console.log('[SW] Content is cached for offline use.');

              if (config && config.onSuccess) {
                config.onSuccess(registration);
              }
            }
          }
        };
      };

      // Setup background sync
      setupBackgroundSync(registration);
      
      // Setup push notifications
      setupPushNotifications(registration);
    })
    .catch((error) => {
      console.error('[SW] Service Worker registration failed:', error);
    });
}

/**
 * Check if service worker is valid
 */
function checkValidServiceWorker(swUrl: string, config?: ServiceWorkerConfig): void {
  fetch(swUrl, {
    headers: { 'Service-Worker': 'script' },
  })
    .then((response) => {
      const contentType = response.headers.get('content-type');
      if (
        response.status === 404 ||
        (contentType != null && contentType.indexOf('javascript') === -1)
      ) {
        navigator.serviceWorker.ready.then((registration) => {
          registration.unregister().then(() => {
            window.location.reload();
          });
        });
      } else {
        registerValidServiceWorker(swUrl, config);
      }
    })
    .catch(() => {
      console.log('[SW] No internet connection found. App is running in offline mode.');
    });
}

/**
 * Setup connection event listeners
 */
function setupConnectionListeners(config?: ServiceWorkerConfig): void {
  window.addEventListener('online', () => {
    console.log('[SW] Connection restored');
    if (config && config.onOnline) {
      config.onOnline();
    }
    
    // Trigger background sync when coming back online
    triggerBackgroundSync();
  });

  window.addEventListener('offline', () => {
    console.log('[SW] Connection lost');
    if (config && config.onOffline) {
      config.onOffline();
    }
  });
}

/**
 * Setup background sync
 */
function setupBackgroundSync(registration: ServiceWorkerRegistration): void {
  if ('sync' in registration) {
    console.log('[SW] Background Sync is supported');
    
    // Register periodic sync for performance metrics
    setInterval(() => {
      if (navigator.onLine) {
        registration.sync.register('performance-metrics');
      }
    }, 5 * 60 * 1000); // Every 5 minutes
  }
}

/**
 * Setup push notifications
 */
function setupPushNotifications(registration: ServiceWorkerRegistration): void {
  if ('PushManager' in window) {
    console.log('[SW] Push messaging is supported');
    
    // Request notification permission
    Notification.requestPermission().then((permission) => {
      if (permission === 'granted') {
        console.log('[SW] Notification permission granted');
        subscribeToPushNotifications(registration);
      }
    });
  }
}

/**
 * Subscribe to push notifications
 */
async function subscribeToPushNotifications(registration: ServiceWorkerRegistration): Promise<void> {
  try {
    const subscription = await registration.pushManager.subscribe({
      userVisibleOnly: true,
      applicationServerKey: process.env.REACT_APP_VAPID_PUBLIC_KEY
    });
    
    console.log('[SW] Push subscription successful:', subscription);
    
    // Send subscription to server
    await fetch('/api/push/subscribe', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(subscription),
    });
  } catch (error) {
    console.error('[SW] Push subscription failed:', error);
  }
}

/**
 * Trigger background sync manually
 */
export function triggerBackgroundSync(): void {
  if ('serviceWorker' in navigator) {
    navigator.serviceWorker.ready.then((registration) => {
      if ('sync' in registration) {
        Promise.all([
          registration.sync.register('workspace-sync'),
          registration.sync.register('task-sync'),
          registration.sync.register('performance-metrics')
        ]).then(() => {
          console.log('[SW] Background sync triggered');
        }).catch((error) => {
          console.error('[SW] Background sync failed:', error);
        });
      }
    });
  }
}

/**
 * Send message to service worker
 */
export function sendMessageToServiceWorker(message: any): void {
  if ('serviceWorker' in navigator && navigator.serviceWorker.controller) {
    navigator.serviceWorker.controller.postMessage(message);
  }
}

/**
 * Store offline action for later sync
 */
export function storeOfflineAction(type: string, action: any): void {
  const offlineActions = JSON.parse(localStorage.getItem('offlineActions') || '[]');
  offlineActions.push({
    type,
    action,
    timestamp: Date.now()
  });
  localStorage.setItem('offlineActions', JSON.stringify(offlineActions));
  
  console.log('[SW] Offline action stored:', type);
}

/**
 * Get stored offline actions
 */
export function getOfflineActions(type?: string): any[] {
  const offlineActions = JSON.parse(localStorage.getItem('offlineActions') || '[]');
  
  if (type) {
    return offlineActions.filter((item: any) => item.type === type);
  }
  
  return offlineActions;
}

/**
 * Clear offline actions
 */
export function clearOfflineActions(type?: string): void {
  if (type) {
    const offlineActions = JSON.parse(localStorage.getItem('offlineActions') || '[]');
    const filtered = offlineActions.filter((item: any) => item.type !== type);
    localStorage.setItem('offlineActions', JSON.stringify(filtered));
  } else {
    localStorage.removeItem('offlineActions');
  }
  
  console.log('[SW] Offline actions cleared:', type || 'all');
}

/**
 * Check if app is running standalone (PWA)
 */
export function isRunningStandalone(): boolean {
  return window.matchMedia('(display-mode: standalone)').matches ||
         (window.navigator as any).standalone === true;
}

/**
 * Performance monitoring integration
 */
export function reportPerformanceMetric(metric: any): void {
  // Store metric locally
  const metrics = JSON.parse(localStorage.getItem('performanceMetrics') || '[]');
  metrics.push({
    ...metric,
    timestamp: Date.now(),
    standalone: isRunningStandalone()
  });
  
  // Keep only last 100 metrics
  if (metrics.length > 100) {
    metrics.splice(0, metrics.length - 100);
  }
  
  localStorage.setItem('performanceMetrics', JSON.stringify(metrics));
  
  // Send to service worker for background sync
  sendMessageToServiceWorker({
    type: 'PERFORMANCE_METRIC',
    metric
  });
}

/**
 * Unregister service worker
 */
export function unregisterServiceWorker(): void {
  if ('serviceWorker' in navigator) {
    navigator.serviceWorker.ready
      .then((registration) => {
        registration.unregister();
      })
      .catch((error) => {
        console.error('[SW] Service Worker unregistration failed:', error);
      });
  }
}

/**
 * Update service worker
 */
export function updateServiceWorker(): void {
  if ('serviceWorker' in navigator) {
    navigator.serviceWorker.ready.then((registration) => {
      registration.update();
    });
  }
}

// Default configuration
const defaultConfig: ServiceWorkerConfig = {
  onSuccess: () => console.log('[SW] Content is cached for offline use.'),
  onUpdate: () => console.log('[SW] New content is available; please refresh.'),
  onOffline: () => console.log('[SW] App is now offline.'),
  onOnline: () => console.log('[SW] App is back online.')
};

// Auto-register with default config if no explicit registration
if (process.env.NODE_ENV === 'production') {
  registerServiceWorker(defaultConfig);
}