import React, { useState, useEffect } from 'react';
import { useErrorHandler } from '../hooks/useErrorHandler';

interface Workspace {
  id: string;
  name: string;
  description?: string;
  created_at: string;
  updated_at: string;
}

const WorkspaceList: React.FC = () => {
  const [workspaces, setWorkspaces] = useState<Workspace[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const { handleError } = useErrorHandler({ component: 'WorkspaceList' });

  useEffect(() => {
    loadWorkspaces();
  }, []);

  const loadWorkspaces = async () => {
    try {
      setLoading(true);
      setError(null);
      
      // Mock data for now - replace with actual API call
      const mockWorkspaces: Workspace[] = [
        {
          id: '1',
          name: 'Personal Projects',
          description: 'My personal workspace for side projects',
          created_at: new Date().toISOString(),
          updated_at: new Date().toISOString()
        },
        {
          id: '2',
          name: 'Team Collaboration',
          description: 'Shared workspace for team projects',
          created_at: new Date().toISOString(),
          updated_at: new Date().toISOString()
        }
      ];
      
      setWorkspaces(mockWorkspaces);
    } catch (err) {
      const message = handleError(err);
      setError(message);
    } finally {
      setLoading(false);
    }
  };

  const createWorkspace = async (name: string, description?: string) => {
    try {
      // Mock creation - replace with actual API call
      const newWorkspace: Workspace = {
        id: Date.now().toString(),
        name,
        description,
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString()
      };
      
      setWorkspaces(prev => [...prev, newWorkspace]);
    } catch (err) {
      const message = handleError(err);
      setError(message);
    }
  };

  if (loading) {
    return (
      <div className="workspace-list-loading">
        <div className="spinner"></div>
        <p>Loading workspaces...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="workspace-list-error">
        <p>Error: {error}</p>
        <button onClick={loadWorkspaces}>Retry</button>
      </div>
    );
  }

  return (
    <div className="workspace-list">
      <div className="workspace-list-header">
        <h2>Workspaces</h2>
        <button 
          className="create-workspace-btn"
          onClick={() => createWorkspace('New Workspace', 'Description for new workspace')}
        >
          Create Workspace
        </button>
      </div>
      
      <div className="workspaces-grid">
        {workspaces.map(workspace => (
          <div key={workspace.id} className="workspace-card">
            <h3>{workspace.name}</h3>
            {workspace.description && (
              <p className="workspace-description">{workspace.description}</p>
            )}
            <div className="workspace-meta">
              <small>Created: {new Date(workspace.created_at).toLocaleDateString()}</small>
            </div>
            <div className="workspace-actions">
              <button>Open</button>
              <button>Edit</button>
              <button>Delete</button>
            </div>
          </div>
        ))}
      </div>
      
      {workspaces.length === 0 && (
        <div className="no-workspaces">
          <p>No workspaces found. Create your first workspace to get started!</p>
        </div>
      )}
      
      <style jsx>{`
        .workspace-list {
          padding: 20px;
          max-width: 1200px;
          margin: 0 auto;
        }
        
        .workspace-list-header {
          display: flex;
          justify-content: space-between;
          align-items: center;
          margin-bottom: 20px;
        }
        
        .create-workspace-btn {
          padding: 10px 20px;
          background-color: #3b82f6;
          color: white;
          border: none;
          border-radius: 6px;
          cursor: pointer;
          font-weight: 500;
        }
        
        .create-workspace-btn:hover {
          background-color: #2563eb;
        }
        
        .workspaces-grid {
          display: grid;
          grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
          gap: 20px;
        }
        
        .workspace-card {
          background: white;
          border: 1px solid #e5e7eb;
          border-radius: 8px;
          padding: 20px;
          box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
        }
        
        .workspace-card h3 {
          margin: 0 0 10px 0;
          color: #1f2937;
        }
        
        .workspace-description {
          color: #6b7280;
          margin-bottom: 15px;
        }
        
        .workspace-meta {
          margin-bottom: 15px;
        }
        
        .workspace-meta small {
          color: #9ca3af;
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
        
        .workspace-list-loading, 
        .workspace-list-error {
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
        
        .no-workspaces {
          text-align: center;
          padding: 60px 20px;
          color: #6b7280;
        }
      `}</style>
    </div>
  );
};

export default WorkspaceList;