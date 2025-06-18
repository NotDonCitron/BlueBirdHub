import React, { useState, useEffect } from 'react';
import { useErrorHandler } from '../hooks/useErrorHandler';

interface Task {
  id: string;
  title: string;
  description?: string;
  status: 'todo' | 'in_progress' | 'done';
  priority: 'low' | 'medium' | 'high' | 'urgent';
  due_date?: string;
  created_at: string;
  updated_at: string;
}

const TaskList: React.FC = () => {
  const [tasks, setTasks] = useState<Task[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [filter, setFilter] = useState<'all' | 'todo' | 'in_progress' | 'done'>('all');
  const { handleError } = useErrorHandler({ component: 'TaskList' });

  useEffect(() => {
    loadTasks();
  }, []);

  const loadTasks = async () => {
    try {
      setLoading(true);
      setError(null);
      
      // Mock data for now - replace with actual API call
      const mockTasks: Task[] = [
        {
          id: '1',
          title: 'Implement user authentication',
          description: 'Add login and registration functionality',
          status: 'in_progress',
          priority: 'high',
          due_date: '2024-01-15',
          created_at: new Date().toISOString(),
          updated_at: new Date().toISOString()
        },
        {
          id: '2',
          title: 'Design dashboard layout',
          description: 'Create wireframes and mockups for the main dashboard',
          status: 'todo',
          priority: 'medium',
          created_at: new Date().toISOString(),
          updated_at: new Date().toISOString()
        },
        {
          id: '3',
          title: 'Set up database schema',
          description: 'Define tables and relationships for the application',
          status: 'done',
          priority: 'high',
          created_at: new Date().toISOString(),
          updated_at: new Date().toISOString()
        }
      ];
      
      setTasks(mockTasks);
    } catch (err) {
      const message = handleError(err);
      setError(message);
    } finally {
      setLoading(false);
    }
  };

  const updateTaskStatus = async (taskId: string, newStatus: Task['status']) => {
    try {
      setTasks(prev => prev.map(task => 
        task.id === taskId 
          ? { ...task, status: newStatus, updated_at: new Date().toISOString() }
          : task
      ));
    } catch (err) {
      const message = handleError(err);
      setError(message);
    }
  };

  const createTask = async (title: string, description?: string) => {
    try {
      const newTask: Task = {
        id: Date.now().toString(),
        title,
        description,
        status: 'todo',
        priority: 'medium',
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString()
      };
      
      setTasks(prev => [...prev, newTask]);
    } catch (err) {
      const message = handleError(err);
      setError(message);
    }
  };

  const filteredTasks = filter === 'all' 
    ? tasks 
    : tasks.filter(task => task.status === filter);

  const getPriorityColor = (priority: Task['priority']) => {
    switch (priority) {
      case 'urgent': return '#ef4444';
      case 'high': return '#f97316';
      case 'medium': return '#eab308';
      case 'low': return '#22c55e';
      default: return '#6b7280';
    }
  };

  const getStatusColor = (status: Task['status']) => {
    switch (status) {
      case 'todo': return '#6b7280';
      case 'in_progress': return '#3b82f6';
      case 'done': return '#10b981';
      default: return '#6b7280';
    }
  };

  if (loading) {
    return (
      <div className="task-list-loading">
        <div className="spinner"></div>
        <p>Loading tasks...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="task-list-error">
        <p>Error: {error}</p>
        <button onClick={loadTasks}>Retry</button>
      </div>
    );
  }

  return (
    <div className="task-list">
      <div className="task-list-header">
        <h2>Tasks</h2>
        <button 
          className="create-task-btn"
          onClick={() => createTask('New Task', 'Task description')}
        >
          Create Task
        </button>
      </div>
      
      <div className="task-filters">
        {(['all', 'todo', 'in_progress', 'done'] as const).map(status => (
          <button
            key={status}
            className={`filter-btn ${filter === status ? 'active' : ''}`}
            onClick={() => setFilter(status)}
          >
            {status.replace('_', ' ').toUpperCase()}
          </button>
        ))}
      </div>
      
      <div className="tasks-container">
        {filteredTasks.map(task => (
          <div key={task.id} className="task-card">
            <div className="task-header">
              <h3>{task.title}</h3>
              <div className="task-badges">
                <span 
                  className="priority-badge"
                  style={{ backgroundColor: getPriorityColor(task.priority) }}
                >
                  {task.priority}
                </span>
                <span 
                  className="status-badge"
                  style={{ backgroundColor: getStatusColor(task.status) }}
                >
                  {task.status.replace('_', ' ')}
                </span>
              </div>
            </div>
            
            {task.description && (
              <p className="task-description">{task.description}</p>
            )}
            
            {task.due_date && (
              <p className="task-due-date">
                Due: {new Date(task.due_date).toLocaleDateString()}
              </p>
            )}
            
            <div className="task-actions">
              <select
                value={task.status}
                onChange={(e) => updateTaskStatus(task.id, e.target.value as Task['status'])}
              >
                <option value="todo">To Do</option>
                <option value="in_progress">In Progress</option>
                <option value="done">Done</option>
              </select>
              <button>Edit</button>
              <button>Delete</button>
            </div>
            
            <div className="task-meta">
              <small>Created: {new Date(task.created_at).toLocaleDateString()}</small>
            </div>
          </div>
        ))}
      </div>
      
      {filteredTasks.length === 0 && (
        <div className="no-tasks">
          <p>No tasks found. Create your first task to get started!</p>
        </div>
      )}
      
      <style jsx>{`
        .task-list {
          padding: 20px;
          max-width: 1200px;
          margin: 0 auto;
        }
        
        .task-list-header {
          display: flex;
          justify-content: space-between;
          align-items: center;
          margin-bottom: 20px;
        }
        
        .create-task-btn {
          padding: 10px 20px;
          background-color: #10b981;
          color: white;
          border: none;
          border-radius: 6px;
          cursor: pointer;
          font-weight: 500;
        }
        
        .create-task-btn:hover {
          background-color: #059669;
        }
        
        .task-filters {
          display: flex;
          gap: 10px;
          margin-bottom: 20px;
        }
        
        .filter-btn {
          padding: 8px 16px;
          border: 1px solid #d1d5db;
          background: white;
          border-radius: 6px;
          cursor: pointer;
          font-size: 14px;
        }
        
        .filter-btn.active {
          background-color: #3b82f6;
          color: white;
          border-color: #3b82f6;
        }
        
        .filter-btn:hover:not(.active) {
          background-color: #f9fafb;
        }
        
        .tasks-container {
          display: grid;
          grid-template-columns: repeat(auto-fill, minmax(350px, 1fr));
          gap: 20px;
        }
        
        .task-card {
          background: white;
          border: 1px solid #e5e7eb;
          border-radius: 8px;
          padding: 20px;
          box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
        }
        
        .task-header {
          display: flex;
          justify-content: space-between;
          align-items: flex-start;
          margin-bottom: 10px;
        }
        
        .task-header h3 {
          margin: 0;
          color: #1f2937;
          flex: 1;
        }
        
        .task-badges {
          display: flex;
          gap: 8px;
          flex-shrink: 0;
        }
        
        .priority-badge,
        .status-badge {
          padding: 4px 8px;
          border-radius: 12px;
          color: white;
          font-size: 12px;
          font-weight: 500;
          text-transform: capitalize;
        }
        
        .task-description {
          color: #6b7280;
          margin-bottom: 10px;
          line-height: 1.5;
        }
        
        .task-due-date {
          color: #f97316;
          font-weight: 500;
          margin-bottom: 15px;
        }
        
        .task-actions {
          display: flex;
          gap: 10px;
          margin-bottom: 10px;
        }
        
        .task-actions select,
        .task-actions button {
          padding: 6px 12px;
          border: 1px solid #d1d5db;
          background: white;
          border-radius: 4px;
          cursor: pointer;
          font-size: 14px;
        }
        
        .task-actions select:hover,
        .task-actions button:hover {
          background-color: #f9fafb;
        }
        
        .task-meta {
          border-top: 1px solid #f3f4f6;
          padding-top: 10px;
        }
        
        .task-meta small {
          color: #9ca3af;
        }
        
        .task-list-loading, 
        .task-list-error {
          text-align: center;
          padding: 40px;
        }
        
        .spinner {
          width: 40px;
          height: 40px;
          border: 4px solid #f3f4f6;
          border-top: 4px solid #10b981;
          border-radius: 50%;
          animation: spin 1s linear infinite;
          margin: 0 auto 20px;
        }
        
        @keyframes spin {
          0% { transform: rotate(0deg); }
          100% { transform: rotate(360deg); }
        }
        
        .no-tasks {
          text-align: center;
          padding: 60px 20px;
          color: #6b7280;
        }
      `}</style>
    </div>
  );
};

export default TaskList;