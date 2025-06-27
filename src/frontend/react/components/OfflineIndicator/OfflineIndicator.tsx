/**
 * Offline Indicator Component
 * Shows network status and sync progress in the app header
 */

import React, { useState, useEffect } from 'react';
import { syncManager, SyncStatus, SyncEvent } from '../../core/offline/sync/SyncManager';
import './OfflineIndicator.css';

interface OfflineIndicatorProps {
  className?: string;
  showDetails?: boolean;
  position?: 'header' | 'sidebar' | 'floating';
}

export const OfflineIndicator: React.FC<OfflineIndicatorProps> = ({
  className = '',
  showDetails = false,
  position = 'header'
}) => {
  const [status, setStatus] = useState<SyncStatus>({
    isOnline: navigator.onLine,
    isSyncing: false,
    syncProgress: 0,
    queueSize: 0,
    conflictCount: 0,
    lastSync: null,
    nextSync: null
  });

  const [showTooltip, setShowTooltip] = useState(false);
  const [recentSyncEvents, setRecentSyncEvents] = useState<SyncEvent[]>([]);

  useEffect(() => {
    const updateStatus = async () => {
      try {
        const currentStatus = await syncManager.getStatus();
        setStatus(currentStatus);
      } catch (error) {
        console.error('Failed to get sync status:', error);
      }
    };

    const handleSyncEvent = (event: SyncEvent) => {
      setRecentSyncEvents(prev => {
        const newEvents = [event, ...prev.slice(0, 4)]; // Keep last 5 events
        return newEvents;
      });

      if (event.type === 'progress' && event.progress !== undefined) {
        setStatus(prev => ({ ...prev, syncProgress: event.progress! }));
      }

      if (event.type === 'start') {
        setStatus(prev => ({ ...prev, isSyncing: true, syncProgress: 0 }));
      }

      if (event.type === 'complete' || event.type === 'error') {
        setStatus(prev => ({ ...prev, isSyncing: false, syncProgress: 0 }));
        updateStatus(); // Refresh full status
      }
    };

    const handleNetworkChange = () => {
      setStatus(prev => ({ ...prev, isOnline: navigator.onLine }));
      updateStatus();
    };

    // Initial status update
    updateStatus();

    // Set up event listeners
    syncManager.addEventListener(handleSyncEvent);
    window.addEventListener('online', handleNetworkChange);
    window.addEventListener('offline', handleNetworkChange);

    // Periodic status updates
    const interval = setInterval(updateStatus, 10000); // Update every 10 seconds

    return () => {
      syncManager.removeEventListener(handleSyncEvent);
      window.removeEventListener('online', handleNetworkChange);
      window.removeEventListener('offline', handleNetworkChange);
      clearInterval(interval);
    };
  }, []);

  const getStatusIcon = () => {
    if (status.isSyncing) {
      return '🔄';
    }
    if (!status.isOnline) {
      return '📶';
    }
    if (status.conflictCount > 0) {
      return '⚠️';
    }
    if (status.queueSize > 0) {
      return '⏳';
    }
    return '✅';
  };

  const getStatusColor = () => {
    if (status.isSyncing) return 'syncing';
    if (!status.isOnline) return 'offline';
    if (status.conflictCount > 0) return 'warning';
    if (status.queueSize > 0) return 'pending';
    return 'online';
  };

  const getStatusText = () => {
    if (status.isSyncing) {
      return `Synchronisiere... ${Math.round(status.syncProgress)}%`;
    }
    if (!status.isOnline) {
      return 'Offline';
    }
    if (status.conflictCount > 0) {
      return `${status.conflictCount} Konflikte`;
    }
    if (status.queueSize > 0) {
      return `${status.queueSize} ausstehend`;
    }
    return 'Online';
  };

  const handleClick = async () => {
    if (!status.isOnline) return;
    
    if (status.queueSize > 0 && !status.isSyncing) {
      try {
        await syncManager.sync();
      } catch (error) {
        console.error('Manual sync failed:', error);
      }
    }
  };

  const formatLastSync = (timestamp: number | null) => {
    if (!timestamp) return 'Nie';
    
    const now = Date.now();
    const diff = now - timestamp;
    
    if (diff < 60000) return 'Gerade eben';
    if (diff < 3600000) return `vor ${Math.floor(diff / 60000)} Min.`;
    if (diff < 86400000) return `vor ${Math.floor(diff / 3600000)} Std.`;
    return `vor ${Math.floor(diff / 86400000)} Tagen`;
  };

  const renderTooltip = () => (
    <div className="offline-indicator__tooltip">
      <div className="tooltip-header">
        <span className="tooltip-title">Sync Status</span>
        <span className={`status-badge status-badge--${getStatusColor()}`}>
          {getStatusText()}
        </span>
      </div>
      
      <div className="tooltip-content">
        <div className="status-row">
          <span>Verbindung:</span>
          <span className={status.isOnline ? 'text-success' : 'text-error'}>
            {status.isOnline ? 'Online' : 'Offline'}
          </span>
        </div>
        
        <div className="status-row">
          <span>Sync Queue:</span>
          <span>{status.queueSize} Elemente</span>
        </div>
        
        <div className="status-row">
          <span>Konflikte:</span>
          <span className={status.conflictCount > 0 ? 'text-warning' : ''}>
            {status.conflictCount}
          </span>
        </div>
        
        <div className="status-row">
          <span>Letzte Sync:</span>
          <span>{formatLastSync(status.lastSync)}</span>
        </div>

        {status.isSyncing && (
          <div className="sync-progress">
            <div className="progress-bar">
              <div 
                className="progress-fill" 
                style={{ width: `${status.syncProgress}%` }}
              />
            </div>
            <span className="progress-text">{Math.round(status.syncProgress)}%</span>
          </div>
        )}

        {recentSyncEvents.length > 0 && (
          <div className="recent-events">
            <div className="events-title">Letzte Ereignisse:</div>
            {recentSyncEvents.map((event, index) => (
              <div key={index} className={`event-item event-${event.type}`}>
                <span className="event-icon">
                  {event.type === 'complete' ? '✅' : 
                   event.type === 'error' ? '❌' : 
                   event.type === 'conflict' ? '⚠️' : '🔄'}
                </span>
                <span className="event-text">
                  {event.type === 'complete' ? 'Sync abgeschlossen' :
                   event.type === 'error' ? `Fehler: ${event.error}` :
                   event.type === 'conflict' ? 'Konflikt erkannt' :
                   event.entityType ? `${event.entityType} wird synchronisiert` : 'Sync gestartet'}
                </span>
              </div>
            ))}
          </div>
        )}
      </div>

      {(status.queueSize > 0 && !status.isSyncing && status.isOnline) && (
        <div className="tooltip-actions">
          <button className="sync-button" onClick={handleClick}>
            Jetzt synchronisieren
          </button>
        </div>
      )}
    </div>
  );

  return (
    <div 
      className={`offline-indicator offline-indicator--${position} ${className}`}
      onMouseEnter={() => setShowTooltip(true)}
      onMouseLeave={() => setShowTooltip(false)}
      onClick={handleClick}
    >
      <div className={`indicator-main indicator-main--${getStatusColor()}`}>
        <span className="indicator-icon">{getStatusIcon()}</span>
        {showDetails && (
          <span className="indicator-text">{getStatusText()}</span>
        )}
        {status.isSyncing && (
          <div className="sync-spinner" />
        )}
      </div>

      {showTooltip && renderTooltip()}
    </div>
  );
};

export default OfflineIndicator;