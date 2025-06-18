import React, { useState, useEffect, useCallback } from 'react';
import { useApi } from '../../contexts/ApiContext';
import './EnhancedTaskManager.css';

interface Task {
  id: string;
  title: string;
  description: string;
  status: string;
  priority: string;
  workspace_id: number;
  created_at: string;
  due_date?: string;
}

interface TaskAssignment {
  id: number;
  assigned_to: number;
  assigned_by: number;
  role: string;
  completion_percentage: number;
  assigned_at: string;
  assignee: {
    id: number;
    username: string;
    email: string;
  };
}

interface TaskComment {
  id: number;
  content: string;
  comment_type: string;
  created_at: string;
  user: {
    id: number;
    username: string;
  };
  mentions: number[];
  parent_comment_id?: number;
}

interface Workspace {
  id: number;
  name: string;
  description: string;
  access_type: 'owner' | 'shared';
  permissions: string[];
}

interface User {
  id: number;
  username: string;
  email: string;
}

const EnhancedTaskManager: React.FC = () => {
  const { apiCall } = useApi();
  
  // State management
  const [activeTab, setActiveTab] = useState('overview');
  const [tasks, setTasks] = useState<Task[]>([]);
  const [workspaces, setWorkspaces] = useState<Workspace[]>([]);
  const [selectedTask, setSelectedTask] = useState<Task | null>(null);
  const [taskAssignments, setTaskAssignments] = useState<{ [taskId: string]: TaskAssignment[] }>({});
  const [taskComments, setTaskComments] = useState<{ [taskId: string]: TaskComment[] }>({});
  const [availableUsers, setAvailableUsers] = useState<User[]>([]);
  
  // Form states
  const [showAssignTask, setShowAssignTask] = useState(false);
  const [showAddComment, setShowAddComment] = useState(false);
  const [newComment, setNewComment] = useState('');
  const [assignmentData, setAssignmentData] = useState({
    assigned_to: '',
    role: 'collaborator',
    estimated_hours: ''
  });
  
  // Filter states
  const [statusFilter, setStatusFilter] = useState('');
  const [priorityFilter, setPriorityFilter] = useState('');
  const [assigneeFilter, setAssigneeFilter] = useState('');

  // Load data
  const loadTasks = useCallback(async () => {
    try {
      const response = await apiCall('/tasks/taskmaster/all', 'GET');
      setTasks(response.tasks || []);
    } catch (error) {
      console.error('Failed to load tasks:', error);
    }
  }, [apiCall]);

  const loadWorkspaces = useCallback(async () => {
    try {
      const response = await apiCall('/collaboration/workspaces', 'GET');
      setWorkspaces(response.map((item: any) => ({
        id: item.workspace.id,
        name: item.workspace.name,
        description: item.workspace.description,
        access_type: item.access_type,
        permissions: item.permissions
      })));
    } catch (error) {
      console.error('Failed to load workspaces:', error);
    }
  }, [apiCall]);

  const loadTaskAssignments = useCallback(async (taskId: string) => {
    try {
      const response = await apiCall(`/tasks/${taskId}/assignments`, 'GET');
      setTaskAssignments(prev => ({ ...prev, [taskId]: response }));
    } catch (error) {
      console.error('Failed to load task assignments:', error);
    }
  }, [apiCall]);

  const loadTaskComments = useCallback(async (taskId: string) => {
    try {
      const response = await apiCall(`/collaboration/tasks/${taskId}/comments`, 'GET');
      setTaskComments(prev => ({ ...prev, [taskId]: response }));
    } catch (error) {
      console.error('Failed to load task comments:', error);
    }
  }, [apiCall]);

  const loadAvailableUsers = useCallback(async () => {
    try {
      // This would be a new endpoint to get workspace users
      const response = await apiCall('/users/workspace-members', 'GET');
      setAvailableUsers(response);
    } catch (error) {
      console.error('Failed to load available users:', error);
      // Mock data for demo
      setAvailableUsers([
        { id: 1, username: 'john_doe', email: 'john@example.com' },
        { id: 2, username: 'jane_smith', email: 'jane@example.com' },
        { id: 3, username: 'bob_wilson', email: 'bob@example.com' }
      ]);
    }
  }, [apiCall]);

  useEffect(() => {
    loadTasks();
    loadWorkspaces();
    loadAvailableUsers();
  }, [loadTasks, loadWorkspaces, loadAvailableUsers]);

  useEffect(() => {
    if (selectedTask) {
      loadTaskAssignments(selectedTask.id);
      loadTaskComments(selectedTask.id);
    }
  }, [selectedTask, loadTaskAssignments, loadTaskComments]);

  // Handlers
  const handleAssignTask = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedTask) return;
    
    try {
      await apiCall(`/collaboration/tasks/${selectedTask.id}/assign`, 'POST', {
        assigned_to: parseInt(assignmentData.assigned_to),
        role: assignmentData.role,
        estimated_hours: assignmentData.estimated_hours ? parseInt(assignmentData.estimated_hours) : undefined
      });
      
      setShowAssignTask(false);
      setAssignmentData({ assigned_to: '', role: 'collaborator', estimated_hours: '' });
      loadTaskAssignments(selectedTask.id);
    } catch (error) {
      console.error('Failed to assign task:', error);
    }
  };

  const handleAddComment = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedTask || !newComment.trim()) return;
    
    try {
      await apiCall(`/collaboration/tasks/${selectedTask.id}/comments`, 'POST', {
        content: newComment,
        comment_type: 'comment'
      });
      
      setNewComment('');
      setShowAddComment(false);
      loadTaskComments(selectedTask.id);
    } catch (error) {
      console.error('Failed to add comment:', error);
    }
  };

  const handleUpdateProgress = async (taskId: string, percentage: number) => {
    try {
      await apiCall(`/collaboration/tasks/${taskId}/progress`, 'PUT', {
        completion_percentage: percentage
      });
      
      loadTaskAssignments(taskId);
    } catch (error) {
      console.error('Failed to update progress:', error);
    }
  };

  const getFilteredTasks = () => {
    return tasks.filter(task => {
      if (statusFilter && task.status !== statusFilter) return false;
      if (priorityFilter && task.priority !== priorityFilter) return false;
      
      // Assignment filter would require additional logic to check task assignments
      if (assigneeFilter) {
        const assignments = taskAssignments[task.id] || [];
        if (!assignments.some(a => a.assignee.id.toString() === assigneeFilter)) return false;
      }
      
      return true;
    });
  };

  const renderTaskCard = (task: Task) => {
    const assignments = taskAssignments[task.id] || [];
    const comments = taskComments[task.id] || [];
    
    return (
      <div 
        key={task.id} 
        className={`enhanced-task-card ${selectedTask?.id === task.id ? 'selected' : ''}`}
        onClick={() => setSelectedTask(task)}
      >
        <div className="task-header">
          <h4>{task.title}</h4>
          <div className="task-badges">
            <span className={`status-badge ${task.status}`}>{task.status}</span>
            <span className={`priority-badge ${task.priority}`}>{task.priority}</span>
          </div>
        </div>
        
        <p className="task-description">{task.description}</p>
        
        {assignments.length > 0 && (
          <div className="task-assignments">
            <h5>👥 Assigned to:</h5>
            <div className="assignee-list">
              {assignments.map(assignment => (
                <div key={assignment.id} className="assignee-item">
                  <span className="assignee-name">{assignment.assignee.username}</span>
                  <span className="assignee-role">{assignment.role}</span>
                  <div className="progress-mini">
                    <div 
                      className="progress-fill-mini" 
                      style={{ width: `${assignment.completion_percentage}%` }}
                    />
                  </div>
                  <span className="progress-text">{assignment.completion_percentage}%</span>
                </div>
              ))}
            </div>
          </div>
        )}
        
        <div className="task-footer">
          <div className="task-meta">
            <span>📅 {new Date(task.created_at).toLocaleDateString()}</span>
            {comments.length > 0 && <span>💬 {comments.length} comments</span>}
          </div>
          
          <div className="task-actions">
            <button 
              className="btn-small btn-primary"
              onClick={(e) => {
                e.stopPropagation();
                setSelectedTask(task);
                setShowAssignTask(true);
              }}
            >
              Assign
            </button>
            <button 
              className="btn-small btn-secondary"
              onClick={(e) => {
                e.stopPropagation();
                setSelectedTask(task);
                setShowAddComment(true);
              }}
            >
              Comment
            </button>
          </div>
        </div>
      </div>
    );
  };

  const renderTaskDetail = () => {
    if (!selectedTask) return null;
    
    const assignments = taskAssignments[selectedTask.id] || [];
    const comments = taskComments[selectedTask.id] || [];
    
    return (
      <div className="task-detail-panel">
        <div className="detail-header">
          <h3>{selectedTask.title}</h3>
          <button onClick={() => setSelectedTask(null)}>×</button>
        </div>
        
        <div className="detail-content">
          <div className="task-info">
            <p><strong>Description:</strong> {selectedTask.description}</p>
            <p><strong>Status:</strong> <span className={`status-badge ${selectedTask.status}`}>{selectedTask.status}</span></p>
            <p><strong>Priority:</strong> <span className={`priority-badge ${selectedTask.priority}`}>{selectedTask.priority}</span></p>
            <p><strong>Workspace:</strong> {workspaces.find(w => w.id === selectedTask.workspace_id)?.name || 'Unknown'}</p>
          </div>
          
          <div className="assignments-section">
            <div className="section-header">
              <h4>👥 Assignments</h4>
              <button 
                className="btn-small btn-primary"
                onClick={() => setShowAssignTask(true)}
              >
                Add Assignment
              </button>
            </div>
            
            {assignments.map(assignment => (
              <div key={assignment.id} className="assignment-detail">
                <div className="assignment-info">
                  <span className="assignee-name">{assignment.assignee.username}</span>
                  <span className="assignee-email">{assignment.assignee.email}</span>
                  <span className={`role-badge ${assignment.role}`}>{assignment.role}</span>
                </div>
                
                <div className="progress-section">
                  <div className="progress-header">
                    <span>Progress: {assignment.completion_percentage}%</span>
                    <input
                      type="range"
                      min="0"
                      max="100"
                      value={assignment.completion_percentage}
                      onChange={(e) => handleUpdateProgress(selectedTask.id, parseInt(e.target.value))}
                      className="progress-slider"
                    />
                  </div>
                  <div className="progress-bar">
                    <div 
                      className="progress-fill" 
                      style={{ width: `${assignment.completion_percentage}%` }}
                    />
                  </div>
                </div>
                
                <div className="assignment-meta">
                  Assigned: {new Date(assignment.assigned_at).toLocaleDateString()}
                </div>
              </div>
            ))}
          </div>
          
          <div className="comments-section">
            <div className="section-header">
              <h4>💬 Comments</h4>
              <button 
                className="btn-small btn-secondary"
                onClick={() => setShowAddComment(true)}
              >
                Add Comment
              </button>
            </div>
            
            <div className="comments-list">
              {comments.map(comment => (
                <div key={comment.id} className="comment-item">
                  <div className="comment-header">
                    <span className="comment-author">{comment.user.username}</span>
                    <span className="comment-date">{new Date(comment.created_at).toLocaleString()}</span>
                  </div>
                  <div className="comment-content">{comment.content}</div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    );
  };

  const renderFilters = () => (
    <div className="filters-section">
      <div className="filter-group">
        <label>Status:</label>
        <select value={statusFilter} onChange={(e) => setStatusFilter(e.target.value)}>
          <option value="">All Statuses</option>
          <option value="pending">Pending</option>
          <option value="in-progress">In Progress</option>
          <option value="completed">Completed</option>
        </select>
      </div>
      
      <div className="filter-group">
        <label>Priority:</label>
        <select value={priorityFilter} onChange={(e) => setPriorityFilter(e.target.value)}>
          <option value="">All Priorities</option>
          <option value="low">Low</option>
          <option value="medium">Medium</option>
          <option value="high">High</option>
        </select>
      </div>
      
      <div className="filter-group">
        <label>Assignee:</label>
        <select value={assigneeFilter} onChange={(e) => setAssigneeFilter(e.target.value)}>
          <option value="">All Assignees</option>
          {availableUsers.map(user => (
            <option key={user.id} value={user.id.toString()}>{user.username}</option>
          ))}
        </select>
      </div>
      
      <button 
        className="btn-secondary"
        onClick={() => {
          setStatusFilter('');
          setPriorityFilter('');
          setAssigneeFilter('');
        }}
      >
        Clear Filters
      </button>
    </div>
  );

  const filteredTasks = getFilteredTasks();

  return (
    <div className="enhanced-task-manager">
      <div className="manager-header">
        <h2>🚀 Enhanced Collaborative Task Manager</h2>
        <p>Assign tasks, track progress, and collaborate with your team</p>
      </div>

      {renderFilters()}

      <div className="manager-content">
        <div className="tasks-grid">
          <h3>📋 Tasks ({filteredTasks.length})</h3>
          {filteredTasks.map(renderTaskCard)}
        </div>
        
        {selectedTask && renderTaskDetail()}
      </div>

      {/* Assign Task Modal */}
      {showAssignTask && (
        <div className="modal-overlay">
          <div className="modal">
            <div className="modal-header">
              <h3>Assign Task: {selectedTask?.title}</h3>
              <button onClick={() => setShowAssignTask(false)}>×</button>
            </div>
            <form onSubmit={handleAssignTask}>
              <div className="form-group">
                <label>Assign to User</label>
                <select
                  value={assignmentData.assigned_to}
                  onChange={(e) => setAssignmentData({...assignmentData, assigned_to: e.target.value})}
                  required
                >
                  <option value="">Select user...</option>
                  {availableUsers.map(user => (
                    <option key={user.id} value={user.id}>{user.username} ({user.email})</option>
                  ))}
                </select>
              </div>
              
              <div className="form-group">
                <label>Role</label>
                <select
                  value={assignmentData.role}
                  onChange={(e) => setAssignmentData({...assignmentData, role: e.target.value})}
                >
                  <option value="collaborator">Collaborator</option>
                  <option value="owner">Owner</option>
                  <option value="reviewer">Reviewer</option>
                </select>
              </div>
              
              <div className="form-group">
                <label>Estimated Hours (optional)</label>
                <input
                  type="number"
                  value={assignmentData.estimated_hours}
                  onChange={(e) => setAssignmentData({...assignmentData, estimated_hours: e.target.value})}
                  min="1"
                />
              </div>
              
              <div className="modal-actions">
                <button type="button" onClick={() => setShowAssignTask(false)}>Cancel</button>
                <button type="submit" className="btn-primary">Assign Task</button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Add Comment Modal */}
      {showAddComment && (
        <div className="modal-overlay">
          <div className="modal">
            <div className="modal-header">
              <h3>Add Comment: {selectedTask?.title}</h3>
              <button onClick={() => setShowAddComment(false)}>×</button>
            </div>
            <form onSubmit={handleAddComment}>
              <div className="form-group">
                <label>Comment</label>
                <textarea
                  value={newComment}
                  onChange={(e) => setNewComment(e.target.value)}
                  placeholder="Add your comment here..."
                  required
                  rows={4}
                />
              </div>
              
              <div className="modal-actions">
                <button type="button" onClick={() => setShowAddComment(false)}>Cancel</button>
                <button type="submit" className="btn-primary">Add Comment</button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};

export default EnhancedTaskManager;