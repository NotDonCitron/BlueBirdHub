// API Response Types
export interface ApiResponse<T = any> {
  success: boolean;
  data?: T;
  error?: string;
  message?: string;
}

// Authentication Types
export interface LoginRequest {
  username: string;
  password: string;
}

export interface LoginResponse {
  success: boolean;
  token: string;
  message: string;
  user: User;
}

export interface User {
  id: string;
  username: string;
  last_login: string;
  created_at?: string;
}

// Task Types
export interface Task {
  id: string;
  title: string;
  description?: string;
  status: TaskStatus;
  priority: TaskPriority;
  dependencies?: string[];
  subtasks?: Task[];
  parent_task_id?: string;
  workspace_id?: number;
  due_date?: string;
  tags?: string[];
  attachments?: string[];
  created_at: string;
  details?: string;
  testStrategy?: string;
  related_files?: string[];
}

export type TaskStatus = 'pending' | 'in-progress' | 'done' | 'blocked' | 'completed';
export type TaskPriority = 'low' | 'medium' | 'high';

export interface CreateTaskRequest {
  title: string;
  description?: string;
  priority?: TaskPriority;
  dependencies?: string[];
  workspace_id?: number;
  parent_task_id?: string;
}

export interface UpdateTaskRequest {
  title?: string;
  description?: string;
  status?: TaskStatus;
  priority?: TaskPriority;
  dependencies?: string[];
}

// Subtask Types
export interface CreateSubtaskRequest {
  title: string;
  description?: string;
  priority?: TaskPriority;
}

export interface UpdateSubtaskRequest {
  title?: string;
  description?: string;
  status?: TaskStatus;
  priority?: TaskPriority;
}

// Workspace Types
export interface Workspace {
  id: number;
  name: string;
  color: string;
  description?: string;
  theme?: string;
  icon?: string;
  task_count?: number;
  created_at: string;
}

export interface CreateWorkspaceRequest {
  name: string;
  description?: string;
  color?: string;
  theme?: string;
  icon?: string;
}

export interface UpdateWorkspaceRequest {
  name?: string;
  description?: string;
  color?: string;
  theme?: string;
  icon?: string;
}

// Progress Types
export interface TaskProgress {
  total_tasks: number;
  completed_tasks: number;
  pending_tasks: number;
  in_progress_tasks: number;
  completion_percentage: number;
}

// File Types
export interface FileMetadata {
  id: string;
  filename: string;
  size: number;
  size_formatted: string;
  mime_type: string;
  upload_date: string;
  task_id?: string;
  workspace_id?: number;
}

// Error Types
export interface ApiError {
  error: string;
  details?: string;
  status?: number;
}

// Search Types
export interface SearchResult {
  type: 'task' | 'workspace';
  id: string;
  title: string;
  description?: string;
  color?: string;
  status?: string;
  priority?: string;
}

// Health Check Types
export interface HealthResponse {
  status: string;
  message: string;
  backend: string;
  version?: string;
} 