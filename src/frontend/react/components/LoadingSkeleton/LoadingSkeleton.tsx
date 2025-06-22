import React from 'react';
import './LoadingSkeleton.css';

interface LoadingSkeletonProps {
  type?: 'dashboard' | 'workspace' | 'tasks' | 'files' | 'chat' | 'collaboration' | 'automation' | 'content' | 'default';
  className?: string;
}

const LoadingSkeleton: React.FC<LoadingSkeletonProps> = ({ 
  type = 'default', 
  className = '' 
}) => {
  const getSkeletonContent = () => {
    switch (type) {
      case 'dashboard':
        return (
          <div className="skeleton-dashboard">
            <div className="skeleton-header">
              <div className="skeleton-rect skeleton-title"></div>
              <div className="skeleton-rect skeleton-subtitle"></div>
            </div>
            <div className="skeleton-stats">
              {[...Array(4)].map((_, i) => (
                <div key={i} className="skeleton-stat-card">
                  <div className="skeleton-circle"></div>
                  <div className="skeleton-rect skeleton-stat-text"></div>
                </div>
              ))}
            </div>
            <div className="skeleton-content">
              <div className="skeleton-rect skeleton-large"></div>
              <div className="skeleton-rect skeleton-medium"></div>
              <div className="skeleton-rect skeleton-small"></div>
            </div>
          </div>
        );
      
      case 'workspace':
        return (
          <div className="skeleton-workspace">
            <div className="skeleton-toolbar">
              <div className="skeleton-rect skeleton-button"></div>
              <div className="skeleton-rect skeleton-search"></div>
            </div>
            <div className="skeleton-grid">
              {[...Array(6)].map((_, i) => (
                <div key={i} className="skeleton-workspace-card">
                  <div className="skeleton-rect skeleton-card-header"></div>
                  <div className="skeleton-rect skeleton-card-content"></div>
                  <div className="skeleton-rect skeleton-card-footer"></div>
                </div>
              ))}
            </div>
          </div>
        );
      
      case 'tasks':
        return (
          <div className="skeleton-tasks">
            <div className="skeleton-task-header">
              <div className="skeleton-rect skeleton-filter"></div>
              <div className="skeleton-rect skeleton-sort"></div>
            </div>
            <div className="skeleton-task-list">
              {[...Array(8)].map((_, i) => (
                <div key={i} className="skeleton-task-item">
                  <div className="skeleton-circle skeleton-checkbox"></div>
                  <div className="skeleton-task-content">
                    <div className="skeleton-rect skeleton-task-title"></div>
                    <div className="skeleton-rect skeleton-task-meta"></div>
                  </div>
                  <div className="skeleton-rect skeleton-priority"></div>
                </div>
              ))}
            </div>
          </div>
        );
      
      case 'files':
        return (
          <div className="skeleton-files">
            <div className="skeleton-breadcrumb">
              <div className="skeleton-rect skeleton-path"></div>
            </div>
            <div className="skeleton-file-list">
              {[...Array(10)].map((_, i) => (
                <div key={i} className="skeleton-file-item">
                  <div className="skeleton-rect skeleton-file-icon"></div>
                  <div className="skeleton-rect skeleton-file-name"></div>
                  <div className="skeleton-rect skeleton-file-size"></div>
                  <div className="skeleton-rect skeleton-file-date"></div>
                </div>
              ))}
            </div>
          </div>
        );
      
      case 'chat':
        return (
          <div className="skeleton-chat">
            <div className="skeleton-chat-header">
              <div className="skeleton-circle skeleton-avatar"></div>
              <div className="skeleton-rect skeleton-chat-title"></div>
            </div>
            <div className="skeleton-messages">
              {[...Array(5)].map((_, i) => (
                <div key={i} className={`skeleton-message ${i % 2 === 0 ? 'user' : 'ai'}`}>
                  <div className="skeleton-circle skeleton-message-avatar"></div>
                  <div className="skeleton-message-content">
                    <div className="skeleton-rect skeleton-message-text"></div>
                    <div className="skeleton-rect skeleton-message-text short"></div>
                  </div>
                </div>
              ))}
            </div>
            <div className="skeleton-input">
              <div className="skeleton-rect skeleton-text-input"></div>
              <div className="skeleton-rect skeleton-send-button"></div>
            </div>
          </div>
        );
      
      case 'collaboration':
        return (
          <div className="skeleton-collaboration">
            <div className="skeleton-participants">
              {[...Array(4)].map((_, i) => (
                <div key={i} className="skeleton-participant">
                  <div className="skeleton-circle skeleton-participant-avatar"></div>
                  <div className="skeleton-rect skeleton-participant-name"></div>
                </div>
              ))}
            </div>
            <div className="skeleton-activity">
              {[...Array(6)].map((_, i) => (
                <div key={i} className="skeleton-activity-item">
                  <div className="skeleton-rect skeleton-activity-content"></div>
                  <div className="skeleton-rect skeleton-activity-time"></div>
                </div>
              ))}
            </div>
          </div>
        );
      
      case 'automation':
        return (
          <div className="skeleton-automation">
            <div className="skeleton-workflow-list">
              {[...Array(4)].map((_, i) => (
                <div key={i} className="skeleton-workflow">
                  <div className="skeleton-rect skeleton-workflow-title"></div>
                  <div className="skeleton-rect skeleton-workflow-description"></div>
                  <div className="skeleton-workflow-steps">
                    {[...Array(3)].map((_, j) => (
                      <div key={j} className="skeleton-rect skeleton-step"></div>
                    ))}
                  </div>
                </div>
              ))}
            </div>
          </div>
        );
      
      case 'content':
        return (
          <div className="skeleton-content-assignment">
            <div className="skeleton-content-header">
              <div className="skeleton-rect skeleton-content-title"></div>
              <div className="skeleton-rect skeleton-content-status"></div>
            </div>
            <div className="skeleton-content-grid">
              {[...Array(6)].map((_, i) => (
                <div key={i} className="skeleton-content-item">
                  <div className="skeleton-rect skeleton-content-thumbnail"></div>
                  <div className="skeleton-rect skeleton-content-name"></div>
                  <div className="skeleton-rect skeleton-content-progress"></div>
                </div>
              ))}
            </div>
          </div>
        );
      
      default:
        return (
          <div className="skeleton-default">
            <div className="skeleton-rect skeleton-large"></div>
            <div className="skeleton-rect skeleton-medium"></div>
            <div className="skeleton-rect skeleton-small"></div>
          </div>
        );
    }
  };

  return (
    <div className={`loading-skeleton ${className}`} aria-label="Loading content">
      {getSkeletonContent()}
    </div>
  );
};

export default LoadingSkeleton;