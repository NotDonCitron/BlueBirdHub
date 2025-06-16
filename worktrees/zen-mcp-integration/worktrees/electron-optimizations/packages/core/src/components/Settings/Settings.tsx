import React, { useState, useEffect } from 'react';
import { useTheme } from '../../contexts/ThemeContext';
import { useApi } from '../../contexts/ApiContext';
import './Settings.css';

interface UserSettings {
  theme: 'light' | 'dark' | 'auto';
  language: string;
  aiEnabled: boolean;
  autoOrganize: boolean;
  notificationsEnabled: boolean;
  defaultWorkspace: string;
  filePreviewEnabled: boolean;
  autoBackup: boolean;
  storageCleanupDays: number;
}

const Settings: React.FC = () => {
  const { theme, toggleTheme } = useTheme();
  const { makeApiRequest, apiStatus } = useApi();
  const [settings, setSettings] = useState<UserSettings>({
    theme: 'auto',
    language: 'en',
    aiEnabled: true,
    autoOrganize: false,
    notificationsEnabled: true,
    defaultWorkspace: 'default',
    filePreviewEnabled: true,
    autoBackup: false,
    storageCleanupDays: 30
  });
  const [saved, setSaved] = useState(false);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    loadSettings();
  }, []);

  const loadSettings = async () => {
    try {
      // Load from localStorage as fallback
      const savedSettings = localStorage.getItem('ordnungshub-settings');
      if (savedSettings) {
        setSettings({ ...settings, ...JSON.parse(savedSettings) });
      }
    } catch (error) {
      console.error('Failed to load settings:', error);
    }
  };

  const saveSettings = async () => {
    setLoading(true);
    try {
      // Save to localStorage
      localStorage.setItem('ordnungshub-settings', JSON.stringify(settings));
      
      // TODO: Save to backend when user API is available
      // await makeApiRequest('/users/settings', 'PUT', settings);
      
      setSaved(true);
      setTimeout(() => setSaved(false), 2000);
    } catch (error) {
      console.error('Failed to save settings:', error);
    } finally {
      setLoading(false);
    }
  };

  const resetSettings = () => {
    const defaultSettings: UserSettings = {
      theme: 'auto',
      language: 'en',
      aiEnabled: true,
      autoOrganize: false,
      notificationsEnabled: true,
      defaultWorkspace: 'default',
      filePreviewEnabled: true,
      autoBackup: false,
      storageCleanupDays: 30
    };
    setSettings(defaultSettings);
  };

  const handleSettingChange = (key: keyof UserSettings, value: any) => {
    setSettings(prev => ({ ...prev, [key]: value }));
  };

  const clearStorageData = async () => {
    if (confirm('Are you sure you want to clear all local storage data? This cannot be undone.')) {
      try {
        await makeApiRequest('/file-management/smart-cleanup', 'POST', {
          user_id: 1,
          cleanup_old: true,
          cleanup_duplicates: true,
          cleanup_temp: true
        });
        alert('Storage cleanup completed successfully!');
      } catch (error) {
        console.error('Failed to clean storage:', error);
        alert('Storage cleanup failed. Please try again.');
      }
    }
  };

  return (
    <div className="settings">
      <div className="settings-header">
        <h2>⚙️ Settings</h2>
        <p>Customize your OrdnungsHub experience</p>
      </div>

      <div className="settings-content">
        {/* Appearance Settings */}
        <div className="settings-section">
          <h3>🎨 Appearance</h3>
          <div className="setting-item">
            <label>Theme</label>
            <select 
              value={settings.theme} 
              onChange={(e) => handleSettingChange('theme', e.target.value)}
            >
              <option value="auto">Auto (Follow System)</option>
              <option value="light">Light</option>
              <option value="dark">Dark</option>
            </select>
          </div>
          <div className="setting-item">
            <label>Language</label>
            <select 
              value={settings.language} 
              onChange={(e) => handleSettingChange('language', e.target.value)}
            >
              <option value="en">English</option>
              <option value="de">Deutsch</option>
              <option value="fr">Français</option>
              <option value="es">Español</option>
            </select>
          </div>
        </div>

        {/* AI & Automation Settings */}
        <div className="settings-section">
          <h3>🤖 AI & Automation</h3>
          <div className="setting-item">
            <label>
              <input
                type="checkbox"
                checked={settings.aiEnabled}
                onChange={(e) => handleSettingChange('aiEnabled', e.target.checked)}
              />
              Enable AI-powered features
            </label>
            <small>Use AI for file categorization and suggestions</small>
          </div>
          <div className="setting-item">
            <label>
              <input
                type="checkbox"
                checked={settings.autoOrganize}
                onChange={(e) => handleSettingChange('autoOrganize', e.target.checked)}
              />
              Auto-organize new files
            </label>
            <small>Automatically organize files when added to watched folders</small>
          </div>
        </div>

        {/* File Management Settings */}
        <div className="settings-section">
          <h3>📁 File Management</h3>
          <div className="setting-item">
            <label>Default Workspace</label>
            <select 
              value={settings.defaultWorkspace} 
              onChange={(e) => handleSettingChange('defaultWorkspace', e.target.value)}
            >
              <option value="default">Default</option>
              <option value="development">Development</option>
              <option value="creative">Creative</option>
              <option value="business">Business</option>
            </select>
          </div>
          <div className="setting-item">
            <label>
              <input
                type="checkbox"
                checked={settings.filePreviewEnabled}
                onChange={(e) => handleSettingChange('filePreviewEnabled', e.target.checked)}
              />
              Enable file previews
            </label>
            <small>Show file content previews in file manager</small>
          </div>
          <div className="setting-item">
            <label>Storage cleanup after (days)</label>
            <input
              type="number"
              min="1"
              max="365"
              value={settings.storageCleanupDays}
              onChange={(e) => handleSettingChange('storageCleanupDays', parseInt(e.target.value))}
            />
            <small>Automatically suggest cleanup for files older than this many days</small>
          </div>
        </div>

        {/* Backup & Data Settings */}
        <div className="settings-section">
          <h3>💾 Backup & Data</h3>
          <div className="setting-item">
            <label>
              <input
                type="checkbox"
                checked={settings.autoBackup}
                onChange={(e) => handleSettingChange('autoBackup', e.target.checked)}
              />
              Enable automatic backups
            </label>
            <small>Automatically backup workspace configurations</small>
          </div>
          <div className="setting-item">
            <label>
              <input
                type="checkbox"
                checked={settings.notificationsEnabled}
                onChange={(e) => handleSettingChange('notificationsEnabled', e.target.checked)}
              />
              Enable notifications
            </label>
            <small>Show notifications for completed operations and suggestions</small>
          </div>
        </div>

        {/* System Information */}
        <div className="settings-section">
          <h3>ℹ️ System Information</h3>
          <div className="system-info">
            <div className="info-item">
              <span>API Status:</span>
              <span className={`status ${apiStatus}`}>{apiStatus}</span>
            </div>
            <div className="info-item">
              <span>Version:</span>
              <span>0.1.0</span>
            </div>
            <div className="info-item">
              <span>Theme:</span>
              <span>{theme}</span>
            </div>
          </div>
        </div>

        {/* Danger Zone */}
        <div className="settings-section danger-zone">
          <h3>⚠️ Danger Zone</h3>
          <div className="danger-actions">
            <button 
              className="btn btn-warning"
              onClick={resetSettings}
            >
              Reset to Defaults
            </button>
            <button 
              className="btn btn-danger"
              onClick={clearStorageData}
            >
              Clear Storage Data
            </button>
          </div>
        </div>
      </div>

      {/* Action Buttons */}
      <div className="settings-actions">
        <button 
          className="btn btn-secondary"
          onClick={loadSettings}
        >
          Reset Changes
        </button>
        <button 
          className={`btn btn-primary ${saved ? 'btn-success' : ''}`}
          onClick={saveSettings}
          disabled={loading}
        >
          {loading ? 'Saving...' : saved ? 'Saved!' : 'Save Settings'}
        </button>
      </div>
    </div>
  );
};

export default Settings;