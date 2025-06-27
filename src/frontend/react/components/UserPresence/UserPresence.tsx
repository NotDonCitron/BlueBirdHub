/**
 * User Presence Component - Shows active users and their status
 */

import React from 'react';
import './UserPresence.css';

interface User {
  id: string;
  username: string;
  email: string;
  status: 'active' | 'idle' | 'offline';
  connected_at: string;
  last_activity: string;
  cursor_color: string;
  current_activity?: string;
}

interface UserPresenceProps {
  users: User[];
  currentUserId?: string;
  typingUsers?: string[];
  maxDisplayUsers?: number;
  showActivityStatus?: boolean;
  className?: string;
}

const UserPresence: React.FC<UserPresenceProps> = ({
  users,
  currentUserId,
  typingUsers = [],
  maxDisplayUsers = 8,
  showActivityStatus = true,
  className = ''
}) => {
  const activeUsers = users.filter(user => user.status === 'active');
  const displayUsers = activeUsers.slice(0, maxDisplayUsers);
  const remainingCount = Math.max(0, activeUsers.length - maxDisplayUsers);

  const getStatusIcon = (user: User) => {
    if (typingUsers.includes(user.id)) {
      return '✏️';
    }
    
    switch (user.status) {
      case 'active':
        return '🟢';
      case 'idle':
        return '🟡';
      case 'offline':
        return '🔴';
      default:
        return '⚪';
    }
  };

  const getActivityText = (user: User) => {
    if (typingUsers.includes(user.id)) {
      return 'typing...';
    }
    
    return user.current_activity || 'viewing workspace';
  };

  const formatTimeAgo = (timestamp: string) => {
    const now = new Date();
    const time = new Date(timestamp);
    const diffMs = now.getTime() - time.getTime();
    const diffMinutes = Math.floor(diffMs / (1000 * 60));
    
    if (diffMinutes < 1) return 'just now';
    if (diffMinutes < 60) return `${diffMinutes}m ago`;
    
    const diffHours = Math.floor(diffMinutes / 60);
    if (diffHours < 24) return `${diffHours}h ago`;
    
    const diffDays = Math.floor(diffHours / 24);
    return `${diffDays}d ago`;
  };

  return (
    <div className={`user-presence ${className}`}>
      <div className="presence-header">
        <span className="presence-title">
          👥 Active Users ({activeUsers.length})
        </span>
      </div>
      
      <div className="user-avatars">
        {displayUsers.map(user => (
          <div
            key={user.id}
            className={`user-avatar ${user.id === currentUserId ? 'current-user' : ''}`}
            title={`${user.username} - ${getActivityText(user)}`}
          >
            <div 
              className="avatar-circle"
              style={{ borderColor: user.cursor_color }}
            >
              <span className="avatar-initial">
                {user.username.charAt(0).toUpperCase()}
              </span>
              
              <div className="status-indicator">
                {getStatusIcon(user)}
              </div>
              
              {typingUsers.includes(user.id) && (
                <div className="typing-indicator">
                  <div className="typing-dots">
                    <span></span>
                    <span></span>
                    <span></span>
                  </div>
                </div>
              )}
            </div>
            
            <div className="user-info">
              <div className="username">{user.username}</div>
              {showActivityStatus && (
                <div className="activity-status">
                  {getActivityText(user)}
                </div>
              )}
              <div className="last-seen">
                {formatTimeAgo(user.last_activity)}
              </div>
            </div>
          </div>
        ))}
        
        {remainingCount > 0 && (
          <div className="remaining-users" title={`${remainingCount} more users`}>
            <div className="avatar-circle">
              <span className="avatar-initial">+{remainingCount}</span>
            </div>
          </div>
        )}
      </div>
      
      {activeUsers.length === 0 && (
        <div className="no-users">
          <span className="empty-state">👤 You're the only one here</span>
        </div>
      )}
      
      {typingUsers.length > 0 && (
        <div className="global-typing-indicator">
          {typingUsers.length === 1 ? (
            <span>
              {displayUsers.find(u => u.id === typingUsers[0])?.username || 'Someone'} is typing...
            </span>
          ) : (
            <span>
              {typingUsers.length} people are typing...
            </span>
          )}
        </div>
      )}
    </div>
  );
};

export default UserPresence;