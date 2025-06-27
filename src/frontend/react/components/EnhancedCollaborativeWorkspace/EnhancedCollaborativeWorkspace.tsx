/**
 * Enhanced Collaborative Workspace with Real-time Features
 */

import React, { useState, useEffect, useCallback } from 'react';
import { useApi } from '../../contexts/ApiContext';
import { useCollaboration } from '../../hooks/useCollaboration';
import UserPresence from '../UserPresence/UserPresence';
import RealtimeNotifications from '../RealtimeNotifications/RealtimeNotifications';
import CollaborativeCursor from '../CollaborativeCursor/CollaborativeCursor';
import './EnhancedCollaborativeWorkspace.css';

interface User {
  id: number;
  username: string;
  email: string;
}

interface Team {
  id: number;
  name: string;
  description: string;
  is_public: boolean;
  created_at: string;
}

interface Workspace {
  id: number;
  name: string;
  description: string;
  created_at: string;
}

interface AccessibleWorkspace {
  workspace: Workspace;
  access_type: 'owner' | 'shared';
  permissions: string[];
  shared_at?: string;
}

interface TaskAssignment {
  task: {
    id: number;
    title: string;
    description: string;
    status: string;
    priority: string;
    workspace_id: number;
  };
  assignment: {
    role: string;
    assigned_at: string;
    completion_percentage: number;
  };
}

interface WorkspaceActivity {
  id: number;
  action_type: string;
  description: string;
  created_at: string;
  user: {
    id: number;
    username: string;
  };
  entity_type?: string;
  entity_id?: number;
}

const EnhancedCollaborativeWorkspace: React.FC = () => {
  const { apiCall } = useApi();
  
  // State management
  const [activeTab, setActiveTab] = useState('workspaces');
  const [workspaces, setWorkspaces] = useState<AccessibleWorkspace[]>([]);
  const [teams, setTeams] = useState<Team[]>([]);
  const [assignedTasks, setAssignedTasks] = useState<TaskAssignment[]>([]);
  const [selectedWorkspace, setSelectedWorkspace] = useState<number | null>(null);
  const [workspaceActivity, setWorkspaceActivity] = useState<WorkspaceActivity[]>([]);
  const [currentUser, setCurrentUser] = useState<User | null>(null);
  
  // Real-time collaboration state
  const [realtimeActivities, setRealtimeActivities] = useState<any[]>([]);
  const [documentUpdates, setDocumentUpdates] = useState<any[]>([]);
  const [systemNotifications, setSystemNotifications] = useState<any[]>([]);
  const [showSidebar, setShowSidebar] = useState(true);
  
  // Form states
  const [showCreateTeam, setShowCreateTeam] = useState(false);
  const [showShareWorkspace, setShowShareWorkspace] = useState(false);
  const [showInviteUser, setShowInviteUser] = useState(false);
  
  const [newTeam, setNewTeam] = useState({
    name: '',
    description: '',
    max_members: 50,
    is_public: false
  });
  
  const [shareData, setShareData] = useState({
    user_id: '',
    team_id: '',
    permissions: ['read', 'write'],
    expires_in_days: ''
  });
  
  const [inviteData, setInviteData] = useState({
    invited_email: '',
    invited_user_id: '',
    permissions: ['read', 'write'],
    expires_in_days: 7,
    message: ''
  });

  // Collaboration hooks
  const collaboration = useCollaboration({
    workspaceId: selectedWorkspace || 0,
    onUserJoined: (user) => {
      console.log('User joined:', user);
      setRealtimeActivities(prev => [...prev, {
        user_id: user.id,
        username: user.username,
        activity: 'joined_workspace',
        timestamp: new Date().toISOString()
      }]);
    },
    onUserLeft: (userId) => {
      console.log('User left:', userId);
      setRealtimeActivities(prev => [...prev, {
        user_id: userId,
        username: 'User',
        activity: 'left_workspace',
        timestamp: new Date().toISOString()
      }]);
    },
    onCursorUpdate: (cursor) => {
      console.log('Cursor update:', cursor);
    },
    onDocumentUpdate: (update) => {
      console.log('Document update:', update);
      setDocumentUpdates(prev => [...prev, update]);
    },
    onActivityUpdate: (activity) => {
      console.log('Activity update:', activity);
      setRealtimeActivities(prev => [...prev, activity]);
    },
    onUserTyping: (userId, isTyping, location) => {
      console.log('User typing:', userId, isTyping, location);
    }
  });

  // Load data functions
  const loadWorkspaces = useCallback(async () => {
    try {
      const response = await apiCall('/collaboration/workspaces', 'GET');
      setWorkspaces(response);
    } catch (error) {
      console.error('Failed to load workspaces:', error);
    }
  }, [apiCall]);

  const loadTeams = useCallback(async () => {
    try {
      const response = await apiCall('/collaboration/teams', 'GET');
      setTeams(response);
    } catch (error) {
      console.error('Failed to load teams:', error);
    }
  }, [apiCall]);

  const loadAssignedTasks = useCallback(async () => {
    try {
      const response = await apiCall('/collaboration/tasks/assigned', 'GET');
      setAssignedTasks(response);
    } catch (error) {
      console.error('Failed to load assigned tasks:', error);
    }
  }, [apiCall]);

  const loadWorkspaceActivity = useCallback(async (workspaceId: number) => {
    try {
      const response = await apiCall(`/collaboration/workspaces/${workspaceId}/activity`, 'GET');
      setWorkspaceActivity(response);
    } catch (error) {
      console.error('Failed to load workspace activity:', error);
    }
  }, [apiCall]);

  // Load current user
  useEffect(() => {
    const loadCurrentUser = async () => {
      try {
        const response = await apiCall('/auth/me', 'GET');
        setCurrentUser(response);
      } catch (error) {
        console.error('Failed to load current user:', error);
      }
    };
    loadCurrentUser();
  }, [apiCall]);

  useEffect(() => {
    loadWorkspaces();
    loadTeams();
    loadAssignedTasks();
  }, [loadWorkspaces, loadTeams, loadAssignedTasks]);

  useEffect(() => {
    if (selectedWorkspace) {
      loadWorkspaceActivity(selectedWorkspace);
      
      // Update activity
      collaboration.updateActivity('viewing_workspace', {
        workspace_id: selectedWorkspace
      });
    }
  }, [selectedWorkspace, loadWorkspaceActivity, collaboration]);

  // Handlers
  const handleCreateTeam = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      await apiCall('/collaboration/teams', 'POST', newTeam);
      setShowCreateTeam(false);
      setNewTeam({ name: '', description: '', max_members: 50, is_public: false });
      loadTeams();
      
      setSystemNotifications(prev => [...prev, {
        id: Date.now().toString(),
        type: 'success' as const,
        title: 'Team Created',
        message: `Team "${newTeam.name}" was created successfully`,
        timestamp: new Date().toISOString(),
        autoHide: true
      }]);
    } catch (error) {
      console.error('Failed to create team:', error);
      setSystemNotifications(prev => [...prev, {
        id: Date.now().toString(),
        type: 'error' as const,
        title: 'Error',
        message: 'Failed to create team',
        timestamp: new Date().toISOString(),
        autoHide: true
      }]);
    }
  };

  const handleWorkspaceSelect = (workspaceId: number) => {
    setSelectedWorkspace(workspaceId);
    
    // Send activity update
    collaboration.updateActivity('workspace_selected', {
      workspace_id: workspaceId
    });
  };

  const handleTaskProgressUpdate = async (taskId: number, percentage: number) => {
    try {
      await apiCall(`/collaboration/tasks/${taskId}/progress`, 'PUT', {
        completion_percentage: percentage
      });
      loadAssignedTasks();
      
      // Send real-time update
      collaboration.updateActivity('task_progress_updated', {
        task_id: taskId,
        progress: percentage
      });
    } catch (error) {
      console.error('Failed to update task progress:', error);
    }
  };

  const dismissNotification = (id: string) => {
    setSystemNotifications(prev => prev.filter(n => n.id !== id));
  };

  return (
    <div className="enhanced-collaborative-workspace">
      {/* Header */}
      <div className="workspace-header">
        <div className="header-content">
          <h2>🤝 Collaborative Workspace</h2>
          <p>Real-time collaboration with live updates</p>
        </div>
        
        <div className="header-actions">
          <div className="connection-status">
            <span className={`status-indicator ${collaboration.isConnected ? 'connected' : 'disconnected'}`}>
              {collaboration.isConnected ? '🟢 Connected' : '🔴 Disconnected'}
            </span>
          </div>
          
          <button
            className="sidebar-toggle"
            onClick={() => setShowSidebar(!showSidebar)}
            title="Toggle sidebar"
          >
            {showSidebar ? '👁️‍🗨️' : '👁️'}
          </button>
        </div>
      </div>

      <div className="workspace-layout">
        {/* Main Content */}
        <div className="main-content">
          {/* Navigation Tabs */}
          <div className="workspace-tabs">
            <button 
              className={`tab ${activeTab === 'workspaces' ? 'active' : ''}`}
              onClick={() => setActiveTab('workspaces')}
            >
              🗂️ Workspaces
            </button>
            <button 
              className={`tab ${activeTab === 'teams' ? 'active' : ''}`}
              onClick={() => setActiveTab('teams')}
            >
              👥 Teams
            </button>
            <button 
              className={`tab ${activeTab === 'tasks' ? 'active' : ''}`}
              onClick={() => setActiveTab('tasks')}
            >
              📋 My Tasks
            </button>
          </div>

          {/* Tab Content */}
          <div className="tab-content">
            {activeTab === 'workspaces' && (
              <div className="workspaces-section">
                <div className="section-header">
                  <h3>🗂️ Collaborative Workspaces</h3>
                  <div className="header-actions">
                    <button 
                      className="btn-primary" 
                      onClick={() => setShowShareWorkspace(true)}
                      disabled={!selectedWorkspace}
                    >
                      Share Workspace
                    </button>
                    <button 
                      className="btn-secondary" 
                      onClick={() => setShowInviteUser(true)}
                      disabled={!selectedWorkspace}
                    >
                      Invite Users
                    </button>
                  </div>
                </div>

                <div className="workspaces-grid">
                  {workspaces.map((item) => (
                    <div 
                      key={item.workspace.id} 
                      className={`workspace-card ${selectedWorkspace === item.workspace.id ? 'selected' : ''}`}
                      onClick={() => handleWorkspaceSelect(item.workspace.id)}
                    >
                      <div className="workspace-header">
                        <h4>{item.workspace.name}</h4>
                        <span className={`access-badge ${item.access_type}`}>
                          {item.access_type === 'owner' ? '👑 Owner' : '🤝 Shared'}
                        </span>
                      </div>
                      <p className="workspace-description">{item.workspace.description}</p>
                      
                      {/* Show active users count for selected workspace */}
                      {selectedWorkspace === item.workspace.id && collaboration.isConnected && (
                        <div className="workspace-status">
                          <span className="active-users-count">
                            👥 {collaboration.activeUsers.length} active user{collaboration.activeUsers.length !== 1 ? 's' : ''}
                          </span>
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              </div>
            )}

            {activeTab === 'teams' && (
              <div className="teams-section">
                <div className="section-header">
                  <h3>👥 Teams</h3>
                  <button className="btn-primary" onClick={() => setShowCreateTeam(true)}>
                    Create Team
                  </button>
                </div>

                <div className="teams-grid">
                  {teams.map((team) => (
                    <div key={team.id} className="team-card">
                      <div className="team-header">
                        <h4>{team.name}</h4>
                        <span className={`visibility-badge ${team.is_public ? 'public' : 'private'}`}>
                          {team.is_public ? '🌐 Public' : '🔒 Private'}
                        </span>
                      </div>
                      <p className="team-description">{team.description}</p>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {activeTab === 'tasks' && (
              <div className="tasks-section">
                <div className="section-header">
                  <h3>📋 Assigned Tasks</h3>
                </div>

                <div className="assigned-tasks">
                  {assignedTasks.map((item) => (
                    <div key={item.task.id} className="assigned-task-card">
                      <div className="task-header">
                        <h4>{item.task.title}</h4>
                        <div className="task-badges">
                          <span className={`status-badge ${item.task.status}`}>{item.task.status}</span>
                          <span className={`priority-badge ${item.task.priority}`}>{item.task.priority}</span>
                        </div>
                      </div>
                      
                      <p className="task-description">{item.task.description}</p>
                      
                      <div className="progress-section">
                        <div className="progress-header">
                          <span>Progress: {item.assignment.completion_percentage}%</span>
                          <input
                            type="range"
                            min="0"
                            max="100"
                            value={item.assignment.completion_percentage}
                            onChange={(e) => handleTaskProgressUpdate(item.task.id, parseInt(e.target.value))}
                            className="progress-slider"
                          />
                        </div>
                        <div className="progress-bar">
                          <div 
                            className="progress-fill" 
                            style={{ width: `${item.assignment.completion_percentage}%` }}
                          />
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        </div>

        {/* Sidebar */}
        {showSidebar && (
          <div className="collaboration-sidebar">
            {/* User Presence */}
            <UserPresence
              users={collaboration.activeUsers}
              currentUserId={currentUser?.id.toString()}
              typingUsers={collaboration.typingUsers}
              showActivityStatus={true}
              className="presence-widget"
            />

            {/* Real-time Notifications */}
            <RealtimeNotifications
              activities={realtimeActivities}
              documentUpdates={documentUpdates}
              systemNotifications={systemNotifications}
              onDismissNotification={dismissNotification}
              className="notifications-widget"
            />
          </div>
        )}
      </div>

      {/* Collaborative Cursors */}
      <CollaborativeCursor
        cursors={collaboration.cursorPositions}
        editorContainer={null} // This would be set to your editor container
        className="collaborative-cursors"
      />

      {/* Modals (same as original component) */}
      {showCreateTeam && (
        <div className="modal-overlay">
          <div className="modal">
            <div className="modal-header">
              <h3>Create New Team</h3>
              <button onClick={() => setShowCreateTeam(false)}>×</button>
            </div>
            <form onSubmit={handleCreateTeam}>
              <div className="form-group">
                <label>Team Name</label>
                <input
                  type="text"
                  value={newTeam.name}
                  onChange={(e) => setNewTeam({...newTeam, name: e.target.value})}
                  required
                />
              </div>
              <div className="form-group">
                <label>Description</label>
                <textarea
                  value={newTeam.description}
                  onChange={(e) => setNewTeam({...newTeam, description: e.target.value})}
                />
              </div>
              <div className="modal-actions">
                <button type="button" onClick={() => setShowCreateTeam(false)}>Cancel</button>
                <button type="submit" className="btn-primary">Create Team</button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};

export default EnhancedCollaborativeWorkspace;