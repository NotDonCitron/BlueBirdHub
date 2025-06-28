import type {
  ApiResponse,
  LoginRequest,
  LoginResponse,
  User,
  Task,
  CreateTaskRequest,
  UpdateTaskRequest,
  CreateSubtaskRequest,
  UpdateSubtaskRequest,
  Workspace,
  CreateWorkspaceRequest,
  UpdateWorkspaceRequest,
  TaskProgress,
  HealthResponse,
  ApiError
} from '@types/api';

class ApiClient {
  private baseUrl: string;
  private token: string | null = null;

  constructor(baseUrl: string = 'http://localhost:8000') {
    this.baseUrl = baseUrl;
    this.token = localStorage.getItem('auth_token');
  }

  async request<T>(
    endpoint: string,
    options: RequestInit = {}
  ): Promise<T> {
    const url = `${this.baseUrl}${endpoint}`;
    
    const headers: Record<string, string> = {
      'Content-Type': 'application/json',
      ...((options.headers as Record<string, string>) || {})
    };

    if (this.token) {
      headers.Authorization = `Bearer ${this.token}`;
    }

    const config: RequestInit = {
      ...options,
      headers
    };

    console.log(`🌐 API Request: ${options.method || 'GET'} ${endpoint}`, {
      body: options.body,
      headers
    });

    try {
      const response = await fetch(url, config);
      
      let data: any;
      const contentType = response.headers.get('content-type');
      
      if (contentType && contentType.includes('application/json')) {
        data = await response.json();
      } else {
        const text = await response.text();
        throw new Error(`Invalid JSON response: ${text.substring(0, 100)}...`);
      }

      console.log(`📡 API Response: ${endpoint}`, {
        status: response.status,
        data
      });

      if (!response.ok) {
        const error: ApiError = {
          error: data.error || `HTTP ${response.status}: ${response.statusText}`,
          details: data.details,
          status: response.status
        };
        throw error;
      }

      return data;
    } catch (error) {
      console.error(`❌ API Error: ${endpoint}`, error);
      
      if (error instanceof TypeError && error.message.includes('fetch')) {
        throw new Error('Network error: Unable to connect to server. Please check if the backend is running.');
      }
      
      throw error;
    }
  }

  // Authentication
  async login(credentials: LoginRequest): Promise<LoginResponse> {
    const response = await this.request<LoginResponse>('/auth/login-json', {
      method: 'POST',
      body: JSON.stringify(credentials)
    });

    if (response.access_token) {
      this.token = response.access_token;
      localStorage.setItem('auth_token', response.access_token);
    }

    return response;
  }

  async logout(): Promise<void> {
    try {
      await this.request('/auth/logout', { method: 'POST' });
    } finally {
      this.token = null;
      localStorage.removeItem('auth_token');
    }
  }

  async getCurrentUser(): Promise<User> {
    return this.request<User>('/auth/me');
  }

  // Health Check
  async healthCheck(): Promise<HealthResponse> {
    return this.request<HealthResponse>('/health');
  }

  // Tasks
  async getTasks(): Promise<{ tasks: Task[] }> {
    return this.request<{ tasks: Task[] }>('/tasks/taskmaster/all');
  }

  async getTask(taskId: string): Promise<Task> {
    return this.request<Task>(`/tasks/taskmaster/${taskId}`);
  }

  async createTask(task: CreateTaskRequest): Promise<Task> {
    return this.request<Task>('/tasks/taskmaster/add', {
      method: 'POST',
      body: JSON.stringify(task)
    });
  }

  async updateTask(taskId: string, updates: UpdateTaskRequest): Promise<Task> {
    return this.request<Task>(`/api/tasks/taskmaster/${taskId}`, {
      method: 'PUT',
      body: JSON.stringify(updates)
    });
  }

  async deleteTask(taskId: string): Promise<void> {
    await this.request(`/tasks/taskmaster/${taskId}`, {
      method: 'DELETE'
    });
  }

  async getTaskProgress(): Promise<TaskProgress> {
    return this.request<TaskProgress>('/tasks/taskmaster/progress');
  }

  async getNextTask(): Promise<{ task: Task | null }> {
    return this.request<{ task: Task | null }>('/tasks/taskmaster/next');
  }

  // Subtasks
  async createSubtask(parentTaskId: string, subtask: CreateSubtaskRequest): Promise<Task> {
    return this.request<Task>(`/tasks/${parentTaskId}/subtasks`, {
      method: 'POST',
      body: JSON.stringify(subtask)
    });
  }

  async updateSubtask(subtaskId: string, updates: UpdateSubtaskRequest): Promise<Task> {
    return this.request<Task>(`/api/subtasks/${subtaskId}`, {
      method: 'PUT',
      body: JSON.stringify(updates)
    });
  }

  // Workspaces
  async getWorkspaces(): Promise<Workspace[]> {
    return this.request<Workspace[]>('/workspaces');
  }

  async getWorkspace(workspaceId: number): Promise<Workspace> {
    return this.request<Workspace>(`/workspaces/${workspaceId}`);
  }

  async createWorkspace(workspace: CreateWorkspaceRequest): Promise<Workspace> {
    return this.request<Workspace>('/workspaces', {
      method: 'POST',
      body: JSON.stringify(workspace)
    });
  }

  async updateWorkspace(workspaceId: number, updates: UpdateWorkspaceRequest): Promise<Workspace> {
    return this.request<Workspace>(`/api/workspaces/${workspaceId}`, {
      method: 'PUT',
      body: JSON.stringify(updates)
    });
  }

  async deleteWorkspace(workspaceId: number): Promise<void> {
    await this.request(`/workspaces/${workspaceId}`, {
      method: 'DELETE'
    });
  }

  // Utility methods
  setToken(token: string): void {
    this.token = token;
    localStorage.setItem('auth_token', token);
  }

  clearToken(): void {
    this.token = null;
    localStorage.removeItem('auth_token');
  }

  isAuthenticated(): boolean {
    return !!this.token;
  }
}

// Create singleton instance
export const apiClient = new ApiClient();

// Export as 'api' for backward compatibility
export const api = apiClient;

// Export class for testing
export { ApiClient }; 