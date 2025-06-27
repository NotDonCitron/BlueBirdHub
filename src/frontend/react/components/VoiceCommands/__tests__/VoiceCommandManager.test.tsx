import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import '@testing-library/jest-dom';
import VoiceCommandManager from '../VoiceCommandManager';
import { AuthProvider } from '../../../contexts/AuthContext';
import { ApiProvider } from '../../../contexts/ApiContext';

// Mock Web Speech API
const mockSpeechRecognition = {
  start: jest.fn(),
  stop: jest.fn(),
  continuous: false,
  interimResults: false,
  lang: 'en-US',
  onresult: null,
  onerror: null,
  onend: null
};

const mockSpeechSynthesis = {
  speak: jest.fn(),
  cancel: jest.fn(),
  getVoices: jest.fn(() => []),
  speaking: false
};

// Mock getUserMedia
const mockGetUserMedia = jest.fn();

// Mock API responses
const mockApi = {
  get: jest.fn(),
  post: jest.fn(),
  put: jest.fn(),
  delete: jest.fn()
};

// Mock user
const mockUser = {
  id: '1',
  email: 'test@example.com',
  name: 'Test User'
};

const TestWrapper: React.FC<{ children: React.ReactNode }> = ({ children }) => (
  <AuthProvider>
    <ApiProvider apiStatus="connected" onRetryConnection={() => {}}>
      {children}
    </ApiProvider>
  </AuthProvider>
);

describe('VoiceCommandManager', () => {
  beforeEach(() => {
    // Setup Web Speech API mocks
    (window as any).webkitSpeechRecognition = jest.fn(() => mockSpeechRecognition);
    (window as any).SpeechRecognition = jest.fn(() => mockSpeechRecognition);
    (window as any).speechSynthesis = mockSpeechSynthesis;
    
    // Setup MediaDevices mock
    Object.defineProperty(navigator, 'mediaDevices', {
      writable: true,
      value: {
        getUserMedia: mockGetUserMedia.mockResolvedValue({
          getTracks: () => [{ stop: jest.fn() }]
        })
      }
    });

    // Setup AudioContext mock
    (window as any).AudioContext = jest.fn(() => ({
      createAnalyser: () => ({
        fftSize: 256,
        frequencyBinCount: 128,
        getByteFrequencyData: jest.fn()
      }),
      createMediaStreamSource: () => ({
        connect: jest.fn()
      }),
      close: jest.fn()
    }));

    // Clear all mocks
    jest.clearAllMocks();
  });

  afterEach(() => {
    // Clean up
    delete (window as any).webkitSpeechRecognition;
    delete (window as any).SpeechRecognition;
    delete (window as any).speechSynthesis;
    delete (window as any).AudioContext;
  });

  describe('Rendering', () => {
    it('renders voice command manager', () => {
      render(
        <TestWrapper>
          <VoiceCommandManager />
        </TestWrapper>
      );

      expect(screen.getByText('Start Voice Commands')).toBeInTheDocument();
      expect(screen.getByTitle('Voice Settings')).toBeInTheDocument();
      expect(screen.getByTitle('Command History')).toBeInTheDocument();
      expect(screen.getByTitle('Voice Commands Help')).toBeInTheDocument();
      expect(screen.getByTitle('Voice Analytics')).toBeInTheDocument();
    });

    it('displays browser compatibility warning when speech recognition is not supported', () => {
      // Remove speech recognition support
      delete (window as any).webkitSpeechRecognition;
      delete (window as any).SpeechRecognition;

      render(
        <TestWrapper>
          <VoiceCommandManager />
        </TestWrapper>
      );

      expect(screen.getByText(/Speech recognition is not supported/)).toBeInTheDocument();
    });
  });

  describe('Voice Controls', () => {
    it('starts listening when toggle button is clicked', async () => {
      render(
        <TestWrapper>
          <VoiceCommandManager />
        </TestWrapper>
      );

      const toggleButton = screen.getByText('Start Voice Commands');
      fireEvent.click(toggleButton);

      await waitFor(() => {
        expect(mockSpeechRecognition.start).toHaveBeenCalled();
        expect(mockGetUserMedia).toHaveBeenCalled();
      });
    });

    it('stops listening when toggle button is clicked while listening', async () => {
      render(
        <TestWrapper>
          <VoiceCommandManager />
        </TestWrapper>
      );

      const toggleButton = screen.getByText('Start Voice Commands');
      
      // Start listening
      fireEvent.click(toggleButton);
      await waitFor(() => {
        expect(screen.getByText('Stop Voice Commands')).toBeInTheDocument();
      });

      // Stop listening
      fireEvent.click(screen.getByText('Stop Voice Commands'));
      expect(mockSpeechRecognition.stop).toHaveBeenCalled();
    });

    it('opens settings modal when settings button is clicked', () => {
      render(
        <TestWrapper>
          <VoiceCommandManager />
        </TestWrapper>
      );

      const settingsButton = screen.getByTitle('Voice Settings');
      fireEvent.click(settingsButton);

      expect(screen.getByText('Voice Command Settings')).toBeInTheDocument();
    });

    it('opens help modal when help button is clicked', () => {
      render(
        <TestWrapper>
          <VoiceCommandManager />
        </TestWrapper>
      );

      const helpButton = screen.getByTitle('Voice Commands Help');
      fireEvent.click(helpButton);

      expect(screen.getByText('Voice Commands Guide')).toBeInTheDocument();
    });

    it('opens analytics modal when analytics button is clicked', () => {
      render(
        <TestWrapper>
          <VoiceCommandManager />
        </TestWrapper>
      );

      const analyticsButton = screen.getByTitle('Voice Analytics');
      fireEvent.click(analyticsButton);

      expect(screen.getByText('Voice Command Analytics')).toBeInTheDocument();
    });
  });

  describe('Voice Recognition', () => {
    it('processes speech recognition results', async () => {
      mockApi.post.mockResolvedValue({
        type: 'create_task',
        text: 'create task test',
        confidence: 0.9,
        parameters: { title: 'test' },
        timestamp: new Date().toISOString(),
        language: 'en'
      });

      render(
        <TestWrapper>
          <VoiceCommandManager />
        </TestWrapper>
      );

      // Start listening
      const toggleButton = screen.getByText('Start Voice Commands');
      fireEvent.click(toggleButton);

      // Simulate speech recognition result
      const mockEvent = {
        results: [{
          0: { transcript: 'hey bluebird create task test', confidence: 0.9 },
          isFinal: true
        }],
        resultIndex: 0
      };

      // Trigger the speech recognition result
      if (mockSpeechRecognition.onresult) {
        mockSpeechRecognition.onresult(mockEvent);
      }

      await waitFor(() => {
        expect(mockApi.post).toHaveBeenCalledWith('/api/voice/process-text', {
          text: 'create task test',
          language: 'en',
          confidence: 0.9
        });
      });
    });

    it('handles speech recognition errors', () => {
      render(
        <TestWrapper>
          <VoiceCommandManager />
        </TestWrapper>
      );

      // Start listening
      const toggleButton = screen.getByText('Start Voice Commands');
      fireEvent.click(toggleButton);

      // Simulate speech recognition error
      const mockErrorEvent = {
        error: 'no-speech'
      };

      if (mockSpeechRecognition.onerror) {
        mockSpeechRecognition.onerror(mockErrorEvent);
      }

      expect(screen.getByText(/No speech detected/)).toBeInTheDocument();
    });
  });

  describe('Wake Word Detection', () => {
    it('detects wake word in speech', async () => {
      render(
        <TestWrapper>
          <VoiceCommandManager />
        </TestWrapper>
      );

      // Start listening
      const toggleButton = screen.getByText('Start Voice Commands');
      fireEvent.click(toggleButton);

      // Simulate wake word detection
      const mockEvent = {
        results: [{
          0: { transcript: 'hey bluebird create a task', confidence: 0.9 },
          isFinal: true
        }],
        resultIndex: 0
      };

      if (mockSpeechRecognition.onresult) {
        mockSpeechRecognition.onresult(mockEvent);
      }

      await waitFor(() => {
        expect(screen.getByText(/Listening/)).toBeInTheDocument();
      });
    });

    it('ignores commands without wake word', async () => {
      render(
        <TestWrapper>
          <VoiceCommandManager />
        </TestWrapper>
      );

      // Start listening
      const toggleButton = screen.getByText('Start Voice Commands');
      fireEvent.click(toggleButton);

      // Simulate speech without wake word
      const mockEvent = {
        results: [{
          0: { transcript: 'create a task', confidence: 0.9 },
          isFinal: true
        }],
        resultIndex: 0
      };

      if (mockSpeechRecognition.onresult) {
        mockSpeechRecognition.onresult(mockEvent);
      }

      // Should not process the command
      expect(mockApi.post).not.toHaveBeenCalled();
    });
  });

  describe('Voice Feedback', () => {
    it('provides voice feedback when enabled', async () => {
      mockApi.get.mockResolvedValue({
        voice_feedback_enabled: true,
        language_preference: 'en'
      });

      render(
        <TestWrapper>
          <VoiceCommandManager />
        </TestWrapper>
      );

      await waitFor(() => {
        expect(mockApi.get).toHaveBeenCalledWith('/api/voice/profile');
      });

      // Trigger a successful command
      mockApi.post.mockResolvedValue({
        type: 'create_task',
        text: 'create task test',
        confidence: 0.9,
        parameters: { title: 'test' }
      });

      const toggleButton = screen.getByText('Start Voice Commands');
      fireEvent.click(toggleButton);

      const mockEvent = {
        results: [{
          0: { transcript: 'hey bluebird create task test', confidence: 0.9 },
          isFinal: true
        }],
        resultIndex: 0
      };

      if (mockSpeechRecognition.onresult) {
        mockSpeechRecognition.onresult(mockEvent);
      }

      await waitFor(() => {
        expect(mockSpeechSynthesis.speak).toHaveBeenCalled();
      });
    });
  });

  describe('Accessibility', () => {
    it('provides proper ARIA labels', () => {
      render(
        <TestWrapper>
          <VoiceCommandManager />
        </TestWrapper>
      );

      expect(screen.getByTitle('Voice Settings')).toHaveAttribute('title');
      expect(screen.getByTitle('Command History')).toHaveAttribute('title');
      expect(screen.getByTitle('Voice Commands Help')).toHaveAttribute('title');
    });

    it('handles keyboard navigation', () => {
      render(
        <TestWrapper>
          <VoiceCommandManager />
        </TestWrapper>
      );

      const toggleButton = screen.getByText('Start Voice Commands');
      toggleButton.focus();
      
      expect(document.activeElement).toBe(toggleButton);
    });
  });

  describe('Error Handling', () => {
    it('handles API errors gracefully', async () => {
      mockApi.post.mockRejectedValue(new Error('API Error'));

      render(
        <TestWrapper>
          <VoiceCommandManager />
        </TestWrapper>
      );

      const toggleButton = screen.getByText('Start Voice Commands');
      fireEvent.click(toggleButton);

      const mockEvent = {
        results: [{
          0: { transcript: 'hey bluebird create task test', confidence: 0.9 },
          isFinal: true
        }],
        resultIndex: 0
      };

      if (mockSpeechRecognition.onresult) {
        mockSpeechRecognition.onresult(mockEvent);
      }

      await waitFor(() => {
        expect(screen.getByText(/Failed to process command/)).toBeInTheDocument();
      });
    });

    it('handles microphone access denial', async () => {
      mockGetUserMedia.mockRejectedValue(new Error('Permission denied'));

      render(
        <TestWrapper>
          <VoiceCommandManager />
        </TestWrapper>
      );

      const toggleButton = screen.getByText('Start Voice Commands');
      fireEvent.click(toggleButton);

      await waitFor(() => {
        expect(screen.getByText(/Could not access microphone/)).toBeInTheDocument();
      });
    });
  });

  describe('Profile Management', () => {
    it('loads voice profile on mount', async () => {
      mockApi.get.mockResolvedValue({
        language_preference: 'en',
        voice_feedback_enabled: true
      });

      render(
        <TestWrapper>
          <VoiceCommandManager />
        </TestWrapper>
      );

      await waitFor(() => {
        expect(mockApi.get).toHaveBeenCalledWith('/api/voice/profile');
      });
    });

    it('updates voice profile settings', async () => {
      mockApi.put.mockResolvedValue({
        language_preference: 'es',
        voice_feedback_enabled: false
      });

      render(
        <TestWrapper>
          <VoiceCommandManager />
        </TestWrapper>
      );

      // Open settings
      const settingsButton = screen.getByTitle('Voice Settings');
      fireEvent.click(settingsButton);

      // Change language setting (assuming the settings modal is rendered)
      await waitFor(() => {
        expect(screen.getByText('Voice Command Settings')).toBeInTheDocument();
      });
    });
  });

  describe('Command History', () => {
    it('tracks command history', async () => {
      mockApi.post.mockResolvedValue({
        type: 'create_task',
        text: 'create task test',
        confidence: 0.9,
        parameters: { title: 'test' }
      });

      render(
        <TestWrapper>
          <VoiceCommandManager />
        </TestWrapper>
      );

      const toggleButton = screen.getByText('Start Voice Commands');
      fireEvent.click(toggleButton);

      const mockEvent = {
        results: [{
          0: { transcript: 'hey bluebird create task test', confidence: 0.9 },
          isFinal: true
        }],
        resultIndex: 0
      };

      if (mockSpeechRecognition.onresult) {
        mockSpeechRecognition.onresult(mockEvent);
      }

      await waitFor(() => {
        expect(screen.getByText('create task test')).toBeInTheDocument();
      });
    });
  });
});