import { APIRequestContext } from '@playwright/test';

export class WorkspaceAPIClient {
  constructor(private request: APIRequestContext) {}

  async getWorkspaces() {
    const response = await this.request.get('/api/workspaces/');
    return response.json();
  }

  async getWorkspace(id: number) {
    const response = await this.request.get(`/api/workspaces/${id}`);
    return response.json();
  }

  async createWorkspace(data: any) {
    const response = await this.request.post('/api/workspaces/', {
      data
    });
    return response.json();
  }

  async updateWorkspace(id: number, data: any) {
    const response = await this.request.put(`/api/workspaces/${id}`, {
      data
    });
    return response.json();
  }

  async deleteWorkspace(id: number) {
    const response = await this.request.delete(`/api/workspaces/${id}`);
    return response.json();
  }

  async switchWorkspace(id: number) {
    const response = await this.request.post(`/api/workspaces/${id}/switch`);
    return response.json();
  }

  async updateWorkspaceState(id: number, state: any) {
    const response = await this.request.put(`/api/workspaces/${id}/state`, {
      data: { state }
    });
    return response.json();
  }

  async getWorkspaceState(id: number) {
    const response = await this.request.get(`/api/workspaces/${id}/state`);
    return response.json();
  }

  async getTemplates() {
    const response = await this.request.get('/api/workspaces/templates');
    return response.json();
  }

  async getThemes() {
    const response = await this.request.get('/api/workspaces/themes');
    return response.json();
  }

  async createFromTemplate(templateName: string, workspaceName: string, userId?: number) {
    const response = await this.request.post('/api/workspaces/create-from-template', {
      data: {
        template_name: templateName,
        workspace_name: workspaceName,
        user_id: userId
      }
    });
    return response.json();
  }

  async assignContent(workspaceId: number, content: any) {
    const response = await this.request.post(`/api/workspaces/${workspaceId}/assign-content`, {
      data: content
    });
    return response.json();
  }

  async getAnalytics(workspaceId: number) {
    const response = await this.request.get(`/api/workspaces/${workspaceId}/analytics`);
    return response.json();
  }

  async updateAmbientSound(workspaceId: number, sound: string) {
    const response = await this.request.post(`/api/workspaces/${workspaceId}/ambient-sound`, {
      data: { ambient_sound: sound }
    });
    return response.json();
  }
}