/**
 * Real-time Notifications Component - Shows live updates and activities
 */

import React, { useState, useEffect } from 'react';
import './RealtimeNotifications.css';

interface ActivityUpdate {
  user_id: string;
  username: string;
  activity: string;
  details?: any;
  timestamp: string;
}

interface DocumentUpdate {
  document_id: string;
  user_id: string;
  username: string;
  version: number;
  operation: {
    type: 'insert' | 'delete' | 'replace';
    position: { line: number; column: number };
    content?: string;
    length?: number;
  };
  timestamp: string;
}

interface SystemNotification {
  id: string;
  type: 'info' | 'warning' | 'error' | 'success';
  title: string;
  message: string;
  timestamp: string;
  autoHide?: boolean;
  actions?: Array<{
    label: string;
    action: () => void;
    type?: 'primary' | 'secondary';
  }>;
}

interface RealtimeNotificationsProps {
  activities: ActivityUpdate[];
  documentUpdates: DocumentUpdate[];
  systemNotifications: SystemNotification[];
  maxActivities?: number;
  maxDocumentUpdates?: number;
  showTimestamps?: boolean;
  autoHideDelay?: number;
  onDismissNotification?: (id: string) => void;
  className?: string;
}

const RealtimeNotifications: React.FC<RealtimeNotificationsProps> = ({
  activities,
  documentUpdates,
  systemNotifications,
  maxActivities = 10,
  maxDocumentUpdates = 5,
  showTimestamps = true,
  autoHideDelay = 5000,
  onDismissNotification,
  className = ''
}) => {
  const [visibleNotifications, setVisibleNotifications] = useState<Set<string>>(new Set());

  // Auto-hide system notifications
  useEffect(() => {
    systemNotifications.forEach(notification => {
      if (notification.autoHide !== false) {
        const timer = setTimeout(() => {
          setVisibleNotifications(prev => {
            const newSet = new Set(prev);
            newSet.delete(notification.id);
            return newSet;
          });
          onDismissNotification?.(notification.id);
        }, autoHideDelay);

        return () => clearTimeout(timer);
      }
    });
  }, [systemNotifications, autoHideDelay, onDismissNotification]);

  const formatTimestamp = (timestamp: string) => {
    const now = new Date();
    const time = new Date(timestamp);
    const diffMs = now.getTime() - time.getTime();
    const diffMinutes = Math.floor(diffMs / (1000 * 60));

    if (diffMinutes < 1) return 'now';
    if (diffMinutes < 60) return `${diffMinutes}m`;
    const diffHours = Math.floor(diffMinutes / 60);
    if (diffHours < 24) return `${diffHours}h`;
    const diffDays = Math.floor(diffHours / 24);
    return `${diffDays}d`;
  };

  const getActivityIcon = (activity: string) => {
    switch (activity.toLowerCase()) {
      case 'file_opened':
      case 'viewing_file':
        return '📁';
      case 'editing_file':
      case 'document_edit':
        return '✏️';
      case 'task_created':
        return '📝';
      case 'task_completed':
        return '✅';
      case 'comment_added':
        return '💬';
      case 'file_uploaded':
        return '📤';
      case 'workspace_shared':
        return '🤝';
      default:
        return '🔄';
    }
  };

  const getOperationText = (operation: DocumentUpdate['operation']) => {
    switch (operation.type) {
      case 'insert':
        return `inserted "${operation.content?.substring(0, 20)}${operation.content && operation.content.length > 20 ? '...' : ''}"`;
      case 'delete':
        return `deleted ${operation.length} characters`;
      case 'replace':
        return `replaced text with "${operation.content?.substring(0, 20)}${operation.content && operation.content.length > 20 ? '...' : ''}"`;
      default:
        return 'made changes';
    }
  };

  const getNotificationIcon = (type: SystemNotification['type']) => {
    switch (type) {
      case 'info':
        return 'ℹ️';
      case 'warning':
        return '⚠️';
      case 'error':
        return '❌';
      case 'success':
        return '✅';
      default:
        return 'ℹ️';
    }
  };

  const recentActivities = activities
    .sort((a, b) => new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime())
    .slice(0, maxActivities);

  const recentDocumentUpdates = documentUpdates
    .sort((a, b) => new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime())
    .slice(0, maxDocumentUpdates);

  return (
    <div className={`realtime-notifications ${className}`}>
      {/* System Notifications */}
      {systemNotifications.length > 0 && (
        <div className="notifications-section system-notifications">
          {systemNotifications.map(notification => (
            <div
              key={notification.id}
              className={`notification notification-${notification.type}`}
              style={{
                display: visibleNotifications.has(notification.id) ? 'none' : 'flex'
              }}
            >
              <div className="notification-icon">
                {getNotificationIcon(notification.type)}
              </div>
              
              <div className="notification-content">
                <div className="notification-title">{notification.title}</div>
                <div className="notification-message">{notification.message}</div>
                
                {notification.actions && (
                  <div className="notification-actions">
                    {notification.actions.map((action, index) => (
                      <button
                        key={index}
                        className={`notification-action ${action.type || 'secondary'}`}
                        onClick={action.action}
                      >
                        {action.label}
                      </button>
                    ))}
                  </div>
                )}
              </div>
              
              <button
                className="notification-close"
                onClick={() => {
                  setVisibleNotifications(prev => {
                    const newSet = new Set(prev);
                    newSet.add(notification.id);
                    return newSet;
                  });
                  onDismissNotification?.(notification.id);
                }}
              >
                ×
              </button>
            </div>
          ))}
        </div>
      )}

      {/* Activity Feed */}
      {recentActivities.length > 0 && (
        <div className="notifications-section activity-feed">
          <div className="section-header">
            <span className="section-title">🔄 Recent Activity</span>
          </div>
          
          <div className="activity-list">
            {recentActivities.map((activity, index) => (
              <div key={`${activity.user_id}-${activity.timestamp}-${index}`} className="activity-item">
                <div className="activity-icon">
                  {getActivityIcon(activity.activity)}
                </div>
                
                <div className="activity-content">
                  <span className="activity-user">{activity.username}</span>
                  <span className="activity-text">{activity.activity.replace(/_/g, ' ')}</span>
                  {activity.details && (
                    <span className="activity-details">
                      {typeof activity.details === 'string' ? activity.details : JSON.stringify(activity.details)}
                    </span>
                  )}
                </div>
                
                {showTimestamps && (
                  <div className="activity-time">
                    {formatTimestamp(activity.timestamp)}
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Document Updates */}
      {recentDocumentUpdates.length > 0 && (
        <div className="notifications-section document-updates">
          <div className="section-header">
            <span className="section-title">📝 Recent Edits</span>
          </div>
          
          <div className="update-list">
            {recentDocumentUpdates.map((update, index) => (
              <div key={`${update.document_id}-${update.version}-${index}`} className="update-item">
                <div className="update-icon">✏️</div>
                
                <div className="update-content">
                  <span className="update-user">{update.username}</span>
                  <span className="update-text">{getOperationText(update.operation)}</span>
                  <span className="update-location">
                    at line {update.operation.position.line + 1}
                  </span>
                </div>
                
                {showTimestamps && (
                  <div className="update-time">
                    {formatTimestamp(update.timestamp)}
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Empty State */}
      {recentActivities.length === 0 && recentDocumentUpdates.length === 0 && systemNotifications.length === 0 && (
        <div className="empty-state">
          <div className="empty-icon">🔇</div>
          <div className="empty-message">No recent activity</div>
        </div>
      )}
    </div>
  );
};

export default RealtimeNotifications;