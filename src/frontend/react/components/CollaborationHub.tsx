import React, { useState, useEffect } from 'react';
import { useErrorHandler } from '../hooks/useErrorHandler';

interface TeamMember {
  id: string;
  name: string;
  email: string;
  role: 'admin' | 'member' | 'viewer';
  status: 'online' | 'offline' | 'away';
  avatar?: string;
  joined_at: string;
}

interface SharedWorkspace {
  id: string;
  name: string;
  description?: string;
  members: TeamMember[];
  created_at: string;
  updated_at: string;
}

const CollaborationHub: React.FC = () => {
  const [workspaces, setWorkspaces] = useState<SharedWorkspace[]>([]);
  const [teamMembers, setTeamMembers] = useState<TeamMember[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<'workspaces' | 'members' | 'invites'>('workspaces');
  const { handleError } = useErrorHandler({ component: 'CollaborationHub' });

  useEffect(() => {
    loadCollaborationData();
  }, []);

  const loadCollaborationData = async () => {
    try {
      setLoading(true);
      setError(null);
      
      // Mock data for now - replace with actual API calls
      const mockMembers: TeamMember[] = [
        {
          id: '1',
          name: 'John Doe',
          email: 'john@example.com',
          role: 'admin',
          status: 'online',
          joined_at: '2024-01-01T00:00:00Z'
        },
        {
          id: '2',
          name: 'Jane Smith',
          email: 'jane@example.com',
          role: 'member',
          status: 'away',
          joined_at: '2024-01-05T00:00:00Z'
        },
        {
          id: '3',
          name: 'Mike Johnson',
          email: 'mike@example.com',
          role: 'viewer',
          status: 'offline',
          joined_at: '2024-01-10T00:00:00Z'
        }
      ];

      const mockWorkspaces: SharedWorkspace[] = [
        {
          id: '1',
          name: 'Product Development',
          description: 'Main product development workspace',
          members: mockMembers.slice(0, 2),
          created_at: '2024-01-01T00:00:00Z',
          updated_at: '2024-01-15T00:00:00Z'
        },
        {
          id: '2',
          name: 'Marketing Campaign',
          description: 'Q1 marketing campaign planning',
          members: mockMembers,
          created_at: '2024-01-05T00:00:00Z',
          updated_at: '2024-01-12T00:00:00Z'
        }
      ];
      
      setTeamMembers(mockMembers);
      setWorkspaces(mockWorkspaces);
    } catch (err) {
      const message = handleError(err);
      setError(message);
    } finally {
      setLoading(false);
    }
  };

  const inviteTeamMember = async (email: string, role: TeamMember['role']) => {
    try {
      // Mock invitation - replace with actual API call
      console.log(`Inviting ${email} as ${role}`);
      // You would typically send an invitation email here
    } catch (err) {
      const message = handleError(err);
      setError(message);
    }
  };

  const updateMemberRole = async (memberId: string, newRole: TeamMember['role']) => {
    try {
      setTeamMembers(prev => prev.map(member => 
        member.id === memberId 
          ? { ...member, role: newRole }
          : member
      ));
      
      // Update workspaces that contain this member
      setWorkspaces(prev => prev.map(workspace => ({
        ...workspace,
        members: workspace.members.map(member => 
          member.id === memberId 
            ? { ...member, role: newRole }
            : member
        )
      })));
    } catch (err) {
      const message = handleError(err);
      setError(message);
    }
  };

  const getStatusColor = (status: TeamMember['status']) => {
    switch (status) {
      case 'online': return '#10b981';
      case 'away': return '#f59e0b';
      case 'offline': return '#6b7280';
      default: return '#6b7280';
    }
  };

  const getRoleColor = (role: TeamMember['role']) => {
    switch (role) {
      case 'admin': return '#ef4444';
      case 'member': return '#3b82f6';
      case 'viewer': return '#6b7280';
      default: return '#6b7280';
    }
  };

  if (loading) {
    return (
      <div className="collaboration-loading">
        <div className="spinner"></div>
        <p>Loading collaboration data...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="collaboration-error">
        <p>Error: {error}</p>
        <button onClick={loadCollaborationData}>Retry</button>
      </div>
    );
  }

  return (
    <div className="collaboration-hub">
      <div className="collaboration-header">
        <h2>Collaboration Hub</h2>
        <button className="invite-btn">
          Invite Team Member
        </button>
      </div>

      <div className="collaboration-tabs">
        {(['workspaces', 'members', 'invites'] as const).map(tab => (
          <button
            key={tab}
            className={`tab ${activeTab === tab ? 'active' : ''}`}
            onClick={() => setActiveTab(tab)}
          >
            {tab.charAt(0).toUpperCase() + tab.slice(1)}
          </button>
        ))}
      </div>

      <div className="collaboration-content">
        {activeTab === 'workspaces' && (
          <div className="workspaces-section">
            <h3>Shared Workspaces</h3>
            <div className="workspaces-grid">
              {workspaces.map(workspace => (
                <div key={workspace.id} className="workspace-card">
                  <h4>{workspace.name}</h4>
                  {workspace.description && (
                    <p className="workspace-description">{workspace.description}</p>
                  )}
                  
                  <div className="workspace-members">
                    <h5>Members ({workspace.members.length})</h5>
                    <div className="members-list">
                      {workspace.members.map(member => (
                        <div key={member.id} className="member-item">
                          <div className="member-avatar">
                            {member.name.split(' ').map(n => n[0]).join('')}
                          </div>
                          <div className="member-info">
                            <span className="member-name">{member.name}</span>
                            <span 
                              className="member-role"
                              style={{ color: getRoleColor(member.role) }}
                            >
                              {member.role}
                            </span>
                          </div>
                          <div 
                            className="member-status"
                            style={{ backgroundColor: getStatusColor(member.status) }}
                          ></div>
                        </div>
                      ))}
                    </div>
                  </div>
                  
                  <div className="workspace-actions">
                    <button>Open</button>
                    <button>Manage</button>
                    <button>Settings</button>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {activeTab === 'members' && (
          <div className="members-section">
            <h3>Team Members</h3>
            <div className="members-table">
              {teamMembers.map(member => (
                <div key={member.id} className="member-row">
                  <div className="member-basic">
                    <div className="member-avatar">
                      {member.name.split(' ').map(n => n[0]).join('')}
                    </div>
                    <div className="member-details">
                      <div className="member-name">{member.name}</div>
                      <div className="member-email">{member.email}</div>
                    </div>
                  </div>
                  
                  <div className="member-role-selector">
                    <select
                      value={member.role}
                      onChange={(e) => updateMemberRole(member.id, e.target.value as TeamMember['role'])}
                    >
                      <option value="viewer">Viewer</option>
                      <option value="member">Member</option>
                      <option value="admin">Admin</option>
                    </select>
                  </div>
                  
                  <div className="member-status-display">
                    <span 
                      className="status-indicator"
                      style={{ backgroundColor: getStatusColor(member.status) }}
                    ></span>
                    {member.status}
                  </div>
                  
                  <div className="member-actions">
                    <button>Message</button>
                    <button>Remove</button>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {activeTab === 'invites' && (
          <div className="invites-section">
            <h3>Send Invitations</h3>
            <div className="invite-form">
              <input
                type="email"
                placeholder="Enter email address"
                className="email-input"
              />
              <select className="role-select">
                <option value="viewer">Viewer</option>
                <option value="member">Member</option>
                <option value="admin">Admin</option>
              </select>
              <button 
                className="send-invite-btn"
                onClick={() => inviteTeamMember('example@email.com', 'member')}
              >
                Send Invite
              </button>
            </div>
            
            <div className="pending-invites">
              <h4>Pending Invitations</h4>
              <p className="no-invites">No pending invitations</p>
            </div>
          </div>
        )}
      </div>

      <style jsx>{`
        .collaboration-hub {
          padding: 20px;
          max-width: 1200px;
          margin: 0 auto;
        }

        .collaboration-header {
          display: flex;
          justify-content: space-between;
          align-items: center;
          margin-bottom: 30px;
        }

        .invite-btn {
          padding: 10px 20px;
          background-color: #3b82f6;
          color: white;
          border: none;
          border-radius: 6px;
          cursor: pointer;
          font-weight: 500;
        }

        .invite-btn:hover {
          background-color: #2563eb;
        }

        .collaboration-tabs {
          display: flex;
          border-bottom: 1px solid #e5e7eb;
          margin-bottom: 20px;
        }

        .tab {
          padding: 12px 24px;
          background: none;
          border: none;
          border-bottom: 2px solid transparent;
          cursor: pointer;
          font-weight: 500;
          color: #6b7280;
        }

        .tab.active {
          color: #3b82f6;
          border-bottom-color: #3b82f6;
        }

        .tab:hover:not(.active) {
          color: #374151;
        }

        .workspaces-grid {
          display: grid;
          grid-template-columns: repeat(auto-fill, minmax(400px, 1fr));
          gap: 20px;
        }

        .workspace-card {
          background: white;
          border: 1px solid #e5e7eb;
          border-radius: 8px;
          padding: 20px;
          box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
        }

        .workspace-card h4 {
          margin: 0 0 10px 0;
          color: #1f2937;
        }

        .workspace-description {
          color: #6b7280;
          margin-bottom: 20px;
        }

        .workspace-members h5 {
          margin: 0 0 10px 0;
          color: #374151;
          font-size: 14px;
        }

        .members-list {
          display: flex;
          flex-direction: column;
          gap: 8px;
          margin-bottom: 20px;
        }

        .member-item {
          display: flex;
          align-items: center;
          gap: 12px;
        }

        .member-avatar {
          width: 32px;
          height: 32px;
          background: #3b82f6;
          color: white;
          border-radius: 50%;
          display: flex;
          align-items: center;
          justify-content: center;
          font-size: 12px;
          font-weight: 500;
        }

        .member-info {
          flex: 1;
          display: flex;
          flex-direction: column;
        }

        .member-name {
          font-weight: 500;
          font-size: 14px;
        }

        .member-role {
          font-size: 12px;
          text-transform: capitalize;
        }

        .member-status {
          width: 8px;
          height: 8px;
          border-radius: 50%;
        }

        .workspace-actions {
          display: flex;
          gap: 10px;
        }

        .workspace-actions button {
          padding: 6px 12px;
          border: 1px solid #d1d5db;
          background: white;
          border-radius: 4px;
          cursor: pointer;
          font-size: 14px;
        }

        .workspace-actions button:hover {
          background-color: #f9fafb;
        }

        .members-table {
          display: flex;
          flex-direction: column;
          gap: 12px;
        }

        .member-row {
          display: flex;
          align-items: center;
          gap: 20px;
          padding: 15px;
          background: white;
          border: 1px solid #e5e7eb;
          border-radius: 8px;
        }

        .member-basic {
          display: flex;
          align-items: center;
          gap: 12px;
          flex: 1;
        }

        .member-details {
          display: flex;
          flex-direction: column;
        }

        .member-email {
          color: #6b7280;
          font-size: 14px;
        }

        .member-role-selector select {
          padding: 6px 12px;
          border: 1px solid #d1d5db;
          border-radius: 4px;
          background: white;
        }

        .member-status-display {
          display: flex;
          align-items: center;
          gap: 8px;
          color: #6b7280;
          font-size: 14px;
          text-transform: capitalize;
        }

        .status-indicator {
          width: 8px;
          height: 8px;
          border-radius: 50%;
        }

        .member-actions {
          display: flex;
          gap: 8px;
        }

        .member-actions button {
          padding: 6px 12px;
          border: 1px solid #d1d5db;
          background: white;
          border-radius: 4px;
          cursor: pointer;
          font-size: 14px;
        }

        .member-actions button:hover {
          background-color: #f9fafb;
        }

        .invite-form {
          display: flex;
          gap: 12px;
          margin-bottom: 30px;
          padding: 20px;
          background: white;
          border: 1px solid #e5e7eb;
          border-radius: 8px;
        }

        .email-input {
          flex: 1;
          padding: 10px 12px;
          border: 1px solid #d1d5db;
          border-radius: 6px;
          outline: none;
        }

        .email-input:focus {
          border-color: #3b82f6;
          box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
        }

        .role-select {
          padding: 10px 12px;
          border: 1px solid #d1d5db;
          border-radius: 6px;
          background: white;
        }

        .send-invite-btn {
          padding: 10px 20px;
          background-color: #10b981;
          color: white;
          border: none;
          border-radius: 6px;
          cursor: pointer;
          font-weight: 500;
        }

        .send-invite-btn:hover {
          background-color: #059669;
        }

        .pending-invites h4 {
          margin-bottom: 15px;
          color: #374151;
        }

        .no-invites {
          color: #6b7280;
          font-style: italic;
        }

        .collaboration-loading, 
        .collaboration-error {
          text-align: center;
          padding: 40px;
        }

        .spinner {
          width: 40px;
          height: 40px;
          border: 4px solid #f3f4f6;
          border-top: 4px solid #3b82f6;
          border-radius: 50%;
          animation: spin 1s linear infinite;
          margin: 0 auto 20px;
        }

        @keyframes spin {
          0% { transform: rotate(0deg); }
          100% { transform: rotate(360deg); }
        }
      `}</style>
    </div>
  );
};

export default CollaborationHub;