import React, { useState, useEffect } from 'react';
import { useApi } from '../../contexts/ApiContext';
import './TaskManager.css';

interface Task {
  id: string;
  title: string;
  description?: string;
  status: 'pending' | 'in-progress' | 'done' | 'blocked' | 'completed';
  priority: 'low' | 'medium' | 'high';
  dependencies?: string[];
  subtasks?: Task[];
  details?: string;
  testStrategy?: string;
  workspace_id?: number;
  related_files?: string[];
}

interface Workspace {
  id: number;
  name: string;
  color: string;
}

interface WorkspaceTaskOverview {
  workspace_name: string;
  workspace_color: string;
  statistics: {
    total_tasks: number;
    completed_tasks: number;
    in_progress_tasks: number;
    pending_tasks: number;
    completion_rate: number;
  };
  recent_tasks: Task[];
  tasks: Task[];
}

interface TaskProgress {
  total_tasks: number;
  completed_tasks: number;
  pending_tasks: number;
  in_progress_tasks: number;
  completion_percentage: number;
}

interface DependencyNode {
  id: string;
  title: string;
  status: string;
  priority: string;
}

interface DependencyEdge {
  from: string;
  to: string;
}

const TaskManager: React.FC = () => {
  const { makeApiRequest } = useApi();
  
  // State management
  const [tasks, setTasks] = useState<Task[]>([]);
  const [nextTask, setNextTask] = useState<Task | null>(null);
  const [progress, setProgress] = useState<TaskProgress | null>(null);
  const [selectedTask, setSelectedTask] = useState<Task | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [activeTab, setActiveTab] = useState<'overview' | 'tasks' | 'dependencies' | 'add' | 'workspace-overview'>('overview');
  const [complexityReport, setComplexityReport] = useState<any>(null);
  
  // Workspace integration state
  const [workspaces, setWorkspaces] = useState<Workspace[]>([]);
  const [workspaceOverview, setWorkspaceOverview] = useState<{[key: number]: WorkspaceTaskOverview}>({});
  const [selectedWorkspace, setSelectedWorkspace] = useState<number | null>(null);
  const [workspaceSuggestions, setWorkspaceSuggestions] = useState<any[]>([]);
  
  // New task form
  const [newTask, setNewTask] = useState({
    title: '',
    description: '',
    priority: 'medium' as 'low' | 'medium' | 'high',
    dependencies: [] as string[],
    workspace_id: null as number | null
  });

  useEffect(() => {
    loadTaskData();
    loadWorkspaces();
  }, []);

  const loadWorkspaces = async () => {
    try {
      const response = await makeApiRequest('/workspaces/');
      setWorkspaces(response);
    } catch (error) {
      console.error('Failed to load workspaces:', error);
    }
  };

  const loadWorkspaceOverview = async () => {
    try {
      const response = await makeApiRequest('/tasks/taskmaster/workspace-overview');
      if (response.success) {
        setWorkspaceOverview(response.overview);
      }
    } catch (error) {
      console.error('Failed to load workspace overview:', error);
    }
  };

  const suggestWorkspaceForTask = async (title: string, description: string) => {
    try {
      const response = await makeApiRequest('/tasks/taskmaster/suggest-workspace', 'POST', {
        title,
        description
      });
      if (response.success) {
        setWorkspaceSuggestions(response.suggestions);
        return response.auto_suggestion;
      }
    } catch (error) {
      console.error('Failed to get workspace suggestions:', error);
    }
    return null;
  };

  const linkTaskToWorkspace = async (taskId: string, workspaceId: number) => {
    try {
      const response = await makeApiRequest(`/tasks/taskmaster/${taskId}/link-workspace`, 'POST', {
        task_id: taskId,
        workspace_id: workspaceId
      });
      if (response.success) {
        loadTaskData(); // Reload tasks to show updated workspace links
        return true;
      }
    } catch (error) {
      console.error('Failed to link task to workspace:', error);
    }
    return false;
  };

  const loadTaskData = async () => {
    setIsLoading(true);
    try {
      await Promise.all([
        loadTasks(),
        loadProgress(),
        loadNextTask()
      ]);
    } catch (error) {
      console.error('Failed to load task data:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const loadTasks = async () => {
    try {
      const response = await makeApiRequest('/tasks/taskmaster/all', 'GET');
      setTasks(response.tasks || []);
    } catch (error) {
      console.error('Failed to load tasks:', error);
    }
  };

  const loadProgress = async () => {
    try {
      const response = await makeApiRequest('/tasks/taskmaster/progress', 'GET');
      setProgress(response);
    } catch (error) {
      console.error('Failed to load progress:', error);
    }
  };

  const loadNextTask = async () => {
    try {
      const response = await makeApiRequest('/tasks/taskmaster/next', 'GET');
      setNextTask(response.task);
    } catch (error) {
      console.error('Failed to load next task:', error);
    }
  };

  const handleTaskStatusUpdate = async (taskId: string, newStatus: string) => {
    try {
      await makeApiRequest(`/tasks/taskmaster/${taskId}/status`, 'PUT', { status: newStatus });
      await loadTaskData(); // Reload all data
    } catch (error) {
      console.error('Failed to update task status:', error);
    }
  };

  const handleExpandTask = async (taskId: string) => {
    try {
      setIsLoading(true);
      await makeApiRequest(`/tasks/taskmaster/${taskId}/expand`, 'POST');
      await loadTasks(); // Reload tasks to show new subtasks
    } catch (error) {
      console.error('Failed to expand task:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const handleAddTask = async () => {
    if (!newTask.title.trim()) return;

    try {
      setIsLoading(true);
      
      // Get AI workspace suggestion if no workspace is selected
      let taskToAdd = { ...newTask };
      if (!taskToAdd.workspace_id && taskToAdd.title) {
        const suggestion = await suggestWorkspaceForTask(taskToAdd.title, taskToAdd.description || '');
        if (suggestion && suggestion.confidence > 0.65) {  // Lower threshold for better matching
          taskToAdd.workspace_id = suggestion.workspace_id;
        }
      }
      
      await makeApiRequest('/tasks/taskmaster/add', 'POST', taskToAdd);
      setNewTask({ 
        title: '', 
        description: '', 
        priority: 'medium', 
        dependencies: [], 
        workspace_id: null 
      });
      setWorkspaceSuggestions([]);
      await loadTaskData();
    } catch (error) {
      console.error('Failed to add task:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const handleTaskInputChange = async (field: string, value: any) => {
    const updatedTask = { ...newTask, [field]: value };
    setNewTask(updatedTask);
    
    // Trigger workspace suggestions when title is available (description optional)
    if (updatedTask.title.trim() && !updatedTask.workspace_id) {
      await suggestWorkspaceForTask(updatedTask.title, updatedTask.description || '');
    }
  };

  const handleAnalyzeComplexity = async () => {
    try {
      setIsLoading(true);
      const report = await makeApiRequest('/tasks/taskmaster/analyze-complexity', 'POST');
      setComplexityReport(report);
    } catch (error) {
      console.error('Failed to analyze complexity:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'done': return '#10b981';
      case 'in-progress': return '#3b82f6';
      case 'pending': return '#f59e0b';
      case 'blocked': return '#ef4444';
      default: return '#6b7280';
    }
  };

  const getPriorityColor = (priority: string) => {
    switch (priority) {
      case 'high': return '#ef4444';
      case 'medium': return '#f59e0b';
      case 'low': return '#10b981';
      default: return '#6b7280';
    }
  };

  const renderTaskCard = (task: Task, isSubtask = false) => (
    <div 
      key={task.id} 
      className={`task-card ${isSubtask ? 'subtask' : ''} ${selectedTask?.id === task.id ? 'selected' : ''}`}
      onClick={() => setSelectedTask(task)}
    >
      <div className="task-header">
        <h4>{task.title}</h4>
        <div className="task-badges">
          <span 
            className="status-badge" 
            style={{ backgroundColor: getStatusColor(task.status) }}
          >
            {task.status}
          </span>
          <span 
            className="priority-badge" 
            style={{ backgroundColor: getPriorityColor(task.priority) }}
          >
            {task.priority}
          </span>
          {task.workspace_id && (
            <span 
              className="workspace-badge"
              style={{ 
                backgroundColor: workspaces.find(w => w.id === task.workspace_id)?.color || '#6b7280',
                color: 'white'
              }}
            >
              🗂️ {workspaces.find(w => w.id === task.workspace_id)?.name || 'Unknown'}
            </span>
          )}
        </div>
      </div>
      
      {task.description && (
        <p className="task-description">{task.description}</p>
      )}
      
      {task.dependencies && task.dependencies.length > 0 && (
        <div className="task-dependencies">
          <small>Depends on: {task.dependencies.join(', ')}</small>
        </div>
      )}
      
      <div className="task-actions">
        {task.status !== 'done' && (
          <>
            <button
              onClick={(e) => {
                e.stopPropagation();
                handleTaskStatusUpdate(task.id, task.status === 'pending' ? 'in-progress' : 'done');
              }}
              className="btn btn-sm btn-primary"
            >
              {task.status === 'pending' ? 'Start' : 'Complete'}
            </button>
            
            {task.status === 'pending' && !task.subtasks?.length && (
              <button
                onClick={(e) => {
                  e.stopPropagation();
                  handleExpandTask(task.id);
                }}
                className="btn btn-sm btn-secondary"
                disabled={isLoading}
              >
                Expand
              </button>
            )}
          </>
        )}
      </div>
      
      {task.subtasks && task.subtasks.length > 0 && (
        <div className="subtasks">
          {task.subtasks.map(subtask => renderTaskCard(subtask, true))}
        </div>
      )}
    </div>
  );

  const renderTaskDetails = () => {
    if (!selectedTask) return null;

    return (
      <div className="task-details">
        <h3>{selectedTask.title}</h3>
        
        <div className="task-meta">
          <span className="status" style={{ color: getStatusColor(selectedTask.status) }}>
            Status: {selectedTask.status}
          </span>
          <span className="priority" style={{ color: getPriorityColor(selectedTask.priority) }}>
            Priority: {selectedTask.priority}
          </span>
        </div>
        
        {selectedTask.description && (
          <div className="section">
            <h4>Description</h4>
            <p>{selectedTask.description}</p>
          </div>
        )}
        
        {selectedTask.details && (
          <div className="section">
            <h4>Implementation Details</h4>
            <div className="details-content">
              {selectedTask.details.split('\n').map((line, index) => (
                <p key={index}>{line}</p>
              ))}
            </div>
          </div>
        )}
        
        {selectedTask.testStrategy && (
          <div className="section">
            <h4>Test Strategy</h4>
            <div className="test-strategy-content">
              {selectedTask.testStrategy.split('\n').map((line, index) => (
                <p key={index}>{line}</p>
              ))}
            </div>
          </div>
        )}
        
        {selectedTask.dependencies && selectedTask.dependencies.length > 0 && (
          <div className="section">
            <h4>Dependencies</h4>
            <ul>
              {selectedTask.dependencies.map(dep => (
                <li key={dep}>Task {dep}</li>
              ))}
            </ul>
          </div>
        )}
      </div>
    );
  };

  return (
    <div className="task-manager">
      <div className="task-manager-header">
        <h2>AI-Powered Task Management</h2>
        <p>Intelligent task planning and execution with Taskmaster AI</p>
      </div>

      <div className="task-manager-tabs">
        <button 
          className={`tab ${activeTab === 'overview' ? 'active' : ''}`}
          onClick={() => setActiveTab('overview')}
        >
          Overview
        </button>
        <button 
          className={`tab ${activeTab === 'tasks' ? 'active' : ''}`}
          onClick={() => setActiveTab('tasks')}
        >
          All Tasks
        </button>
        <button 
          className={`tab ${activeTab === 'dependencies' ? 'active' : ''}`}
          onClick={() => setActiveTab('dependencies')}
        >
          Dependencies
        </button>
        <button 
          className={`tab ${activeTab === 'add' ? 'active' : ''}`}
          onClick={() => setActiveTab('add')}
        >
          Add Task
        </button>
        <button 
          className={`tab ${activeTab === 'workspace-overview' ? 'active' : ''}`}
          onClick={() => {
            setActiveTab('workspace-overview');
            loadWorkspaceOverview();
          }}
        >
          🗂️ Workspaces
        </button>
      </div>

      <div className="task-manager-content">
        {activeTab === 'overview' && (
          <div className="overview-tab">
            {/* Progress Overview */}
            {progress && (
              <div className="progress-overview">
                <h3>Project Progress</h3>
                <div className="progress-stats">
                  <div className="stat">
                    <span className="number">{progress.completion_percentage}%</span>
                    <span className="label">Complete</span>
                  </div>
                  <div className="stat">
                    <span className="number">{progress.completed_tasks}</span>
                    <span className="label">Done</span>
                  </div>
                  <div className="stat">
                    <span className="number">{progress.in_progress_tasks}</span>
                    <span className="label">In Progress</span>
                  </div>
                  <div className="stat">
                    <span className="number">{progress.pending_tasks}</span>
                    <span className="label">Pending</span>
                  </div>
                </div>
                
                <div className="progress-bar">
                  <div 
                    className="progress-fill" 
                    style={{ width: `${progress.completion_percentage}%` }}
                  />
                </div>
              </div>
            )}

            {/* Next Task Recommendation */}
            {nextTask && (
              <div className="next-task-recommendation">
                <h3>🎯 Recommended Next Task</h3>
                {renderTaskCard(nextTask)}
              </div>
            )}

            {/* AI Actions */}
            <div className="ai-actions">
              <h3>AI Tools</h3>
              <div className="action-buttons">
                <button
                  onClick={handleAnalyzeComplexity}
                  disabled={isLoading}
                  className="btn btn-primary"
                >
                  {isLoading ? 'Analyzing...' : 'Analyze Task Complexity'}
                </button>
                <button
                  onClick={loadTaskData}
                  disabled={isLoading}
                  className="btn btn-secondary"
                >
                  Refresh Data
                </button>
              </div>
              
              {complexityReport && (
                <div className="complexity-report">
                  <h4>Complexity Analysis Results</h4>
                  <pre>{JSON.stringify(complexityReport, null, 2)}</pre>
                </div>
              )}
            </div>
          </div>
        )}

        {activeTab === 'tasks' && (
          <div className="tasks-tab">
            <div className="tasks-layout">
              <div className="tasks-list">
                <h3>All Tasks ({tasks.length})</h3>
                <div className="tasks-container">
                  {tasks.map(task => renderTaskCard(task))}
                </div>
              </div>
              
              {selectedTask && (
                <div className="task-details-panel">
                  {renderTaskDetails()}
                </div>
              )}
            </div>
          </div>
        )}

        {activeTab === 'add' && (
          <div className="add-task-tab">
            <h3>Add New Task</h3>
            <div className="add-task-form">
              <div className="form-group">
                <label htmlFor="task-title">Title *</label>
                <input
                  id="task-title"
                  type="text"
                  value={newTask.title}
                  onChange={(e) => handleTaskInputChange('title', e.target.value)}
                  placeholder="Enter task title..."
                />
              </div>
              
              <div className="form-group">
                <label htmlFor="task-description">Description</label>
                <textarea
                  id="task-description"
                  value={newTask.description}
                  onChange={(e) => handleTaskInputChange('description', e.target.value)}
                  placeholder="Describe the task..."
                  rows={4}
                />
              </div>
              
              <div className="form-group">
                <label htmlFor="task-priority">Priority</label>
                <select
                  id="task-priority"
                  value={newTask.priority}
                  onChange={(e) => setNewTask({ ...newTask, priority: e.target.value as any })}
                >
                  <option value="low">Low</option>
                  <option value="medium">Medium</option>
                  <option value="high">High</option>
                </select>
              </div>
              
              <div className="form-group">
                <label htmlFor="workspace-select">Workspace</label>
                <select
                  id="workspace-select"
                  value={newTask.workspace_id || ''}
                  onChange={(e) => {
                    if (e.target.value === 'create_new') {
                      // TODO: Implement create new workspace functionality
                      alert('Create new workspace functionality will be implemented');
                    } else {
                      setNewTask({ ...newTask, workspace_id: e.target.value ? parseInt(e.target.value) : null });
                    }
                  }}
                >
                  <option value="">🤖 Let AI suggest (recommended)</option>
                  <option value="create_new">➕ Create New Workspace</option>
                  {workspaces.map(workspace => (
                    <option key={workspace.id} value={workspace.id}>
                      🗂️ {workspace.name}
                    </option>
                  ))}
                </select>
              </div>

              {workspaceSuggestions.length > 0 && (
                <div className="workspace-suggestions">
                  <h4>🤖 AI Workspace Vorschläge:</h4>
                  <div className="suggestions-list">
                    {workspaceSuggestions.map((suggestion, index) => (
                      <div 
                        key={index} 
                        className="suggestion-item"
                        onClick={() => setNewTask({ ...newTask, workspace_id: suggestion.workspace_id })}
                      >
                        <div className="suggestion-header">
                          <span className="workspace-name" style={{ color: workspaces.find(w => w.id === suggestion.workspace_id)?.color }}>
                            🗂️ {suggestion.workspace_name}
                          </span>
                          <span className="confidence-badge">
                            {Math.round(suggestion.confidence * 100)}% sicher
                          </span>
                        </div>
                        <div className="suggestion-reason">
                          {suggestion.reason}
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}
              
              <button
                onClick={handleAddTask}
                disabled={!newTask.title.trim() || isLoading}
                className="btn btn-primary"
              >
                {isLoading ? 'Adding...' : 'Add Task with AI'}
              </button>
            </div>
          </div>
        )}

        {activeTab === 'workspace-overview' && (
          <div className="workspace-overview-tab">
            <h3>🗂️ Tasks by Workspace</h3>
            
            {Object.keys(workspaceOverview).length === 0 ? (
              <div className="loading-state">
                <p>Loading workspace overview...</p>
              </div>
            ) : (
              <div className="workspace-overview-grid">
                {Object.entries(workspaceOverview).map(([workspaceId, overview]) => (
                  <div key={workspaceId} className="workspace-overview-card">
                    <div className="workspace-header">
                      <div className="workspace-info">
                        <h4 style={{ color: overview.workspace_color }}>
                          🗂️ {overview.workspace_name}
                        </h4>
                        <div className="completion-rate">
                          {overview.statistics.completion_rate.toFixed(1)}% complete
                        </div>
                      </div>
                      <div className="task-count">
                        {overview.statistics.total_tasks} tasks
                      </div>
                    </div>
                    
                    <div className="workspace-stats">
                      <div className="stat-item completed">
                        <span className="stat-number">{overview.statistics.completed_tasks}</span>
                        <span className="stat-label">Completed</span>
                      </div>
                      <div className="stat-item in-progress">
                        <span className="stat-number">{overview.statistics.in_progress_tasks}</span>
                        <span className="stat-label">In Progress</span>
                      </div>
                      <div className="stat-item pending">
                        <span className="stat-number">{overview.statistics.pending_tasks}</span>
                        <span className="stat-label">Pending</span>
                      </div>
                    </div>
                    
                    {overview.recent_tasks.length > 0 && (
                      <div className="recent-tasks">
                        <h5>Recent Tasks:</h5>
                        {overview.recent_tasks.map(task => (
                          <div key={task.id} className="mini-task-card">
                            <span className="mini-task-title">{task.title}</span>
                            <span 
                              className="mini-task-status"
                              style={{ backgroundColor: getStatusColor(task.status) }}
                            >
                              {task.status}
                            </span>
                          </div>
                        ))}
                      </div>
                    )}
                    
                    <div className="workspace-actions">
                      <button 
                        className="btn btn-sm btn-secondary"
                        onClick={() => setSelectedWorkspace(parseInt(workspaceId))}
                      >
                        View All Tasks
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            )}
            
            {selectedWorkspace && workspaceOverview[selectedWorkspace] && (
              <div className="workspace-detail">
                <h4>All Tasks in {workspaceOverview[selectedWorkspace].workspace_name}</h4>
                <div className="workspace-tasks-list">
                  {workspaceOverview[selectedWorkspace].tasks.map(task => renderTaskCard(task))}
                </div>
                <button 
                  className="btn btn-secondary"
                  onClick={() => setSelectedWorkspace(null)}
                >
                  Close
                </button>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
};

export default TaskManager;