import { api } from './api';
import type { 
  AgentCard, 
  A2AAgent, 
  AnubisWorkflow, 
  AgentTask, 
  AgentMessage, 
  AgentSystem 
} from '../types/agents';

class AgentApiClient {
  private baseUrl = 'http://localhost:8000/api';

  // A2A Protocol Integration
  async discoverA2AAgents(): Promise<A2AAgent[]> {
    try {
      const response = await api.get('/agents/a2a/discover');
      return response.data;
    } catch (error) {
      console.error('Failed to discover A2A agents:', error);
      return [];
    }
  }

  async connectA2AAgent(agentCard: Partial<A2AAgent>): Promise<A2AAgent> {
    const response = await api.post('/agents/a2a/connect', agentCard);
    return response.data;
  }

  async sendA2AMessage(agentId: string, message: string): Promise<AgentMessage> {
    const response = await api.post(`/agents/a2a/${agentId}/message`, { message });
    return response.data;
  }

  // Anubis Workflow Management
  async initializeAnubisWorkflow(projectName: string): Promise<AnubisWorkflow> {
    const response = await api.post('/agents/anubis/init', { projectName });
    return response.data;
  }

  async getWorkflowGuidance(executionId: string, roleId: string): Promise<any> {
    const response = await api.get(`/agents/anubis/workflows/${executionId}/guidance/${roleId}`);
    return response.data;
  }

  async reportStepCompletion(executionId: string, result: any): Promise<void> {
    await api.post(`/agents/anubis/workflows/${executionId}/complete`, result);
  }

  async generateWorkflowReport(executionId: string): Promise<string> {
    const response = await api.get(`/agents/anubis/workflows/${executionId}/report`);
    return response.data.html;
  }

  // Serena Code Analysis Integration
  async activateSerenaProject(projectPath: string): Promise<void> {
    await api.post('/agents/serena/activate', { projectPath });
  }

  async searchCode(query: string, language?: string): Promise<any[]> {
    const response = await api.post('/agents/serena/search', { query, language });
    return response.data;
  }

  async analyzeCodeSymbol(filePath: string, symbol: string): Promise<any> {
    const response = await api.post('/agents/serena/analyze', { filePath, symbol });
    return response.data;
  }

  async refactorCode(filePath: string, changes: any): Promise<void> {
    await api.post('/agents/serena/refactor', { filePath, changes });
  }

  // Unified Agent Management
  async getAllAgents(): Promise<AgentCard[]> {
    const response = await api.get('/agents');
    return response.data;
  }

  async getAgentStatus(agentId: string): Promise<AgentCard> {
    const response = await api.get(`/agents/${agentId}/status`);
    return response.data;
  }

  async createTask(task: Omit<AgentTask, 'id' | 'createdAt' | 'updatedAt'>): Promise<AgentTask> {
    const response = await api.post('/agents/tasks', task);
    return response.data;
  }

  async getTasks(): Promise<AgentTask[]> {
    const response = await api.get('/agents/tasks');
    return response.data;
  }

  async updateTaskStatus(taskId: string, status: AgentTask['status']): Promise<AgentTask> {
    const response = await api.patch(`/agents/tasks/${taskId}`, { status });
    return response.data;
  }

  async getAgentMessages(agentId?: string): Promise<AgentMessage[]> {
    const url = agentId ? `/agents/messages?agentId=${agentId}` : '/agents/messages';
    const response = await api.get(url);
    return response.data;
  }

  async getSystemStatus(): Promise<AgentSystem> {
    const response = await api.get('/agents/system');
    return response.data;
  }

  // Agent Communication Hub
  async broadcastMessage(message: string, targetAgents?: string[]): Promise<void> {
    await api.post('/agents/broadcast', { message, targetAgents });
  }

  async delegateTask(taskId: string, targetAgent: string): Promise<void> {
    await api.post(`/agents/tasks/${taskId}/delegate`, { targetAgent });
  }

  // Advanced Workflow Orchestration
  async createCollaborativeWorkflow(
    name: string, 
    participants: string[], 
    objective: string
  ): Promise<AnubisWorkflow> {
    const response = await api.post('/agents/workflows/collaborative', {
      name,
      participants,
      objective
    });
    return response.data;
  }

  async getWorkflowRecommendations(context: any): Promise<any[]> {
    const response = await api.post('/agents/workflows/recommendations', context);
    return response.data;
  }
}

export const agentApi = new AgentApiClient(); 