/**
 * OrdnungsHub Service Worker - Phase 2 Performance Optimization
 * Provides offline capabilities, advanced caching, and background sync
 */

const CACHE_NAME = 'ordnungshub-v2.0.0';
const STATIC_CACHE = 'ordnungshub-static-v2';
const DYNAMIC_CACHE = 'ordnungshub-dynamic-v2';
const API_CACHE = 'ordnungshub-api-v2';

// Cache duration configurations (in milliseconds)
const CACHE_DURATIONS = {
  static: 7 * 24 * 60 * 60 * 1000, // 7 days
  dynamic: 3 * 24 * 60 * 60 * 1000, // 3 days
  api: 10 * 60 * 1000, // 10 minutes
  images: 30 * 24 * 60 * 60 * 1000 // 30 days
};

// Resources to cache immediately
const STATIC_ASSETS = [
  '/',
  '/manifest.json',
  '/static/css/main.css',
  '/static/js/main.js',
  '/static/js/vendor.js',
  '/static/images/logo.svg',
  '/offline.html'
];

// API endpoints to cache with stale-while-revalidate strategy
const CACHEABLE_API_ROUTES = [
  '/api/workspaces',
  '/api/tasks',
  '/api/dashboard',
  '/api/performance/health'
];

// Network-first routes (always try network first)
const NETWORK_FIRST_ROUTES = [
  '/api/auth',
  '/api/files/upload',
  '/api/performance/metrics'
];

/**
 * Service Worker Installation
 */
self.addEventListener('install', event => {
  console.log('[SW] Installing Service Worker v2.0.0');
    
  event.waitUntil(
    Promise.all([
      // Cache static assets
      caches.open(STATIC_CACHE).then(cache => {
        console.log('[SW] Pre-caching static assets');
        return cache.addAll(STATIC_ASSETS);
      }),
            
      // Skip waiting to activate immediately
      self.skipWaiting()
    ])
  );
});

/**
 * Service Worker Activation
 */
self.addEventListener('activate', event => {
  console.log('[SW] Activating Service Worker v2.0.0');
    
  event.waitUntil(
    Promise.all([
      // Clean up old caches
      cleanupOldCaches(),
            
      // Claim all clients immediately
      self.clients.claim()
    ])
  );
});

/**
 * Fetch Event Handler - Advanced Caching Strategies
 */
self.addEventListener('fetch', event => {
  const { request } = event;
  const url = new URL(request.url);
    
  // Skip cross-origin requests
  if (url.origin !== location.origin) {
    return;
  }
    
  // Route requests to appropriate caching strategy
  if (isStaticAsset(request)) {
    event.respondWith(cacheFirstStrategy(request, STATIC_CACHE));
  } else if (isAPIRequest(request)) {
    event.respondWith(handleAPIRequest(request));
  } else if (isImageRequest(request)) {
    event.respondWith(cacheFirstStrategy(request, DYNAMIC_CACHE));
  } else {
    event.respondWith(networkFirstStrategy(request));
  }
});

/**
 * Background Sync for offline actions
 */
self.addEventListener('sync', event => {
  console.log('[SW] Background sync triggered:', event.tag);
    
  switch (event.tag) {
  case 'workspace-sync':
    event.waitUntil(syncWorkspaces());
    break;
  case 'task-sync':
    event.waitUntil(syncTasks());
    break;
  case 'performance-metrics':
    event.waitUntil(syncPerformanceMetrics());
    break;
  }
});

/**
 * Push Notifications
 */
self.addEventListener('push', event => {
  const options = {
    body: event.data ? event.data.text() : 'OrdnungsHub notification',
    icon: '/static/images/icon-192.png',
    badge: '/static/images/badge-72.png',
    tag: 'ordnungshub-notification',
    requireInteraction: false
  };
    
  event.waitUntil(
    self.registration.showNotification('OrdnungsHub', options)
  );
});

/**
 * Caching Strategies
 */

// Cache First Strategy - Good for static assets
async function cacheFirstStrategy(request, cacheName) {
  try {
    const cache = await caches.open(cacheName);
    const cachedResponse = await cache.match(request);
        
    if (cachedResponse && !isExpired(cachedResponse)) {
      // Return cached version and update in background
      updateCacheInBackground(request, cache);
      return cachedResponse;
    }
        
    // Fetch from network and cache
    const networkResponse = await fetch(request);
    if (networkResponse.ok) {
      await cache.put(request, networkResponse.clone());
    }
    return networkResponse;
        
  } catch (error) {
    console.warn('[SW] Cache first strategy failed:', error);
    return await caches.match('/offline.html');
  }
}

// Network First Strategy - Good for dynamic content
async function networkFirstStrategy(request) {
  try {
    const networkResponse = await fetch(request);
        
    if (networkResponse.ok) {
      const cache = await caches.open(DYNAMIC_CACHE);
      await cache.put(request, networkResponse.clone());
    }
        
    return networkResponse;
        
  } catch (error) {
    console.log('[SW] Network failed, trying cache:', request.url);
    const cachedResponse = await caches.match(request);
        
    if (cachedResponse) {
      return cachedResponse;
    }
        
    // Return offline page for navigation requests
    if (request.mode === 'navigate') {
      return await caches.match('/offline.html');
    }
        
    throw error;
  }
}

// Stale While Revalidate - Good for API responses
async function staleWhileRevalidateStrategy(request) {
  const cache = await caches.open(API_CACHE);
  const cachedResponse = await cache.match(request);
    
  // Fetch from network in background
  const networkPromise = fetch(request).then(response => {
    if (response.ok) {
      cache.put(request, response.clone());
    }
    return response;
  }).catch(error => {
    console.warn('[SW] Network request failed:', error);
    return null;
  });
    
  // Return cached version immediately if available
  if (cachedResponse && !isExpired(cachedResponse)) {
    // Update cache in background
    networkPromise;
    return cachedResponse;
  }
    
  // Return network response if no cache or cache expired
  return await networkPromise || cachedResponse;
}

/**
 * API Request Handler
 */
async function handleAPIRequest(request) {
  const url = new URL(request.url);
  const pathname = url.pathname;
    
  // Network-first for critical endpoints
  if (NETWORK_FIRST_ROUTES.some(route => pathname.startsWith(route))) {
    return await networkFirstStrategy(request);
  }
    
  // Stale-while-revalidate for cacheable endpoints
  if (CACHEABLE_API_ROUTES.some(route => pathname.startsWith(route))) {
    return await staleWhileRevalidateStrategy(request);
  }
    
  // Default to network-first for other API requests
  return await networkFirstStrategy(request);
}

/**
 * Background Sync Functions
 */
async function syncWorkspaces() {
  try {
    const offlineActions = await getOfflineActions('workspaces');
        
    for (const action of offlineActions) {
      await fetch(action.url, {
        method: action.method,
        headers: action.headers,
        body: action.body
      });
    }
        
    await clearOfflineActions('workspaces');
    console.log('[SW] Workspace sync completed');
        
  } catch (error) {
    console.error('[SW] Workspace sync failed:', error);
  }
}

async function syncTasks() {
  try {
    const offlineActions = await getOfflineActions('tasks');
        
    for (const action of offlineActions) {
      await fetch(action.url, {
        method: action.method,
        headers: action.headers,
        body: action.body
      });
    }
        
    await clearOfflineActions('tasks');
    console.log('[SW] Task sync completed');
        
  } catch (error) {
    console.error('[SW] Task sync failed:', error);
  }
}

async function syncPerformanceMetrics() {
  try {
    const metrics = await getStoredMetrics();
        
    if (metrics.length > 0) {
      await fetch('/api/performance/metrics', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ metrics })
      });
            
      await clearStoredMetrics();
      console.log('[SW] Performance metrics synced');
    }
        
  } catch (error) {
    console.error('[SW] Performance metrics sync failed:', error);
  }
}

/**
 * Utility Functions
 */
function isStaticAsset(request) {
  const url = new URL(request.url);
  return url.pathname.startsWith('/static/') || 
           url.pathname === '/' ||
           url.pathname.endsWith('.html') ||
           url.pathname.endsWith('.css') ||
           url.pathname.endsWith('.js');
}

function isAPIRequest(request) {
  const url = new URL(request.url);
  return url.pathname.startsWith('/api/');
}

function isImageRequest(request) {
  const url = new URL(request.url);
  return /\.(jpg|jpeg|png|gif|webp|svg)$/i.test(url.pathname);
}

function isExpired(response) {
  const dateHeader = response.headers.get('date');
  if (!dateHeader) return false;
    
  const responseDate = new Date(dateHeader);
  const now = new Date();
  const maxAge = CACHE_DURATIONS.api; // Default cache duration
    
  return (now - responseDate) > maxAge;
}

async function updateCacheInBackground(request, cache) {
  try {
    const networkResponse = await fetch(request);
    if (networkResponse.ok) {
      await cache.put(request, networkResponse.clone());
    }
  } catch (error) {
    console.warn('[SW] Background cache update failed:', error);
  }
}

async function cleanupOldCaches() {
  const cacheNames = await caches.keys();
  const validCaches = [CACHE_NAME, STATIC_CACHE, DYNAMIC_CACHE, API_CACHE];
    
  const deletePromises = cacheNames
    .filter(cacheName => !validCaches.includes(cacheName))
    .map(cacheName => caches.delete(cacheName));
    
  await Promise.all(deletePromises);
  console.log('[SW] Old caches cleaned up');
}

// IndexedDB helpers for offline data
async function getOfflineActions(type) {
  // Implementation would use IndexedDB to store offline actions
  return [];
}

async function clearOfflineActions(type) {
  // Implementation would clear offline actions from IndexedDB
}

async function getStoredMetrics() {
  // Implementation would retrieve performance metrics from IndexedDB
  return [];
}

async function clearStoredMetrics() {
  // Implementation would clear stored metrics from IndexedDB
}

// Performance monitoring
self.addEventListener('message', event => {
  if (event.data && event.data.type === 'PERFORMANCE_METRIC') {
    // Store performance metrics for background sync
    storePerformanceMetric(event.data.metric);
  }
});

async function storePerformanceMetric(metric) {
  // Implementation would store metrics in IndexedDB for later sync
  console.log('[SW] Performance metric stored:', metric);
}

console.log('[SW] OrdnungsHub Service Worker v2.0.0 loaded with advanced caching strategies');