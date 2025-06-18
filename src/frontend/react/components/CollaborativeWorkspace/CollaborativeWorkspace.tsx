import React, { useState, useEffect, useCallback } from 'react';
import { useApi } from '../../contexts/ApiContext';
import './CollaborativeWorkspace.css';

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

interface TeamMember {
  user_id: number;
  username: string;
  email: string;
  role: string;
  joined_at: string;
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

const CollaborativeWorkspace: React.FC = () => {
  const { apiCall } = useApi();
  
  // State management
  const [activeTab, setActiveTab] = useState('workspaces');
  const [workspaces, setWorkspaces] = useState<AccessibleWorkspace[]>([]);
  const [teams, setTeams] = useState<Team[]>([]);
  const [assignedTasks, setAssignedTasks] = useState<TaskAssignment[]>([]);
  const [selectedWorkspace, setSelectedWorkspace] = useState<number | null>(null);
  const [workspaceActivity, setWorkspaceActivity] = useState<WorkspaceActivity[]>([]);
  const [teamMembers, setTeamMembers] = useState<{ [teamId: number]: TeamMember[] }>({});
  
  // Form states
  const [showCreateTeam, setShowCreateTeam] = useState(false);
  const [showShareWorkspace, setShowShareWorkspace] = useState(false);
  const [showInviteUser, setShowInviteUser] = useState(false);
  const [selectedTeamId, setSelectedTeamId] = useState<number | null>(null);
  
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

  // Load data
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

  const loadTeamMembers = useCallback(async (teamId: number) => {
    try {
      const response = await apiCall(`/collaboration/teams/${teamId}/members`, 'GET');
      setTeamMembers(prev => ({ ...prev, [teamId]: response }));
    } catch (error) {
      console.error('Failed to load team members:', error);
    }
  }, [apiCall]);

  useEffect(() => {
    loadWorkspaces();
    loadTeams();
    loadAssignedTasks();
  }, [loadWorkspaces, loadTeams, loadAssignedTasks]);

  useEffect(() => {
    if (selectedWorkspace) {
      loadWorkspaceActivity(selectedWorkspace);
    }
  }, [selectedWorkspace, loadWorkspaceActivity]);

  // Handlers
  const handleCreateTeam = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      await apiCall('/collaboration/teams', 'POST', newTeam);
      setShowCreateTeam(false);
      setNewTeam({ name: '', description: '', max_members: 50, is_public: false });
      loadTeams();
    } catch (error) {
      console.error('Failed to create team:', error);
    }
  };

  const handleShareWorkspace = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedWorkspace) return;
    
    try {
      const payload = {
        ...(shareData.user_id && { user_id: parseInt(shareData.user_id) }),
        ...(shareData.team_id && { team_id: parseInt(shareData.team_id) }),
        permissions: shareData.permissions,
        ...(shareData.expires_in_days && { expires_in_days: parseInt(shareData.expires_in_days) })
      };
      
      await apiCall(`/collaboration/workspaces/${selectedWorkspace}/share`, 'POST', payload);
      setShowShareWorkspace(false);
      setShareData({ user_id: '', team_id: '', permissions: ['read', 'write'], expires_in_days: '' });
    } catch (error) {
      console.error('Failed to share workspace:', error);
    }
  };

  const handleCreateInvite = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedWorkspace) return;
    
    try {
      const payload = {
        ...(inviteData.invited_email && { invited_email: inviteData.invited_email }),
        ...(inviteData.invited_user_id && { invited_user_id: parseInt(inviteData.invited_user_id) }),
        permissions: inviteData.permissions,
        expires_in_days: inviteData.expires_in_days,
        message: inviteData.message
      };
      
      const response = await apiCall(`/collaboration/workspaces/${selectedWorkspace}/invite`, 'POST', payload);
      alert(`Invitation created! Code: ${response.invite_code}`);
      setShowInviteUser(false);
      setInviteData({ invited_email: '', invited_user_id: '', permissions: ['read', 'write'], expires_in_days: 7, message: '' });
    } catch (error) {
      console.error('Failed to create invite:', error);
    }
  };

  const handleUpdateTaskProgress = async (taskId: number, percentage: number) => {
    try {
      await apiCall(`/collaboration/tasks/${taskId}/progress`, 'PUT', {
        completion_percentage: percentage
      });
      loadAssignedTasks();
    } catch (error) {
      console.error('Failed to update task progress:', error);
    }
  };

  const renderWorkspacesTab = () => (
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
            onClick={() => setSelectedWorkspace(item.workspace.id)}
          >
            <div className="workspace-header">
              <h4>{item.workspace.name}</h4>
              <span className={`access-badge ${item.access_type}`}>
                {item.access_type === 'owner' ? '👑 Owner' : '🤝 Shared'}
              </span>
            </div>
            <p className="workspace-description">{item.workspace.description}</p>
            <div className="workspace-permissions">
              <strong>Permissions:</strong>
              {item.permissions.map(permission => (
                <span key={permission} className="permission-tag">{permission}</span>
              ))}
            </div>
            {item.shared_at && (
              <div className="shared-info">
                Shared: {new Date(item.shared_at).toLocaleDateString()}
              </div>
            )}
          </div>
        ))}
      </div>

      {selectedWorkspace && (
        <div className="workspace-activity">
          <h4>Recent Activity</h4>
          <div className="activity-feed">
            {workspaceActivity.map((activity) => (
              <div key={activity.id} className="activity-item">
                <div className="activity-icon">
                  {activity.action_type === 'shared' && '🤝'}
                  {activity.action_type === 'task_assigned' && '📋'}
                  {activity.action_type === 'task_commented' && '💬'}
                  {!['shared', 'task_assigned', 'task_commented'].includes(activity.action_type) && '📝'}
                </div>
                <div className="activity-content">
                  <div className="activity-description">{activity.description}</div>
                  <div className="activity-meta">
                    By {activity.user.username} • {new Date(activity.created_at).toLocaleString()}
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );

  const renderTeamsTab = () => (
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
            <div className="team-actions">
              <button 
                className="btn-secondary"
                onClick={() => {
                  setSelectedTeamId(team.id);
                  loadTeamMembers(team.id);
                }}
              >
                View Members
              </button>
            </div>
            
            {selectedTeamId === team.id && teamMembers[team.id] && (
              <div className="team-members">
                <h5>Team Members</h5>
                {teamMembers[team.id].map((member) => (
                  <div key={member.user_id} className="member-item">
                    <div className="member-info">
                      <span className="member-name">{member.username}</span>
                      <span className="member-email">{member.email}</span>
                    </div>
                    <span className={`role-badge ${member.role}`}>{member.role}</span>
                  </div>
                ))}
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  );

  const renderTasksTab = () => (
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
                <span className={`role-badge ${item.assignment.role}`}>{item.assignment.role}</span>
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
                  onChange={(e) => handleUpdateTaskProgress(item.task.id, parseInt(e.target.value))}
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
            
            <div className="task-meta">
              Assigned: {new Date(item.assignment.assigned_at).toLocaleDateString()}
            </div>
          </div>
        ))}
      </div>
    </div>
  );

  return (
    <div className="collaborative-workspace">
      <div className="workspace-header">
        <h2>🤝 Collaborative Workspace Management</h2>
        <p>Manage teams, share workspaces, and collaborate on tasks</p>
      </div>

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

      <div className="tab-content">
        {activeTab === 'workspaces' && renderWorkspacesTab()}
        {activeTab === 'teams' && renderTeamsTab()}
        {activeTab === 'tasks' && renderTasksTab()}
      </div>

      {/* Create Team Modal */}
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
              <div className="form-group">
                <label>Max Members</label>
                <input
                  type="number"
                  value={newTeam.max_members}
                  onChange={(e) => setNewTeam({...newTeam, max_members: parseInt(e.target.value)})}
                />
              </div>
              <div className="form-group">
                <label>
                  <input
                    type="checkbox"
                    checked={newTeam.is_public}
                    onChange={(e) => setNewTeam({...newTeam, is_public: e.target.checked})}
                  />
                  Public Team
                </label>
              </div>
              <div className="modal-actions">
                <button type="button" onClick={() => setShowCreateTeam(false)}>Cancel</button>
                <button type="submit" className="btn-primary">Create Team</button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Share Workspace Modal */}
      {showShareWorkspace && (
        <div className="modal-overlay">
          <div className="modal">
            <div className="modal-header">
              <h3>Share Workspace</h3>
              <button onClick={() => setShowShareWorkspace(false)}>×</button>
            </div>
            <form onSubmit={handleShareWorkspace}>
              <div className="form-group">
                <label>User ID (optional)</label>
                <input
                  type="number"
                  value={shareData.user_id}
                  onChange={(e) => setShareData({...shareData, user_id: e.target.value})}
                />
              </div>
              <div className="form-group">
                <label>Team ID (optional)</label>
                <input
                  type="number"
                  value={shareData.team_id}
                  onChange={(e) => setShareData({...shareData, team_id: e.target.value})}
                />
              </div>
              <div className="form-group">
                <label>Permissions</label>
                <select 
                  multiple 
                  value={shareData.permissions}
                  onChange={(e) => setShareData({
                    ...shareData, 
                    permissions: Array.from(e.target.selectedOptions, option => option.value)
                  })}
                >
                  <option value="read">Read</option>
                  <option value="write">Write</option>
                  <option value="delete">Delete</option>
                  <option value="share">Share</option>
                  <option value="admin">Admin</option>
                </select>
              </div>
              <div className="form-group">
                <label>Expires in (days, optional)</label>
                <input
                  type="number"
                  value={shareData.expires_in_days}
                  onChange={(e) => setShareData({...shareData, expires_in_days: e.target.value})}
                />
              </div>
              <div className="modal-actions">
                <button type="button" onClick={() => setShowShareWorkspace(false)}>Cancel</button>
                <button type="submit" className="btn-primary">Share Workspace</button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Invite User Modal */}
      {showInviteUser && (
        <div className="modal-overlay">
          <div className="modal">
            <div className="modal-header">
              <h3>Invite User to Workspace</h3>
              <button onClick={() => setShowInviteUser(false)}>×</button>
            </div>
            <form onSubmit={handleCreateInvite}>
              <div className="form-group">
                <label>Email (optional)</label>
                <input
                  type="email"
                  value={inviteData.invited_email}
                  onChange={(e) => setInviteData({...inviteData, invited_email: e.target.value})}
                />
              </div>
              <div className="form-group">
                <label>User ID (optional)</label>
                <input
                  type="number"
                  value={inviteData.invited_user_id}
                  onChange={(e) => setInviteData({...inviteData, invited_user_id: e.target.value})}
                />
              </div>
              <div className="form-group">
                <label>Permissions</label>
                <select 
                  multiple 
                  value={inviteData.permissions}
                  onChange={(e) => setInviteData({
                    ...inviteData, 
                    permissions: Array.from(e.target.selectedOptions, option => option.value)
                  })}
                >
                  <option value="read">Read</option>
                  <option value="write">Write</option>
                  <option value="delete">Delete</option>
                  <option value="share">Share</option>
                  <option value="admin">Admin</option>
                </select>
              </div>
              <div className="form-group">
                <label>Expires in (days)</label>
                <input
                  type="number"
                  value={inviteData.expires_in_days}
                  onChange={(e) => setInviteData({...inviteData, expires_in_days: parseInt(e.target.value)})}
                />
              </div>
              <div className="form-group">
                <label>Message</label>
                <textarea
                  value={inviteData.message}
                  onChange={(e) => setInviteData({...inviteData, message: e.target.value})}
                  placeholder="Optional invitation message"
                />
              </div>
              <div className="modal-actions">
                <button type="button" onClick={() => setShowInviteUser(false)}>Cancel</button>
                <button type="submit" className="btn-primary">Create Invitation</button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};

export default CollaborativeWorkspace;