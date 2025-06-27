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
 * Enhanced Background Sync for offline actions with comprehensive support
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
  case 'file-sync':
    event.waitUntil(syncFiles());
    break;
  case 'performance-metrics':
    event.waitUntil(syncPerformanceMetrics());
    break;
  case 'full-sync':
    event.waitUntil(performFullSync());
    break;
  case 'network-status-change':
    event.waitUntil(handleNetworkStatusChange());
    break;
  default:
    console.warn('[SW] Unknown sync tag:', event.tag);
  }
});

/**
 * Network status change handling
 */
async function handleNetworkStatusChange() {
  try {
    const isOnline = navigator.onLine;
    await recordNetworkStatus(isOnline, {
      timestamp: Date.now(),
      triggered: 'sync-event'
    });
    
    if (isOnline) {
      console.log('[SW] Network restored, starting full sync');
      await performFullSync();
    } else {
      console.log('[SW] Network lost, caching mode active');
    }
  } catch (error) {
    console.error('[SW] Error handling network status change:', error);
  }
}

/**
 * Perform full synchronization of all entities
 */
async function performFullSync() {
  try {
    console.log('[SW] Starting full sync...');
    
    // Sync all entity types in priority order
    await syncWorkspaces();
    await syncTasks();
    await syncFiles();
    await syncPerformanceMetrics();
    
    // Clean up old data
    await cleanupOldSyncData();
    
    console.log('[SW] Full sync completed');
    
    // Notify clients about completion
    await notifyClients({
      type: 'FULL_SYNC_COMPLETE',
      timestamp: Date.now()
    });
    
  } catch (error) {
    console.error('[SW] Full sync failed:', error);
    
    await notifyClients({
      type: 'FULL_SYNC_ERROR',
      error: error.message,
      timestamp: Date.now()
    });
  }
}

/**
 * Clean up old sync data and optimize storage
 */
async function cleanupOldSyncData() {
  const db = await initOfflineDB();
  const now = Date.now();
  const oldThreshold = now - (7 * 24 * 60 * 60 * 1000); // 7 days
  
  // Clean up old network status records
  const networkTransaction = db.transaction(['network_status'], 'readwrite');
  const networkStore = networkTransaction.objectStore('network_status');
  const networkIndex = networkStore.index('timestamp');
  
  const networkRequest = networkIndex.openCursor(IDBKeyRange.upperBound(oldThreshold));
  networkRequest.onsuccess = (event) => {
    const cursor = event.target.result;
    if (cursor) {
      cursor.delete();
      cursor.continue();
    }
  };
  
  // Clean up old cached responses
  const cacheTransaction = db.transaction(['cached_responses'], 'readwrite');
  const cacheStore = cacheTransaction.objectStore('cached_responses');
  
  const cacheRequest = cacheStore.openCursor();
  cacheRequest.onsuccess = (event) => {
    const cursor = event.target.result;
    if (cursor) {
      const record = cursor.value;
      if (record.expiresAt < now) {
        cursor.delete();
      }
      cursor.continue();
    }
  };
  
  console.log('[SW] Cleanup completed');
}

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
 * Enhanced Background Sync Functions with intelligent retry and conflict resolution
 */
async function syncWorkspaces() {
  try {
    console.log('[SW] Starting workspace sync...');
    await performEntitySync('workspaces', '/api/workspaces');
  } catch (error) {
    console.error('[SW] Workspace sync failed:', error);
  }
}

async function syncTasks() {
  try {
    console.log('[SW] Starting task sync...');
    await performEntitySync('tasks', '/api/tasks');
  } catch (error) {
    console.error('[SW] Task sync failed:', error);
  }
}

async function syncFiles() {
  try {
    console.log('[SW] Starting file sync...');
    await performEntitySync('files', '/api/files');
  } catch (error) {
    console.error('[SW] File sync failed:', error);
  }
}

async function performEntitySync(entityType, baseUrl) {
  const syncQueue = await getSyncQueue();
  const entityItems = syncQueue.filter(item => item.entityType === entityType);
  
  console.log(`[SW] Found ${entityItems.length} ${entityType} items to sync`);
  
  for (const item of entityItems) {
    try {
      // Check if it's time to retry
      if (item.nextRetry && Date.now() < item.nextRetry) {
        continue;
      }
      
      const success = await syncSingleItem(item);
      
      if (success) {
        await removeSyncQueueItem(item.id);
        console.log(`[SW] Successfully synced ${entityType} item:`, item.entityId);
        
        // Notify clients about successful sync
        await notifyClients({
          type: 'SYNC_SUCCESS',
          entityType,
          entityId: item.entityId,
          action: item.action
        });
      } else {
        // Handle failed sync with exponential backoff
        await handleSyncFailure(item);
      }
      
    } catch (error) {
      console.error(`[SW] Error syncing ${entityType} item:`, error);
      await handleSyncFailure(item, error.message);
    }
  }
}

async function syncSingleItem(item) {
  try {
    const response = await fetch(item.url, {
      method: item.method,
      headers: {
        'Content-Type': 'application/json',
        ...item.headers
      },
      body: item.data ? JSON.stringify(item.data) : undefined
    });
    
    if (response.ok) {
      // Check for conflicts based on response
      if (response.status === 409) {
        await handleSyncConflict(item, response);
        return false;
      }
      
      // Update local data with server response if needed
      if (item.action === 'create' || item.action === 'update') {
        const responseData = await response.json();
        await updateLocalEntity(item.entityType, item.entityId, responseData);
      }
      
      return true;
    } else if (response.status === 404 && item.action === 'delete') {
      // Item already deleted on server, consider this a success
      return true;
    } else {
      console.warn(`[SW] Sync failed with status ${response.status}:`, response.statusText);
      return false;
    }
    
  } catch (error) {
    if (error.name === 'TypeError' && error.message.includes('fetch')) {
      // Network error, will retry later
      console.log('[SW] Network error during sync, will retry');
      return false;
    }
    throw error;
  }
}

async function handleSyncFailure(item, errorMessage = null) {
  const retryCount = (item.retryCount || 0) + 1;
  
  if (retryCount >= item.maxRetries) {
    console.error(`[SW] Max retries reached for item ${item.id}, removing from queue`);
    await removeSyncQueueItem(item.id);
    
    // Notify clients about permanent failure
    await notifyClients({
      type: 'SYNC_FAILURE',
      entityType: item.entityType,
      entityId: item.entityId,
      action: item.action,
      error: errorMessage || 'Max retries exceeded'
    });
    
    return;
  }
  
  // Calculate exponential backoff delay
  const baseDelay = 1000; // 1 second
  const delay = baseDelay * Math.pow(2, retryCount);
  const nextRetry = Date.now() + delay + (Math.random() * 1000); // Add jitter
  
  await updateSyncQueueItem(item.id, {
    retryCount,
    nextRetry,
    lastError: errorMessage
  });
  
  console.log(`[SW] Scheduled retry ${retryCount}/${item.maxRetries} for item ${item.id} in ${delay}ms`);
}

async function handleSyncConflict(item, response) {
  try {
    const serverData = await response.json();
    const localData = item.data;
    
    // Store conflict for user resolution
    const conflict = {
      entityType: item.entityType,
      entityId: item.entityId,
      localData,
      serverData,
      conflictFields: detectConflictFields(localData, serverData),
      syncAction: item.action,
      timestamp: Date.now()
    };
    
    await storeConflict(conflict);
    
    // Notify clients about conflict
    await notifyClients({
      type: 'SYNC_CONFLICT',
      conflict
    });
    
    console.log(`[SW] Conflict detected for ${item.entityType} ${item.entityId}`);
    
  } catch (error) {
    console.error('[SW] Error handling sync conflict:', error);
  }
}

function detectConflictFields(local, server) {
  const conflictFields = [];
  const excludeFields = ['id', 'created_at', 'updated_at', 'version', 'sync_status'];
  
  for (const key in local) {
    if (excludeFields.includes(key)) continue;
    
    if (local[key] !== server[key]) {
      conflictFields.push(key);
    }
  }
  
  return conflictFields;
}

async function storeConflict(conflict) {
  const db = await initOfflineDB();
  const transaction = db.transaction(['conflicts'], 'readwrite');
  const store = transaction.objectStore('conflicts');
  
  const conflictWithId = {
    ...conflict,
    id: generateUUID()
  };
  
  return new Promise((resolve, reject) => {
    const request = store.add(conflictWithId);
    request.onsuccess = () => resolve(conflictWithId);
    request.onerror = () => reject(request.error);
  });
}

async function updateLocalEntity(entityType, entityId, serverData) {
  // Send message to clients to update local storage
  await notifyClients({
    type: 'UPDATE_LOCAL_ENTITY',
    entityType,
    entityId,
    data: serverData
  });
}

async function notifyClients(message) {
  const clients = await self.clients.matchAll();
  clients.forEach(client => {
    client.postMessage(message);
  });
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

// Enhanced IndexedDB helpers for comprehensive offline data management
let offlineDB = null;

async function initOfflineDB() {
  if (offlineDB) return offlineDB;
  
  return new Promise((resolve, reject) => {
    const request = indexedDB.open('BlueBirdHubServiceWorker', 2);
    
    request.onerror = () => reject(request.error);
    request.onsuccess = () => {
      offlineDB = request.result;
      resolve(offlineDB);
    };
    
    request.onupgradeneeded = (event) => {
      const db = event.target.result;
      
      // Offline actions store
      if (!db.objectStoreNames.contains('offline_actions')) {
        const store = db.createObjectStore('offline_actions', { keyPath: 'id' });
        store.createIndex('type', 'type', { unique: false });
        store.createIndex('timestamp', 'timestamp', { unique: false });
        store.createIndex('priority', 'priority', { unique: false });
      }
      
      // Performance metrics store
      if (!db.objectStoreNames.contains('performance_metrics')) {
        const metricsStore = db.createObjectStore('performance_metrics', { keyPath: 'id' });
        metricsStore.createIndex('timestamp', 'timestamp', { unique: false });
        metricsStore.createIndex('type', 'type', { unique: false });
      }
      
      // Cached responses store
      if (!db.objectStoreNames.contains('cached_responses')) {
        const cacheStore = db.createObjectStore('cached_responses', { keyPath: 'id' });
        cacheStore.createIndex('url', 'url', { unique: false });
        cacheStore.createIndex('timestamp', 'timestamp', { unique: false });
      }
      
      // Sync queue store
      if (!db.objectStoreNames.contains('sync_queue')) {
        const syncStore = db.createObjectStore('sync_queue', { keyPath: 'id' });
        syncStore.createIndex('entityType', 'entityType', { unique: false });
        syncStore.createIndex('priority', 'priority', { unique: false });
        syncStore.createIndex('retryCount', 'retryCount', { unique: false });
      }
      
      // Network status store
      if (!db.objectStoreNames.contains('network_status')) {
        const networkStore = db.createObjectStore('network_status', { keyPath: 'id' });
        networkStore.createIndex('timestamp', 'timestamp', { unique: false });
      }
    };
  });
}

async function getOfflineActions(type) {
  const db = await initOfflineDB();
  const transaction = db.transaction(['offline_actions'], 'readonly');
  const store = transaction.objectStore('offline_actions');
  const index = store.index('type');
  
  return new Promise((resolve, reject) => {
    const request = index.getAll(type);
    request.onsuccess = () => resolve(request.result || []);
    request.onerror = () => reject(request.error);
  });
}

async function addOfflineAction(action) {
  const db = await initOfflineDB();
  const transaction = db.transaction(['offline_actions'], 'readwrite');
  const store = transaction.objectStore('offline_actions');
  
  const actionWithId = {
    ...action,
    id: generateUUID(),
    timestamp: Date.now(),
    retryCount: 0,
    maxRetries: 3
  };
  
  return new Promise((resolve, reject) => {
    const request = store.add(actionWithId);
    request.onsuccess = () => resolve(actionWithId);
    request.onerror = () => reject(request.error);
  });
}

async function clearOfflineActions(type) {
  const db = await initOfflineDB();
  const transaction = db.transaction(['offline_actions'], 'readwrite');
  const store = transaction.objectStore('offline_actions');
  const index = store.index('type');
  
  return new Promise((resolve) => {
    const request = index.openCursor(type);
    request.onsuccess = (event) => {
      const cursor = event.target.result;
      if (cursor) {
        cursor.delete();
        cursor.continue();
      } else {
        resolve();
      }
    };
  });
}

async function removeOfflineAction(id) {
  const db = await initOfflineDB();
  const transaction = db.transaction(['offline_actions'], 'readwrite');
  const store = transaction.objectStore('offline_actions');
  
  return new Promise((resolve, reject) => {
    const request = store.delete(id);
    request.onsuccess = () => resolve();
    request.onerror = () => reject(request.error);
  });
}

async function getStoredMetrics() {
  const db = await initOfflineDB();
  const transaction = db.transaction(['performance_metrics'], 'readonly');
  const store = transaction.objectStore('performance_metrics');
  
  return new Promise((resolve, reject) => {
    const request = store.getAll();
    request.onsuccess = () => resolve(request.result || []);
    request.onerror = () => reject(request.error);
  });
}

async function clearStoredMetrics() {
  const db = await initOfflineDB();
  const transaction = db.transaction(['performance_metrics'], 'readwrite');
  const store = transaction.objectStore('performance_metrics');
  
  return new Promise((resolve, reject) => {
    const request = store.clear();
    request.onsuccess = () => resolve();
    request.onerror = () => reject(request.error);
  });
}

async function storeMetric(metric) {
  const db = await initOfflineDB();
  const transaction = db.transaction(['performance_metrics'], 'readwrite');
  const store = transaction.objectStore('performance_metrics');
  
  const metricWithId = {
    ...metric,
    id: generateUUID(),
    timestamp: Date.now()
  };
  
  return new Promise((resolve, reject) => {
    const request = store.add(metricWithId);
    request.onsuccess = () => resolve();
    request.onerror = () => reject(request.error);
  });
}

async function addToSyncQueue(item) {
  const db = await initOfflineDB();
  const transaction = db.transaction(['sync_queue'], 'readwrite');
  const store = transaction.objectStore('sync_queue');
  
  const queueItem = {
    ...item,
    id: generateUUID(),
    timestamp: Date.now(),
    retryCount: 0,
    maxRetries: 5,
    nextRetry: Date.now() + (1000 * Math.pow(2, 0)) // Exponential backoff
  };
  
  return new Promise((resolve, reject) => {
    const request = store.add(queueItem);
    request.onsuccess = () => resolve(queueItem);
    request.onerror = () => reject(request.error);
  });
}

async function getSyncQueue() {
  const db = await initOfflineDB();
  const transaction = db.transaction(['sync_queue'], 'readonly');
  const store = transaction.objectStore('sync_queue');
  
  return new Promise((resolve, reject) => {
    const request = store.getAll();
    request.onsuccess = () => {
      const items = request.result || [];
      // Sort by priority (higher first) then by timestamp
      items.sort((a, b) => (b.priority || 0) - (a.priority || 0) || a.timestamp - b.timestamp);
      resolve(items);
    };
    request.onerror = () => reject(request.error);
  });
}

async function removeSyncQueueItem(id) {
  const db = await initOfflineDB();
  const transaction = db.transaction(['sync_queue'], 'readwrite');
  const store = transaction.objectStore('sync_queue');
  
  return new Promise((resolve, reject) => {
    const request = store.delete(id);
    request.onsuccess = () => resolve();
    request.onerror = () => reject(request.error);
  });
}

async function updateSyncQueueItem(id, updates) {
  const db = await initOfflineDB();
  const transaction = db.transaction(['sync_queue'], 'readwrite');
  const store = transaction.objectStore('sync_queue');
  
  return new Promise((resolve, reject) => {
    const getRequest = store.get(id);
    getRequest.onsuccess = () => {
      const item = getRequest.result;
      if (item) {
        const updatedItem = { ...item, ...updates };
        const putRequest = store.put(updatedItem);
        putRequest.onsuccess = () => resolve(updatedItem);
        putRequest.onerror = () => reject(putRequest.error);
      } else {
        reject(new Error('Item not found'));
      }
    };
    getRequest.onerror = () => reject(getRequest.error);
  });
}

async function storeCachedResponse(url, response, ttl = 3600000) { // 1 hour default TTL
  const db = await initOfflineDB();
  const transaction = db.transaction(['cached_responses'], 'readwrite');
  const store = transaction.objectStore('cached_responses');
  
  const cachedItem = {
    id: btoa(url), // Use base64 encoded URL as ID
    url,
    response: {
      status: response.status,
      statusText: response.statusText,
      headers: Object.fromEntries(response.headers.entries()),
      body: await response.text()
    },
    timestamp: Date.now(),
    ttl,
    expiresAt: Date.now() + ttl
  };
  
  return new Promise((resolve, reject) => {
    const request = store.put(cachedItem);
    request.onsuccess = () => resolve();
    request.onerror = () => reject(request.error);
  });
}

async function getCachedResponse(url) {
  const db = await initOfflineDB();
  const transaction = db.transaction(['cached_responses'], 'readonly');
  const store = transaction.objectStore('cached_responses');
  
  return new Promise((resolve, reject) => {
    const request = store.get(btoa(url));
    request.onsuccess = () => {
      const cached = request.result;
      if (cached && cached.expiresAt > Date.now()) {
        // Create a new Response object from cached data
        const response = new Response(cached.response.body, {
          status: cached.response.status,
          statusText: cached.response.statusText,
          headers: cached.response.headers
        });
        resolve(response);
      } else {
        resolve(null);
      }
    };
    request.onerror = () => reject(request.error);
  });
}

async function recordNetworkStatus(isOnline, details = {}) {
  const db = await initOfflineDB();
  const transaction = db.transaction(['network_status'], 'readwrite');
  const store = transaction.objectStore('network_status');
  
  const statusRecord = {
    id: generateUUID(),
    isOnline,
    timestamp: Date.now(),
    connectionType: navigator.connection?.effectiveType || 'unknown',
    downlink: navigator.connection?.downlink || null,
    rtt: navigator.connection?.rtt || null,
    ...details
  };
  
  return new Promise((resolve, reject) => {
    const request = store.add(statusRecord);
    request.onsuccess = () => resolve();
    request.onerror = () => reject(request.error);
  });
}

// Enhanced message handling for offline functionality
self.addEventListener('message', event => {
  const { data } = event;
  
  if (!data) return;
  
  switch (data.type) {
  case 'PERFORMANCE_METRIC':
    event.waitUntil(storePerformanceMetric(data.metric));
    break;
    
  case 'OFFLINE_ACTION':
    event.waitUntil(handleOfflineAction(data.action));
    break;
    
  case 'FORCE_SYNC':
    event.waitUntil(performFullSync());
    break;
    
  case 'CLEAR_CACHE':
    event.waitUntil(clearAllCaches());
    break;
    
  case 'GET_OFFLINE_STATUS':
    event.waitUntil(sendOfflineStatus(event.ports[0]));
    break;
    
  case 'RESOLVE_CONFLICT':
    event.waitUntil(resolveConflict(data.conflictId, data.resolution));
    break;
    
  default:
    console.log('[SW] Unknown message type:', data.type);
  }
});

async function handleOfflineAction(action) {
  try {
    // Add action to sync queue
    await addToSyncQueue({
      entityType: action.entityType,
      entityId: action.entityId,
      action: action.action,
      data: action.data,
      url: action.url,
      method: action.method,
      headers: action.headers,
      priority: action.priority || 1
    });
    
    console.log('[SW] Offline action queued:', action);
    
    // Try to register background sync
    if ('serviceWorker' in navigator && 'sync' in window.ServiceWorkerRegistration.prototype) {
      try {
        await self.registration.sync.register(`${action.entityType}-sync`);
      } catch (error) {
        console.warn('[SW] Background sync registration failed:', error);
      }
    }
    
  } catch (error) {
    console.error('[SW] Error handling offline action:', error);
  }
}

async function storePerformanceMetric(metric) {
  try {
    await storeMetric({
      type: 'performance',
      data: metric,
      timestamp: Date.now(),
      offline: !navigator.onLine
    });
    
    console.log('[SW] Performance metric stored:', metric.name);
    
  } catch (error) {
    console.error('[SW] Error storing performance metric:', error);
  }
}

async function clearAllCaches() {
  try {
    const cacheNames = await caches.keys();
    await Promise.all(cacheNames.map(name => caches.delete(name)));
    
    // Clear IndexedDB caches
    const db = await initOfflineDB();
    const transaction = db.transaction(['cached_responses'], 'readwrite');
    const store = transaction.objectStore('cached_responses');
    await new Promise((resolve, reject) => {
      const request = store.clear();
      request.onsuccess = () => resolve();
      request.onerror = () => reject(request.error);
    });
    
    console.log('[SW] All caches cleared');
    
  } catch (error) {
    console.error('[SW] Error clearing caches:', error);
  }
}

async function sendOfflineStatus(port) {
  try {
    const syncQueue = await getSyncQueue();
    const db = await initOfflineDB();
    
    // Get conflict count
    const conflictTransaction = db.transaction(['conflicts'], 'readonly');
    const conflictStore = conflictTransaction.objectStore('conflicts');
    const conflictCount = await new Promise((resolve, reject) => {
      const request = conflictStore.count();
      request.onsuccess = () => resolve(request.result);
      request.onerror = () => reject(request.error);
    });
    
    const status = {
      isOnline: navigator.onLine,
      syncQueueSize: syncQueue.length,
      conflictCount,
      lastSync: await getLastSyncTime(),
      cacheSize: await estimateCacheSize()
    };
    
    port.postMessage(status);
    
  } catch (error) {
    console.error('[SW] Error getting offline status:', error);
    port.postMessage({ error: error.message });
  }
}

async function resolveConflict(conflictId, resolution) {
  try {
    const db = await initOfflineDB();
    const transaction = db.transaction(['conflicts'], 'readwrite');
    const store = transaction.objectStore('conflicts');
    
    // Get the conflict
    const conflict = await new Promise((resolve, reject) => {
      const request = store.get(conflictId);
      request.onsuccess = () => resolve(request.result);
      request.onerror = () => reject(request.error);
    });
    
    if (!conflict) {
      throw new Error('Conflict not found');
    }
    
    // Apply resolution
    let resolvedData;
    switch (resolution.strategy) {
    case 'local':
      resolvedData = conflict.localData;
      break;
    case 'remote':
      resolvedData = conflict.serverData;
      break;
    case 'merge':
      resolvedData = { ...conflict.serverData, ...resolution.mergedData };
      break;
    default:
      throw new Error('Unknown resolution strategy');
    }
    
    // Update the conflict record
    const updatedConflict = {
      ...conflict,
      resolved: true,
      resolvedAt: Date.now(),
      resolution: resolution.strategy,
      resolvedData
    };
    
    await new Promise((resolve, reject) => {
      const request = store.put(updatedConflict);
      request.onsuccess = () => resolve();
      request.onerror = () => reject(request.error);
    });
    
    // Add resolved data to sync queue
    await addToSyncQueue({
      entityType: conflict.entityType,
      entityId: conflict.entityId,
      action: 'update',
      data: resolvedData,
      url: `/api/${conflict.entityType}/${conflict.entityId}`,
      method: 'PUT',
      priority: 2 // High priority for conflict resolution
    });
    
    console.log('[SW] Conflict resolved:', conflictId);
    
  } catch (error) {
    console.error('[SW] Error resolving conflict:', error);
  }
}

async function getLastSyncTime() {
  try {
    const db = await initOfflineDB();
    const transaction = db.transaction(['metadata'], 'readonly');
    const store = transaction.objectStore('metadata');
    
    const result = await new Promise((resolve, reject) => {
      const request = store.get('lastSyncTime');
      request.onsuccess = () => resolve(request.result);
      request.onerror = () => reject(request.error);
    });
    
    return result ? result.value : null;
    
  } catch (error) {
    console.error('[SW] Error getting last sync time:', error);
    return null;
  }
}

async function setLastSyncTime(timestamp) {
  try {
    const db = await initOfflineDB();
    const transaction = db.transaction(['metadata'], 'readwrite');
    const store = transaction.objectStore('metadata');
    
    await new Promise((resolve, reject) => {
      const request = store.put({
        key: 'lastSyncTime',
        value: timestamp,
        updatedAt: Date.now()
      });
      request.onsuccess = () => resolve();
      request.onerror = () => reject(request.error);
    });
    
  } catch (error) {
    console.error('[SW] Error setting last sync time:', error);
  }
}

async function estimateCacheSize() {
  try {
    if ('storage' in navigator && 'estimate' in navigator.storage) {
      const estimate = await navigator.storage.estimate();
      return estimate.usage || 0;
    }
    return 0;
  } catch (error) {
    console.error('[SW] Error estimating cache size:', error);
    return 0;
  }
}

// UUID generator utility
function generateUUID() {
  return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function(c) {
    const r = Math.random() * 16 | 0;
    const v = c === 'x' ? r : (r & 0x3 | 0x8);
    return v.toString(16);
  });
}

console.log('[SW] OrdnungsHub Service Worker v2.0.0 loaded with advanced caching strategies');