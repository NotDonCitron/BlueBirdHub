import React, { useState, useEffect, useCallback } from 'react';
import { useI18n } from '../../contexts/I18nContext';
import './TranslationManager.css';

interface TranslationKey {
  id: string;
  key: string;
  namespace: string;
  description?: string;
  context?: string;
  pluralizable?: boolean;
  genderizable?: boolean;
  values: Record<string, string>;
  lastModified: Date;
  status: 'complete' | 'partial' | 'missing' | 'outdated';
}

interface TranslationManagerProps {
  onClose?: () => void;
  initialLanguage?: string;
}

const TranslationManager: React.FC<TranslationManagerProps> = ({
  onClose,
  initialLanguage
}) => {
  const { t, availableLanguages, currentLanguage } = useI18n();
  const [selectedLanguage, setSelectedLanguage] = useState(initialLanguage || currentLanguage);
  const [selectedNamespace, setSelectedNamespace] = useState('common');
  const [searchTerm, setSearchTerm] = useState('');
  const [filterStatus, setFilterStatus] = useState<'all' | 'complete' | 'partial' | 'missing'>('all');
  const [translations, setTranslations] = useState<TranslationKey[]>([]);
  const [loading, setLoading] = useState(false);
  const [selectedKey, setSelectedKey] = useState<TranslationKey | null>(null);
  const [editingValue, setEditingValue] = useState('');
  const [isEditing, setIsEditing] = useState(false);

  const namespaces = ['common', 'navigation', 'dashboard', 'workspace', 'tasks', 'files', 'ai', 'settings', 'auth', 'errors'];

  // Mock data - in real app, this would come from API
  const mockTranslations: TranslationKey[] = [
    {
      id: '1',
      key: 'app.name',
      namespace: 'common',
      description: 'Application name',
      values: {
        en: 'BlueBirdHub',
        es: 'BlueBirdHub',
        fr: 'BlueBirdHub',
        de: 'BlueBirdHub',
        zh: 'BlueBirdHub',
        ja: 'BlueBirdHub',
        ar: 'BlueBirdHub',
        he: 'BlueBirdHub'
      },
      lastModified: new Date(),
      status: 'complete'
    },
    {
      id: '2',
      key: 'common.loading',
      namespace: 'common',
      description: 'Loading indicator text',
      values: {
        en: 'Loading...',
        es: 'Cargando...',
        fr: 'Chargement...',
        de: 'Wird geladen...',
        zh: '加载中...',
        ja: '読み込み中...',
        ar: 'جاري التحميل...',
        he: 'טוען...'
      },
      lastModified: new Date(),
      status: 'complete'
    },
    {
      id: '3',
      key: 'pluralization.file',
      namespace: 'common',
      description: 'File count with pluralization',
      pluralizable: true,
      values: {
        en: 'file',
        es: 'archivo',
        fr: 'fichier',
        de: 'Datei',
        zh: '文件',
        ja: 'ファイル',
        ar: 'ملف',
        he: ''  // Missing translation
      },
      lastModified: new Date(),
      status: 'partial'
    }
  ];

  // Load translations
  const loadTranslations = useCallback(async () => {
    setLoading(true);
    try {
      // In real app, fetch from API
      // const response = await fetch(`/api/translations/${selectedNamespace}`);
      // const data = await response.json();
      
      // Mock delay
      await new Promise(resolve => setTimeout(resolve, 500));
      setTranslations(mockTranslations.filter(t => t.namespace === selectedNamespace));
    } catch (error) {
      console.error('Failed to load translations:', error);
    } finally {
      setLoading(false);
    }
  }, [selectedNamespace]);

  useEffect(() => {
    loadTranslations();
  }, [loadTranslations]);

  // Filter translations
  const filteredTranslations = translations.filter(translation => {
    const matchesSearch = translation.key.toLowerCase().includes(searchTerm.toLowerCase()) ||
                         translation.description?.toLowerCase().includes(searchTerm.toLowerCase());
    
    const matchesFilter = filterStatus === 'all' || translation.status === filterStatus;
    
    return matchesSearch && matchesFilter;
  });

  // Get translation status
  const getTranslationStatus = (translation: TranslationKey): 'complete' | 'partial' | 'missing' => {
    const totalLanguages = availableLanguages.length;
    const translatedLanguages = availableLanguages.filter(lang => 
      translation.values[lang.code] && translation.values[lang.code].trim()
    ).length;
    
    if (translatedLanguages === 0) return 'missing';
    if (translatedLanguages < totalLanguages) return 'partial';
    return 'complete';
  };

  // Handle translation edit
  const handleEdit = (translation: TranslationKey) => {
    setSelectedKey(translation);
    setEditingValue(translation.values[selectedLanguage] || '');
    setIsEditing(true);
  };

  // Save translation
  const handleSave = async () => {
    if (!selectedKey) return;
    
    try {
      const updatedTranslation = {
        ...selectedKey,
        values: {
          ...selectedKey.values,
          [selectedLanguage]: editingValue
        },
        lastModified: new Date(),
        status: getTranslationStatus({
          ...selectedKey,
          values: {
            ...selectedKey.values,
            [selectedLanguage]: editingValue
          }
        })
      };

      // In real app, save to API
      // await fetch(`/api/translations/${selectedKey.id}`, {
      //   method: 'PUT',
      //   headers: { 'Content-Type': 'application/json' },
      //   body: JSON.stringify(updatedTranslation)
      // });

      // Update local state
      setTranslations(prev => 
        prev.map(t => t.id === selectedKey.id ? updatedTranslation : t)
      );
      
      setIsEditing(false);
      setSelectedKey(null);
    } catch (error) {
      console.error('Failed to save translation:', error);
    }
  };

  // Export translations
  const handleExport = async () => {
    try {
      const exportData = {
        namespace: selectedNamespace,
        language: selectedLanguage,
        translations: filteredTranslations.reduce((acc, t) => {
          acc[t.key] = t.values[selectedLanguage] || '';
          return acc;
        }, {} as Record<string, string>),
        exportDate: new Date().toISOString()
      };

      const blob = new Blob([JSON.stringify(exportData, null, 2)], { 
        type: 'application/json' 
      });
      
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `${selectedNamespace}-${selectedLanguage}.json`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
    } catch (error) {
      console.error('Export failed:', error);
    }
  };

  // Import translations
  const handleImport = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) return;

    const reader = new FileReader();
    reader.onload = async (e) => {
      try {
        const content = e.target?.result as string;
        const importData = JSON.parse(content);
        
        // Validate import data
        if (!importData.translations || typeof importData.translations !== 'object') {
          throw new Error('Invalid import format');
        }

        // Update translations
        const updatedTranslations = translations.map(t => {
          if (importData.translations[t.key]) {
            return {
              ...t,
              values: {
                ...t.values,
                [selectedLanguage]: importData.translations[t.key]
              },
              lastModified: new Date(),
              status: getTranslationStatus({
                ...t,
                values: {
                  ...t.values,
                  [selectedLanguage]: importData.translations[t.key]
                }
              })
            };
          }
          return t;
        });

        setTranslations(updatedTranslations);
        
        // Reset file input
        event.target.value = '';
      } catch (error) {
        console.error('Import failed:', error);
        alert('Import failed: Invalid file format');
      }
    };
    
    reader.readAsText(file);
  };

  // Get completion statistics
  const getStats = () => {
    const total = translations.length;
    const complete = translations.filter(t => t.status === 'complete').length;
    const partial = translations.filter(t => t.status === 'partial').length;
    const missing = translations.filter(t => t.status === 'missing').length;
    
    return { total, complete, partial, missing };
  };

  const stats = getStats();

  return (
    <div className="translation-manager">
      <div className="translation-manager-header">
        <h2>{t('admin.translation_manager')}</h2>
        {onClose && (
          <button 
            className="close-button" 
            onClick={onClose}
            aria-label={t('common.close')}
          >
            ×
          </button>
        )}
      </div>

      <div className="translation-manager-controls">
        <div className="control-group">
          <label htmlFor="namespace-select">{t('admin.namespace')}</label>
          <select
            id="namespace-select"
            value={selectedNamespace}
            onChange={(e) => setSelectedNamespace(e.target.value)}
          >
            {namespaces.map(ns => (
              <option key={ns} value={ns}>{ns}</option>
            ))}
          </select>
        </div>

        <div className="control-group">
          <label htmlFor="language-select">{t('common.language')}</label>
          <select
            id="language-select"
            value={selectedLanguage}
            onChange={(e) => setSelectedLanguage(e.target.value)}
          >
            {availableLanguages.map(lang => (
              <option key={lang.code} value={lang.code}>
                {lang.nativeName} ({lang.name})
              </option>
            ))}
          </select>
        </div>

        <div className="control-group">
          <label htmlFor="filter-select">{t('common.filter')}</label>
          <select
            id="filter-select"
            value={filterStatus}
            onChange={(e) => setFilterStatus(e.target.value as any)}
          >
            <option value="all">{t('common.all')}</option>
            <option value="complete">{t('admin.complete')}</option>
            <option value="partial">{t('admin.partial')}</option>
            <option value="missing">{t('admin.missing')}</option>
          </select>
        </div>

        <div className="control-group">
          <label htmlFor="search-input">{t('common.search')}</label>
          <input
            id="search-input"
            type="text"
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            placeholder={t('admin.search_translations')}
          />
        </div>
      </div>

      <div className="translation-stats">
        <div className="stat-item">
          <span className="stat-label">{t('admin.total')}</span>
          <span className="stat-value">{stats.total}</span>
        </div>
        <div className="stat-item complete">
          <span className="stat-label">{t('admin.complete')}</span>
          <span className="stat-value">{stats.complete}</span>
        </div>
        <div className="stat-item partial">
          <span className="stat-label">{t('admin.partial')}</span>
          <span className="stat-value">{stats.partial}</span>
        </div>
        <div className="stat-item missing">
          <span className="stat-label">{t('admin.missing')}</span>
          <span className="stat-value">{stats.missing}</span>
        </div>
        <div className="stat-item">
          <span className="stat-label">{t('admin.completion')}</span>
          <span className="stat-value">
            {stats.total > 0 ? Math.round((stats.complete / stats.total) * 100) : 0}%
          </span>
        </div>
      </div>

      <div className="translation-actions">
        <button onClick={handleExport} className="export-button">
          {t('common.export')}
        </button>
        <label className="import-button">
          {t('common.import')}
          <input
            type="file"
            accept=".json"
            onChange={handleImport}
            style={{ display: 'none' }}
          />
        </label>
      </div>

      <div className="translation-list">
        {loading ? (
          <div className="loading-state">{t('common.loading')}</div>
        ) : (
          <div className="translation-table">
            <div className="table-header">
              <div className="column-key">{t('admin.key')}</div>
              <div className="column-value">{t('admin.value')}</div>
              <div className="column-status">{t('admin.status')}</div>
              <div className="column-actions">{t('admin.actions')}</div>
            </div>
            
            {filteredTranslations.map(translation => (
              <div key={translation.id} className="table-row">
                <div className="column-key">
                  <div className="key-text">{translation.key}</div>
                  {translation.description && (
                    <div className="key-description">{translation.description}</div>
                  )}
                  <div className="key-meta">
                    {translation.pluralizable && (
                      <span className="meta-tag">Plural</span>
                    )}
                    {translation.genderizable && (
                      <span className="meta-tag">Gender</span>
                    )}
                  </div>
                </div>
                
                <div className="column-value">
                  <div className="value-text">
                    {translation.values[selectedLanguage] || (
                      <span className="empty-value">{t('admin.no_translation')}</span>
                    )}
                  </div>
                </div>
                
                <div className="column-status">
                  <span className={`status-badge ${getTranslationStatus(translation)}`}>
                    {t(`admin.${getTranslationStatus(translation)}`)}
                  </span>
                </div>
                
                <div className="column-actions">
                  <button
                    onClick={() => handleEdit(translation)}
                    className="edit-button"
                    aria-label={t('common.edit')}
                  >
                    {t('common.edit')}
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {isEditing && selectedKey && (
        <div className="edit-modal-overlay">
          <div className="edit-modal">
            <div className="edit-modal-header">
              <h3>{t('admin.edit_translation')}</h3>
              <button
                onClick={() => setIsEditing(false)}
                className="close-button"
                aria-label={t('common.close')}
              >
                ×
              </button>
            </div>
            
            <div className="edit-modal-content">
              <div className="edit-field">
                <label>{t('admin.key')}</label>
                <div className="key-display">{selectedKey.key}</div>
              </div>
              
              {selectedKey.description && (
                <div className="edit-field">
                  <label>{t('admin.description')}</label>
                  <div className="description-display">{selectedKey.description}</div>
                </div>
              )}
              
              <div className="edit-field">
                <label>
                  {t('admin.translation_for')} {availableLanguages.find(l => l.code === selectedLanguage)?.nativeName}
                </label>
                <textarea
                  value={editingValue}
                  onChange={(e) => setEditingValue(e.target.value)}
                  rows={4}
                  className="translation-input"
                />
              </div>
              
              <div className="reference-translations">
                <h4>{t('admin.reference_translations')}</h4>
                {availableLanguages
                  .filter(lang => lang.code !== selectedLanguage && selectedKey.values[lang.code])
                  .map(lang => (
                    <div key={lang.code} className="reference-item">
                      <span className="reference-lang">{lang.nativeName}</span>
                      <span className="reference-value">{selectedKey.values[lang.code]}</span>
                    </div>
                  ))}
              </div>
            </div>
            
            <div className="edit-modal-actions">
              <button onClick={() => setIsEditing(false)} className="cancel-button">
                {t('common.cancel')}
              </button>
              <button onClick={handleSave} className="save-button">
                {t('common.save')}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default TranslationManager;