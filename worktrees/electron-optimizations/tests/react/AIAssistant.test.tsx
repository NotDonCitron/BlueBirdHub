import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import '@testing-library/jest-dom';
import AIAssistant from '../../src/frontend/react/components/AIAssistant/AIAssistant';
import { ApiContext } from '../../src/frontend/react/contexts/ApiContext';

// Mock API context
const mockApiContext = {
  apiUrl: 'http://localhost:8001',
  isConnected: true,
  get: jest.fn(),
  post: jest.fn(),
  put: jest.fn(),
  delete: jest.fn()
};

describe('AIAssistant Component', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  const renderWithContext = (component: React.ReactElement) => {
    return render(
      <ApiContext.Provider value={mockApiContext}>
        {component}
      </ApiContext.Provider>
    );
  };

  test('renders AI assistant interface', () => {
    renderWithContext(<AIAssistant />);
    
    expect(screen.getByText(/ai assistant/i)).toBeInTheDocument();
    expect(screen.getByPlaceholderText(/type or paste your text here/i)).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /analyze text/i })).toBeInTheDocument();
    expect(screen.getByText(/text analysis/i)).toBeInTheDocument();
    expect(screen.getByText(/file categorization/i)).toBeInTheDocument();
  });

  test('analyzes text and displays results', async () => {
    mockApiContext.makeApiRequest.mockResolvedValueOnce({
      sentiment: { label: 'positive', score: 0.8 },
      priority: 'high',
      category: 'work',
      keywords: ['project', 'deadline']
    });

    mockApiContext.makeApiRequest.mockResolvedValueOnce({
      tags: ['urgent', 'development']
    });

    renderWithContext(<AIAssistant />);

    const textArea = screen.getByPlaceholderText(/type or paste your text here/i);
    fireEvent.change(textArea, { target: { value: 'This is urgent project work with deadline' } });

    const analyzeButton = screen.getByRole('button', { name: /analyze text/i });
    fireEvent.click(analyzeButton);

    await waitFor(() => {
      expect(mockApiContext.makeApiRequest).toHaveBeenCalledWith(
        '/ai/analyze-text',
        'POST',
        expect.objectContaining({ text: 'This is urgent project work with deadline' })
      );
    });
  });

  test('displays conversation history', async () => {
    const mockHistory = {
      conversations: [
        {
          id: 1,
          messages: [
            { role: 'user', content: 'Hello', timestamp: '2024-01-01T10:00:00' },
            { role: 'assistant', content: 'Hi! How can I help?', timestamp: '2024-01-01T10:00:01' }
          ]
        }
      ]
    };

    mockApiContext.get.mockResolvedValueOnce({ data: mockHistory });

    renderWithContext(<AIAssistant />);

    await waitFor(() => {
      expect(screen.getByText('Hello')).toBeInTheDocument();
      expect(screen.getByText('Hi! How can I help?')).toBeInTheDocument();
    });
  });

  test('handles file analysis request', async () => {
    mockApiContext.post.mockResolvedValueOnce({
      data: {
        response: 'This appears to be a Python script with 150 lines of code.',
        analysis: {
          file_type: 'python',
          lines: 150,
          complexity: 'medium',
          suggestions: ['Add docstrings', 'Split into smaller functions']
        }
      }
    });

    renderWithContext(<AIAssistant />);

    // Simulate file drop
    const dropZone = screen.getByTestId('chat-drop-zone');
    const file = new File(['print("test")'], 'test.py', { type: 'text/python' });

    fireEvent.drop(dropZone, {
      dataTransfer: { files: [file] }
    });

    await waitFor(() => {
      expect(mockApiContext.post).toHaveBeenCalledWith(
        '/api/ai/analyze-file',
        expect.any(FormData)
      );
      expect(screen.getByText(/python script with 150 lines/i)).toBeInTheDocument();
      expect(screen.getByText('Add docstrings')).toBeInTheDocument();
    });
  });

  test('displays quick actions', () => {
    renderWithContext(<AIAssistant />);

    expect(screen.getByRole('button', { name: /organize files/i })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /create task/i })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /suggest automation/i })).toBeInTheDocument();
  });

  test('handles quick action clicks', async () => {
    mockApiContext.post.mockResolvedValueOnce({
      data: {
        response: 'I\'ll help you organize your files. Let me analyze your file structure...',
        action: 'file_organization_started'
      }
    });

    renderWithContext(<AIAssistant />);

    const organizeButton = screen.getByRole('button', { name: /organize files/i });
    fireEvent.click(organizeButton);

    await waitFor(() => {
      expect(mockApiContext.post).toHaveBeenCalledWith(
        '/api/ai/quick-action',
        expect.objectContaining({ action: 'organize_files' })
      );
      expect(screen.getByText(/analyze your file structure/i)).toBeInTheDocument();
    });
  });

  test('handles context-aware suggestions', async () => {
    mockApiContext.get.mockResolvedValueOnce({
      data: {
        context: {
          current_workspace: 'Development',
          recent_files: ['app.js', 'test.py'],
          active_tasks: 2
        },
        suggestions: [
          'Review pending pull requests',
          'Run tests for recent changes',
          'Update project documentation'
        ]
      }
    });

    renderWithContext(<AIAssistant />);

    await waitFor(() => {
      expect(screen.getByText('Review pending pull requests')).toBeInTheDocument();
      expect(screen.getByText('Run tests for recent changes')).toBeInTheDocument();
    });
  });

  test('handles voice input', async () => {
    // Mock speech recognition
    const mockSpeechRecognition = {
      start: jest.fn(),
      stop: jest.fn(),
      addEventListener: jest.fn()
    };
    
    window.SpeechRecognition = jest.fn(() => mockSpeechRecognition) as any;

    renderWithContext(<AIAssistant />);

    const voiceButton = screen.getByRole('button', { name: /voice input/i });
    fireEvent.click(voiceButton);

    expect(mockSpeechRecognition.start).toHaveBeenCalled();
    expect(screen.getByText(/listening/i)).toBeInTheDocument();
  });

  test('exports conversation', async () => {
    const mockConversation = {
      messages: [
        { role: 'user', content: 'Test message' },
        { role: 'assistant', content: 'Test response' }
      ]
    };

    mockApiContext.get.mockResolvedValueOnce({ data: mockConversation });

    renderWithContext(<AIAssistant />);

    const exportButton = screen.getByRole('button', { name: /export/i });
    fireEvent.click(exportButton);

    await waitFor(() => {
      expect(mockApiContext.get).toHaveBeenCalledWith('/api/ai/export-conversation');
    });
  });

  test('clears conversation with confirmation', async () => {
    renderWithContext(<AIAssistant />);

    // Add some messages first
    const input = screen.getByPlaceholderText(/ask me anything/i);
    fireEvent.change(input, { target: { value: 'Test message' } });
    fireEvent.submit(input.closest('form')!);

    const clearButton = screen.getByRole('button', { name: /clear/i });
    fireEvent.click(clearButton);

    const confirmButton = await screen.findByRole('button', { name: /confirm/i });
    fireEvent.click(confirmButton);

    expect(screen.queryByText('Test message')).not.toBeInTheDocument();
  });

  test('handles AI command shortcuts', async () => {
    mockApiContext.post.mockResolvedValueOnce({
      data: {
        response: 'Created task: Review documentation',
        task_created: true,
        task_id: 5
      }
    });

    renderWithContext(<AIAssistant />);

    const input = screen.getByPlaceholderText(/ask me anything/i);
    fireEvent.change(input, { target: { value: '/task Review documentation' } });
    fireEvent.submit(input.closest('form')!);

    await waitFor(() => {
      expect(mockApiContext.post).toHaveBeenCalledWith(
        '/api/ai/command',
        expect.objectContaining({
          command: 'task',
          args: 'Review documentation'
        })
      );
      expect(screen.getByText(/created task: review documentation/i)).toBeInTheDocument();
    });
  });

  test('displays typing indicator while AI responds', async () => {
    let resolvePromise: (value: any) => void;
    const promise = new Promise((resolve) => {
      resolvePromise = resolve;
    });

    mockApiContext.post.mockReturnValueOnce(promise);

    renderWithContext(<AIAssistant />);

    const input = screen.getByPlaceholderText(/ask me anything/i);
    fireEvent.change(input, { target: { value: 'Test' } });
    fireEvent.submit(input.closest('form')!);

    expect(screen.getByTestId('typing-indicator')).toBeInTheDocument();

    resolvePromise!({
      data: { response: 'Test response' }
    });

    await waitFor(() => {
      expect(screen.queryByTestId('typing-indicator')).not.toBeInTheDocument();
      expect(screen.getByText('Test response')).toBeInTheDocument();
    });
  });

  test('handles network errors gracefully', async () => {
    mockApiContext.post.mockRejectedValueOnce(new Error('Network error'));

    renderWithContext(<AIAssistant />);

    const input = screen.getByPlaceholderText(/ask me anything/i);
    fireEvent.change(input, { target: { value: 'Test message' } });
    fireEvent.submit(input.closest('form')!);

    await waitFor(() => {
      expect(screen.getByText(/unable to connect/i)).toBeInTheDocument();
      expect(screen.getByRole('button', { name: /retry/i })).toBeInTheDocument();
    });
  });
});