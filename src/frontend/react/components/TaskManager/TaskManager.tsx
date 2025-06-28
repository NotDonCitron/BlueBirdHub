import React, { useState, useEffect } from 'react';
import { apiClient } from '../../lib/api';
import './TaskManager.css';
import LoadingSpinner from '../../components/LoadingSpinner';
import { AgentHub } from '../AgentHub/AgentHub';

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
  description?: string;
  theme?: string;
  icon?: string;
  task_count?: number;
}

interface NewWorkspace {
  name: string;
  description: string;
  color: string;
  theme: string;
  icon: string;
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
  // API request helper with detailed error logging
  const makeApiRequest = async (endpoint: string, method: string = 'GET', data?: any) => {
    try {
      console.log(`🔄 Making API request: ${method} ${endpoint}`, data);
      
      const config: RequestInit = { method };
      if (data && (method === 'POST' || method === 'PUT')) {
        config.body = JSON.stringify(data);
        config.headers = { 'Content-Type': 'application/json' };
      }
      
      // Use the apiClient.request method and handle errors
      const response = await apiClient.request(endpoint, config);
      console.log(`✅ API Success: ${method} ${endpoint}`, response);
      return response;
    } catch (error) {
      console.error(`❌ API Error: ${method} ${endpoint}`, error);
      
      // Log detailed error information
      if (error instanceof Error) {
        console.error('Error details:', {
          message: error.message,
          stack: error.stack,
          endpoint,
          method,
          data
        });
      }
      
      // Set appropriate error states
      if (endpoint.includes('/workspaces')) {
        setWorkspacesError(`Failed to ${method.toLowerCase()} workspace data: ${error instanceof Error ? error.message : 'Unknown error'}`);
      } else if (endpoint.includes('/tasks')) {
        setTasksError(`Failed to ${method.toLowerCase()} task data: ${error instanceof Error ? error.message : 'Unknown error'}`);
      }
      
      throw error;
    }
  };

  // Auto-check system to verify fixes
  const autoCheckForErrors = async () => {
    console.log('🔍 Running auto-check for API connectivity...');
    
    try {
      // Test health endpoint
      await makeApiRequest('/health');
      console.log('✅ Health check passed');
      
      // Test workspaces endpoint
      await makeApiRequest('/workspaces');
      console.log('✅ Workspaces endpoint working');
      
      // Test tasks endpoint
      await makeApiRequest('/tasks/taskmaster/all');
      console.log('✅ Tasks endpoint working');
      
      // Test workspace suggestion endpoint (NEW)
      await makeApiRequest('/tasks/taskmaster/suggest-workspace', 'POST', {
        title: 'test task',
        description: 'test description'
      });
      console.log('✅ Workspace suggestion endpoint working');
      
      console.log('🎉 All API endpoints are working correctly!');
      return true;
    } catch (error) {
      console.error('❌ Auto-check failed:', error);
      return false;
    }
  };

  // State management with error tracking
  const [autoCheckResults, setAutoCheckResults] = useState<{status: string, lastCheck: string} | null>(null);

  // State management
  const [tasks, setTasks] = useState<Task[]>([]);
  const [workspaces, setWorkspaces] = useState<Workspace[]>([]);
  const [isLoadingTasks, setIsLoadingTasks] = useState(false);
  const [isLoadingWorkspaces, setIsLoadingWorkspaces] = useState(false);
  const [tasksError, setTasksError] = useState<string | null>(null);
  const [workspacesError, setWorkspacesError] = useState<string | null>(null);
  const [nextTask, setNextTask] = useState<Task | null>(null);
  const [progress, setProgress] = useState<TaskProgress | null>(null);
  const [selectedTask, setSelectedTask] = useState<Task | null>(null);
  const [activeTab, setActiveTab] = useState<'overview' | 'tasks' | 'dependencies' | 'add' | 'workspace-overview' | 'workspace-detail' | 'agents'>('overview');
  const [complexityReport, setComplexityReport] = useState<any>(null);
  const [showSubtaskForm, setShowSubtaskForm] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  
  // Workspace integration state
  const [workspaceOverview, setWorkspaceOverview] = useState<{[key: number]: WorkspaceTaskOverview}>({});
  const [selectedWorkspace, setSelectedWorkspace] = useState<number | null>(null);
  const [workspaceSuggestions, setWorkspaceSuggestions] = useState<any[]>([]);
  const [workspaceDetail, setWorkspaceDetail] = useState<any>(null);
  
  // New workspace creation
  const [showCreateWorkspace, setShowCreateWorkspace] = useState(false);
  const [aiWorkspaceSuggestions, setAiWorkspaceSuggestions] = useState<any[]>([]);
  const [newWorkspace, setNewWorkspace] = useState<NewWorkspace>({
    name: '',
    description: '',
    color: '#3b82f6',
    theme: 'modern_light',
    icon: '📁'
  });
  
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
    
    // Run auto-check after initial load
    setTimeout(async () => {
      const checkResult = await autoCheckForErrors();
      setAutoCheckResults({
        status: checkResult ? 'success' : 'failed',
        lastCheck: new Date().toLocaleTimeString()
      });
    }, 2000);
  }, []);

  useEffect(() => {
    if (activeTab === 'workspace-overview' && workspaces.length > 0) {
      loadWorkspaceOverview();
    }
  }, [activeTab, workspaces, tasks]);

  const loadWorkspaces = async () => {
    setIsLoadingWorkspaces(true);
    setWorkspacesError(null);
    try {
      const response = await makeApiRequest('/workspaces');
      setWorkspaces(response);
    } catch (error) {
      console.error('Failed to load workspaces:', error);
      setWorkspacesError('Failed to load workspaces');
    } finally {
      setIsLoadingWorkspaces(false);
    }
  };

  const loadWorkspaceOverview = async () => {
    try {
      // For now, create overview from existing workspaces and tasks data
      const overview: {[key: number]: WorkspaceTaskOverview} = {};
      
      for (const workspace of workspaces) {
        const workspaceTasks = tasks.filter(task => task.workspace_id === workspace.id);
        const completedTasks = workspaceTasks.filter(task => task.status === 'completed' || task.status === 'done');
        const inProgressTasks = workspaceTasks.filter(task => task.status === 'in-progress');
        const pendingTasks = workspaceTasks.filter(task => task.status === 'pending');
        
        overview[workspace.id] = {
          workspace_name: workspace.name,
          workspace_color: workspace.color,
          statistics: {
            total_tasks: workspaceTasks.length,
            completed_tasks: completedTasks.length,
            in_progress_tasks: inProgressTasks.length,
            pending_tasks: pendingTasks.length,
            completion_rate: workspaceTasks.length > 0 ? (completedTasks.length / workspaceTasks.length) * 100 : 0
          },
          recent_tasks: workspaceTasks.slice(0, 3),
          tasks: workspaceTasks
        };
      }
      
      setWorkspaceOverview(overview);
    } catch (error) {
      console.error('Failed to load workspace overview:', error);
    }
  };

  const loadWorkspaceDetail = async (workspaceId: number) => {
    try {
      const response = await makeApiRequest(`/workspaces/${workspaceId}/detail`);
      setWorkspaceDetail(response);
      setSelectedWorkspace(workspaceId);
      setActiveTab('workspace-detail');
    } catch (error) {
      console.error('Failed to load workspace detail:', error);
    }
  };

  const generateAIWorkspaceSuggestions = async (taskTitle: string, taskDescription: string) => {
    try {
      const response = await makeApiRequest('/tasks/ai-suggestions', 'POST', {
        task_title: taskTitle,
        task_description: taskDescription,
        existing_workspaces: workspaces.map(w => ({ 
          id: w.id,
          name: w.name, 
          description: w.description,
          theme: w.theme,
          color: w.color
        }))
      });
      if (response.suggestions) {
        setAiWorkspaceSuggestions(response.suggestions);
      }
    } catch (error) {
      console.error('Failed to get AI workspace suggestions:', error);
    }
  };

  const createWorkspace = async () => {
    if (!newWorkspace.name.trim()) return;

    try {
      setIsLoading(true);
      const response = await makeApiRequest('/workspaces', 'POST', newWorkspace);
      
      // Add new workspace to list
      setWorkspaces([...workspaces, response]);
      
      // Reset form
      setNewWorkspace({
        name: '',
        description: '',
        color: '#3b82f6',
        theme: 'modern_light',
        icon: '📁'
      });
      setShowCreateWorkspace(false);
      setAiWorkspaceSuggestions([]);
      
      return response;
    } catch (error) {
      console.error('Failed to create workspace:', error);
      return null;
    } finally {
      setIsLoading(false);
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
    setIsLoadingTasks(true);
    setTasksError(null);
    try {
      const response = await makeApiRequest('/tasks/taskmaster/all', 'GET');
      setTasks(response.tasks || []);
    } catch (error) {
      console.error('Failed to load tasks:', error);
      setTasksError('Failed to load tasks');
    } finally {
      setIsLoadingTasks(false);
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
      // Also generate AI suggestions for new workspaces
      await generateAIWorkspaceSuggestions(updatedTask.title, updatedTask.description || '');
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

  const createSubtask = async (parentTaskId: string, title: string) => {
    try {
      const response = await makeApiRequest(`/tasks/${parentTaskId}/subtasks`, 'POST', { title });
      if (response) {
        // Optimistically update the UI or reload all tasks
        loadTaskData();
        setShowSubtaskForm(null); // Hide form on success
      }
    } catch (error) {
      console.error('Failed to create subtask:', error);
    }
  };

  const updateSubtaskStatus = async (subtaskId: string, newStatus: string) => {
    try {
      const response = await makeApiRequest(`/subtasks/${subtaskId}`, 'PUT', { status: newStatus });
      if (response) {
        // Optimistically update the UI or reload all tasks
        loadTaskData();
      }
    } catch (error) {
      console.error('Failed to update subtask status:', error);
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
      
      {!isSubtask && (
        <div className="task-actions">
          <button onClick={(e) => { e.stopPropagation(); handleExpandTask(task.id); }}>
            {selectedTask?.id === task.id && selectedTask.subtasks ? 'Collapse' : 'Expand'}
          </button>
          <button onClick={(e) => { e.stopPropagation(); setShowSubtaskForm(task.id); }}>Add Subtask</button>
        </div>
      )}
      
      {showSubtaskForm === task.id && (
        <form
          className="subtask-form"
          onClick={(e) => e.stopPropagation()}
          onSubmit={(e) => {
            e.preventDefault();
            const titleInput = (e.currentTarget.elements.namedItem('subtaskTitle') as HTMLInputElement);
            if (titleInput.value) {
              createSubtask(task.id, titleInput.value);
              titleInput.value = '';
            }
          }}
        >
          <input name="subtaskTitle" type="text" placeholder="New subtask..." />
          <button type="submit">Add</button>
          <button type="button" onClick={() => setShowSubtaskForm(null)}>Cancel</button>
        </form>
      )}
      
      {selectedTask?.id === task.id && task.subtasks && task.subtasks.length > 0 && (
        <div className="subtask-list">
          <h5>Subtasks:</h5>
          {task.subtasks.map(subtask => (
            <div key={subtask.id} className="subtask-item">
              <input 
                type="checkbox" 
                checked={subtask.status === 'done' || subtask.status === 'completed'}
                onChange={(e) => {
                  e.stopPropagation();
                  updateSubtaskStatus(subtask.id, e.target.checked ? 'done' : 'pending');
                }}
              />
              <span className={subtask.status === 'done' || subtask.status === 'completed' ? 'completed' : ''}>
                {subtask.title}
              </span>
            </div>
          ))}
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

  if (isLoadingTasks || isLoadingWorkspaces) {
    return <LoadingSpinner />;
  }

  if (tasksError || workspacesError) {
    return <div className="error-message">Error loading data. Please try again later.</div>;
  }

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
        <button 
          className={`tab ${activeTab === 'agents' ? 'active' : ''}`}
          onClick={() => setActiveTab('agents')}
        >
          🧠 AI Agents
        </button>
      </div>

      {/* Auto-check status indicator */}
      {autoCheckResults && (
        <div className={`auto-check-status ${autoCheckResults.status}`}>
          <span className="auto-check-icon">
            {autoCheckResults.status === 'success' ? '✅' : '❌'}
          </span>
          <span className="auto-check-message">
            API Status: {autoCheckResults.status === 'success' ? 'All systems operational' : 'Connection issues detected'}
          </span>
          <span className="auto-check-time">
            Last checked: {autoCheckResults.lastCheck}
          </span>
          <button 
            className="auto-check-retry"
            onClick={async () => {
              const checkResult = await autoCheckForErrors();
              setAutoCheckResults({
                status: checkResult ? 'success' : 'failed',
                lastCheck: new Date().toLocaleTimeString()
              });
            }}
          >
            🔄 Recheck
          </button>
        </div>
      )}

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
                      setShowCreateWorkspace(true);
                      // Generate AI suggestions for new workspace
                      if (newTask.title.trim()) {
                        generateAIWorkspaceSuggestions(newTask.title, newTask.description || '');
                      }
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
                      <button 
                        className="btn btn-sm btn-primary"
                        onClick={() => loadWorkspaceDetail(parseInt(workspaceId))}
                      >
                        📊 Workspace Detail
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

        {/* Create Workspace Modal */}
        {showCreateWorkspace && (
          <div className="modal-overlay">
            <div className="modal-content">
              <div className="modal-header">
                <h3>🤖 Create New Workspace with AI</h3>
                <button 
                  className="close-button"
                  onClick={() => {
                    setShowCreateWorkspace(false);
                    setAiWorkspaceSuggestions([]);
                  }}
                >
                  ✕
                </button>
              </div>
              
              <div className="modal-body">
                {aiWorkspaceSuggestions.length > 0 && (
                  <div className="ai-workspace-suggestions">
                    <h4>🤖 AI suggests these workspaces for your task:</h4>
                    <div className="suggestions-grid">
                      {aiWorkspaceSuggestions.map((suggestion, index) => (
                        <div key={index} className="ai-suggestion-card">
                          <div className="suggestion-header">
                            <span className="suggestion-icon">{suggestion.icon}</span>
                            <h5>{suggestion.name}</h5>
                            <span className="confidence-badge">
                              {(suggestion.confidence * 100).toFixed(0)}% match
                            </span>
                          </div>
                          <p className="suggestion-description">{suggestion.description}</p>
                          <div className="suggestion-tags">
                            {suggestion.suggested_categories?.map((cat: string, idx: number) => (
                              <span key={idx} className="category-tag">{cat}</span>
                            ))}
                          </div>
                          <button
                            className="btn btn-primary"
                            onClick={() => {
                              setNewWorkspace({
                                name: suggestion.name,
                                description: suggestion.description,
                                color: suggestion.color || '#3b82f6',
                                theme: suggestion.theme || 'modern_light',
                                icon: suggestion.icon || '📁'
                              });
                            }}
                          >
                            Use This Suggestion
                          </button>
                        </div>
                      ))}
                    </div>
                    <div className="divider">
                      <span>or create custom workspace</span>
                    </div>
                  </div>
                )}
                
                <div className="create-workspace-form">
                  <div className="form-group">
                    <label>Workspace Name *</label>
                    <input
                      type="text"
                      value={newWorkspace.name}
                      onChange={(e) => setNewWorkspace({ ...newWorkspace, name: e.target.value })}
                      placeholder="Enter workspace name..."
                    />
                  </div>
                  
                  <div className="form-group">
                    <label>Description</label>
                    <textarea
                      value={newWorkspace.description}
                      onChange={(e) => setNewWorkspace({ ...newWorkspace, description: e.target.value })}
                      placeholder="Describe this workspace..."
                      rows={3}
                    />
                  </div>
                  
                  <div className="form-row">
                    <div className="form-group">
                      <label>Icon</label>
                      <select
                        value={newWorkspace.icon}
                        onChange={(e) => setNewWorkspace({ ...newWorkspace, icon: e.target.value })}
                      >
                        <option value="📁">📁 Folder</option>
                        <option value="💼">💼 Work</option>
                        <option value="🏠">🏠 Home</option>
                        <option value="🎨">🎨 Creative</option>
                        <option value="📚">📚 Learning</option>
                        <option value="⚡">⚡ Quick</option>
                        <option value="🔬">🔬 Research</option>
                        <option value="🎯">🎯 Goals</option>
                        <option value="🚀">🚀 Projects</option>
                        <option value="📊">📊 Data</option>
                      </select>
                    </div>
                    
                    <div className="form-group">
                      <label>Color Theme</label>
                      <div className="color-picker">
                        {['#3b82f6', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6', '#06b6d4', '#84cc16', '#f97316'].map(color => (
                          <button
                            key={color}
                            className={`color-option ${newWorkspace.color === color ? 'selected' : ''}`}
                            style={{ backgroundColor: color }}
                            onClick={() => setNewWorkspace({ ...newWorkspace, color })}
                          />
                        ))}
                      </div>
                    </div>
                  </div>
                </div>
              </div>
              
              <div className="modal-footer">
                <button 
                  className="btn btn-secondary"
                  onClick={() => {
                    setShowCreateWorkspace(false);
                    setAiWorkspaceSuggestions([]);
                  }}
                >
                  Cancel
                </button>
                <button 
                  className="btn btn-primary"
                  onClick={async () => {
                    const workspace = await createWorkspace();
                    if (workspace) {
                      setNewTask({ ...newTask, workspace_id: workspace.id });
                    }
                  }}
                  disabled={!newWorkspace.name.trim() || isLoading}
                >
                  {isLoading ? 'Creating...' : 'Create & Use Workspace'}
                </button>
              </div>
            </div>
          </div>
        )}

        {activeTab === 'agents' && (
          <div className="agents-tab">
            <AgentHub className="agent-hub-container" />
          </div>
        )}

        {/* Workspace Detail View */}
        {activeTab === 'workspace-detail' && workspaceDetail && (
          <div className="workspace-detail-tab">
            <div className="workspace-detail-header">
              <div className="workspace-info">
                <span 
                  className="workspace-icon" 
                  style={{ color: workspaceDetail.workspace?.color }}
                >
                  {workspaceDetail.workspace?.icon || '📁'}
                </span>
                <div>
                  <h3 style={{ color: workspaceDetail.workspace?.color }}>
                    {workspaceDetail.workspace?.name}
                  </h3>
                  <p className="workspace-description">
                    {workspaceDetail.workspace?.description}
                  </p>
                </div>
              </div>
              <button 
                className="btn btn-secondary"
                onClick={() => setActiveTab('workspace-overview')}
              >
                ← Back to Overview
              </button>
            </div>
            
            {workspaceDetail.statistics && (
              <div className="workspace-stats-detailed">
                <div className="stat-card">
                  <div className="stat-number">{workspaceDetail.statistics.tasks?.total || 0}</div>
                  <div className="stat-label">Total Tasks</div>
                </div>
                <div className="stat-card completed">
                  <div className="stat-number">{workspaceDetail.statistics.tasks?.completed || 0}</div>
                  <div className="stat-label">Completed</div>
                </div>
                <div className="stat-card in-progress">
                  <div className="stat-number">{workspaceDetail.statistics.tasks?.in_progress || 0}</div>
                  <div className="stat-label">In Progress</div>
                </div>
                <div className="stat-card pending">
                  <div className="stat-number">{workspaceDetail.statistics.tasks?.pending || 0}</div>
                  <div className="stat-label">Pending</div>
                </div>
                <div className="stat-card completion">
                  <div className="stat-number">{workspaceDetail.statistics.tasks?.completion_rate?.toFixed(1) || 0}%</div>
                  <div className="stat-label">Completion Rate</div>
                </div>
                {workspaceDetail.statistics.files && (
                  <div className="stat-card files">
                    <div className="stat-number">{workspaceDetail.statistics.files.total || 0}</div>
                    <div className="stat-label">Files</div>
                  </div>
                )}
              </div>
            )}
            
            <div className="workspace-content">
              <div className="workspace-section">
                <h4>📋 All Tasks</h4>
                <div className="workspace-tasks-grid">
                  {workspaceDetail.tasks?.map((task: Task) => (
                    <div key={task.id} className="workspace-task-card">
                      <div className="task-header">
                        <h5>{task.title}</h5>
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
                        </div>
                      </div>
                      {task.description && (
                        <p className="task-description">{task.description}</p>
                      )}
                    </div>
                  ))}
                </div>
                
                {(!workspaceDetail.tasks || workspaceDetail.tasks.length === 0) && (
                  <div className="empty-state">
                    <p>No tasks in this workspace yet.</p>
                    <button 
                      className="btn btn-primary"
                      onClick={() => setActiveTab('add')}
                    >
                      Add First Task
                    </button>
                  </div>
                )}
              </div>
              
              {workspaceDetail.files && workspaceDetail.files.length > 0 && (
                <div className="workspace-section">
                  <h4>📁 Related Files</h4>
                  <div className="workspace-files-grid">
                    {workspaceDetail.files.map((file: any, index: number) => (
                      <div key={index} className="file-card">
                        <div className="file-icon">📄</div>
                        <div className="file-info">
                          <span className="file-name">{file.name}</span>
                          <span className="file-size">{file.size}</span>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default TaskManager;