import React, { useState } from 'react';
import { useApi } from '../../contexts/ApiContext';
import './AIAssistant.css';

interface AnalysisResult {
  entities?: {
    emails: string[];
    phones: string[];
    urls: string[];
  };
  sentiment?: {
    label: string;
    score: number;
  };
  priority?: string;
  category?: string;
  keywords?: string[];
  tags?: string[];
}

const AIAssistant: React.FC = () => {
  const [inputText, setInputText] = useState('');
  const [analysisResult, setAnalysisResult] = useState<AnalysisResult | null>(null);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [activeTab, setActiveTab] = useState<'analyze' | 'categorize'>('analyze');
  const { makeApiRequest } = useApi();

  const handleAnalyze = async () => {
    if (!inputText.trim() || !makeApiRequest) return;

    setIsAnalyzing(true);
    try {
      const response = await makeApiRequest('/ai/analyze-text', 'POST', {
        text: inputText
      });

      // Also get tag suggestions
      const tagsResponse = await makeApiRequest('/ai/suggest-tags', 'POST', {
        text: inputText
      });

      setAnalysisResult({
        ...response,
        tags: tagsResponse.tags
      });
    } catch (error) {
      console.error('Analysis failed:', error);
      setAnalysisResult(null);
    } finally {
      setIsAnalyzing(false);
    }
  };

  const handleCategorizeFile = async () => {
    if (!inputText.trim() || !makeApiRequest) return;

    setIsAnalyzing(true);
    try {
      const response = await makeApiRequest('/ai/categorize-file', 'POST', {
        filename: inputText,
        content_preview: ''
      });

      setAnalysisResult({
        category: response.category,
        tags: response.tags,
        priority: response.priority
      });
    } catch (error) {
      console.error('Categorization failed:', error);
      setAnalysisResult(null);
    } finally {
      setIsAnalyzing(false);
    }
  };

  const renderAnalysisResult = () => {
    if (!analysisResult) return null;

    return (
      <div className="analysis-result">
        <h3>Analysis Results</h3>
        
        {analysisResult.sentiment && (
          <div className="result-section">
            <h4>Sentiment</h4>
            <div className={`sentiment-badge ${analysisResult.sentiment.label}`}>
              {analysisResult.sentiment.label}
              <span className="sentiment-score">
                ({analysisResult.sentiment.score.toFixed(2)})
              </span>
            </div>
          </div>
        )}

        {analysisResult.priority && (
          <div className="result-section">
            <h4>Priority</h4>
            <div className={`priority-badge priority-${analysisResult.priority}`}>
              {analysisResult.priority}
            </div>
          </div>
        )}

        {analysisResult.category && (
          <div className="result-section">
            <h4>Category</h4>
            <div className="category-badge">{analysisResult.category}</div>
          </div>
        )}

        {analysisResult.keywords && analysisResult.keywords.length > 0 && (
          <div className="result-section">
            <h4>Keywords</h4>
            <div className="keywords-list">
              {analysisResult.keywords.map((keyword, index) => (
                <span key={index} className="keyword-tag">{keyword}</span>
              ))}
            </div>
          </div>
        )}

        {analysisResult.tags && analysisResult.tags.length > 0 && (
          <div className="result-section">
            <h4>Suggested Tags</h4>
            <div className="tags-list">
              {analysisResult.tags.map((tag, index) => (
                <span key={index} className="tag">{tag}</span>
              ))}
            </div>
          </div>
        )}

        {analysisResult.entities && (
          <div className="result-section">
            <h4>Extracted Entities</h4>
            {analysisResult.entities.emails.length > 0 && (
              <div className="entity-group">
                <strong>Emails:</strong> {analysisResult.entities.emails.join(', ')}
              </div>
            )}
            {analysisResult.entities.phones.length > 0 && (
              <div className="entity-group">
                <strong>Phones:</strong> {analysisResult.entities.phones.join(', ')}
              </div>
            )}
            {analysisResult.entities.urls.length > 0 && (
              <div className="entity-group">
                <strong>URLs:</strong> {analysisResult.entities.urls.join(', ')}
              </div>
            )}
          </div>
        )}
      </div>
    );
  };

  return (
    <div className="ai-assistant">
      <div className="ai-header">
        <h2>AI Assistant</h2>
        <p>Use AI to analyze text, categorize files, and get intelligent suggestions.</p>
      </div>

      <div className="ai-tabs">
        <button
          className={`tab ${activeTab === 'analyze' ? 'active' : ''}`}
          onClick={() => setActiveTab('analyze')}
        >
          Text Analysis
        </button>
        <button
          className={`tab ${activeTab === 'categorize' ? 'active' : ''}`}
          onClick={() => setActiveTab('categorize')}
        >
          File Categorization
        </button>
      </div>

      <div className="ai-content">
        {activeTab === 'analyze' ? (
          <>
            <div className="input-section">
              <label htmlFor="text-input">Enter text to analyze:</label>
              <textarea
                id="text-input"
                className="text-input"
                value={inputText}
                onChange={(e) => setInputText(e.target.value)}
                placeholder="Type or paste your text here..."
                rows={6}
              />
              <button
                className="analyze-button"
                onClick={handleAnalyze}
                disabled={!inputText.trim() || isAnalyzing}
              >
                {isAnalyzing ? 'Analyzing...' : 'Analyze Text'}
              </button>
            </div>
          </>
        ) : (
          <>
            <div className="input-section">
              <label htmlFor="filename-input">Enter filename to categorize:</label>
              <input
                id="filename-input"
                type="text"
                className="filename-input"
                value={inputText}
                onChange={(e) => setInputText(e.target.value)}
                placeholder="e.g., project_report.pdf"
              />
              <button
                className="analyze-button"
                onClick={handleCategorizeFile}
                disabled={!inputText.trim() || isAnalyzing}
              >
                {isAnalyzing ? 'Categorizing...' : 'Categorize File'}
              </button>
            </div>
          </>
        )}

        {renderAnalysisResult()}
      </div>

      <div className="ai-footer">
        <p className="privacy-note">
          🔒 All analysis is performed locally for your privacy
        </p>
      </div>
    </div>
  );
};

export default AIAssistant;