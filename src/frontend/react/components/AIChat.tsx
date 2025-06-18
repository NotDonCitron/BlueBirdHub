import React, { useState, useEffect, useRef } from 'react';
import { useErrorHandler } from '../hooks/useErrorHandler';

interface ChatMessage {
  id: string;
  content: string;
  role: 'user' | 'assistant';
  timestamp: string;
}

const AIChat: React.FC = () => {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [inputValue, setInputValue] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const { handleError } = useErrorHandler({ component: 'AIChat' });

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  useEffect(() => {
    // Add welcome message
    const welcomeMessage: ChatMessage = {
      id: 'welcome',
      content: 'Hello! I\'m your AI assistant. How can I help you organize your workspace today?',
      role: 'assistant',
      timestamp: new Date().toISOString()
    };
    setMessages([welcomeMessage]);
  }, []);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  const sendMessage = async (content: string) => {
    if (!content.trim()) return;

    const userMessage: ChatMessage = {
      id: Date.now().toString(),
      content: content.trim(),
      role: 'user',
      timestamp: new Date().toISOString()
    };

    setMessages(prev => [...prev, userMessage]);
    setInputValue('');
    setIsLoading(true);
    setError(null);

    try {
      // Mock AI response - replace with actual AI service call
      await new Promise(resolve => setTimeout(resolve, 1000)); // Simulate API delay
      
      const aiResponse = generateMockResponse(content);
      
      const assistantMessage: ChatMessage = {
        id: (Date.now() + 1).toString(),
        content: aiResponse,
        role: 'assistant',
        timestamp: new Date().toISOString()
      };

      setMessages(prev => [...prev, assistantMessage]);
    } catch (err) {
      const message = handleError(err);
      setError(message);
      
      const errorMessage: ChatMessage = {
        id: (Date.now() + 1).toString(),
        content: 'Sorry, I encountered an error. Please try again.',
        role: 'assistant',
        timestamp: new Date().toISOString()
      };
      
      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
    }
  };

  const generateMockResponse = (userInput: string): string => {
    const input = userInput.toLowerCase();
    
    if (input.includes('task') || input.includes('todo')) {
      return 'I can help you manage your tasks! You can create new tasks, set priorities, and track progress. Would you like me to help you create a task or organize your existing ones?';
    }
    
    if (input.includes('workspace') || input.includes('project')) {
      return 'Great! I can assist with workspace management. You can create new workspaces, organize your projects, and set up collaboration with team members. What would you like to do with your workspace?';
    }
    
    if (input.includes('organize') || input.includes('structure')) {
      return 'I\'d be happy to help you organize! Here are some suggestions:\n\n1. Create themed workspaces for different projects\n2. Use priority levels for your tasks\n3. Set up regular review schedules\n4. Organize files by project and date\n\nWhich area would you like to focus on?';
    }
    
    if (input.includes('help') || input.includes('what') || input.includes('how')) {
      return 'I can help you with:\n\n• **Task Management** - Create, organize, and track tasks\n• **Workspace Setup** - Organize your projects and files\n• **Team Collaboration** - Set up shared workspaces\n• **Productivity Tips** - Optimize your workflow\n• **File Organization** - Structure your documents\n\nWhat would you like assistance with?';
    }
    
    if (input.includes('file') || input.includes('document')) {
      return 'I can help you organize your files! Consider creating a folder structure like:\n\n📁 Projects/\n  📁 [Project Name]/\n    📁 Documents/\n    📁 Resources/\n    📁 Archives/\n\nWould you like me to help you set up a specific organization system?';
    }
    
    return 'That\'s an interesting question! I\'m here to help you organize your workspace and improve productivity. Could you tell me more about what you\'re trying to accomplish?';
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage(inputValue);
    }
  };

  const clearChat = () => {
    setMessages([{
      id: 'welcome',
      content: 'Chat cleared! How can I help you organize your workspace?',
      role: 'assistant',
      timestamp: new Date().toISOString()
    }]);
    setError(null);
  };

  return (
    <div className="ai-chat">
      <div className="chat-header">
        <div className="chat-title">
          <h2>🤖 AI Assistant</h2>
          <span className="chat-status">Online</span>
        </div>
        <button className="clear-chat-btn" onClick={clearChat}>
          Clear Chat
        </button>
      </div>

      {error && (
        <div className="chat-error">
          <p>Error: {error}</p>
          <button onClick={() => setError(null)}>Dismiss</button>
        </div>
      )}

      <div className="messages-container">
        {messages.map(message => (
          <div key={message.id} className={`message ${message.role}`}>
            <div className="message-content">
              {message.content.split('\n').map((line, index) => (
                <React.Fragment key={index}>
                  {line}
                  {index < message.content.split('\n').length - 1 && <br />}
                </React.Fragment>
              ))}
            </div>
            <div className="message-time">
              {new Date(message.timestamp).toLocaleTimeString()}
            </div>
          </div>
        ))}
        
        {isLoading && (
          <div className="message assistant loading">
            <div className="typing-indicator">
              <span></span>
              <span></span>
              <span></span>
            </div>
          </div>
        )}
        
        <div ref={messagesEndRef} />
      </div>

      <div className="chat-input-container">
        <div className="chat-input-wrapper">
          <textarea
            value={inputValue}
            onChange={(e) => setInputValue(e.target.value)}
            onKeyPress={handleKeyPress}
            placeholder="Ask me anything about organizing your workspace..."
            rows={2}
            disabled={isLoading}
          />
          <button
            onClick={() => sendMessage(inputValue)}
            disabled={isLoading || !inputValue.trim()}
            className="send-btn"
          >
            Send
          </button>
        </div>
      </div>

      <style jsx>{`
        .ai-chat {
          display: flex;
          flex-direction: column;
          height: 100vh;
          max-height: 800px;
          background: white;
          border-radius: 8px;
          box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
          overflow: hidden;
        }

        .chat-header {
          display: flex;
          justify-content: space-between;
          align-items: center;
          padding: 20px;
          background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
          color: white;
        }

        .chat-title h2 {
          margin: 0;
          font-size: 20px;
        }

        .chat-status {
          background: #10b981;
          padding: 4px 8px;
          border-radius: 12px;
          font-size: 12px;
          margin-left: 10px;
        }

        .clear-chat-btn {
          padding: 8px 16px;
          background: rgba(255, 255, 255, 0.2);
          color: white;
          border: 1px solid rgba(255, 255, 255, 0.3);
          border-radius: 6px;
          cursor: pointer;
          font-size: 14px;
        }

        .clear-chat-btn:hover {
          background: rgba(255, 255, 255, 0.3);
        }

        .chat-error {
          background: #fef2f2;
          border: 1px solid #fecaca;
          color: #dc2626;
          padding: 12px 20px;
          display: flex;
          justify-content: space-between;
          align-items: center;
        }

        .chat-error button {
          background: none;
          border: none;
          color: #dc2626;
          cursor: pointer;
          text-decoration: underline;
        }

        .messages-container {
          flex: 1;
          overflow-y: auto;
          padding: 20px;
          background: #f9fafb;
        }

        .message {
          margin-bottom: 20px;
          display: flex;
          flex-direction: column;
        }

        .message.user {
          align-items: flex-end;
        }

        .message.assistant {
          align-items: flex-start;
        }

        .message-content {
          max-width: 70%;
          padding: 12px 16px;
          border-radius: 18px;
          font-size: 14px;
          line-height: 1.5;
          white-space: pre-wrap;
        }

        .message.user .message-content {
          background: #3b82f6;
          color: white;
          border-bottom-right-radius: 6px;
        }

        .message.assistant .message-content {
          background: white;
          color: #1f2937;
          border: 1px solid #e5e7eb;
          border-bottom-left-radius: 6px;
        }

        .message-time {
          font-size: 12px;
          color: #9ca3af;
          margin-top: 4px;
          padding: 0 8px;
        }

        .loading .message-content {
          background: white;
          border: 1px solid #e5e7eb;
          padding: 16px;
        }

        .typing-indicator {
          display: flex;
          gap: 4px;
          align-items: center;
        }

        .typing-indicator span {
          width: 6px;
          height: 6px;
          background: #9ca3af;
          border-radius: 50%;
          animation: typing 1.4s infinite ease-in-out;
        }

        .typing-indicator span:nth-child(2) {
          animation-delay: 0.2s;
        }

        .typing-indicator span:nth-child(3) {
          animation-delay: 0.4s;
        }

        @keyframes typing {
          0%, 60%, 100% {
            transform: translateY(0);
            opacity: 0.5;
          }
          30% {
            transform: translateY(-10px);
            opacity: 1;
          }
        }

        .chat-input-container {
          padding: 20px;
          background: white;
          border-top: 1px solid #e5e7eb;
        }

        .chat-input-wrapper {
          display: flex;
          gap: 12px;
          align-items: flex-end;
        }

        .chat-input-wrapper textarea {
          flex: 1;
          padding: 12px;
          border: 1px solid #d1d5db;
          border-radius: 8px;
          resize: none;
          outline: none;
          font-family: inherit;
          font-size: 14px;
          line-height: 1.5;
        }

        .chat-input-wrapper textarea:focus {
          border-color: #3b82f6;
          box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
        }

        .send-btn {
          padding: 12px 24px;
          background: #3b82f6;
          color: white;
          border: none;
          border-radius: 8px;
          cursor: pointer;
          font-weight: 500;
          font-size: 14px;
          height: fit-content;
        }

        .send-btn:hover:not(:disabled) {
          background: #2563eb;
        }

        .send-btn:disabled {
          background: #9ca3af;
          cursor: not-allowed;
        }
      `}</style>
    </div>
  );
};

export default AIChat;