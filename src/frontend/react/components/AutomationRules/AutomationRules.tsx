import React, { useState, useEffect } from 'react';
import { makeApiRequest } from '../../lib/api';
import './AutomationRules.css';

interface AutomationRule {
  id: string;
  name: string;
  description: string;
  trigger: {
    type: string;
    conditions: Array<{
      field: string;
      operator: string;
      value: any;
    }>;
  };
  actions: Array<{
    type: string;
    [key: string]: any;
  }>;
  enabled: boolean;
  executions: number;
  created_at: string;
  updated_at: string;
}

interface RuleFormData {
  name: string;
  description: string;
  triggerType: string;
  conditions: Array<{
    field: string;
    operator: string;
    value: string;
  }>;
  actions: Array<{
    type: string;
    [key: string]: any;
  }>;
}

const AutomationRules: React.FC = () => {
  const [rules, setRules] = useState<AutomationRule[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showCreateForm, setShowCreateForm] = useState(false);
  const [editingRule, setEditingRule] = useState<AutomationRule | null>(null);
  const [formData, setFormData] = useState<RuleFormData>({
    name: '',
    description: '',
    triggerType: 'task_created',
    conditions: [{ field: 'priority', operator: 'equals', value: 'high' }],
    actions: [{ type: 'create_task', title: 'Follow-up Task', priority: 'medium' }]
  });

  useEffect(() => {
    loadRules();
  }, []);

  const loadRules = async () => {
    setLoading(true);
    setError(null);
    
    try {
      const response = await makeApiRequest('/automation/rules', 'GET');
      setRules(response.rules || []);
    } catch (err: any) {
      setError(err.message || 'Failed to load automation rules');
    } finally {
      setLoading(false);
    }
  };

  const createRule = async () => {
    try {
      const ruleData = {
        name: formData.name,
        description: formData.description,
        trigger: {
          type: formData.triggerType,
          conditions: formData.conditions
        },
        actions: formData.actions,
        enabled: true
      };

      await makeApiRequest('/automation/rules', 'POST', ruleData);
      await loadRules();
      resetForm();
      setShowCreateForm(false);
    } catch (err: any) {
      setError(`Failed to create rule: ${err.message}`);
    }
  };

  const toggleRule = async (ruleId: string) => {
    try {
      await makeApiRequest(`/automation/rules/${ruleId}/toggle`, 'PUT');
      await loadRules();
    } catch (err: any) {
      setError(`Failed to toggle rule: ${err.message}`);
    }
  };

  const testRule = async (rule: AutomationRule) => {
    try {
      // Simulate a test event
      const testEvent = {
        type: rule.trigger.type,
        priority: 'high',
        title: 'Test Task',
        workspace_id: 1
      };

      const response = await makeApiRequest('/automation/rules/execute', 'POST', {
        event: testEvent
      });

      alert(`Rule test completed. Executed ${response.executed_rules.length} rules.`);
    } catch (err: any) {
      setError(`Failed to test rule: ${err.message}`);
    }
  };

  const resetForm = () => {
    setFormData({
      name: '',
      description: '',
      triggerType: 'task_created',
      conditions: [{ field: 'priority', operator: 'equals', value: 'high' }],
      actions: [{ type: 'create_task', title: 'Follow-up Task', priority: 'medium' }]
    });
    setEditingRule(null);
  };

  const addCondition = () => {
    setFormData(prev => ({
      ...prev,
      conditions: [...prev.conditions, { field: 'status', operator: 'equals', value: 'pending' }]
    }));
  };

  const removeCondition = (index: number) => {
    setFormData(prev => ({
      ...prev,
      conditions: prev.conditions.filter((_, i) => i !== index)
    }));
  };

  const updateCondition = (index: number, field: keyof typeof formData.conditions[0], value: string) => {
    setFormData(prev => ({
      ...prev,
      conditions: prev.conditions.map((condition, i) => 
        i === index ? { ...condition, [field]: value } : condition
      )
    }));
  };

  const addAction = () => {
    setFormData(prev => ({
      ...prev,
      actions: [...prev.actions, { type: 'send_notification', message: 'Automated notification' }]
    }));
  };

  const removeAction = (index: number) => {
    setFormData(prev => ({
      ...prev,
      actions: prev.actions.filter((_, i) => i !== index)
    }));
  };

  const updateAction = (index: number, field: string, value: any) => {
    setFormData(prev => ({
      ...prev,
      actions: prev.actions.map((action, i) => 
        i === index ? { ...action, [field]: value } : action
      )
    }));
  };

  const triggerTypes = [
    { value: 'task_created', label: 'Task Created' },
    { value: 'task_completed', label: 'Task Completed' },
    { value: 'file_uploaded', label: 'File Uploaded' },
    { value: 'workspace_created', label: 'Workspace Created' }
  ];

  const conditionFields = [
    { value: 'priority', label: 'Priority' },
    { value: 'status', label: 'Status' },
    { value: 'title', label: 'Title' },
    { value: 'workspace_id', label: 'Workspace ID' }
  ];

  const operators = [
    { value: 'equals', label: 'Equals' },
    { value: 'contains', label: 'Contains' },
    { value: 'greater_than', label: 'Greater Than' }
  ];

  const actionTypes = [
    { value: 'create_task', label: 'Create Task' },
    { value: 'move_file', label: 'Move File' },
    { value: 'send_notification', label: 'Send Notification' }
  ];

  if (loading) {
    return (
      <div className="automation-rules loading">
        <div className="loading-spinner"></div>
        <p>Loading automation rules...</p>
      </div>
    );
  }

  return (
    <div className="automation-rules">
      <div className="rules-header">
        <h2>🤖 Automation Rules</h2>
        <button 
          onClick={() => setShowCreateForm(true)}
          className="create-rule-btn"
        >
          ➕ Create Rule
        </button>
      </div>

      {error && (
        <div className="error-message">
          {error}
          <button onClick={() => setError(null)}>✕</button>
        </div>
      )}

      <div className="rules-stats">
        <div className="stat">
          <span className="stat-value">{rules.length}</span>
          <span className="stat-label">Total Rules</span>
        </div>
        <div className="stat">
          <span className="stat-value">{rules.filter(r => r.enabled).length}</span>
          <span className="stat-label">Active Rules</span>
        </div>
        <div className="stat">
          <span className="stat-value">{rules.reduce((sum, r) => sum + r.executions, 0)}</span>
          <span className="stat-label">Total Executions</span>
        </div>
      </div>

      <div className="rules-list">
        {rules.length === 0 ? (
          <div className="no-rules">
            <div className="no-rules-icon">🤖</div>
            <h3>No automation rules yet</h3>
            <p>Create your first rule to automate repetitive tasks</p>
            <button 
              onClick={() => setShowCreateForm(true)}
              className="create-first-rule-btn"
            >
              Create Your First Rule
            </button>
          </div>
        ) : (
          rules.map(rule => (
            <div key={rule.id} className={`rule-card ${rule.enabled ? 'enabled' : 'disabled'}`}>
              <div className="rule-header">
                <div className="rule-info">
                  <h3>{rule.name}</h3>
                  <p>{rule.description}</p>
                </div>
                <div className="rule-controls">
                  <button
                    onClick={() => toggleRule(rule.id)}
                    className={`toggle-btn ${rule.enabled ? 'enabled' : 'disabled'}`}
                  >
                    {rule.enabled ? '🟢' : '🔴'}
                  </button>
                  <button
                    onClick={() => testRule(rule)}
                    className="test-btn"
                  >
                    🧪 Test
                  </button>
                </div>
              </div>
              
              <div className="rule-details">
                <div className="rule-trigger">
                  <h4>🔔 Trigger</h4>
                  <div className="trigger-info">
                    <span className="trigger-type">{rule.trigger.type}</span>
                    {rule.trigger.conditions.map((condition, index) => (
                      <div key={index} className="condition">
                        {condition.field} {condition.operator} {condition.value}
                      </div>
                    ))}
                  </div>
                </div>
                
                <div className="rule-actions">
                  <h4>⚡ Actions</h4>
                  <div className="actions-info">
                    {rule.actions.map((action, index) => (
                      <div key={index} className="action">
                        <span className="action-type">{action.type}</span>
                        {action.title && <span className="action-detail">"{action.title}"</span>}
                        {action.message && <span className="action-detail">"{action.message}"</span>}
                      </div>
                    ))}
                  </div>
                </div>
              </div>
              
              <div className="rule-stats">
                <span>Executions: {rule.executions}</span>
                <span>Created: {new Date(rule.created_at).toLocaleDateString()}</span>
              </div>
            </div>
          ))
        )}
      </div>

      {showCreateForm && (
        <div className="rule-form-overlay">
          <div className="rule-form">
            <div className="form-header">
              <h3>Create Automation Rule</h3>
              <button onClick={() => { setShowCreateForm(false); resetForm(); }}>✕</button>
            </div>
            
            <div className="form-content">
              <div className="form-section">
                <h4>Basic Information</h4>
                <div className="form-group">
                  <label>Rule Name</label>
                  <input
                    type="text"
                    value={formData.name}
                    onChange={(e) => setFormData(prev => ({ ...prev, name: e.target.value }))}
                    placeholder="Enter rule name"
                  />
                </div>
                <div className="form-group">
                  <label>Description</label>
                  <textarea
                    value={formData.description}
                    onChange={(e) => setFormData(prev => ({ ...prev, description: e.target.value }))}
                    placeholder="Describe what this rule does"
                  />
                </div>
              </div>

              <div className="form-section">
                <h4>🔔 Trigger</h4>
                <div className="form-group">
                  <label>When this happens:</label>
                  <select
                    value={formData.triggerType}
                    onChange={(e) => setFormData(prev => ({ ...prev, triggerType: e.target.value }))}
                  >
                    {triggerTypes.map(type => (
                      <option key={type.value} value={type.value}>{type.label}</option>
                    ))}
                  </select>
                </div>
                
                <div className="conditions-section">
                  <div className="section-header">
                    <label>Conditions</label>
                    <button type="button" onClick={addCondition} className="add-btn">+ Add Condition</button>
                  </div>
                  {formData.conditions.map((condition, index) => (
                    <div key={index} className="condition-row">
                      <select
                        value={condition.field}
                        onChange={(e) => updateCondition(index, 'field', e.target.value)}
                      >
                        {conditionFields.map(field => (
                          <option key={field.value} value={field.value}>{field.label}</option>
                        ))}
                      </select>
                      <select
                        value={condition.operator}
                        onChange={(e) => updateCondition(index, 'operator', e.target.value)}
                      >
                        {operators.map(op => (
                          <option key={op.value} value={op.value}>{op.label}</option>
                        ))}
                      </select>
                      <input
                        type="text"
                        value={condition.value}
                        onChange={(e) => updateCondition(index, 'value', e.target.value)}
                        placeholder="Value"
                      />
                      <button 
                        type="button" 
                        onClick={() => removeCondition(index)}
                        className="remove-btn"
                      >
                        ✕
                      </button>
                    </div>
                  ))}
                </div>
              </div>

              <div className="form-section">
                <h4>⚡ Actions</h4>
                <div className="actions-section">
                  <div className="section-header">
                    <label>Do these actions:</label>
                    <button type="button" onClick={addAction} className="add-btn">+ Add Action</button>
                  </div>
                  {formData.actions.map((action, index) => (
                    <div key={index} className="action-row">
                      <select
                        value={action.type}
                        onChange={(e) => updateAction(index, 'type', e.target.value)}
                      >
                        {actionTypes.map(type => (
                          <option key={type.value} value={type.value}>{type.label}</option>
                        ))}
                      </select>
                      
                      {action.type === 'create_task' && (
                        <>
                          <input
                            type="text"
                            value={action.title || ''}
                            onChange={(e) => updateAction(index, 'title', e.target.value)}
                            placeholder="Task title"
                          />
                          <select
                            value={action.priority || 'medium'}
                            onChange={(e) => updateAction(index, 'priority', e.target.value)}
                          >
                            <option value="low">Low Priority</option>
                            <option value="medium">Medium Priority</option>
                            <option value="high">High Priority</option>
                          </select>
                        </>
                      )}
                      
                      {action.type === 'send_notification' && (
                        <input
                          type="text"
                          value={action.message || ''}
                          onChange={(e) => updateAction(index, 'message', e.target.value)}
                          placeholder="Notification message"
                        />
                      )}
                      
                      {action.type === 'move_file' && (
                        <input
                          type="text"
                          value={action.target_folder || ''}
                          onChange={(e) => updateAction(index, 'target_folder', e.target.value)}
                          placeholder="Target folder"
                        />
                      )}
                      
                      <button 
                        type="button" 
                        onClick={() => removeAction(index)}
                        className="remove-btn"
                      >
                        ✕
                      </button>
                    </div>
                  ))}
                </div>
              </div>
            </div>
            
            <div className="form-actions">
              <button onClick={() => { setShowCreateForm(false); resetForm(); }} className="cancel-btn">
                Cancel
              </button>
              <button onClick={createRule} className="create-btn">
                Create Rule
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default AutomationRules;