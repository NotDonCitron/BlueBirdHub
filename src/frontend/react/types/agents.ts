// Agent System Types for BlueBirdHub
export interface AgentCard {
  id: string;
  name: string;
  description: string;
  capabilities: string[];
  status: 'active' | 'inactive' | 'error';
  endpoint?: string;
  version: string;
}

export interface A2AAgent extends AgentCard {
  type: 'a2a';
  protocol: 'json-rpc-2.0';
  transport: 'http' | 'https';
  authentication?: {
    type: 'bearer' | 'api-key';
    required: boolean;
  };
}

export interface AnubisWorkflow {
  id: string;
  name: string;
  currentRole: 'boomerang' | 'researcher' | 'architect' | 'senior-developer' | 'code-review';
  completedSteps: string[];
  context: {
    decisions: string[];
    rationale: string;
    nextSteps: string[];
  };
  status: 'active' | 'paused' | 'completed' | 'error';
  createdAt: string;
  updatedAt: string;
}

export interface SerenaCapability {
  language: string;
  features: string[];
  lspSupport: boolean;
  semanticAnalysis: boolean;
}

export interface AgentTask {
  id: string;
  title: string;
  description: string;
  assignedAgent: string;
  status: 'pending' | 'in-progress' | 'completed' | 'failed';
  priority: 'low' | 'medium' | 'high' | 'critical';
  workflow?: AnubisWorkflow;
  createdAt: string;
  updatedAt: string;
  result?: any;
}

export interface AgentMessage {
  id: string;
  agentId: string;
  content: string;
  type: 'text' | 'code' | 'file' | 'report';
  timestamp: string;
  metadata?: Record<string, any>;
}

export interface AgentSystem {
  agents: AgentCard[];
  activeWorkflows: AnubisWorkflow[];
  tasks: AgentTask[];
  messages: AgentMessage[];
  status: 'initializing' | 'ready' | 'error';
} 