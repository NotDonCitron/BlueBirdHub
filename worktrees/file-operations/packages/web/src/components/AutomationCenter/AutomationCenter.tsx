import React, { useState, useEffect } from 'react';
import { useApi } from '../../contexts/ApiContext';
import './AutomationCenter.css';

interface AutomationRule {
  id: string;
  name: string;
  description: string;
  conditions: {
    file_extension?: string | string[];
    filename_contains?: string[];
    content_keywords?: string[];
    file_size_mb?: { min?: number; max?: number };
  };
  actions: {
    move_to_workspace?: number;
    move_to_folder?: string;
    add_tags?: string[];
    priority?: string;
    compress?: boolean;
    notify?: boolean;
  };
  enabled: boolean;
  created_at: string;
  last_triggered?: string;
  trigger_count: number;
}

interface ScheduledTask {
  id: string;
  name: string;
  description: string;
  schedule: {
    type: 'daily' | 'weekly' | 'monthly';
    time: string;
    timezone: string;
    day?: string;
    day_of_month?: number;
  };
  actions: string[];
  enabled: boolean;
  last_run?: string;
  next_run: string;
  run_count: number;
  status: string;
}

interface AutomationDashboard {
  statistics: {
    rules: {
      total: number;
      enabled: number;
      total_triggers: number;
    };
    scheduled_tasks: {
      total: number;
      enabled: number;
      total_runs: number;
    };
  };
  most_active_rules: AutomationRule[];
  upcoming_tasks: ScheduledTask[];
  recent_activity: Array<{
    timestamp: string;
    type: string;
    message: string;
  }>;
}

const AutomationCenter: React.FC = () => {
  const { makeApiRequest } = useApi();
  const [activeTab, setActiveTab] = useState<'dashboard' | 'rules' | 'schedules'>('dashboard');
  const [automationRules, setAutomationRules] = useState<AutomationRule[]>([]);
  const [scheduledTasks, setScheduledTasks] = useState<ScheduledTask[]>([]);
  const [dashboard, setDashboard] = useState<AutomationDashboard | null>(null);
  const [loading, setLoading] = useState(false);
  const [showCreateRuleModal, setShowCreateRuleModal] = useState(false);
  const [showCreateScheduleModal, setShowCreateScheduleModal] = useState(false);
  const [editingRule, setEditingRule] = useState<AutomationRule | null>(null);
  const [editingSchedule, setEditingSchedule] = useState<ScheduledTask | null>(null);

  // Form state for new rule
  const [newRule, setNewRule] = useState({
    name: '',
    description: '',
    conditions: {
      file_extension: '',
      filename_contains: [] as string[],
      file_size_mb: { min: 0, max: 0 }
    },
    actions: {
      move_to_workspace: 0,
      move_to_folder: '',
      add_tags: [] as string[]
    },
    enabled: true
  });

  // Form state for new schedule
  const [newSchedule, setNewSchedule] = useState({
    name: '',
    description: '',
    schedule: {
      type: 'daily' as const,
      time: '09:00',
      timezone: 'Europe/Berlin'
    },
    actions: [] as string[],
    enabled: true
  });

  useEffect(() => {
    loadAutomationData();
  }, []);

  const loadAutomationData = async () => {
    setLoading(true);
    try {
      await Promise.all([
        loadDashboard(),
        loadAutomationRules(),
        loadScheduledTasks()
      ]);
    } catch (error) {
      console.error('Failed to load automation data:', error);
    } finally {
      setLoading(false);
    }
  };

  const loadDashboard = async () => {
    try {
      const response = await makeApiRequest('/automation/dashboard');
      if (response.success) {
        setDashboard(response);
      }
    } catch (error) {
      console.error('Failed to load dashboard:', error);
    }
  };

  const loadAutomationRules = async () => {
    try {
      const response = await makeApiRequest('/automation/rules');
      if (response.success) {
        setAutomationRules(response.rules);
      }
    } catch (error) {
      console.error('Failed to load automation rules:', error);
    }
  };

  const loadScheduledTasks = async () => {
    try {
      const response = await makeApiRequest('/automation/scheduled-tasks');
      if (response.success) {
        setScheduledTasks(response.tasks);
      }
    } catch (error) {
      console.error('Failed to load scheduled tasks:', error);
    }
  };

  const createRule = async () => {
    try {
      const response = await makeApiRequest('/automation/rules', 'POST', newRule);
      if (response.success) {
        await loadAutomationRules();
        setShowCreateRuleModal(false);
        resetNewRule();
      }
    } catch (error) {
      console.error('Failed to create rule:', error);
    }
  };

  const toggleRule = async (ruleId: string) => {
    try {
      const response = await makeApiRequest(`/automation/rules/${ruleId}/toggle`, 'POST');
      if (response.success) {
        await loadAutomationRules();
      }
    } catch (error) {
      console.error('Failed to toggle rule:', error);
    }
  };

  const deleteRule = async (ruleId: string) => {
    if (!confirm('Sind Sie sicher, dass Sie diese Regel löschen möchten?')) return;
    
    try {
      const response = await makeApiRequest(`/automation/rules/${ruleId}`, 'DELETE');
      if (response.success) {
        await loadAutomationRules();
      }
    } catch (error) {
      console.error('Failed to delete rule:', error);
    }
  };

  const createSchedule = async () => {
    try {
      const response = await makeApiRequest('/automation/scheduled-tasks', 'POST', newSchedule);
      if (response.success) {
        await loadScheduledTasks();
        setShowCreateScheduleModal(false);
        resetNewSchedule();
      }
    } catch (error) {
      console.error('Failed to create schedule:', error);
    }
  };

  const toggleSchedule = async (taskId: string) => {
    try {
      const response = await makeApiRequest(`/automation/scheduled-tasks/${taskId}/toggle`, 'POST');
      if (response.success) {
        await loadScheduledTasks();
      }
    } catch (error) {
      console.error('Failed to toggle schedule:', error);
    }
  };

  const runScheduleNow = async (taskId: string) => {
    try {
      const response = await makeApiRequest(`/automation/scheduled-tasks/${taskId}/run`, 'POST');
      if (response.success) {
        await loadScheduledTasks();
        alert(`Task "${response.task.name}" wurde erfolgreich ausgeführt!`);
      }
    } catch (error) {
      console.error('Failed to run schedule:', error);
    }
  };

  const deleteSchedule = async (taskId: string) => {
    if (!confirm('Sind Sie sicher, dass Sie diesen geplanten Task löschen möchten?')) return;
    
    try {
      const response = await makeApiRequest(`/automation/scheduled-tasks/${taskId}`, 'DELETE');
      if (response.success) {
        await loadScheduledTasks();
      }
    } catch (error) {
      console.error('Failed to delete schedule:', error);
    }
  };

  const resetNewRule = () => {
    setNewRule({
      name: '',
      description: '',
      conditions: {
        file_extension: '',
        filename_contains: [],
        file_size_mb: { min: 0, max: 0 }
      },
      actions: {
        move_to_workspace: 0,
        move_to_folder: '',
        add_tags: []
      },
      enabled: true
    });
  };

  const resetNewSchedule = () => {
    setNewSchedule({
      name: '',
      description: '',
      schedule: {
        type: 'daily',
        time: '09:00',
        timezone: 'Europe/Berlin'
      },
      actions: [],
      enabled: true
    });
  };

  const renderDashboard = () => {
    if (!dashboard) return <div className="loading">Dashboard wird geladen...</div>;

    return (
      <div className="automation-dashboard">
        <h3>🎯 Automation Dashboard</h3>
        
        <div className="stats-grid">
          <div className="stat-card">
            <div className="stat-icon">📋</div>
            <div className="stat-content">
              <h4>Automation Regeln</h4>
              <div className="stat-number">{dashboard.statistics.rules.total}</div>
              <div className="stat-detail">
                {dashboard.statistics.rules.enabled} aktiv • {dashboard.statistics.rules.total_triggers} Ausführungen
              </div>
            </div>
          </div>
          
          <div className="stat-card">
            <div className="stat-icon">⏰</div>
            <div className="stat-content">
              <h4>Geplante Tasks</h4>
              <div className="stat-number">{dashboard.statistics.scheduled_tasks.total}</div>
              <div className="stat-detail">
                {dashboard.statistics.scheduled_tasks.enabled} aktiv • {dashboard.statistics.scheduled_tasks.total_runs} Ausführungen
              </div>
            </div>
          </div>
        </div>

        <div className="dashboard-sections">
          <div className="dashboard-section">
            <h4>🔥 Aktivste Regeln</h4>
            <div className="active-rules-list">
              {dashboard.most_active_rules.map(rule => (
                <div key={rule.id} className="active-rule-item">
                  <div className="rule-info">
                    <span className="rule-name">{rule.name}</span>
                    <span className="rule-description">{rule.description}</span>
                  </div>
                  <div className="rule-stats">
                    <span className="trigger-count">{rule.trigger_count} mal ausgeführt</span>
                  </div>
                </div>
              ))}
            </div>
          </div>

          <div className="dashboard-section">
            <h4>📅 Nächste geplante Tasks</h4>
            <div className="upcoming-tasks-list">
              {dashboard.upcoming_tasks.map(task => (
                <div key={task.id} className="upcoming-task-item">
                  <div className="task-info">
                    <span className="task-name">{task.name}</span>
                    <span className="task-schedule">
                      Nächste Ausführung: {new Date(task.next_run).toLocaleString('de-DE')}
                    </span>
                  </div>
                  <button
                    className="btn btn-sm btn-secondary"
                    onClick={() => runScheduleNow(task.id)}
                  >
                    Jetzt ausführen
                  </button>
                </div>
              ))}
            </div>
          </div>

          <div className="dashboard-section">
            <h4>📊 Letzte Aktivitäten</h4>
            <div className="activity-list">
              {dashboard.recent_activity.map((activity, index) => (
                <div key={index} className="activity-item">
                  <span className="activity-time">
                    {new Date(activity.timestamp).toLocaleString('de-DE')}
                  </span>
                  <span className="activity-message">{activity.message}</span>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    );
  };

  const renderRules = () => (
    <div className="automation-rules">
      <div className="rules-header">
        <h3>📋 Automation Regeln</h3>
        <button 
          className="btn btn-primary"
          onClick={() => setShowCreateRuleModal(true)}
        >
          + Neue Regel erstellen
        </button>
      </div>

      <div className="rules-list">
        {automationRules.map(rule => (
          <div key={rule.id} className={`rule-card ${!rule.enabled ? 'disabled' : ''}`}>
            <div className="rule-header">
              <div className="rule-title">
                <h4>{rule.name}</h4>
                <p>{rule.description}</p>
              </div>
              <div className="rule-actions">
                <button
                  className={`toggle-btn ${rule.enabled ? 'active' : ''}`}
                  onClick={() => toggleRule(rule.id)}
                >
                  {rule.enabled ? '✓ Aktiv' : '○ Inaktiv'}
                </button>
                <button
                  className="btn btn-sm btn-secondary"
                  onClick={() => setEditingRule(rule)}
                >
                  Bearbeiten
                </button>
                <button
                  className="btn btn-sm btn-danger"
                  onClick={() => deleteRule(rule.id)}
                >
                  Löschen
                </button>
              </div>
            </div>
            
            <div className="rule-details">
              <div className="rule-conditions">
                <h5>Bedingungen:</h5>
                <ul>
                  {rule.conditions.file_extension && (
                    <li>Dateityp: {Array.isArray(rule.conditions.file_extension) ? 
                      rule.conditions.file_extension.join(', ') : rule.conditions.file_extension}</li>
                  )}
                  {rule.conditions.filename_contains && rule.conditions.filename_contains.length > 0 && (
                    <li>Dateiname enthält: {rule.conditions.filename_contains.join(', ')}</li>
                  )}
                  {rule.conditions.file_size_mb && (
                    <li>
                      Dateigröße: 
                      {rule.conditions.file_size_mb.min && ` Min: ${rule.conditions.file_size_mb.min}MB`}
                      {rule.conditions.file_size_mb.max && ` Max: ${rule.conditions.file_size_mb.max}MB`}
                    </li>
                  )}
                </ul>
              </div>
              
              <div className="rule-actions-list">
                <h5>Aktionen:</h5>
                <ul>
                  {rule.actions.move_to_workspace && (
                    <li>Verschiebe zu Workspace ID: {rule.actions.move_to_workspace}</li>
                  )}
                  {rule.actions.move_to_folder && (
                    <li>Verschiebe in Ordner: {rule.actions.move_to_folder}</li>
                  )}
                  {rule.actions.add_tags && rule.actions.add_tags.length > 0 && (
                    <li>Füge Tags hinzu: {rule.actions.add_tags.join(', ')}</li>
                  )}
                  {rule.actions.compress && <li>Komprimiere Datei</li>}
                  {rule.actions.notify && <li>Sende Benachrichtigung</li>}
                </ul>
              </div>
            </div>
            
            <div className="rule-stats">
              <span>{rule.trigger_count} mal ausgeführt</span>
              {rule.last_triggered && (
                <span>Zuletzt: {new Date(rule.last_triggered).toLocaleString('de-DE')}</span>
              )}
            </div>
          </div>
        ))}
      </div>
    </div>
  );

  const renderSchedules = () => (
    <div className="scheduled-tasks">
      <div className="schedules-header">
        <h3>⏰ Geplante Tasks</h3>
        <button 
          className="btn btn-primary"
          onClick={() => setShowCreateScheduleModal(true)}
        >
          + Neuen Task planen
        </button>
      </div>

      <div className="schedules-list">
        {scheduledTasks.map(task => (
          <div key={task.id} className={`schedule-card ${!task.enabled ? 'disabled' : ''}`}>
            <div className="schedule-header">
              <div className="schedule-title">
                <h4>{task.name}</h4>
                <p>{task.description}</p>
              </div>
              <div className="schedule-actions">
                <button
                  className={`toggle-btn ${task.enabled ? 'active' : ''}`}
                  onClick={() => toggleSchedule(task.id)}
                >
                  {task.enabled ? '✓ Aktiv' : '○ Inaktiv'}
                </button>
                <button
                  className="btn btn-sm btn-primary"
                  onClick={() => runScheduleNow(task.id)}
                >
                  Jetzt ausführen
                </button>
                <button
                  className="btn btn-sm btn-secondary"
                  onClick={() => setEditingSchedule(task)}
                >
                  Bearbeiten
                </button>
                <button
                  className="btn btn-sm btn-danger"
                  onClick={() => deleteSchedule(task.id)}
                >
                  Löschen
                </button>
              </div>
            </div>
            
            <div className="schedule-details">
              <div className="schedule-info">
                <h5>Zeitplan:</h5>
                <p>
                  {task.schedule.type === 'daily' && `Täglich um ${task.schedule.time} Uhr`}
                  {task.schedule.type === 'weekly' && `Wöchentlich ${task.schedule.day} um ${task.schedule.time} Uhr`}
                  {task.schedule.type === 'monthly' && `Monatlich am ${task.schedule.day_of_month}. um ${task.schedule.time} Uhr`}
                </p>
                <p className="timezone">Zeitzone: {task.schedule.timezone}</p>
              </div>
              
              <div className="schedule-actions-list">
                <h5>Aktionen:</h5>
                <ul>
                  {task.actions.map((action, index) => (
                    <li key={index}>{action.replace(/_/g, ' ')}</li>
                  ))}
                </ul>
              </div>
            </div>
            
            <div className="schedule-stats">
              <span>{task.run_count} mal ausgeführt</span>
              <span>Status: {task.status}</span>
              {task.last_run && (
                <span>Zuletzt: {new Date(task.last_run).toLocaleString('de-DE')}</span>
              )}
              <span>Nächste Ausführung: {new Date(task.next_run).toLocaleString('de-DE')}</span>
            </div>
          </div>
        ))}
      </div>
    </div>
  );

  return (
    <div className="automation-center">
      <div className="automation-header">
        <h2>🤖 Automation Center</h2>
        <p>Automatisieren Sie Ihre Dateiorganisation mit intelligenten Regeln und Zeitplänen</p>
      </div>

      <div className="automation-tabs">
        <button
          className={`tab ${activeTab === 'dashboard' ? 'active' : ''}`}
          onClick={() => setActiveTab('dashboard')}
        >
          🎯 Dashboard
        </button>
        <button
          className={`tab ${activeTab === 'rules' ? 'active' : ''}`}
          onClick={() => setActiveTab('rules')}
        >
          📋 Regeln
        </button>
        <button
          className={`tab ${activeTab === 'schedules' ? 'active' : ''}`}
          onClick={() => setActiveTab('schedules')}
        >
          ⏰ Zeitpläne
        </button>
      </div>

      <div className="automation-content">
        {loading ? (
          <div className="loading">Automation-Daten werden geladen...</div>
        ) : (
          <>
            {activeTab === 'dashboard' && renderDashboard()}
            {activeTab === 'rules' && renderRules()}
            {activeTab === 'schedules' && renderSchedules()}
          </>
        )}
      </div>
    </div>
  );
};

export default AutomationCenter;