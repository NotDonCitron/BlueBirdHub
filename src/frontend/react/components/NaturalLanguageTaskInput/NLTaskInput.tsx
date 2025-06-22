import React, { useState, useRef, useEffect } from 'react';
import { apiClient } from '../../lib/api';
import './NLTaskInput.css';

interface ParsedTask {
  title: string;
  description?: string;
  priority: 'low' | 'medium' | 'high';
  dueDate?: string;
  workspace?: string;
  tags?: string[];
  confidence: number;
}

interface NLTaskInputProps {
  onTaskCreated?: (task: any) => void;
  placeholder?: string;
}

const NLTaskInput: React.FC<NLTaskInputProps> = ({
  onTaskCreated,
  placeholder = "Tell me what you need to do... (e.g., 'Remind me to call John about the project meeting tomorrow at 3pm')"
}) => {
  const [input, setInput] = useState('');
  const [isProcessing, setIsProcessing] = useState(false);
  const [parsedTask, setParsedTask] = useState<ParsedTask | null>(null);
  const [showPreview, setShowPreview] = useState(false);
  const [isListening, setIsListening] = useState(false);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  // Auto-resize textarea
  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
      textareaRef.current.style.height = `${textareaRef.current.scrollHeight}px`;
    }
  }, [input]);

  // Simple NLP parsing function (would be enhanced with real AI/NLP service)
  const parseNaturalLanguage = (text: string): ParsedTask => {
    const lowercaseText = text.toLowerCase();
    
    // Extract priority
    let priority: 'low' | 'medium' | 'high' = 'medium';
    if (lowercaseText.includes('urgent') || lowercaseText.includes('asap') || lowercaseText.includes('important')) {
      priority = 'high';
    } else if (lowercaseText.includes('low priority') || lowercaseText.includes('when possible')) {
      priority = 'low';
    }

    // Extract due date patterns
    let dueDate: string | undefined;
    const tomorrow = new Date();
    tomorrow.setDate(tomorrow.getDate() + 1);
    
    if (lowercaseText.includes('tomorrow')) {
      dueDate = tomorrow.toISOString().split('T')[0];
    } else if (lowercaseText.includes('today')) {
      dueDate = new Date().toISOString().split('T')[0];
    } else if (lowercaseText.includes('next week')) {
      const nextWeek = new Date();
      nextWeek.setDate(nextWeek.getDate() + 7);
      dueDate = nextWeek.toISOString().split('T')[0];
    }

    // Extract time patterns
    const timeMatch = text.match(/(\d{1,2}):?(\d{2})?\s*(am|pm)/i);
    if (timeMatch && dueDate) {
      let hours = parseInt(timeMatch[1]);
      const minutes = timeMatch[2] ? parseInt(timeMatch[2]) : 0;
      const isPM = timeMatch[3]?.toLowerCase() === 'pm';
      
      if (isPM && hours !== 12) hours += 12;
      if (!isPM && hours === 12) hours = 0;
      
      const dateTime = new Date(dueDate);
      dateTime.setHours(hours, minutes);
      dueDate = dateTime.toISOString();
    }

    // Extract action verbs and create title
    const actionWords = ['call', 'email', 'meet', 'remind', 'schedule', 'buy', 'finish', 'start', 'review'];
    let title = text;
    
    // Remove common prefixes
    title = title.replace(/^(remind me to|i need to|todo:?|task:?)\s*/i, '');
    
    // Capitalize first letter
    title = title.charAt(0).toUpperCase() + title.slice(1);

    // Extract workspace hints
    let workspace: string | undefined;
    if (lowercaseText.includes('work') || lowercaseText.includes('office') || lowercaseText.includes('meeting')) {
      workspace = 'Work';
    } else if (lowercaseText.includes('personal') || lowercaseText.includes('home')) {
      workspace = 'Personal';
    } else if (lowercaseText.includes('project') || lowercaseText.includes('code') || lowercaseText.includes('development')) {
      workspace = 'Projects';
    }

    // Extract tags
    const tags: string[] = [];
    if (lowercaseText.includes('meeting')) tags.push('meeting');
    if (lowercaseText.includes('call')) tags.push('call');
    if (lowercaseText.includes('email')) tags.push('email');
    if (lowercaseText.includes('buy') || lowercaseText.includes('purchase')) tags.push('shopping');

    // Calculate confidence based on how many elements we successfully parsed
    let confidence = 0.5; // Base confidence
    if (title.length > 5) confidence += 0.2;
    if (priority !== 'medium') confidence += 0.1;
    if (dueDate) confidence += 0.2;
    if (workspace) confidence += 0.1;
    if (tags.length > 0) confidence += 0.1;

    return {
      title,
      description: text !== title ? text : undefined,
      priority,
      dueDate,
      workspace,
      tags,
      confidence: Math.min(confidence, 1.0)
    };
  };

  const handleInputChange = async (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    const value = e.target.value;
    setInput(value);

    if (value.trim().length > 10) {
      setIsProcessing(true);
      
      // Debounce the parsing
      setTimeout(() => {
        const parsed = parseNaturalLanguage(value);
        setParsedTask(parsed);
        setShowPreview(true);
        setIsProcessing(false);
      }, 500);
    } else {
      setShowPreview(false);
      setParsedTask(null);
    }
  };

  const handleCreateTask = async () => {
    if (!parsedTask) return;

    try {
      setIsProcessing(true);
      
      const taskData = {
        title: parsedTask.title,
        description: parsedTask.description || '',
        priority: parsedTask.priority,
        due_date: parsedTask.dueDate,
        tags: parsedTask.tags || [],
        // Add workspace_id if we can match the workspace name
        workspace_id: parsedTask.workspace === 'Work' ? 2 : parsedTask.workspace === 'Personal' ? 1 : 3
      };

      const response = await apiClient.request('/tasks/taskmaster', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(taskData)
      });

      if (response) {
        console.log('✅ Task created from natural language:', response);
        onTaskCreated?.(response);
        
        // Clear input
        setInput('');
        setParsedTask(null);
        setShowPreview(false);
      }
    } catch (error) {
      console.error('❌ Failed to create task:', error);
    } finally {
      setIsProcessing(false);
    }
  };

  // Voice input (if browser supports it)
  const startVoiceInput = () => {
    if (!('webkitSpeechRecognition' in window) && !('SpeechRecognition' in window)) {
      alert('Speech recognition not supported in this browser');
      return;
    }

    const SpeechRecognition = (window as any).webkitSpeechRecognition || (window as any).SpeechRecognition;
    const recognition = new SpeechRecognition();
    
    recognition.continuous = false;
    recognition.interimResults = false;
    recognition.lang = 'en-US';

    recognition.onstart = () => {
      setIsListening(true);
    };

    recognition.onresult = (event: any) => {
      const transcript = event.results[0][0].transcript;
      setInput(transcript);
      handleInputChange({ target: { value: transcript } } as any);
    };

    recognition.onend = () => {
      setIsListening(false);
    };

    recognition.onerror = (event: any) => {
      console.error('Speech recognition error:', event.error);
      setIsListening(false);
    };

    recognition.start();
  };

  const getConfidenceColor = (confidence: number) => {
    if (confidence >= 0.8) return '#10b981'; // Green
    if (confidence >= 0.6) return '#f59e0b'; // Yellow
    return '#ef4444'; // Red
  };

  return (
    <div className="nl-task-input">
      <div className="input-container">
        <textarea
          ref={textareaRef}
          value={input}
          onChange={handleInputChange}
          placeholder={placeholder}
          className="nl-input"
          rows={1}
          disabled={isProcessing}
        />
        
        <div className="input-actions">
          <button
            onClick={startVoiceInput}
            className={`voice-button ${isListening ? 'listening' : ''}`}
            disabled={isProcessing || isListening}
            title="Voice input"
          >
            {isListening ? '🎤' : '🎙️'}
          </button>
        </div>
      </div>

      {isProcessing && (
        <div className="processing-indicator">
          <div className="spinner"></div>
          <span>Understanding your request...</span>
        </div>
      )}

      {showPreview && parsedTask && (
        <div className="task-preview">
          <div className="preview-header">
            <h4>📋 Parsed Task</h4>
            <div 
              className="confidence-indicator"
              style={{ backgroundColor: getConfidenceColor(parsedTask.confidence) }}
            >
              {Math.round(parsedTask.confidence * 100)}% confident
            </div>
          </div>

          <div className="preview-content">
            <div className="preview-field">
              <strong>Title:</strong> {parsedTask.title}
            </div>
            
            {parsedTask.description && (
              <div className="preview-field">
                <strong>Description:</strong> {parsedTask.description}
              </div>
            )}
            
            <div className="preview-field">
              <strong>Priority:</strong> 
              <span className={`priority-badge ${parsedTask.priority}`}>
                {parsedTask.priority}
              </span>
            </div>

            {parsedTask.dueDate && (
              <div className="preview-field">
                <strong>Due:</strong> {new Date(parsedTask.dueDate).toLocaleString()}
              </div>
            )}

            {parsedTask.workspace && (
              <div className="preview-field">
                <strong>Workspace:</strong> {parsedTask.workspace}
              </div>
            )}

            {parsedTask.tags && parsedTask.tags.length > 0 && (
              <div className="preview-field">
                <strong>Tags:</strong>
                <div className="tags-container">
                  {parsedTask.tags.map((tag, index) => (
                    <span key={index} className="tag">{tag}</span>
                  ))}
                </div>
              </div>
            )}
          </div>

          <div className="preview-actions">
            <button
              onClick={() => setShowPreview(false)}
              className="btn btn-secondary"
            >
              Cancel
            </button>
            <button
              onClick={handleCreateTask}
              className="btn btn-primary"
              disabled={isProcessing}
            >
              {isProcessing ? 'Creating...' : 'Create Task'}
            </button>
          </div>
        </div>
      )}
    </div>
  );
};

export default NLTaskInput; 