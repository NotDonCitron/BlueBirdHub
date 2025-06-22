/**
 * Progressive Web App Components - Phase 2 Performance Features
 * Provides PWA-specific functionality like install prompts, offline indicators, and share handling
 */

import React, { useState, useEffect, useCallback } from 'react';
import { 
  isRunningStandalone, 
  reportPerformanceMetric,
  sendMessageToServiceWorker 
} from '../utils/serviceWorkerRegistration';

// Types
interface BeforeInstallPromptEvent extends Event {
  prompt(): Promise<void>;
  userChoice: Promise<{ outcome: 'accepted' | 'dismissed' }>;
}

interface ShareData {
  title?: string;
  text?: string;
  url?: string;
  files?: File[];
}

// PWA Install Prompt Component
export const PWAInstallPrompt: React.FC = () => {
  const [deferredPrompt, setDeferredPrompt] = useState<BeforeInstallPromptEvent | null>(null);
  const [showInstallPrompt, setShowInstallPrompt] = useState(false);
  const [isStandalone, setIsStandalone] = useState(false);

  useEffect(() => {
    setIsStandalone(isRunningStandalone());

    const handleBeforeInstallPrompt = (e: Event) => {
      e.preventDefault();
      const installEvent = e as BeforeInstallPromptEvent;
      setDeferredPrompt(installEvent);
      setShowInstallPrompt(true);
      
      reportPerformanceMetric({
        type: 'pwa_install_prompt_shown',
        timestamp: Date.now()
      });
    };

    const handleAppInstalled = () => {
      setShowInstallPrompt(false);
      setDeferredPrompt(null);
      
      reportPerformanceMetric({
        type: 'pwa_app_installed',
        timestamp: Date.now()
      });
    };

    window.addEventListener('beforeinstallprompt', handleBeforeInstallPrompt);
    window.addEventListener('appinstalled', handleAppInstalled);

    return () => {
      window.removeEventListener('beforeinstallprompt', handleBeforeInstallPrompt);
      window.removeEventListener('appinstalled', handleAppInstalled);
    };
  }, []);

  const handleInstallClick = async () => {
    if (!deferredPrompt) return;

    try {
      await deferredPrompt.prompt();
      const choiceResult = await deferredPrompt.userChoice;
      
      reportPerformanceMetric({
        type: 'pwa_install_choice',
        choice: choiceResult.outcome,
        timestamp: Date.now()
      });

      setDeferredPrompt(null);
      setShowInstallPrompt(false);
    } catch (error) {
      console.error('Install prompt failed:', error);
    }
  };

  const handleDismiss = () => {
    setShowInstallPrompt(false);
    
    reportPerformanceMetric({
      type: 'pwa_install_dismissed',
      timestamp: Date.now()
    });
  };

  if (isStandalone || !showInstallPrompt) {
    return null;
  }

  return (
    <div className="pwa-install-prompt">
      <div className="install-prompt-content">
        <div className="install-icon">📱</div>
        <div className="install-text">
          <h3>OrdnungsHub als App installieren</h3>
          <p>Für bessere Performance und Offline-Funktionen</p>
        </div>
        <div className="install-actions">
          <button onClick={handleInstallClick} className="install-button">
            Installieren
          </button>
          <button onClick={handleDismiss} className="dismiss-button">
            Später
          </button>
        </div>
      </div>
    </div>
  );
};

// Network Status Indicator
export const NetworkStatusIndicator: React.FC = () => {
  const [isOnline, setIsOnline] = useState(navigator.onLine);
  const [syncStatus, setSyncStatus] = useState<'idle' | 'syncing' | 'completed'>('idle');

  useEffect(() => {
    const handleOnline = () => {
      setIsOnline(true);
      setSyncStatus('syncing');
      
      reportPerformanceMetric({
        type: 'network_status_change',
        status: 'online',
        timestamp: Date.now()
      });

      // Trigger background sync
      sendMessageToServiceWorker({
        type: 'TRIGGER_SYNC',
        timestamp: Date.now()
      });

      // Reset sync status after delay
      setTimeout(() => setSyncStatus('completed'), 2000);
      setTimeout(() => setSyncStatus('idle'), 4000);
    };

    const handleOffline = () => {
      setIsOnline(false);
      setSyncStatus('idle');
      
      reportPerformanceMetric({
        type: 'network_status_change',
        status: 'offline',
        timestamp: Date.now()
      });
    };

    window.addEventListener('online', handleOnline);
    window.addEventListener('offline', handleOffline);

    return () => {
      window.removeEventListener('online', handleOnline);
      window.removeEventListener('offline', handleOffline);
    };
  }, []);

  return (
    <div className={`network-status ${isOnline ? 'online' : 'offline'}`}>
      <div className="status-indicator">
        <span className={`status-dot ${isOnline ? 'green' : 'red'}`}></span>
        <span className="status-text">
          {isOnline ? (
            syncStatus === 'syncing' ? 'Synchronisiere...' :
            syncStatus === 'completed' ? 'Synchronisiert' :
            'Online'
          ) : 'Offline'}
        </span>
      </div>
    </div>
  );
};

// PWA Share Component
export const PWAShare: React.FC<{ data: ShareData; onShare?: () => void }> = ({ 
  data, 
  onShare 
}) => {
  const [canShare, setCanShare] = useState(false);

  useEffect(() => {
    setCanShare('share' in navigator && navigator.canShare(data));
  }, [data]);

  const handleShare = async () => {
    if (!canShare) return;

    try {
      await navigator.share(data);
      onShare?.();
      
      reportPerformanceMetric({
        type: 'pwa_share_used',
        timestamp: Date.now()
      });
    } catch (error) {
      if ((error as Error).name !== 'AbortError') {
        console.error('Share failed:', error);
      }
    }
  };

  const handleFallbackShare = () => {
    // Fallback sharing methods
    if (data.url) {
      navigator.clipboard.writeText(data.url).then(() => {
        alert('Link copied to clipboard!');
      });
    }
  };

  return (
    <button 
      onClick={canShare ? handleShare : handleFallbackShare}
      className="pwa-share-button"
      title={canShare ? 'Share' : 'Copy link'}
    >
      {canShare ? '🔗 Teilen' : '📋 Link kopieren'}
    </button>
  );
};

// PWA Update Notification
export const PWAUpdateNotification: React.FC = () => {
  const [showUpdate, setShowUpdate] = useState(false);
  const [waitingWorker, setWaitingWorker] = useState<ServiceWorker | null>(null);

  useEffect(() => {
    const handleServiceWorkerUpdate = (event: any) => {
      setWaitingWorker(event.detail.waitingWorker);
      setShowUpdate(true);
    };

    window.addEventListener('serviceworker-update-available', handleServiceWorkerUpdate);

    return () => {
      window.removeEventListener('serviceworker-update-available', handleServiceWorkerUpdate);
    };
  }, []);

  const handleUpdate = () => {
    if (waitingWorker) {
      waitingWorker.postMessage({ type: 'SKIP_WAITING' });
      setShowUpdate(false);
      window.location.reload();
      
      reportPerformanceMetric({
        type: 'pwa_update_applied',
        timestamp: Date.now()
      });
    }
  };

  const handleDismiss = () => {
    setShowUpdate(false);
    
    reportPerformanceMetric({
      type: 'pwa_update_dismissed',
      timestamp: Date.now()
    });
  };

  if (!showUpdate) return null;

  return (
    <div className="pwa-update-notification">
      <div className="update-content">
        <div className="update-icon">🔄</div>
        <div className="update-text">
          <h4>Update verfügbar</h4>
          <p>Eine neue Version von OrdnungsHub ist verfügbar</p>
        </div>
        <div className="update-actions">
          <button onClick={handleUpdate} className="update-button">
            Aktualisieren
          </button>
          <button onClick={handleDismiss} className="dismiss-button">
            Später
          </button>
        </div>
      </div>
    </div>
  );
};

// PWA Performance Monitor
export const PWAPerformanceMonitor: React.FC = () => {
  const [performanceData, setPerformanceData] = useState<any>(null);

  useEffect(() => {
    // Monitor Core Web Vitals
    const observer = new PerformanceObserver((list) => {
      for (const entry of list.getEntries()) {
        if (entry.entryType === 'navigation') {
          const navEntry = entry as PerformanceNavigationTiming;
          
          reportPerformanceMetric({
            type: 'navigation_timing',
            domContentLoaded: navEntry.domContentLoadedEventEnd - navEntry.domContentLoadedEventStart,
            loadComplete: navEntry.loadEventEnd - navEntry.loadEventStart,
            ttfb: navEntry.responseStart - navEntry.requestStart,
            timestamp: Date.now()
          });
        }

        if (entry.entryType === 'paint') {
          reportPerformanceMetric({
            type: 'paint_timing',
            name: entry.name,
            startTime: entry.startTime,
            timestamp: Date.now()
          });
        }
      }
    });

    observer.observe({ entryTypes: ['navigation', 'paint'] });

    // Monitor long tasks
    if ('PerformanceObserver' in window) {
      const longTaskObserver = new PerformanceObserver((list) => {
        for (const entry of list.getEntries()) {
          reportPerformanceMetric({
            type: 'long_task',
            duration: entry.duration,
            startTime: entry.startTime,
            timestamp: Date.now()
          });
        }
      });

      try {
        longTaskObserver.observe({ entryTypes: ['longtask'] });
      } catch (e) {
        // Long task API not supported
      }
    }

    return () => {
      observer.disconnect();
    };
  }, []);

  // This component doesn't render anything, it just monitors performance
  return null;
};

// PWA Badge API Support
export const PWABadge: React.FC<{ count?: number }> = ({ count = 0 }) => {
  useEffect(() => {
    if ('setAppBadge' in navigator) {
      if (count > 0) {
        (navigator as any).setAppBadge(count);
      } else {
        (navigator as any).clearAppBadge();
      }
    }
  }, [count]);

  return null;
};

// Main PWA Provider Component
export const PWAProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [isStandalone, setIsStandalone] = useState(false);

  useEffect(() => {
    setIsStandalone(isRunningStandalone());
    
    // Report PWA mode
    reportPerformanceMetric({
      type: 'pwa_mode',
      standalone: isRunningStandalone(),
      timestamp: Date.now()
    });

    // Add PWA-specific CSS class
    if (isRunningStandalone()) {
      document.body.classList.add('pwa-standalone');
    }

    return () => {
      document.body.classList.remove('pwa-standalone');
    };
  }, []);

  return (
    <div className={`pwa-container ${isStandalone ? 'standalone' : 'browser'}`}>
      <PWAInstallPrompt />
      <PWAUpdateNotification />
      <PWAPerformanceMonitor />
      <NetworkStatusIndicator />
      {children}
    </div>
  );
};

// Styled Components CSS (to be added to CSS file)
export const PWA_STYLES = `
  .pwa-install-prompt {
    position: fixed;
    bottom: 20px;
    left: 20px;
    right: 20px;
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color: white;
    padding: 16px;
    border-radius: 12px;
    box-shadow: 0 8px 32px rgba(0,0,0,0.1);
    backdrop-filter: blur(10px);
    z-index: 1000;
    animation: slideUp 0.3s ease-out;
  }

  .install-prompt-content {
    display: flex;
    align-items: center;
    gap: 12px;
  }

  .install-icon {
    font-size: 2em;
  }

  .install-text h3 {
    margin: 0 0 4px 0;
    font-size: 1.1em;
    font-weight: 600;
  }

  .install-text p {
    margin: 0;
    font-size: 0.9em;
    opacity: 0.9;
  }

  .install-actions {
    display: flex;
    gap: 8px;
    margin-left: auto;
  }

  .install-button, .dismiss-button {
    padding: 8px 16px;
    border: none;
    border-radius: 6px;
    font-weight: 600;
    cursor: pointer;
    transition: all 0.2s ease;
  }

  .install-button {
    background: rgba(255,255,255,0.2);
    color: white;
  }

  .install-button:hover {
    background: rgba(255,255,255,0.3);
  }

  .dismiss-button {
    background: transparent;
    color: rgba(255,255,255,0.8);
  }

  .dismiss-button:hover {
    color: white;
  }

  .network-status {
    position: fixed;
    top: 20px;
    right: 20px;
    z-index: 999;
  }

  .status-indicator {
    display: flex;
    align-items: center;
    gap: 8px;
    padding: 8px 12px;
    background: rgba(255,255,255,0.9);
    border-radius: 20px;
    box-shadow: 0 2px 8px rgba(0,0,0,0.1);
    font-size: 0.9em;
    font-weight: 500;
  }

  .status-dot {
    width: 8px;
    height: 8px;
    border-radius: 50%;
    animation: pulse 2s infinite;
  }

  .status-dot.green {
    background: #4ade80;
  }

  .status-dot.red {
    background: #ef4444;
  }

  .pwa-update-notification {
    position: fixed;
    top: 20px;
    left: 50%;
    transform: translateX(-50%);
    background: white;
    border-radius: 12px;
    box-shadow: 0 8px 32px rgba(0,0,0,0.15);
    padding: 16px;
    z-index: 1000;
    animation: slideDown 0.3s ease-out;
  }

  .update-content {
    display: flex;
    align-items: center;
    gap: 12px;
  }

  .update-icon {
    font-size: 1.5em;
  }

  .update-text h4 {
    margin: 0 0 4px 0;
    font-size: 1em;
    color: #1f2937;
  }

  .update-text p {
    margin: 0;
    font-size: 0.9em;
    color: #6b7280;
  }

  .update-actions {
    display: flex;
    gap: 8px;
    margin-left: auto;
  }

  .update-button {
    background: #3b82f6;
    color: white;
    border: none;
    padding: 8px 16px;
    border-radius: 6px;
    font-weight: 600;
    cursor: pointer;
  }

  .update-button:hover {
    background: #2563eb;
  }

  .pwa-share-button {
    background: #4ade80;
    color: white;
    border: none;
    padding: 8px 16px;
    border-radius: 6px;
    cursor: pointer;
    font-weight: 500;
  }

  .pwa-share-button:hover {
    background: #22c55e;
  }

  .pwa-standalone {
    padding-top: env(safe-area-inset-top);
    padding-bottom: env(safe-area-inset-bottom);
  }

  @keyframes slideUp {
    from { transform: translateY(100%); opacity: 0; }
    to { transform: translateY(0); opacity: 1; }
  }

  @keyframes slideDown {
    from { transform: translateX(-50%) translateY(-100%); opacity: 0; }
    to { transform: translateX(-50%) translateY(0); opacity: 1; }
  }

  @keyframes pulse {
    0%, 100% { opacity: 1; }
    50% { opacity: 0.5; }
  }
`;

export default PWAProvider;