import React, { useState } from 'react';
import './VoiceSettings.css';

interface VoiceProfile {
  language_preference: string;
  accent_model: string;
  voice_shortcuts: Record<string, string>;
  wake_word_sensitivity: number;
  noise_cancellation_level: number;
  confirmation_required: boolean;
  voice_feedback_enabled: boolean;
  custom_commands: Record<string, any>;
}

interface VoiceSettingsProps {
  profile: VoiceProfile;
  onUpdate: (updates: Partial<VoiceProfile>) => void;
  onClose: () => void;
}

const VoiceSettings: React.FC<VoiceSettingsProps> = ({ profile, onUpdate, onClose }) => {
  const [localProfile, setLocalProfile] = useState(profile);
  const [newShortcut, setNewShortcut] = useState({ phrase: '', command: '' });
  const [activeTab, setActiveTab] = useState<'general' | 'shortcuts' | 'advanced'>('general');

  const languages = [
    { code: 'en', name: 'English' },
    { code: 'es', name: 'Spanish' },
    { code: 'fr', name: 'French' },
    { code: 'de', name: 'German' },
    { code: 'it', name: 'Italian' },
    { code: 'pt', name: 'Portuguese' },
    { code: 'zh', name: 'Chinese' },
    { code: 'ja', name: 'Japanese' },
    { code: 'ko', name: 'Korean' },
    { code: 'ru', name: 'Russian' }
  ];

  const accents = [
    { code: 'default', name: 'Default' },
    { code: 'us', name: 'US English' },
    { code: 'uk', name: 'UK English' },
    { code: 'au', name: 'Australian English' },
    { code: 'in', name: 'Indian English' },
    { code: 'ca', name: 'Canadian English' }
  ];

  const handleUpdate = (field: keyof VoiceProfile, value: any) => {
    setLocalProfile(prev => ({ ...prev, [field]: value }));
  };

  const handleSave = () => {
    onUpdate(localProfile);
    onClose();
  };

  const handleAddShortcut = () => {
    if (newShortcut.phrase && newShortcut.command) {
      const updatedShortcuts = {
        ...localProfile.voice_shortcuts,
        [newShortcut.phrase]: newShortcut.command
      };
      handleUpdate('voice_shortcuts', updatedShortcuts);
      setNewShortcut({ phrase: '', command: '' });
    }
  };

  const handleRemoveShortcut = (phrase: string) => {
    const updatedShortcuts = { ...localProfile.voice_shortcuts };
    delete updatedShortcuts[phrase];
    handleUpdate('voice_shortcuts', updatedShortcuts);
  };

  return (
    <div className="voice-settings-overlay">
      <div className="voice-settings-modal">
        <div className="voice-settings-header">
          <h2>Voice Command Settings</h2>
          <button className="close-btn" onClick={onClose}>
            <i className="fas fa-times" />
          </button>
        </div>

        <div className="voice-settings-tabs">
          <button
            className={`tab ${activeTab === 'general' ? 'active' : ''}`}
            onClick={() => setActiveTab('general')}
          >
            General
          </button>
          <button
            className={`tab ${activeTab === 'shortcuts' ? 'active' : ''}`}
            onClick={() => setActiveTab('shortcuts')}
          >
            Shortcuts
          </button>
          <button
            className={`tab ${activeTab === 'advanced' ? 'active' : ''}`}
            onClick={() => setActiveTab('advanced')}
          >
            Advanced
          </button>
        </div>

        <div className="voice-settings-content">
          {activeTab === 'general' && (
            <div className="settings-section">
              <div className="setting-group">
                <label>Language</label>
                <select
                  value={localProfile.language_preference}
                  onChange={(e) => handleUpdate('language_preference', e.target.value)}
                >
                  {languages.map(lang => (
                    <option key={lang.code} value={lang.code}>
                      {lang.name}
                    </option>
                  ))}
                </select>
              </div>

              <div className="setting-group">
                <label>Accent Model</label>
                <select
                  value={localProfile.accent_model}
                  onChange={(e) => handleUpdate('accent_model', e.target.value)}
                >
                  {accents.map(accent => (
                    <option key={accent.code} value={accent.code}>
                      {accent.name}
                    </option>
                  ))}
                </select>
              </div>

              <div className="setting-group">
                <label className="checkbox-label">
                  <input
                    type="checkbox"
                    checked={localProfile.confirmation_required}
                    onChange={(e) => handleUpdate('confirmation_required', e.target.checked)}
                  />
                  <span>Require confirmation for commands</span>
                </label>
              </div>

              <div className="setting-group">
                <label className="checkbox-label">
                  <input
                    type="checkbox"
                    checked={localProfile.voice_feedback_enabled}
                    onChange={(e) => handleUpdate('voice_feedback_enabled', e.target.checked)}
                  />
                  <span>Enable voice feedback</span>
                </label>
              </div>
            </div>
          )}

          {activeTab === 'shortcuts' && (
            <div className="settings-section">
              <div className="shortcuts-header">
                <h3>Voice Shortcuts</h3>
                <p>Create custom phrases to trigger specific commands</p>
              </div>

              <div className="shortcuts-list">
                {Object.entries(localProfile.voice_shortcuts).map(([phrase, command]) => (
                  <div key={phrase} className="shortcut-item">
                    <div className="shortcut-info">
                      <span className="shortcut-phrase">"{phrase}"</span>
                      <span className="shortcut-arrow">→</span>
                      <span className="shortcut-command">{command}</span>
                    </div>
                    <button
                      className="remove-shortcut"
                      onClick={() => handleRemoveShortcut(phrase)}
                    >
                      <i className="fas fa-trash" />
                    </button>
                  </div>
                ))}
              </div>

              <div className="add-shortcut">
                <input
                  type="text"
                  placeholder="Phrase (e.g., 'quick task')"
                  value={newShortcut.phrase}
                  onChange={(e) => setNewShortcut(prev => ({ ...prev, phrase: e.target.value }))}
                />
                <input
                  type="text"
                  placeholder="Command (e.g., 'create task')"
                  value={newShortcut.command}
                  onChange={(e) => setNewShortcut(prev => ({ ...prev, command: e.target.value }))}
                />
                <button onClick={handleAddShortcut}>
                  <i className="fas fa-plus" /> Add
                </button>
              </div>
            </div>
          )}

          {activeTab === 'advanced' && (
            <div className="settings-section">
              <div className="setting-group">
                <label>
                  Wake Word Sensitivity
                  <span className="value">{Math.round(localProfile.wake_word_sensitivity * 100)}%</span>
                </label>
                <input
                  type="range"
                  min="0"
                  max="100"
                  value={localProfile.wake_word_sensitivity * 100}
                  onChange={(e) => handleUpdate('wake_word_sensitivity', Number(e.target.value) / 100)}
                  className="slider"
                />
                <p className="setting-description">
                  Higher sensitivity makes it easier to trigger the wake word
                </p>
              </div>

              <div className="setting-group">
                <label>
                  Noise Cancellation Level
                  <span className="value">{Math.round(localProfile.noise_cancellation_level * 100)}%</span>
                </label>
                <input
                  type="range"
                  min="0"
                  max="100"
                  value={localProfile.noise_cancellation_level * 100}
                  onChange={(e) => handleUpdate('noise_cancellation_level', Number(e.target.value) / 100)}
                  className="slider"
                />
                <p className="setting-description">
                  Higher levels filter out more background noise
                </p>
              </div>

              <div className="setting-group">
                <h4>Voice Profiles</h4>
                <p className="setting-description">
                  Train the system to better recognize your voice
                </p>
                <button className="train-voice-btn">
                  <i className="fas fa-microphone" /> Train Voice Profile
                </button>
              </div>

              <div className="setting-group">
                <h4>Privacy</h4>
                <label className="checkbox-label">
                  <input type="checkbox" defaultChecked />
                  <span>Process voice locally when possible</span>
                </label>
                <label className="checkbox-label">
                  <input type="checkbox" />
                  <span>Store voice command history</span>
                </label>
              </div>
            </div>
          )}
        </div>

        <div className="voice-settings-footer">
          <button className="cancel-btn" onClick={onClose}>
            Cancel
          </button>
          <button className="save-btn" onClick={handleSave}>
            Save Changes
          </button>
        </div>
      </div>
    </div>
  );
};

export default VoiceSettings;