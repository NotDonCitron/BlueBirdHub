// Example: React Component für AI-Features
// Füge das zu deinem React-Frontend hinzu

import { useState } from 'react';

const AIFeatures = () => {
  const [text, setText] = useState('');
  const [summary, setSummary] = useState('');
  const [loading, setLoading] = useState(false);
    
  const handleSummarize = async () => {
    setLoading(true);
    try {
      const response = await fetch('http://127.0.0.1:8000/api/ai/summarize', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ text, length: 'medium' })
      });
      const data = await response.json();
      setSummary(data.summary);
    } catch (error) {
      console.error('Error:', error);
    }
    setLoading(false);
  };
    
  return (
    <div className="ai-features">
      <h3>🧠 AI Text-Zusammenfassung</h3>
      <textarea 
        value={text}
        onChange={(e) => setText(e.target.value)}
        placeholder="Text hier eingeben..."
        rows={5}
        style={{ width: '100%', marginBottom: '10px' }}
      />
      <button 
        onClick={handleSummarize}
        disabled={loading || !text}
        style={{ 
          background: '#2563eb', 
          color: 'white', 
          padding: '10px 20px',
          border: 'none',
          borderRadius: '4px',
          cursor: loading ? 'wait' : 'pointer'
        }}
      >
        {loading ? 'Wird verarbeitet...' : 'Zusammenfassen'}
      </button>
      {summary && (
        <div style={{ 
          marginTop: '20px', 
          padding: '15px', 
          background: '#f0f9ff',
          borderRadius: '4px',
          border: '1px solid #bfdbfe'
        }}>
          <h4>📝 Zusammenfassung:</h4>
          <p>{summary}</p>
        </div>
      )}
    </div>
  );
};

export default AIFeatures;
