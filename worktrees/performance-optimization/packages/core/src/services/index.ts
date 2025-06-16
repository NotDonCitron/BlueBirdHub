// Business logic services
export interface TaskService {
  getTasks(): Promise<any[]>;
  createTask(task: any): Promise<any>;
  updateTask(id: string, task: any): Promise<any>;
  deleteTask(id: string): Promise<void>;
}

export interface FileService {
  getFiles(): Promise<any[]>;
  uploadFile(file: File): Promise<any>;
  deleteFile(id: string): Promise<void>;
}

export interface WorkspaceService {
  getWorkspaces(): Promise<any[]>;
  createWorkspace(workspace: any): Promise<any>;
  updateWorkspace(id: string, workspace: any): Promise<any>;
  deleteWorkspace(id: string): Promise<void>;
}

// Export service implementations
export { defaultApiClient as apiClient } from '../api';