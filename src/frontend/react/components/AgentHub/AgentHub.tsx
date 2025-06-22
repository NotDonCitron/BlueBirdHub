import React, { useState, useEffect } from 'react';
import { agentApi } from '../../lib/agentApi';
import type { AgentCard, AgentTask, AgentSystem, AnubisWorkflow } from '../../types/agents';

interface AgentHubProps {
  className?: string;
}

export const AgentHub: React.FC<AgentHubProps> = ({ className = '' }) => {
  const [agentSystem, setAgentSystem] = useState<AgentSystem>({
    agents: [],
    activeWorkflows: [],
    tasks: [],
    messages: [],
    status: 'initializing'
  });
  const [activeTab, setActiveTab] = useState<'agents' | 'workflows' | 'tasks' | 'messages'>('agents');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    loadAgentSystem();
  }, []);

  const loadAgentSystem = async () => {
    try {
      setLoading(true);
      const systemStatus = await agentApi.getSystemStatus();
      setAgentSystem(systemStatus);
      setError(null);
    } catch (err) {
      setError('Failed to load agent system');
      console.error('Agent system error:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleCreateTask = async () => {
    const title = prompt('Task Title:');
    const description = prompt('Task Description:');
    const assignedAgent = prompt('Assign to Agent ID:');
    
    if (title && description && assignedAgent) {
      try {
        const newTask = await agentApi.createTask({
          title,
          description,
          assignedAgent,
          status: 'pending',
          priority: 'medium'
        });
        
        setAgentSystem(prev => ({
          ...prev,
          tasks: [...prev.tasks, newTask]
        }));
      } catch (err) {
        setError('Failed to create task');
      }
    }
  };

  const handleInitializeWorkflow = async () => {
    const projectName = prompt('Project Name:');
    if (projectName) {
      try {
        const workflow = await agentApi.initializeAnubisWorkflow(projectName);
        setAgentSystem(prev => ({
          ...prev,
          activeWorkflows: [...prev.activeWorkflows, workflow]
        }));
      } catch (err) {
        setError('Failed to initialize workflow');
      }
    }
  };

  const renderAgents = () => (
    <div className="space-y-4">
      <div className="flex justify-between items-center">
        <h3 className="text-lg font-semibold text-gray-900">AI Agents</h3>
        <button
          onClick={loadAgentSystem}
          className="px-3 py-1 bg-blue-500 text-white rounded hover:bg-blue-600 transition-colors"
        >
          Refresh
        </button>
      </div>
      
      {agentSystem.agents.length === 0 ? (
        <div className="text-center py-8 text-gray-500">
          <div className="text-4xl mb-4">🤖</div>
          <p>No agents discovered yet</p>
          <button
            onClick={() => agentApi.discoverA2AAgents()}
            className="mt-4 px-4 py-2 bg-green-500 text-white rounded hover:bg-green-600 transition-colors"
          >
            Discover A2A Agents
          </button>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {agentSystem.agents.map((agent) => (
            <AgentCard key={agent.id} agent={agent} />
          ))}
        </div>
      )}
    </div>
  );

  const renderWorkflows = () => (
    <div className="space-y-4">
      <div className="flex justify-between items-center">
        <h3 className="text-lg font-semibold text-gray-900">Active Workflows</h3>
        <button
          onClick={handleInitializeWorkflow}
          className="px-3 py-1 bg-purple-500 text-white rounded hover:bg-purple-600 transition-colors"
        >
          New Workflow
        </button>
      </div>
      
      {agentSystem.activeWorkflows.length === 0 ? (
        <div className="text-center py-8 text-gray-500">
          <div className="text-4xl mb-4">⚡</div>
          <p>No active workflows</p>
        </div>
      ) : (
        <div className="space-y-4">
          {agentSystem.activeWorkflows.map((workflow) => (
            <WorkflowCard key={workflow.id} workflow={workflow} />
          ))}
        </div>
      )}
    </div>
  );

  const renderTasks = () => (
    <div className="space-y-4">
      <div className="flex justify-between items-center">
        <h3 className="text-lg font-semibold text-gray-900">Agent Tasks</h3>
        <button
          onClick={handleCreateTask}
          className="px-3 py-1 bg-orange-500 text-white rounded hover:bg-orange-600 transition-colors"
        >
          Create Task
        </button>
      </div>
      
      {agentSystem.tasks.length === 0 ? (
        <div className="text-center py-8 text-gray-500">
          <div className="text-4xl mb-4">📋</div>
          <p>No tasks assigned</p>
        </div>
      ) : (
        <div className="space-y-4">
          {agentSystem.tasks.map((task) => (
            <TaskCard key={task.id} task={task} />
          ))}
        </div>
      )}
    </div>
  );

  const renderMessages = () => (
    <div className="space-y-4">
      <h3 className="text-lg font-semibold text-gray-900">Agent Communications</h3>
      
      {agentSystem.messages.length === 0 ? (
        <div className="text-center py-8 text-gray-500">
          <div className="text-4xl mb-4">💬</div>
          <p>No agent messages</p>
        </div>
      ) : (
        <div className="space-y-3 max-h-96 overflow-y-auto">
          {agentSystem.messages.map((message) => (
            <div key={message.id} className="p-3 bg-gray-50 rounded-lg">
              <div className="flex justify-between text-sm text-gray-600 mb-1">
                <span>Agent: {message.agentId}</span>
                <span>{new Date(message.timestamp).toLocaleTimeString()}</span>
              </div>
              <p className="text-gray-900">{message.content}</p>
            </div>
          ))}
        </div>
      )}
    </div>
  );

  if (loading) {
    return (
      <div className={`flex items-center justify-center h-64 ${className}`}>
        <div className="text-center">
          <div className="animate-spin text-4xl mb-4">🤖</div>
          <p className="text-gray-600">Initializing Agent System...</p>
        </div>
      </div>
    );
  }

  return (
    <div className={`bg-white rounded-lg shadow-lg p-6 ${className}`}>
      <div className="flex items-center justify-between mb-6">
        <h2 className="text-2xl font-bold text-gray-900 flex items-center">
          <span className="mr-3">🧠</span>
          AI Agent Hub
        </h2>
        <div className={`px-3 py-1 rounded-full text-sm font-medium ${
          agentSystem.status === 'ready' ? 'bg-green-100 text-green-800' :
          agentSystem.status === 'error' ? 'bg-red-100 text-red-800' :
          'bg-yellow-100 text-yellow-800'
        }`}>
          {agentSystem.status}
        </div>
      </div>

      {error && (
        <div className="mb-4 p-3 bg-red-100 border border-red-400 text-red-700 rounded">
          {error}
        </div>
      )}

      {/* Tab Navigation */}
      <div className="flex space-x-1 mb-6 bg-gray-100 p-1 rounded-lg">
        {[
          { id: 'agents', label: 'Agents', icon: '🤖' },
          { id: 'workflows', label: 'Workflows', icon: '⚡' },
          { id: 'tasks', label: 'Tasks', icon: '📋' },
          { id: 'messages', label: 'Messages', icon: '💬' }
        ].map((tab) => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id as any)}
            className={`flex-1 py-2 px-4 rounded-md text-sm font-medium transition-colors ${
              activeTab === tab.id
                ? 'bg-white text-blue-600 shadow-sm'
                : 'text-gray-600 hover:text-gray-900'
            }`}
          >
            <span className="mr-2">{tab.icon}</span>
            {tab.label}
          </button>
        ))}
      </div>

      {/* Tab Content */}
      <div className="min-h-64">
        {activeTab === 'agents' && renderAgents()}
        {activeTab === 'workflows' && renderWorkflows()}
        {activeTab === 'tasks' && renderTasks()}
        {activeTab === 'messages' && renderMessages()}
      </div>
    </div>
  );
};

// Supporting Components
const AgentCard: React.FC<{ agent: AgentCard }> = ({ agent }) => (
  <div className="p-4 border border-gray-200 rounded-lg hover:shadow-md transition-shadow">
    <div className="flex justify-between items-start mb-2">
      <h4 className="font-semibold text-gray-900">{agent.name}</h4>
      <div className={`w-3 h-3 rounded-full ${
        agent.status === 'active' ? 'bg-green-500' :
        agent.status === 'error' ? 'bg-red-500' : 'bg-gray-400'
      }`} />
    </div>
    <p className="text-sm text-gray-600 mb-3">{agent.description}</p>
    <div className="flex flex-wrap gap-1">
      {agent.capabilities.slice(0, 3).map((capability, index) => (
        <span key={index} className="px-2 py-1 bg-blue-100 text-blue-700 text-xs rounded">
          {capability}
        </span>
      ))}
      {agent.capabilities.length > 3 && (
        <span className="px-2 py-1 bg-gray-100 text-gray-600 text-xs rounded">
          +{agent.capabilities.length - 3} more
        </span>
      )}
    </div>
  </div>
);

const WorkflowCard: React.FC<{ workflow: AnubisWorkflow }> = ({ workflow }) => (
  <div className="p-4 border border-gray-200 rounded-lg">
    <div className="flex justify-between items-start mb-2">
      <h4 className="font-semibold text-gray-900">{workflow.name}</h4>
      <span className={`px-2 py-1 rounded text-xs font-medium ${
        workflow.status === 'active' ? 'bg-green-100 text-green-800' :
        workflow.status === 'completed' ? 'bg-blue-100 text-blue-800' :
        workflow.status === 'error' ? 'bg-red-100 text-red-800' :
        'bg-yellow-100 text-yellow-800'
      }`}>
        {workflow.status}
      </span>
    </div>
    <div className="text-sm text-gray-600 mb-2">
      Current Role: <span className="font-medium">{workflow.currentRole}</span>
    </div>
    <div className="text-sm text-gray-600">
      Progress: {workflow.completedSteps.length} steps completed
    </div>
  </div>
);

const TaskCard: React.FC<{ task: AgentTask }> = ({ task }) => (
  <div className="p-4 border border-gray-200 rounded-lg">
    <div className="flex justify-between items-start mb-2">
      <h4 className="font-semibold text-gray-900">{task.title}</h4>
      <div className="flex items-center space-x-2">
        <span className={`px-2 py-1 rounded text-xs font-medium ${
          task.priority === 'critical' ? 'bg-red-100 text-red-800' :
          task.priority === 'high' ? 'bg-orange-100 text-orange-800' :
          task.priority === 'medium' ? 'bg-yellow-100 text-yellow-800' :
          'bg-gray-100 text-gray-800'
        }`}>
          {task.priority}
        </span>
        <span className={`px-2 py-1 rounded text-xs font-medium ${
          task.status === 'completed' ? 'bg-green-100 text-green-800' :
          task.status === 'in-progress' ? 'bg-blue-100 text-blue-800' :
          task.status === 'failed' ? 'bg-red-100 text-red-800' :
          'bg-gray-100 text-gray-800'
        }`}>
          {task.status}
        </span>
      </div>
    </div>
    <p className="text-sm text-gray-600 mb-2">{task.description}</p>
    <div className="text-xs text-gray-500">
      Assigned to: {task.assignedAgent}
    </div>
  </div>
); 