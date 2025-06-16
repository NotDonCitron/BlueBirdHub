import React, { useState, useEffect } from 'react';
import { useApi } from '../../contexts/ApiContext';
import './AIContentAssignment.css';

interface ContentItem {
  id: string;
  text: string;
  type: 'task' | 'note' | 'file' | 'document' | 'general';
  tags: string[];
}

interface AIAnalysis {
  category: string;
  priority: string;
  sentiment: {
    label: string;
    score: number;
  };
  keywords: string[];
  entities: {
    emails: string[];
    phones: string[];
    urls: string[];
  };
  ml_category?: {
    prediction: string;
    confidence: number;
  };
  ml_priority?: {
    prediction: string;
    confidence: number;
  };
}

interface ScanStatus {
  scanning: boolean;
  progress: number;
  stats: {
    total_files: number;
    processed_files: number;
    new_files: number;
    updated_files: number;
    errors: number;
    categories: Record<string, number>;
  };
}

interface FileInfo {
  id: number;
  filename: string;
  category?: string;
  description?: string;
  similarity_score?: number;
}

interface CompatibilityFactors {
  factors: {
    category_match: number;
    priority_match: number;
    content_type_match: number;
    keyword_match: number;
    theme_alignment: number;
    tag_relevance: number;
  };
  total_score: number;
  recommendation: string;
  recommendation_text: string;
  detailed_reasoning: string;
}

interface WorkspaceRecommendation {
  workspace_id: number;
  workspace_name: string;
  workspace_theme: string;
  compatibility_score: number;
  recommendation: string;
  reasoning: string;
}

interface OrganizationSuggestion {
  type: string;
  suggestion: string;
  reason: string;
  confidence: number;
}

interface AssignmentResult {
  workspace_id: number;
  workspace_name: string;
  content_analysis: any;
  compatibility_factors: CompatibilityFactors;
  overall_compatibility: number;
  recommendation: string;
  reasoning: string;
  organization_suggestions: OrganizationSuggestion[];
  alternative_workspaces: WorkspaceRecommendation[];
}

const AIContentAssignment: React.FC = () => {
  const { makeApiRequest } = useApi();
  const [workspaces, setWorkspaces] = useState<any[]>([]);
  const [selectedWorkspace, setSelectedWorkspace] = useState<number | null>(null);
  const [contentItems, setContentItems] = useState<ContentItem[]>([]);
  const [newContent, setNewContent] = useState<ContentItem>({
    id: '',
    text: '',
    type: 'general',
    tags: []
  });
  const [assignmentResult, setAssignmentResult] = useState<AssignmentResult | null>(null);
  const [bulkResults, setBulkResults] = useState<any>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [activeTab, setActiveTab] = useState<'analyze' | 'scan' | 'organize'>('analyze');
  
  // New AI Features State
  const [analysisText, setAnalysisText] = useState('');
  const [analysis, setAnalysis] = useState<AIAnalysis | null>(null);
  const [analyzing, setAnalyzing] = useState(false);
  const [scanDirectory, setScanDirectory] = useState('');
  const [scanStatus, setScanStatus] = useState<ScanStatus | null>(null);
  const [scanning, setScanning] = useState(false);
  const [similarFiles, setSimilarFiles] = useState<FileInfo[]>([]);
  const [searchText, setSearchText] = useState('');
  const [organizationSuggestions, setOrganizationSuggestions] = useState<any[]>([]);

  useEffect(() => {
    loadWorkspaces();
  }, []);

  const loadWorkspaces = async () => {
    try {
      const response = await makeApiRequest('/workspaces/', 'GET');
      setWorkspaces(response);
    } catch (error) {
      console.error('Failed to load workspaces:', error);
    }
  };

  const handleAddContent = () => {
    if (newContent.text.trim()) {
      const contentWithId = {
        ...newContent,
        id: Date.now().toString(),
        tags: newContent.tags.filter(tag => tag.trim() !== '')
      };
      setContentItems([...contentItems, contentWithId]);
      setNewContent({ id: '', text: '', type: 'general', tags: [] });
    }
  };

  const handleRemoveContent = (id: string) => {
    setContentItems(contentItems.filter(item => item.id !== id));
  };

  const handleSingleAssignment = async () => {
    if (!selectedWorkspace || !newContent.text.trim()) return;

    setIsLoading(true);
    try {
      const response = await makeApiRequest(
        `/workspaces/${selectedWorkspace}/assign-content`,
        'POST',
        {
          text: newContent.text,
          type: newContent.type,
          tags: newContent.tags.filter(tag => tag.trim() !== '')
        }
      );
      setAssignmentResult(response);
    } catch (error) {
      console.error('Assignment failed:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const handleBulkAssignment = async () => {
    if (contentItems.length === 0) return;

    setIsLoading(true);
    try {
      const response = await makeApiRequest('/workspaces/bulk-assign-content', 'POST', contentItems);
      setBulkResults(response);
    } catch (error) {
      console.error('Bulk assignment failed:', error);
    } finally {
      setIsLoading(false);
    }
  };

  // New AI Methods
  const analyzeText = async () => {
    if (!analysisText.trim()) return;
    
    setAnalyzing(true);
    try {
      const result = await makeApiRequest('/ai/enhanced/analyze-text', 'POST', {
        text: analysisText
      });
      setAnalysis(result);
    } catch (error) {
      console.error('Error analyzing text:', error);
    } finally {
      setAnalyzing(false);
    }
  };

  const startDirectoryScan = async () => {
    if (!scanDirectory.trim()) return;
    
    setScanning(true);
    try {
      const result = await makeApiRequest('/ai/scan-directory', 'POST', {
        directory_path: scanDirectory,
        user_id: 1, // TODO: Get actual user ID
        recursive: true
      });
      setScanStatus(result);
    } catch (error) {
      console.error('Error starting scan:', error);
      setScanning(false);
    }
  };

  const findSimilarFiles = async () => {
    if (!searchText.trim()) return;
    
    try {
      // First get some sample files (in real app, this would come from the file database)
      const sampleFiles = [
        { id: 1, filename: 'project-proposal.pdf', category: 'document', description: 'Business proposal for new client' },
        { id: 2, filename: 'meeting-notes.txt', category: 'document', description: 'Notes from team meeting' },
        { id: 3, filename: 'budget-analysis.xlsx', category: 'document', description: 'Financial analysis spreadsheet' }
      ];
      
      const result = await makeApiRequest('/ai/find-similar', 'POST', {
        target_text: searchText,
        file_database: sampleFiles,
        limit: 5
      });
      setSimilarFiles(result.similar_files || []);
    } catch (error) {
      console.error('Error finding similar files:', error);
    }
  };

  const suggestOrganization = async () => {
    try {
      // Sample file data for organization suggestion
      const sampleFiles = [
        { filename: 'project-plan.pdf', category: 'work', description: 'Project planning document' },
        { filename: 'vacation-photos.jpg', category: 'personal', description: 'Family vacation pictures' },
        { filename: 'budget.xlsx', category: 'finance', description: 'Monthly budget spreadsheet' },
        { filename: 'recipe.txt', category: 'personal', description: 'Cooking recipe collection' },
        { filename: 'presentation.pptx', category: 'work', description: 'Client presentation slides' }
      ];
      
      const result = await makeApiRequest('/ai/suggest-organization', 'POST', {
        files: sampleFiles
      });
      setOrganizationSuggestions(result.suggestions || []);
    } catch (error) {
      console.error('Error getting organization suggestions:', error);
    }
  };

  const getRecommendationColor = (recommendation: string) => {
    switch (recommendation) {
      case 'highly_recommended': return '#10b981';
      case 'recommended': return '#3b82f6';
      case 'consider': return '#f59e0b';
      case 'not_recommended': return '#ef4444';
      default: return '#6b7280';
    }
  };

  const renderCompatibilityFactors = (factors: CompatibilityFactors) => (
    <div className="compatibility-factors">
      <h4>Compatibility Analysis</h4>
      <div className="overall-score" style={{ backgroundColor: getRecommendationColor(factors.recommendation) }}>
        <span className="score">{(factors.total_score * 100).toFixed(1)}%</span>
        <span className="recommendation">{factors.recommendation_text}</span>
      </div>
      
      <div className="factor-breakdown">
        {Object.entries(factors.factors).map(([factor, score]) => (
          <div key={factor} className="factor-item">
            <span className="factor-name">{factor.replace('_', ' ')}</span>
            <div className="factor-bar">
              <div 
                className="factor-fill" 
                style={{ width: `${score * 100}%`, backgroundColor: getRecommendationColor(factors.recommendation) }}
              />
            </div>
            <span className="factor-score">{(score * 100).toFixed(0)}%</span>
          </div>
        ))}
      </div>
      
      <div className="reasoning">
        <strong>Reasoning:</strong> {factors.detailed_reasoning}
      </div>
    </div>
  );

  const renderOrganizationSuggestions = (suggestions: OrganizationSuggestion[]) => (
    <div className="organization-suggestions">
      <h4>Organization Suggestions</h4>
      {suggestions.map((suggestion, index) => (
        <div key={index} className="suggestion-item">
          <div className="suggestion-header">
            <span className="suggestion-type">{suggestion.type.replace('_', ' ')}</span>
            <span className="confidence">{(suggestion.confidence * 100).toFixed(0)}% confidence</span>
          </div>
          <div className="suggestion-content">
            <strong>{suggestion.suggestion}</strong>
            <p>{suggestion.reason}</p>
          </div>
        </div>
      ))}
    </div>
  );

  const renderAlternativeWorkspaces = (alternatives: WorkspaceRecommendation[]) => (
    <div className="alternative-workspaces">
      <h4>Alternative Workspaces</h4>
      {alternatives.map((alt, index) => (
        <div key={index} className="alternative-item">
          <div className="alt-header">
            <span className="workspace-name">{alt.workspace_name}</span>
            <span className="compatibility-score">
              {(alt.compatibility_score * 100).toFixed(1)}%
            </span>
          </div>
          <div className="alt-details">
            <span className="theme">Theme: {alt.workspace_theme}</span>
            <p>{alt.reasoning}</p>
          </div>
        </div>
      ))}
    </div>
  );

  // New render methods for AI features
  const renderAnalysisTab = () => (
    <div className="ai-analysis-tab">
      <h3>🧠 AI Text Analysis</h3>
      <div className="analysis-input">
        <textarea
          value={analysisText}
          onChange={(e) => setAnalysisText(e.target.value)}
          placeholder="Enter text to analyze (task description, file content, etc.)"
          rows={4}
          className="analysis-textarea"
        />
        <button
          onClick={analyzeText}
          disabled={analyzing || !analysisText.trim()}
          className="btn btn-primary"
        >
          {analyzing ? 'Analyzing...' : 'Analyze Text'}
        </button>
      </div>
      
      {analysis && (
        <div className="analysis-results">
          <div className="result-grid">
            <div className="result-card">
              <h4>📂 Category</h4>
              <div className="category-result">
                <span className="category-badge">{analysis.category}</span>
                {analysis.ml_category && (
                  <div className="ml-prediction">
                    <small>ML: {analysis.ml_category.prediction} ({Math.round(analysis.ml_category.confidence * 100)}%)</small>
                  </div>
                )}
              </div>
            </div>
            
            <div className="result-card">
              <h4>⚡ Priority</h4>
              <div className="priority-result">
                <span className={`priority-badge priority-${analysis.priority}`}>
                  {analysis.priority}
                </span>
                {analysis.ml_priority && (
                  <div className="ml-prediction">
                    <small>ML: {analysis.ml_priority.prediction} ({Math.round(analysis.ml_priority.confidence * 100)}%)</small>
                  </div>
                )}
              </div>
            </div>
            
            <div className="result-card">
              <h4>😊 Sentiment</h4>
              <div className="sentiment-result">
                <span className={`sentiment-badge sentiment-${analysis.sentiment.label}`}>
                  {analysis.sentiment.label}
                </span>
                <small>Score: {analysis.sentiment.score.toFixed(2)}</small>
              </div>
            </div>
            
            <div className="result-card">
              <h4>🔍 Keywords</h4>
              <div className="keywords-result">
                {analysis.keywords.slice(0, 5).map((keyword, index) => (
                  <span key={index} className="keyword-tag">{keyword}</span>
                ))}
              </div>
            </div>
          </div>
          
          {(analysis.entities.emails.length > 0 || analysis.entities.phones.length > 0 || analysis.entities.urls.length > 0) && (
            <div className="entities-section">
              <h4>📋 Extracted Entities</h4>
              <div className="entities-grid">
                {analysis.entities.emails.length > 0 && (
                  <div className="entity-group">
                    <strong>📧 Emails:</strong>
                    {analysis.entities.emails.map((email, index) => (
                      <span key={index} className="entity-item">{email}</span>
                    ))}
                  </div>
                )}
                {analysis.entities.phones.length > 0 && (
                  <div className="entity-group">
                    <strong>📞 Phones:</strong>
                    {analysis.entities.phones.map((phone, index) => (
                      <span key={index} className="entity-item">{phone}</span>
                    ))}
                  </div>
                )}
                {analysis.entities.urls.length > 0 && (
                  <div className="entity-group">
                    <strong>🔗 URLs:</strong>
                    {analysis.entities.urls.map((url, index) => (
                      <span key={index} className="entity-item">{url}</span>
                    ))}
                  </div>
                )}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );

  const renderScanTab = () => (
    <div className="ai-scan-tab">
      <h3>🔍 AI File Scanner</h3>
      <div className="scan-input">
        <input
          type="text"
          value={scanDirectory}
          onChange={(e) => setScanDirectory(e.target.value)}
          placeholder="Enter directory path to scan (e.g., /Users/username/Documents)"
          className="scan-directory-input"
        />
        <button
          onClick={startDirectoryScan}
          disabled={scanning || !scanDirectory.trim()}
          className="btn btn-primary"
        >
          {scanning ? 'Scanning...' : 'Start Scan'}
        </button>
      </div>
      
      {scanStatus && (
        <div className="scan-results">
          <div className="scan-progress">
            <div className="progress-bar">
              <div 
                className="progress-fill" 
                style={{ width: `${scanStatus.progress}%` }}
              ></div>
            </div>
            <span className="progress-text">{scanStatus.progress}%</span>
          </div>
          
          <div className="scan-stats">
            <div className="stat-grid">
              <div className="stat-item">
                <span className="stat-value">{scanStatus.stats.total_files}</span>
                <span className="stat-label">Total Files</span>
              </div>
              <div className="stat-item">
                <span className="stat-value">{scanStatus.stats.processed_files}</span>
                <span className="stat-label">Processed</span>
              </div>
              <div className="stat-item">
                <span className="stat-value">{scanStatus.stats.new_files}</span>
                <span className="stat-label">New Files</span>
              </div>
              <div className="stat-item">
                <span className="stat-value">{scanStatus.stats.updated_files}</span>
                <span className="stat-label">Updated</span>
              </div>
              <div className="stat-item">
                <span className="stat-value">{scanStatus.stats.errors}</span>
                <span className="stat-label">Errors</span>
              </div>
            </div>
            
            {Object.keys(scanStatus.stats.categories).length > 0 && (
              <div className="categories-breakdown">
                <h4>📂 Categories Found</h4>
                <div className="category-list">
                  {Object.entries(scanStatus.stats.categories).map(([category, count]) => (
                    <div key={category} className="category-stat">
                      <span className="category-name">{category}</span>
                      <span className="category-count">{count}</span>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );

  const renderOrganizeTab = () => (
    <div className="ai-organize-tab">
      <h3>🗂️ AI Organization Assistant</h3>
      
      <div className="organize-section">
        <h4>🔍 Find Similar Files</h4>
        <div className="similarity-search">
          <input
            type="text"
            value={searchText}
            onChange={(e) => setSearchText(e.target.value)}
            placeholder="Describe what you're looking for..."
            className="search-input"
          />
          <button
            onClick={findSimilarFiles}
            disabled={!searchText.trim()}
            className="btn btn-secondary"
          >
            Find Similar
          </button>
        </div>
        
        {similarFiles.length > 0 && (
          <div className="similar-files">
            <h5>📄 Similar Files Found</h5>
            {similarFiles.map((file) => (
              <div key={file.id} className="similar-file-item">
                <span className="file-name">{file.filename}</span>
                <span className="file-category">{file.category}</span>
                <span className="similarity-score">
                  {Math.round((file.similarity_score || 0) * 100)}% match
                </span>
              </div>
            ))}
          </div>
        )}
      </div>
      
      <div className="organize-section">
        <h4>🏗️ Workspace Organization Suggestions</h4>
        <button
          onClick={suggestOrganization}
          className="btn btn-primary"
        >
          Get Organization Suggestions
        </button>
        
        {organizationSuggestions.length > 0 && (
          <div className="organization-suggestions">
            <h5>💡 Suggested Workspaces</h5>
            {organizationSuggestions.map((suggestion, index) => (
              <div key={index} className="suggestion-item">
                <h6>{suggestion.workspace_name}</h6>
                <p>{suggestion.description}</p>
                <div className="suggestion-stats">
                  <span className="file-count">{suggestion.file_count} files</span>
                  <span className="category-badge">{suggestion.category}</span>
                </div>
                <div className="suggestion-files">
                  {suggestion.files.slice(0, 3).map((file: any, fileIndex: number) => (
                    <span key={fileIndex} className="preview-file">{file.filename}</span>
                  ))}
                  {suggestion.files.length > 3 && (
                    <span className="more-files">+{suggestion.files.length - 3} more</span>
                  )}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );

  return (
    <div className="ai-content-assignment">
      <div className="assignment-header">
        <h2>🤖 AI Assistant</h2>
        <p>Intelligent content analysis and organization powered by local AI</p>
      </div>

      <div className="assignment-tabs">
        <button 
          className={`tab ${activeTab === 'analyze' ? 'active' : ''}`}
          onClick={() => setActiveTab('analyze')}
        >
          📝 Text Analysis
        </button>
        <button 
          className={`tab ${activeTab === 'scan' ? 'active' : ''}`}
          onClick={() => setActiveTab('scan')}
        >
          🔍 File Scanner
        </button>
        <button 
          className={`tab ${activeTab === 'organize' ? 'active' : ''}`}
          onClick={() => setActiveTab('organize')}
        >
          🗂️ Organization
        </button>
      </div>

      <div className="ai-content">
        {activeTab === 'analyze' && renderAnalysisTab()}
        {activeTab === 'scan' && renderScanTab()}
        {activeTab === 'organize' && renderOrganizeTab()}
      </div>
    </div>
  );
};

export default AIContentAssignment;