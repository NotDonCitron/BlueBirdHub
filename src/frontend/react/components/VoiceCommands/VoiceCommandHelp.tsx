import React, { useState } from 'react';
import './VoiceCommandHelp.css';

interface VoiceCommandHelpProps {
  onClose: () => void;
}

const VoiceCommandHelp: React.FC<VoiceCommandHelpProps> = ({ onClose }) => {
  const [activeCategory, setActiveCategory] = useState('tasks');

  const commandCategories = {
    tasks: {
      title: 'Task Management',
      icon: 'fa-tasks',
      commands: [
        {
          command: 'Create a task to [description]',
          examples: [
            'Create a task to review Q4 reports',
            'Add new task for meeting preparation',
            'Remind me to call the client tomorrow'
          ],
          description: 'Create a new task with the specified description'
        },
        {
          command: 'Update task [name] to [new value]',
          examples: [
            'Update task review reports to high priority',
            'Change task meeting prep deadline to Friday'
          ],
          description: 'Update an existing task'
        },
        {
          command: 'Delete task [name]',
          examples: [
            'Delete task old meeting notes',
            'Remove task draft proposal',
            'Cancel task team lunch'
          ],
          description: 'Delete or cancel a task'
        },
        {
          command: 'Mark [task] as complete',
          examples: [
            'Mark review task as complete',
            'Complete task send invoice',
            'Finish task update documentation'
          ],
          description: 'Mark a task as completed'
        },
        {
          command: 'Set priority to [level]',
          examples: [
            'Set priority to high',
            'Make it urgent priority',
            'Priority low'
          ],
          description: 'Set task priority (low, medium, high, urgent)'
        },
        {
          command: 'Set deadline [date]',
          examples: [
            'Set deadline tomorrow',
            'Due date next Friday',
            'Schedule for end of month'
          ],
          description: 'Set or update task deadline'
        }
      ]
    },
    search: {
      title: 'Search & Navigation',
      icon: 'fa-search',
      commands: [
        {
          command: 'Search tasks [query]',
          examples: [
            'Search tasks about client meeting',
            'Find high priority tasks',
            'Show tasks due this week'
          ],
          description: 'Search for tasks matching criteria'
        },
        {
          command: 'Go to [page]',
          examples: [
            'Go to dashboard',
            'Navigate to settings',
            'Open task manager'
          ],
          description: 'Navigate to different pages'
        },
        {
          command: 'Show [view]',
          examples: [
            'Show calendar view',
            'Display completed tasks',
            'View workspace details'
          ],
          description: 'Switch between different views'
        }
      ]
    },
    workspace: {
      title: 'Workspace Management',
      icon: 'fa-folder',
      commands: [
        {
          command: 'Create workspace [name]',
          examples: [
            'Create workspace Q1 Planning',
            'New workspace for marketing',
            'Add workspace client projects'
          ],
          description: 'Create a new workspace'
        },
        {
          command: 'Switch to workspace [name]',
          examples: [
            'Switch to workspace development',
            'Change to marketing workspace',
            'Open workspace personal'
          ],
          description: 'Switch to a different workspace'
        }
      ]
    },
    dictation: {
      title: 'Voice Dictation',
      icon: 'fa-microphone',
      commands: [
        {
          command: 'Start dictation',
          examples: [
            'Start dictation',
            'Begin voice input',
            'Enable dictation mode'
          ],
          description: 'Start voice dictation for text input'
        },
        {
          command: 'Stop dictation',
          examples: [
            'Stop dictation',
            'End voice input',
            'Finish dictation'
          ],
          description: 'Stop voice dictation'
        },
        {
          command: 'Add note [content]',
          examples: [
            'Add note discuss budget in next meeting',
            'Note to self check email attachments',
            'Create note review competitor analysis'
          ],
          description: 'Add a note with voice'
        }
      ]
    },
    system: {
      title: 'System Commands',
      icon: 'fa-cog',
      commands: [
        {
          command: 'Help',
          examples: [
            'Help',
            'Show commands',
            'What can you do'
          ],
          description: 'Show available voice commands'
        },
        {
          command: 'Cancel',
          examples: [
            'Cancel',
            'Stop',
            'Never mind'
          ],
          description: 'Cancel current operation'
        },
        {
          command: 'Confirm / Yes',
          examples: [
            'Confirm',
            'Yes',
            'Proceed'
          ],
          description: 'Confirm an action'
        },
        {
          command: 'Undo',
          examples: [
            'Undo',
            'Undo last action',
            'Revert'
          ],
          description: 'Undo the last action'
        }
      ]
    }
  };

  const tips = [
    {
      icon: 'fa-lightbulb',
      title: 'Wake Word',
      description: 'Start commands with "Hey BlueBird" to activate voice recognition'
    },
    {
      icon: 'fa-clock',
      title: 'Natural Timing',
      description: 'Use natural time expressions like "tomorrow", "next week", or "in 3 days"'
    },
    {
      icon: 'fa-language',
      title: 'Multiple Languages',
      description: 'Voice commands support multiple languages. Change in settings.'
    },
    {
      icon: 'fa-keyboard',
      title: 'Shortcuts',
      description: 'Create custom voice shortcuts for frequently used commands'
    },
    {
      icon: 'fa-volume-up',
      title: 'Clear Speech',
      description: 'Speak clearly and at a moderate pace for best recognition'
    },
    {
      icon: 'fa-shield-alt',
      title: 'Privacy',
      description: 'Voice processing can be done locally for enhanced privacy'
    }
  ];

  return (
    <div className="voice-help-overlay">
      <div className="voice-help-modal">
        <div className="voice-help-header">
          <h2>Voice Commands Guide</h2>
          <button className="close-btn" onClick={onClose}>
            <i className="fas fa-times" />
          </button>
        </div>

        <div className="voice-help-body">
          <div className="voice-help-sidebar">
            <h3>Categories</h3>
            {Object.entries(commandCategories).map(([key, category]) => (
              <button
                key={key}
                className={`category-btn ${activeCategory === key ? 'active' : ''}`}
                onClick={() => setActiveCategory(key)}
              >
                <i className={`fas ${category.icon}`} />
                <span>{category.title}</span>
              </button>
            ))}
          </div>

          <div className="voice-help-content">
            <div className="commands-section">
              <h3>{commandCategories[activeCategory].title}</h3>
              
              {commandCategories[activeCategory].commands.map((cmd, index) => (
                <div key={index} className="command-card">
                  <div className="command-header">
                    <i className="fas fa-quote-left" />
                    <span className="command-pattern">{cmd.command}</span>
                  </div>
                  
                  <p className="command-description">{cmd.description}</p>
                  
                  <div className="command-examples">
                    <strong>Examples:</strong>
                    <ul>
                      {cmd.examples.map((example, i) => (
                        <li key={i}>"{example}"</li>
                      ))}
                    </ul>
                  </div>
                </div>
              ))}
            </div>

            <div className="tips-section">
              <h3>Tips & Best Practices</h3>
              <div className="tips-grid">
                {tips.map((tip, index) => (
                  <div key={index} className="tip-card">
                    <i className={`fas ${tip.icon}`} />
                    <h4>{tip.title}</h4>
                    <p>{tip.description}</p>
                  </div>
                ))}
              </div>
            </div>

            <div className="quick-start-section">
              <h3>Quick Start</h3>
              <div className="quick-start-steps">
                <div className="step">
                  <span className="step-number">1</span>
                  <div className="step-content">
                    <h4>Enable Voice Commands</h4>
                    <p>Click the microphone button or say "Hey BlueBird"</p>
                  </div>
                </div>
                <div className="step">
                  <span className="step-number">2</span>
                  <div className="step-content">
                    <h4>Speak Your Command</h4>
                    <p>Say your command clearly after the wake word</p>
                  </div>
                </div>
                <div className="step">
                  <span className="step-number">3</span>
                  <div className="step-content">
                    <h4>Confirm or Cancel</h4>
                    <p>Confirm actions when prompted or say "cancel"</p>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default VoiceCommandHelp;