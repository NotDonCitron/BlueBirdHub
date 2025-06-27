import React, { useState } from 'react';
import './VoiceCommandHistory.css';

interface VoiceCommand {
  id?: number;
  type: string;
  text: string;
  confidence: number;
  parameters: Record<string, any>;
  timestamp: string;
  language: string;
  status?: string;
}

interface VoiceCommandHistoryProps {
  commands: VoiceCommand[];
  onClose: () => void;
}

const VoiceCommandHistory: React.FC<VoiceCommandHistoryProps> = ({ commands, onClose }) => {
  const [filter, setFilter] = useState<string>('all');
  const [searchQuery, setSearchQuery] = useState('');

  const commandTypes = {
    create_task: { icon: 'fa-plus', color: '#10b981', label: 'Create Task' },
    update_task: { icon: 'fa-edit', color: '#3b82f6', label: 'Update Task' },
    delete_task: { icon: 'fa-trash', color: '#ef4444', label: 'Delete Task' },
    search_task: { icon: 'fa-search', color: '#8b5cf6', label: 'Search' },
    navigate: { icon: 'fa-compass', color: '#f59e0b', label: 'Navigate' },
    set_priority: { icon: 'fa-flag', color: '#ec4899', label: 'Set Priority' },
    set_deadline: { icon: 'fa-calendar', color: '#06b6d4', label: 'Set Deadline' },
    help: { icon: 'fa-question-circle', color: '#6b7280', label: 'Help' },
    unknown: { icon: 'fa-question', color: '#6b7280', label: 'Unknown' }
  };

  const filteredCommands = commands.filter(cmd => {
    if (filter !== 'all' && cmd.type !== filter) return false;
    if (searchQuery && !cmd.text.toLowerCase().includes(searchQuery.toLowerCase())) return false;
    return true;
  });

  const getCommandStats = () => {
    const stats = commands.reduce((acc, cmd) => {
      acc[cmd.type] = (acc[cmd.type] || 0) + 1;
      return acc;
    }, {} as Record<string, number>);

    return Object.entries(stats)
      .sort(([, a], [, b]) => b - a)
      .slice(0, 5);
  };

  const formatDate = (timestamp: string) => {
    const date = new Date(timestamp);
    const now = new Date();
    const diff = now.getTime() - date.getTime();
    
    if (diff < 60000) return 'Just now';
    if (diff < 3600000) return `${Math.floor(diff / 60000)} minutes ago`;
    if (diff < 86400000) return `${Math.floor(diff / 3600000)} hours ago`;
    if (diff < 604800000) return `${Math.floor(diff / 86400000)} days ago`;
    
    return date.toLocaleDateString();
  };

  const exportHistory = () => {
    const data = JSON.stringify(commands, null, 2);
    const blob = new Blob([data], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `voice-commands-${new Date().toISOString().split('T')[0]}.json`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  return (
    <div className="voice-history-overlay">
      <div className="voice-history-modal">
        <div className="voice-history-header">
          <h2>Voice Command History</h2>
          <button className="close-btn" onClick={onClose}>
            <i className="fas fa-times" />
          </button>
        </div>

        <div className="voice-history-stats">
          <div className="stat-card">
            <i className="fas fa-microphone" />
            <div className="stat-info">
              <span className="stat-value">{commands.length}</span>
              <span className="stat-label">Total Commands</span>
            </div>
          </div>
          
          {getCommandStats().slice(0, 3).map(([type, count]) => {
            const typeInfo = commandTypes[type] || commandTypes.unknown;
            return (
              <div key={type} className="stat-card">
                <i className={`fas ${typeInfo.icon}`} style={{ color: typeInfo.color }} />
                <div className="stat-info">
                  <span className="stat-value">{count}</span>
                  <span className="stat-label">{typeInfo.label}</span>
                </div>
              </div>
            );
          })}
        </div>

        <div className="voice-history-controls">
          <div className="search-box">
            <i className="fas fa-search" />
            <input
              type="text"
              placeholder="Search commands..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
            />
          </div>

          <div className="filter-buttons">
            <button
              className={`filter-btn ${filter === 'all' ? 'active' : ''}`}
              onClick={() => setFilter('all')}
            >
              All
            </button>
            {Object.entries(commandTypes).slice(0, 5).map(([type, info]) => (
              <button
                key={type}
                className={`filter-btn ${filter === type ? 'active' : ''}`}
                onClick={() => setFilter(type)}
              >
                <i className={`fas ${info.icon}`} style={{ color: info.color }} />
                {info.label}
              </button>
            ))}
          </div>

          <button className="export-btn" onClick={exportHistory}>
            <i className="fas fa-download" /> Export
          </button>
        </div>

        <div className="voice-history-list">
          {filteredCommands.length === 0 ? (
            <div className="empty-state">
              <i className="fas fa-microphone-slash" />
              <p>No commands found</p>
            </div>
          ) : (
            filteredCommands.map((cmd, index) => {
              const typeInfo = commandTypes[cmd.type] || commandTypes.unknown;
              return (
                <div key={cmd.id || index} className="history-item">
                  <div className="history-icon" style={{ backgroundColor: `${typeInfo.color}20` }}>
                    <i className={`fas ${typeInfo.icon}`} style={{ color: typeInfo.color }} />
                  </div>
                  
                  <div className="history-content">
                    <div className="history-text">{cmd.text}</div>
                    <div className="history-meta">
                      <span className="history-type">{typeInfo.label}</span>
                      <span className="history-confidence">
                        {Math.round(cmd.confidence * 100)}% confident
                      </span>
                      <span className="history-time">{formatDate(cmd.timestamp)}</span>
                    </div>
                    
                    {Object.keys(cmd.parameters).length > 0 && (
                      <div className="history-parameters">
                        {Object.entries(cmd.parameters).map(([key, value]) => (
                          <span key={key} className="parameter">
                            {key}: {typeof value === 'object' ? JSON.stringify(value) : value}
                          </span>
                        ))}
                      </div>
                    )}
                  </div>
                  
                  <div className="history-status">
                    <span className={`status ${cmd.status || 'completed'}`}>
                      {cmd.status || 'completed'}
                    </span>
                  </div>
                </div>
              );
            })
          )}
        </div>
      </div>
    </div>
  );
};

export default VoiceCommandHistory;