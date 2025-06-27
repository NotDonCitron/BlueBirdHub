/**
 * Conflict Resolution UI Component
 * Provides interface for users to resolve sync conflicts
 */

import React, { useState, useEffect } from 'react';
import { conflictResolver, ConflictData, ResolutionStrategy } from '../../core/offline/conflict/ConflictResolver';
import { syncManager } from '../../core/offline/sync/SyncManager';
import { offlineStorage } from '../../core/offline/OfflineStorage';
import './ConflictResolver.css';

interface ConflictResolverProps {
  isOpen: boolean;
  onClose: () => void;
  onResolved: (conflictId: string) => void;
}

interface ConflictWithSeverity extends ConflictData {
  severity: 'low' | 'medium' | 'high';
  summary: string;
}

export const ConflictResolverComponent: React.FC<ConflictResolverProps> = ({
  isOpen,
  onClose,
  onResolved
}) => {
  const [conflicts, setConflicts] = useState<ConflictWithSeverity[]>([]);
  const [selectedConflict, setSelectedConflict] = useState<ConflictWithSeverity | null>(null);
  const [resolution, setResolution] = useState<'local' | 'remote' | 'merge'>('local');
  const [fieldResolutions, setFieldResolutions] = useState<Record<string, 'local' | 'remote' | any>>({});
  const [isResolving, setIsResolving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (isOpen) {
      loadConflicts();
    }
  }, [isOpen]);

  const loadConflicts = async () => {
    try {
      const rawConflicts = await offlineStorage.getConflicts();
      const conflictsWithDetails = rawConflicts.map(conflict => ({
        ...conflict,
        severity: conflictResolver.getConflictSeverity(conflict),
        summary: conflictResolver.generateConflictSummary(conflict)
      }));
      
      // Sort by severity (high first) then by timestamp
      conflictsWithDetails.sort((a, b) => {
        const severityOrder = { high: 3, medium: 2, low: 1 };
        const severityDiff = severityOrder[b.severity] - severityOrder[a.severity];
        if (severityDiff !== 0) return severityDiff;
        return b.timestamp - a.timestamp;
      });

      setConflicts(conflictsWithDetails);
      
      if (conflictsWithDetails.length > 0 && !selectedConflict) {
        setSelectedConflict(conflictsWithDetails[0]);
        initializeFieldResolutions(conflictsWithDetails[0]);
      }
    } catch (error) {
      console.error('Failed to load conflicts:', error);
      setError('Fehler beim Laden der Konflikte');
    }
  };

  const initializeFieldResolutions = (conflict: ConflictWithSeverity) => {
    const resolutions: Record<string, 'local' | 'remote'> = {};
    conflict.conflictFields.forEach(field => {
      resolutions[field] = 'local'; // Default to local
    });
    setFieldResolutions(resolutions);
  };

  const handleConflictSelect = (conflict: ConflictWithSeverity) => {
    setSelectedConflict(conflict);
    initializeFieldResolutions(conflict);
    setResolution('local');
    setError(null);
  };

  const handleResolutionChange = (newResolution: 'local' | 'remote' | 'merge') => {
    setResolution(newResolution);
    
    if (newResolution === 'local' && selectedConflict) {
      const resolutions: Record<string, 'local'> = {};
      selectedConflict.conflictFields.forEach(field => {
        resolutions[field] = 'local';
      });
      setFieldResolutions(resolutions);
    } else if (newResolution === 'remote' && selectedConflict) {
      const resolutions: Record<string, 'remote'> = {};
      selectedConflict.conflictFields.forEach(field => {
        resolutions[field] = 'remote';
      });
      setFieldResolutions(resolutions);
    }
  };

  const handleFieldResolutionChange = (field: string, value: 'local' | 'remote') => {
    setFieldResolutions(prev => ({
      ...prev,
      [field]: value
    }));
  };

  const handleResolve = async () => {
    if (!selectedConflict) return;

    setIsResolving(true);
    setError(null);

    try {
      const strategy: ResolutionStrategy = {
        strategy: resolution === 'merge' ? 'merge' : 'user_choice',
        userChoice: resolution === 'merge' ? undefined : resolution,
        fieldResolutions: resolution === 'merge' ? fieldResolutions : undefined
      };

      const success = await syncManager.resolveConflict(selectedConflict.id, strategy);
      
      if (success) {
        onResolved(selectedConflict.id);
        await loadConflicts(); // Refresh conflicts list
        
        // Select next conflict if available
        const remainingConflicts = conflicts.filter(c => c.id !== selectedConflict.id);
        if (remainingConflicts.length > 0) {
          setSelectedConflict(remainingConflicts[0]);
          initializeFieldResolutions(remainingConflicts[0]);
        } else {
          setSelectedConflict(null);
          onClose(); // Close if no more conflicts
        }
      } else {
        setError('Fehler beim Lösen des Konflikts');
      }
    } catch (error) {
      console.error('Failed to resolve conflict:', error);
      setError('Fehler beim Lösen des Konflikts');
    } finally {
      setIsResolving(false);
    }
  };

  const renderValue = (value: any, maxLength = 100) => {
    if (value === null || value === undefined) {
      return <span className="value-null">null</span>;
    }
    
    if (typeof value === 'boolean') {
      return <span className={`value-boolean ${value}`}>{value.toString()}</span>;
    }
    
    if (typeof value === 'number') {
      return <span className="value-number">{value}</span>;
    }
    
    if (typeof value === 'string') {
      const truncated = value.length > maxLength ? value.substring(0, maxLength) + '...' : value;
      return <span className="value-string" title={value}>{truncated}</span>;
    }
    
    if (Array.isArray(value)) {
      return <span className="value-array">[{value.length} Elemente]</span>;
    }
    
    if (typeof value === 'object') {
      return <span className="value-object">{JSON.stringify(value, null, 2)}</span>;
    }
    
    return <span className="value-unknown">{String(value)}</span>;
  };

  const getSeverityColor = (severity: 'low' | 'medium' | 'high') => {
    switch (severity) {
      case 'high': return 'red';
      case 'medium': return 'yellow';
      case 'low': return 'blue';
    }
  };

  if (!isOpen) return null;

  return (
    <div className="conflict-resolver-overlay">
      <div className="conflict-resolver">
        <div className="conflict-resolver__header">
          <h2>Sync-Konflikte lösen</h2>
          <button className="close-button" onClick={onClose}>×</button>
        </div>

        {error && (
          <div className="error-message">
            {error}
          </div>
        )}

        <div className="conflict-resolver__content">
          {conflicts.length === 0 ? (
            <div className="no-conflicts">
              <div className="no-conflicts__icon">✅</div>
              <h3>Keine Konflikte gefunden</h3>
              <p>Alle Daten sind erfolgreich synchronisiert.</p>
            </div>
          ) : (
            <div className="conflicts-layout">
              {/* Conflicts List */}
              <div className="conflicts-list">
                <div className="conflicts-list__header">
                  <h3>Konflikte ({conflicts.length})</h3>
                </div>
                
                <div className="conflicts-list__items">
                  {conflicts.map(conflict => (
                    <div
                      key={conflict.id}
                      className={`conflict-item ${selectedConflict?.id === conflict.id ? 'selected' : ''}`}
                      onClick={() => handleConflictSelect(conflict)}
                    >
                      <div className="conflict-item__header">
                        <span className={`severity-badge severity-${conflict.severity}`}>
                          {conflict.severity.toUpperCase()}
                        </span>
                        <span className="entity-type">{conflict.entityType}</span>
                      </div>
                      
                      <div className="conflict-item__summary">
                        {conflict.summary}
                      </div>
                      
                      <div className="conflict-item__meta">
                        <span className="timestamp">
                          {new Date(conflict.timestamp).toLocaleString()}
                        </span>
                        <span className="fields-count">
                          {conflict.conflictFields.length} Felder
                        </span>
                      </div>
                    </div>
                  ))}
                </div>
              </div>

              {/* Conflict Details */}
              {selectedConflict && (
                <div className="conflict-details">
                  <div className="conflict-details__header">
                    <h3>Konflikt Details</h3>
                    <span className={`severity-badge severity-${selectedConflict.severity}`}>
                      {selectedConflict.severity.toUpperCase()}
                    </span>
                  </div>

                  <div className="resolution-strategy">
                    <h4>Auflösungsstrategie:</h4>
                    <div className="strategy-options">
                      <label className="strategy-option">
                        <input
                          type="radio"
                          value="local"
                          checked={resolution === 'local'}
                          onChange={(e) => handleResolutionChange(e.target.value as any)}
                        />
                        <span>Lokale Version verwenden</span>
                      </label>
                      
                      <label className="strategy-option">
                        <input
                          type="radio"
                          value="remote"
                          checked={resolution === 'remote'}
                          onChange={(e) => handleResolutionChange(e.target.value as any)}
                        />
                        <span>Server-Version verwenden</span>
                      </label>
                      
                      <label className="strategy-option">
                        <input
                          type="radio"
                          value="merge"
                          checked={resolution === 'merge'}
                          onChange={(e) => handleResolutionChange(e.target.value as any)}
                        />
                        <span>Manuell zusammenführen</span>
                      </label>
                    </div>
                  </div>

                  <div className="conflict-fields">
                    <h4>Konfliktfelder:</h4>
                    
                    {selectedConflict.conflictFields.map(field => (
                      <div key={field} className="field-conflict">
                        <div className="field-name">{field}</div>
                        
                        <div className="field-values">
                          <div className="value-option">
                            <div className="value-header">
                              <label>
                                {resolution === 'merge' && (
                                  <input
                                    type="radio"
                                    checked={fieldResolutions[field] === 'local'}
                                    onChange={() => handleFieldResolutionChange(field, 'local')}
                                  />
                                )}
                                <span className="value-label">Lokal:</span>
                              </label>
                            </div>
                            <div className="value-content local">
                              {renderValue(selectedConflict.localData[field])}
                            </div>
                          </div>
                          
                          <div className="value-option">
                            <div className="value-header">
                              <label>
                                {resolution === 'merge' && (
                                  <input
                                    type="radio"
                                    checked={fieldResolutions[field] === 'remote'}
                                    onChange={() => handleFieldResolutionChange(field, 'remote')}
                                  />
                                )}
                                <span className="value-label">Server:</span>
                              </label>
                            </div>
                            <div className="value-content remote">
                              {renderValue(selectedConflict.remoteData[field])}
                            </div>
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>

                  <div className="resolution-actions">
                    <button
                      className="resolve-button"
                      onClick={handleResolve}
                      disabled={isResolving}
                    >
                      {isResolving ? 'Löse Konflikt...' : 'Konflikt lösen'}
                    </button>
                    
                    <button
                      className="skip-button"
                      onClick={() => {
                        const nextConflict = conflicts.find(c => c.id !== selectedConflict.id);
                        if (nextConflict) {
                          setSelectedConflict(nextConflict);
                          initializeFieldResolutions(nextConflict);
                        }
                      }}
                      disabled={conflicts.length <= 1}
                    >
                      Überspringen
                    </button>
                  </div>
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default ConflictResolverComponent;