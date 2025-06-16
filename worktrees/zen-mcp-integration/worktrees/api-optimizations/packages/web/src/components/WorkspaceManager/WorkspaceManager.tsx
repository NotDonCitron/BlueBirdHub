import React, { useState, useEffect } from 'react';
import { useApi } from '../../contexts/ApiContext';
import './WorkspaceManager.css';

interface Workspace {
  id: number;
  name: string;
  description?: string;
  theme?: string;
  color: string;
  icon?: string;
  layout_config?: any;
  ambient_sound?: string;
  is_active: boolean;
  is_default?: boolean;
  last_accessed_at?: string;
  created_at?: string;
  updated_at?: string;
  file_count?: number;
}

interface FileWorkspaceTemplate {
  name: string;
  description: string;
  folders: string[];
  icon: string;
  color: string;
}

interface FileWorkspaceCreationResult {
  workspace_name: string;
  workspace_path: string;
  template: string;
  created_directories: string[];
  info: any;
}

export const WorkspaceManager: React.FC = () => {
  const { makeApiRequest } = useApi();
  const [workspaces, setWorkspaces] = useState<Workspace[]>([]);
  const [fileWorkspaceTemplates, setFileWorkspaceTemplates] = useState<FileWorkspaceTemplate[]>([]);
  const [loading, setLoading] = useState(true);
  const [creatingWorkspace, setCreatingWorkspace] = useState(false);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [showTemplateModal, setShowTemplateModal] = useState(false);
  const [selectedTemplate, setSelectedTemplate] = useState<FileWorkspaceTemplate | null>(null);
  const [activeWorkspace, setActiveWorkspace] = useState<Workspace | null>(null);
  const [newWorkspaceName, setNewWorkspaceName] = useState('');
  const [createdWorkspaces, setCreatedWorkspaces] = useState<FileWorkspaceCreationResult[]>([]);
  const [editingWorkspace, setEditingWorkspace] = useState<number | null>(null);
  const [editName, setEditName] = useState('');
  const [workspaceFiles, setWorkspaceFiles] = useState<{[key: number]: any}>({});
  const [workspaceFolders, setWorkspaceFolders] = useState<{[key: number]: any}>({});
  const [expandedFolders, setExpandedFolders] = useState<{[key: string]: boolean}>({});
  const [organizingSuggestions, setOrganizingSuggestions] = useState<{[key: number]: any}>({});
  const [autoOrganizing, setAutoOrganizing] = useState<{[key: number]: boolean}>({});

  // Default templates with icons and colors
  const defaultTemplates: FileWorkspaceTemplate[] = [
    {
      name: 'default',
      description: 'General purpose workspace with common folders',
      folders: ['Documents', 'Images', 'Videos', 'Audio', 'Archives', 'Projects', 'Temp'],
      icon: '📁',
      color: '#3b82f6'
    },
    {
      name: 'development',
      description: 'Software development workspace with coding structure',
      folders: ['src', 'docs', 'tests', 'resources', 'build', 'dist', 'config', '.vscode'],
      icon: '💻',
      color: '#10b981'
    },
    {
      name: 'creative',
      description: 'Creative projects workspace for designers and artists',
      folders: ['Designs', 'References', 'Exports', 'Projects', 'Assets/Images', 'Assets/Fonts', 'Assets/Icons', 'Archives'],
      icon: '🎨',
      color: '#f59e0b'
    },
    {
      name: 'business',
      description: 'Business and office workspace for professional work',
      folders: ['Contracts', 'Invoices', 'Reports', 'Presentations', 'Meeting Notes', 'Clients', 'Templates', 'Archives'],
      icon: '💼',
      color: '#8b5cf6'
    }
  ];

  useEffect(() => {
    loadWorkspaces();
    loadFileWorkspaceTemplates();
  }, []);

  const loadWorkspaces = async () => {
    try {
      setLoading(true);
      const response = await makeApiRequest('/workspaces/');
      setWorkspaces(response);
      // Find active workspace
      const active = response.find((w: Workspace) => w.is_active);
      setActiveWorkspace(active || null);
    } catch (error) {
      console.error('Failed to load workspaces:', error);
      // If workspace API fails, we'll focus on file workspaces
      setWorkspaces([]);
    } finally {
      setLoading(false);
    }
  };

  const loadFileWorkspaceTemplates = async () => {
    try {
      const response = await makeApiRequest('/file-management/workspace-templates');
      // Merge API templates with our enhanced templates
      const enhancedTemplates = response.templates.map((template: any) => {
        const defaultTemplate = defaultTemplates.find(t => t.name === template.name);
        return {
          ...template,
          icon: defaultTemplate?.icon || '📁',
          color: defaultTemplate?.color || '#6b7280'
        };
      });
      setFileWorkspaceTemplates(enhancedTemplates);
    } catch (error) {
      console.error('Failed to load file workspace templates:', error);
      // Use default templates if API fails
      setFileWorkspaceTemplates(defaultTemplates);
    }
  };

  const createFileWorkspace = async (template: FileWorkspaceTemplate, name: string) => {
    try {
      setCreatingWorkspace(true);
      const response = await makeApiRequest('/file-management/create-workspace', 'POST', {
        workspace_name: name,
        template: template.name
      });
      
      // Add to created workspaces list
      setCreatedWorkspaces(prev => [...prev, response]);
      
      setShowTemplateModal(false);
      setNewWorkspaceName('');
      setSelectedTemplate(null);
      
      alert(`File workspace "${name}" created successfully at: ${response.workspace_path}`);
    } catch (error) {
      console.error('Failed to create file workspace:', error);
      alert('Failed to create workspace. Please try again.');
    } finally {
      setCreatingWorkspace(false);
    }
  };

  const switchToWorkspace = async (workspace: Workspace) => {
    try {
      const response = await makeApiRequest(`/workspaces/${workspace.id}/switch`, 'POST');
      setActiveWorkspace(workspace);
      await loadWorkspaces();
    } catch (error) {
      console.error('Failed to switch workspace:', error);
    }
  };

  const startRenaming = (workspace: Workspace) => {
    setEditingWorkspace(workspace.id);
    setEditName(workspace.name);
  };

  const cancelRenaming = () => {
    setEditingWorkspace(null);
    setEditName('');
  };

  const saveRename = async (workspaceId: number) => {
    if (!editName.trim()) {
      cancelRenaming();
      return;
    }
    
    try {
      const response = await makeApiRequest(`/workspaces/${workspaceId}/rename`, 'PUT', {
        name: editName.trim()
      });
      
      console.log('Rename response:', response);
      
      if (response.success) {
        setWorkspaces(prev => 
          prev.map(w => w.id === workspaceId ? { ...w, name: editName.trim() } : w)
        );
        setEditingWorkspace(null);
        setEditName('');
      } else {
        console.error('Rename failed:', response);
        alert('Failed to rename workspace: ' + (response.error || 'Unknown error'));
        cancelRenaming();
      }
    } catch (error) {
      console.error('Failed to rename workspace:', error);
      alert('Failed to rename workspace: ' + (error instanceof Error ? error.message : 'Unknown error'));
      cancelRenaming();
    }
  };

  const loadWorkspaceFiles = async (workspaceId: number) => {
    try {
      const response = await makeApiRequest(`/workspaces/${workspaceId}/files`);
      if (response.success) {
        setWorkspaceFiles(prev => ({
          ...prev,
          [workspaceId]: response.folders
        }));
        setWorkspaceFolders(prev => ({
          ...prev,
          [workspaceId]: response.structure
        }));
      }
    } catch (error) {
      console.error('Failed to load workspace files:', error);
    }
  };

  const toggleFolder = (workspaceId: number, folderName: string) => {
    const key = `${workspaceId}-${folderName}`;
    setExpandedFolders(prev => ({
      ...prev,
      [key]: !prev[key]
    }));
  };

  const deleteWorkspace = async (workspaceId: number) => {
    if (!confirm('Are you sure you want to delete this workspace?')) return;
    
    try {
      await makeApiRequest(`/workspaces/${workspaceId}`, 'DELETE');
      await loadWorkspaces();
    } catch (error) {
      console.error('Failed to delete workspace:', error);
    }
  };

  const suggestOrganization = async (workspaceId: number) => {
    try {
      // Get files from workspace for organization suggestions
      const files = workspaceFiles[workspaceId];
      if (!files) return;

      // Flatten all files from all folders
      const allFiles = Object.values(files).flat();
      
      const response = await makeApiRequest('/ai/suggest-organization', 'POST', {
        files: allFiles,
        workspace_id: workspaceId
      });
      
      setOrganizingSuggestions(prev => ({
        ...prev,
        [workspaceId]: response.suggestions
      }));
    } catch (error) {
      console.error('Failed to get organization suggestions:', error);
    }
  };

  const autoOrganizeWorkspace = async (workspaceId: number) => {
    if (!confirm('Auto-organize all unorganized files in this workspace?')) return;
    
    try {
      setAutoOrganizing(prev => ({ ...prev, [workspaceId]: true }));
      
      const response = await makeApiRequest('/ai/auto-organize-workspace', 'POST', {
        workspace_id: workspaceId
      });
      
      // Reload workspace files to show updated organization
      await loadWorkspaceFiles(workspaceId);
      
      alert(`${response.message || 'Auto-organization complete!'}\n${response.organized_files} of ${response.total_files} files organized.`);
    } catch (error) {
      console.error('Failed to auto-organize workspace:', error);
      alert('Failed to auto-organize workspace');
    } finally {
      setAutoOrganizing(prev => ({ ...prev, [workspaceId]: false }));
    }
  };

  const handleFileUpload = async (workspaceId: number, files: FileList) => {
    try {
      for (const file of Array.from(files)) {
        const fileData = {
          name: file.name,
          type: file.type || 'application/octet-stream',
          size: `${(file.size / 1024).toFixed(1)}KB`,
          content_preview: '' // Could read first part of file for AI analysis
        };
        
        const response = await makeApiRequest(`/workspaces/${workspaceId}/files`, 'POST', fileData);
        
        if (response.success && response.ai_organization) {
          console.log(`File "${file.name}" auto-organized to "${response.ai_organization.folder}" folder`);
        }
      }
      
      // Reload workspace files to show new files
      await loadWorkspaceFiles(workspaceId);
      
      alert(`${files.length} file(s) uploaded and auto-organized!`);
    } catch (error) {
      console.error('Failed to upload files:', error);
      alert('Failed to upload files');
    }
  };

  const formatLastAccessed = (dateString?: string) => {
    if (!dateString) return 'Never';
    const date = new Date(dateString);
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffMinutes = Math.floor(diffMs / (1000 * 60));
    const diffHours = Math.floor(diffMinutes / 60);
    const diffDays = Math.floor(diffHours / 24);

    if (diffMinutes < 1) return 'Just now';
    if (diffMinutes < 60) return `${diffMinutes}m ago`;
    if (diffHours < 24) return `${diffHours}h ago`;
    if (diffDays < 7) return `${diffDays}d ago`;
    return date.toLocaleDateString();
  };

  if (loading) {
    return (
      <div className="workspace-manager">
        <div className="loading">Loading workspaces...</div>
      </div>
    );
  }

  return (
    <div className="workspace-manager">
      <div className="workspace-header">
        <div>
          <h2>🗂️ Workspace Manager</h2>
          <div className="workspace-actions">
            <button 
              className="btn btn-primary"
              onClick={() => setShowTemplateModal(true)}
            >
              📁 Create File Workspace
            </button>
          </div>
        </div>
        <p>Organize your files and create structured workspaces for different projects</p>
      </div>

      {/* File Workspaces Section */}
      <div className="file-workspaces-section">
        <h3>📁 File Workspaces</h3>
        <p>Create organized folder structures for your projects</p>
        
        {createdWorkspaces.length > 0 && (
          <div className="created-workspaces">
            <h4>Recently Created:</h4>
            <div className="workspace-grid">
              {createdWorkspaces.map((workspace, index) => (
                <div key={index} className="workspace-card file-workspace">
                  <div className="workspace-icon">
                    {defaultTemplates.find(t => t.name === workspace.template)?.icon || '📁'}
                  </div>
                  <div className="workspace-info">
                    <h4>{workspace.workspace_name}</h4>
                    <p>Template: {workspace.template}</p>
                    <small className="workspace-path">{workspace.workspace_path}</small>
                    <div className="folder-count">
                      {workspace.created_directories.length} folders created
                    </div>
                  </div>
                  <div className="workspace-actions">
                    <button 
                      className="btn btn-sm btn-secondary"
                      onClick={() => {
                        // Copy path to clipboard
                        navigator.clipboard.writeText(workspace.workspace_path);
                        alert('Path copied to clipboard!');
                      }}
                    >
                      📋 Copy Path
                    </button>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>

      {/* Virtual Workspaces Section */}
      {workspaces.length > 0 && (
        <>
          {activeWorkspace && (
            <div className="active-workspace">
              <h3>Current Virtual Workspace</h3>
              <div className="workspace-card active" style={{ borderColor: activeWorkspace.color }}>
                <div className="workspace-icon">📊</div>
                <div className="workspace-info">
                  <h4>{activeWorkspace.name}</h4>
                  <p>{activeWorkspace.description}</p>
                  <span className="workspace-theme">{activeWorkspace.theme}</span>
                </div>
                <div className="workspace-status">
                  <span className="status-active">Active</span>
                </div>
              </div>
            </div>
          )}

          <div className="workspace-list">
            <h3>Workspaces</h3>
            <div className="workspace-grid">
              {workspaces.map((workspace) => (
                <div 
                  key={workspace.id}
                  className={`workspace-card ${workspace.id === activeWorkspace?.id ? 'active' : ''}`}
                  style={{ borderColor: workspace.color }}
                  onClick={() => !workspaceFiles[workspace.id] && loadWorkspaceFiles(workspace.id)}
                >
                  <div className="workspace-icon" style={{ backgroundColor: workspace.color }}>
                    {workspace.icon || workspace.name.charAt(0).toUpperCase()}
                  </div>
                  <div className="workspace-info">
                    {editingWorkspace === workspace.id ? (
                      <div className="workspace-name-edit">
                        <input
                          type="text"
                          value={editName}
                          onChange={(e) => setEditName(e.target.value)}
                          onKeyDown={(e) => {
                            if (e.key === 'Enter') saveRename(workspace.id);
                            if (e.key === 'Escape') cancelRenaming();
                          }}
                          onBlur={() => saveRename(workspace.id)}
                          autoFocus
                        />
                      </div>
                    ) : (
                      <h4 
                        onClick={(e) => {
                          e.stopPropagation();
                          startRenaming(workspace);
                        }}
                        style={{ cursor: 'pointer' }}
                        title="Click to rename"
                      >
                        {workspace.name}
                      </h4>
                    )}
                    <p>{workspace.file_count || 0} files</p>
                    <div className="workspace-meta">
                      <span className="workspace-color" style={{ backgroundColor: workspace.color }}></span>
                      {workspace.is_active && <span className="status-active">Active</span>}
                    </div>
                  </div>
                  
                  {/* Folder structure for expanded workspace */}
                  {workspaceFiles[workspace.id] && (
                    <div className="workspace-files">
                      <div className="workspace-files-header">
                        <h5>Ordner-Struktur:</h5>
                        <div className="ai-organization-controls">
                          <button 
                            className="btn btn-sm btn-secondary"
                            onClick={() => suggestOrganization(workspace.id)}
                            title="KI-Organisationsvorschläge"
                          >
                            🤖 Vorschläge
                          </button>
                          <button 
                            className="btn btn-sm btn-primary"
                            onClick={() => autoOrganizeWorkspace(workspace.id)}
                            disabled={autoOrganizing[workspace.id]}
                            title="Automatisch organisieren"
                          >
                            {autoOrganizing[workspace.id] ? '⏳ Organisiere...' : '✨ Auto-Organize'}
                          </button>
                        </div>
                      </div>
                      {workspaceFolders[workspace.id] && Object.keys(workspaceFolders[workspace.id]).length > 0 ? (
                        <div className="folder-structure">
                          {Object.entries(workspaceFolders[workspace.id]).map(([folderName, folderInfo]: [string, any]) => {
                            const folderKey = `${workspace.id}-${folderName}`;
                            const isExpanded = expandedFolders[folderKey];
                            const files = workspaceFiles[workspace.id][folderName] || [];
                            
                            return (
                              <div key={folderName} className="folder-item">
                                <div 
                                  className="folder-header"
                                  onClick={() => toggleFolder(workspace.id, folderName)}
                                >
                                  <span className="folder-icon">
                                    {isExpanded ? '📂' : '📁'}
                                  </span>
                                  <span className="folder-name">{folderName}</span>
                                  <span className="folder-stats">
                                    {folderInfo.count} Dateien • {folderInfo.size}
                                  </span>
                                  <span className="folder-toggle">
                                    {isExpanded ? '▼' : '▶'}
                                  </span>
                                </div>
                                
                                {isExpanded && (
                                  <div className="folder-content">
                                    {files.length > 0 ? (
                                      <div className="file-list">
                                        {files.slice(0, 5).map((file: any) => (
                                          <div key={file.id} className="file-item">
                                            <span className="file-icon">
                                              {file.type === 'image' ? '🖼️' : 
                                               file.type === 'code' ? '💻' : '📄'}
                                            </span>
                                            <span className="file-name">{file.name}</span>
                                            <span className="file-size">{file.size}</span>
                                            <span className="file-priority">
                                              {file.priority === 'high' ? '🔴' : 
                                               file.priority === 'medium' ? '🟡' : '🟢'}
                                            </span>
                                          </div>
                                        ))}
                                        {files.length > 5 && (
                                          <div className="file-item more">
                                            +{files.length - 5} weitere Dateien
                                          </div>
                                        )}
                                      </div>
                                    ) : (
                                      <p className="no-files">Noch keine Dateien</p>
                                    )}
                                    
                                    {/* File drop zone per folder */}
                                    <div 
                                      className="folder-drop-zone"
                                      onDragOver={(e) => e.preventDefault()}
                                      onDrop={(e) => {
                                        e.preventDefault();
                                        const files = e.dataTransfer.files;
                                        if (files.length > 0) {
                                          handleFileUpload(workspace.id, files);
                                        }
                                      }}
                                    >
                                      📁 Dateien hier ablegen (KI-organisiert)
                                    </div>
                                  </div>
                                )}
                              </div>
                            );
                          })}
                        </div>
                      ) : (
                        <p className="no-folders">Keine Ordner-Struktur definiert</p>
                      )}
                      
                      {/* AI Organization Suggestions */}
                      {organizingSuggestions[workspace.id] && (
                        <div className="ai-suggestions">
                          <h5>🤖 KI-Organisationsvorschläge:</h5>
                          <div className="suggestions-list">
                            {organizingSuggestions[workspace.id].map((suggestion: any, index: number) => (
                              <div key={index} className="suggestion-item">
                                <div className="suggestion-header">
                                  <span className="suggestion-file">{suggestion.file.name}</span>
                                  <span className="suggestion-confidence">
                                    {Math.round(suggestion.suggestion.confidence * 100)}% sicher
                                  </span>
                                </div>
                                <div className="suggestion-content">
                                  <span className="suggestion-arrow">→</span>
                                  <span className="suggested-folder">{suggestion.suggestion.folder}</span>
                                  <span className="suggestion-reason">{suggestion.suggestion.reason}</span>
                                </div>
                                {suggestion.suggestion.alternative_folders.length > 0 && (
                                  <div className="alternative-folders">
                                    <small>Alternativen: {suggestion.suggestion.alternative_folders.join(', ')}</small>
                                  </div>
                                )}
                              </div>
                            ))}
                          </div>
                        </div>
                      )}
                      
                      {/* General workspace drop zone with AI auto-organization */}
                      <div 
                        className="workspace-drop-zone"
                        onDragOver={(e) => e.preventDefault()}
                        onDrop={(e) => {
                          e.preventDefault();
                          const files = e.dataTransfer.files;
                          if (files.length > 0) {
                            handleFileUpload(workspace.id, files);
                          }
                        }}
                        onClick={() => {
                          const input = document.createElement('input');
                          input.type = 'file';
                          input.multiple = true;
                          input.onchange = (e) => {
                            const files = (e.target as HTMLInputElement).files;
                            if (files) {
                              handleFileUpload(workspace.id, files);
                            }
                          };
                          input.click();
                        }}
                      >
                        <div className="drop-zone-content">
                          <span className="drop-icon">🤖</span>
                          <span className="drop-text">Dateien hier ablegen für automatische KI-Organisation</span>
                          <small className="drop-hint">Oder klicken zum Datei-Dialog</small>
                        </div>
                      </div>
                    </div>
                  )}
                  
                  <div className="workspace-actions">
                    {workspace.id !== activeWorkspace?.id && (
                      <button 
                        className="btn btn-sm btn-primary"
                        onClick={(e) => {
                          e.stopPropagation();
                          switchToWorkspace(workspace);
                        }}
                      >
                        Switch
                      </button>
                    )}
                    <button 
                      className="btn btn-sm btn-secondary"
                      onClick={(e) => {
                        e.stopPropagation();
                        if (workspaceFiles[workspace.id]) {
                          setWorkspaceFiles(prev => {
                            const newFiles = { ...prev };
                            delete newFiles[workspace.id];
                            return newFiles;
                          });
                        } else {
                          loadWorkspaceFiles(workspace.id);
                        }
                      }}
                    >
                      {workspaceFiles[workspace.id] ? 'Hide Files' : 'Show Files'}
                    </button>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </>
      )}

      {/* File Workspace Template Selection Modal */}
      {showTemplateModal && (
        <div className="modal-overlay">
          <div className="modal">
            <div className="modal-header">
              <h3>📁 Create File Workspace</h3>
              <button 
                className="btn btn-close"
                onClick={() => setShowTemplateModal(false)}
              >
                ×
              </button>
            </div>
            <div className="modal-body">
              <p>Choose a template to create an organized folder structure for your project:</p>
              <div className="template-grid">
                {fileWorkspaceTemplates.map((template) => (
                  <div 
                    key={template.name}
                    className={`template-card ${selectedTemplate?.name === template.name ? 'selected' : ''}`}
                    onClick={() => setSelectedTemplate(template)}
                    style={{ borderColor: selectedTemplate?.name === template.name ? template.color : undefined }}
                  >
                    <div className="template-icon" style={{ color: template.color }}>
                      {template.icon}
                    </div>
                    <h4>{template.name.charAt(0).toUpperCase() + template.name.slice(1)}</h4>
                    <p>{template.description}</p>
                    <div className="template-features">
                      <div className="folder-list">
                        <strong>Folders:</strong>
                        <div className="folders">
                          {template.folders.slice(0, 4).map(folder => (
                            <span key={folder} className="folder-tag">{folder}</span>
                          ))}
                          {template.folders.length > 4 && (
                            <span className="folder-tag">+{template.folders.length - 4} more</span>
                          )}
                        </div>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
              
              {selectedTemplate && (
                <div className="workspace-name-input">
                  <label htmlFor="workspace-name">Workspace Name:</label>
                  <input
                    id="workspace-name"
                    type="text"
                    value={newWorkspaceName}
                    onChange={(e) => setNewWorkspaceName(e.target.value)}
                    placeholder={`My ${selectedTemplate.name.charAt(0).toUpperCase() + selectedTemplate.name.slice(1)} Workspace`}
                    autoFocus
                  />
                  <small>Will be created in: ~/OrdnungsHub/Workspaces/{newWorkspaceName || 'WorkspaceName'}</small>
                </div>
              )}
            </div>
            <div className="modal-footer">
              <button 
                className="btn btn-secondary"
                onClick={() => {
                  setShowTemplateModal(false);
                  setSelectedTemplate(null);
                  setNewWorkspaceName('');
                }}
                disabled={creatingWorkspace}
              >
                Cancel
              </button>
              <button 
                className="btn btn-primary"
                disabled={!selectedTemplate || !newWorkspaceName.trim() || creatingWorkspace}
                onClick={() => selectedTemplate && createFileWorkspace(selectedTemplate, newWorkspaceName.trim())}
              >
                {creatingWorkspace ? 'Creating...' : 'Create Workspace'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default WorkspaceManager;