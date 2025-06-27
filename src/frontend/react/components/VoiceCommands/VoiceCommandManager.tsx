import React, { useState, useEffect, useRef, useCallback } from 'react';
import { useAuth } from '../../contexts/AuthContext';
import { useApi } from '../../contexts/ApiContext';
import VoiceIndicator from './VoiceIndicator';
import VoiceCommandHistory from './VoiceCommandHistory';
import VoiceSettings from './VoiceSettings';
import VoiceCommandHelp from './VoiceCommandHelp';
import VoiceFeedback from './VoiceFeedback';
import VoiceAnalytics from './VoiceAnalytics';
import './VoiceCommandManager.css';

interface VoiceCommand {
  type: string;
  text: string;
  confidence: number;
  parameters: Record<string, any>;
  timestamp: string;
  language: string;
}

interface VoiceProfile {
  language_preference: string;
  accent_model: string;
  voice_shortcuts: Record<string, string>;
  wake_word_sensitivity: number;
  noise_cancellation_level: number;
  confirmation_required: boolean;
  voice_feedback_enabled: boolean;
  custom_commands: Record<string, any>;
}

const VoiceCommandManager: React.FC = () => {
  const { user } = useAuth();
  const api = useApi();
  const [isListening, setIsListening] = useState(false);
  const [isProcessing, setIsProcessing] = useState(false);
  const [showSettings, setShowSettings] = useState(false);
  const [showHistory, setShowHistory] = useState(false);
  const [showHelp, setShowHelp] = useState(false);
  const [showAnalytics, setShowAnalytics] = useState(false);
  const [voiceProfile, setVoiceProfile] = useState<VoiceProfile | null>(null);
  const [lastCommand, setLastCommand] = useState<VoiceCommand | null>(null);
  const [feedback, setFeedback] = useState<{ message: string; type: 'success' | 'error' | 'info' } | null>(null);
  const [audioLevel, setAudioLevel] = useState(0);
  const [commandHistory, setCommandHistory] = useState<VoiceCommand[]>([]);
  
  const recognitionRef = useRef<any>(null);
  const audioContextRef = useRef<AudioContext | null>(null);
  const analyserRef = useRef<AnalyserNode | null>(null);
  const streamRef = useRef<MediaStream | null>(null);
  const animationFrameRef = useRef<number | null>(null);
  const wsRef = useRef<WebSocket | null>(null);
  const wakeWordTimeoutRef = useRef<NodeJS.Timeout | null>(null);

  // Initialize voice recognition
  useEffect(() => {
    if (!('webkitSpeechRecognition' in window) && !('SpeechRecognition' in window)) {
      setFeedback({
        message: 'Speech recognition is not supported in your browser. Please use Chrome or Edge.',
        type: 'error'
      });
      return;
    }

    const SpeechRecognition = (window as any).webkitSpeechRecognition || (window as any).SpeechRecognition;
    recognitionRef.current = new SpeechRecognition();
    
    recognitionRef.current.continuous = true;
    recognitionRef.current.interimResults = true;
    recognitionRef.current.lang = voiceProfile?.language_preference || 'en-US';

    recognitionRef.current.onresult = handleSpeechResult;
    recognitionRef.current.onerror = handleSpeechError;
    recognitionRef.current.onend = handleSpeechEnd;

    loadVoiceProfile();

    return () => {
      if (recognitionRef.current) {
        recognitionRef.current.stop();
      }
      cleanupAudioAnalyser();
      if (wsRef.current) {
        wsRef.current.close();
      }
    };
  }, []);

  // Load user voice profile
  const loadVoiceProfile = async () => {
    try {
      const response = await api.get('/api/voice/profile');
      setVoiceProfile(response);
    } catch (error) {
      console.error('Failed to load voice profile:', error);
    }
  };

  // Setup audio analyser for visual feedback
  const setupAudioAnalyser = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      streamRef.current = stream;
      
      audioContextRef.current = new (window.AudioContext || (window as any).webkitAudioContext)();
      analyserRef.current = audioContextRef.current.createAnalyser();
      analyserRef.current.fftSize = 256;
      
      const source = audioContextRef.current.createMediaStreamSource(stream);
      source.connect(analyserRef.current);
      
      updateAudioLevel();
    } catch (error) {
      console.error('Failed to setup audio analyser:', error);
      setFeedback({
        message: 'Could not access microphone. Please check permissions.',
        type: 'error'
      });
    }
  };

  // Update audio level visualization
  const updateAudioLevel = () => {
    if (!analyserRef.current) return;
    
    const dataArray = new Uint8Array(analyserRef.current.frequencyBinCount);
    analyserRef.current.getByteFrequencyData(dataArray);
    
    const average = dataArray.reduce((a, b) => a + b) / dataArray.length;
    setAudioLevel(average / 255);
    
    animationFrameRef.current = requestAnimationFrame(updateAudioLevel);
  };

  // Cleanup audio analyser
  const cleanupAudioAnalyser = () => {
    if (animationFrameRef.current) {
      cancelAnimationFrame(animationFrameRef.current);
    }
    if (streamRef.current) {
      streamRef.current.getTracks().forEach(track => track.stop());
    }
    if (audioContextRef.current) {
      audioContextRef.current.close();
    }
  };

  // Handle speech recognition results
  const handleSpeechResult = async (event: any) => {
    const last = event.results.length - 1;
    const transcript = event.results[last][0].transcript;
    const confidence = event.results[last][0].confidence || 0.9;
    const isFinal = event.results[last].isFinal;

    if (isFinal) {
      setIsProcessing(true);
      
      // Check for wake word
      const containsWakeWord = checkWakeWord(transcript.toLowerCase());
      
      if (containsWakeWord || wakeWordTimeoutRef.current) {
        // Process command
        const commandText = removeWakeWord(transcript);
        await processVoiceCommand(commandText, confidence);
        
        // Reset wake word timeout
        if (wakeWordTimeoutRef.current) {
          clearTimeout(wakeWordTimeoutRef.current);
        }
        
        // Keep listening for follow-up commands for 30 seconds
        wakeWordTimeoutRef.current = setTimeout(() => {
          wakeWordTimeoutRef.current = null;
          setFeedback({ message: 'Wake word timeout. Say "Hey BlueBird" to continue.', type: 'info' });
        }, 30000);
      }
      
      setIsProcessing(false);
    }
  };

  // Check if transcript contains wake word
  const checkWakeWord = (transcript: string): boolean => {
    const wakeWords = ['hey bluebird', 'okay bluebird', 'bluebird', 'hey blue bird'];
    return wakeWords.some(word => transcript.includes(word));
  };

  // Remove wake word from transcript
  const removeWakeWord = (transcript: string): string => {
    const wakeWords = ['hey bluebird', 'okay bluebird', 'bluebird', 'hey blue bird'];
    let cleanedTranscript = transcript.toLowerCase();
    
    wakeWords.forEach(word => {
      cleanedTranscript = cleanedTranscript.replace(word, '').trim();
    });
    
    return cleanedTranscript;
  };

  // Process voice command
  const processVoiceCommand = async (text: string, confidence: number) => {
    try {
      const response = await api.post('/api/voice/process-text', {
        text,
        language: voiceProfile?.language_preference || 'en',
        confidence
      });

      if (response) {
        setLastCommand(response);
        setCommandHistory(prev => [response, ...prev].slice(0, 50));
        
        // Show feedback based on command type
        handleCommandFeedback(response);
        
        // Speak feedback if enabled
        if (voiceProfile?.voice_feedback_enabled) {
          speakFeedback(getCommandFeedbackMessage(response));
        }
      }
    } catch (error) {
      console.error('Failed to process voice command:', error);
      setFeedback({ message: 'Failed to process command. Please try again.', type: 'error' });
    }
  };

  // Handle command feedback
  const handleCommandFeedback = (command: VoiceCommand) => {
    const messages: Record<string, string> = {
      create_task: `Creating task: ${command.parameters.title || 'New Task'}`,
      update_task: 'Updating task...',
      delete_task: 'Deleting task...',
      search_task: 'Searching tasks...',
      navigate: `Navigating to ${command.parameters.destination || 'page'}...`,
      unknown: "I didn't understand that command. Say 'help' for available commands."
    };

    const message = messages[command.type] || 'Processing command...';
    setFeedback({ message, type: command.type === 'unknown' ? 'error' : 'success' });
  };

  // Get command feedback message
  const getCommandFeedbackMessage = (command: VoiceCommand): string => {
    const messages: Record<string, string> = {
      create_task: `Task created successfully`,
      update_task: 'Task updated',
      delete_task: 'Task deleted',
      search_task: 'Search complete',
      navigate: 'Navigation complete',
      unknown: "Sorry, I didn't understand that"
    };

    return messages[command.type] || 'Command executed';
  };

  // Speak feedback using text-to-speech
  const speakFeedback = (message: string) => {
    if (!('speechSynthesis' in window)) return;

    const utterance = new SpeechSynthesisUtterance(message);
    utterance.lang = voiceProfile?.language_preference || 'en-US';
    utterance.rate = 1.0;
    utterance.pitch = 1.0;
    utterance.volume = 1.0;
    
    speechSynthesis.speak(utterance);
  };

  // Handle speech recognition errors
  const handleSpeechError = (event: any) => {
    console.error('Speech recognition error:', event.error);
    
    const errorMessages: Record<string, string> = {
      'no-speech': 'No speech detected. Please try again.',
      'audio-capture': 'No microphone found. Please check your settings.',
      'not-allowed': 'Microphone access denied. Please enable permissions.',
      'network': 'Network error. Please check your connection.'
    };

    const message = errorMessages[event.error] || `Speech recognition error: ${event.error}`;
    setFeedback({ message, type: 'error' });
  };

  // Handle speech recognition end
  const handleSpeechEnd = () => {
    if (isListening) {
      // Restart recognition if still listening
      recognitionRef.current?.start();
    }
  };

  // Toggle listening
  const toggleListening = async () => {
    if (isListening) {
      stopListening();
    } else {
      await startListening();
    }
  };

  // Start listening
  const startListening = async () => {
    try {
      await setupAudioAnalyser();
      recognitionRef.current?.start();
      setIsListening(true);
      setFeedback({ message: 'Listening... Say "Hey BlueBird" followed by your command.', type: 'info' });
      
      // Setup WebSocket for real-time streaming (optional)
      // setupWebSocketConnection();
    } catch (error) {
      console.error('Failed to start listening:', error);
      setFeedback({ message: 'Failed to start voice recognition. Please try again.', type: 'error' });
    }
  };

  // Stop listening
  const stopListening = () => {
    recognitionRef.current?.stop();
    cleanupAudioAnalyser();
    setIsListening(false);
    setAudioLevel(0);
    
    if (wakeWordTimeoutRef.current) {
      clearTimeout(wakeWordTimeoutRef.current);
      wakeWordTimeoutRef.current = null;
    }
    
    if (wsRef.current) {
      wsRef.current.close();
    }
  };

  // Update voice profile
  const updateVoiceProfile = async (updates: Partial<VoiceProfile>) => {
    try {
      const response = await api.put('/api/voice/profile', updates);
      setVoiceProfile(response);
      
      // Update recognition language
      if (recognitionRef.current && updates.language_preference) {
        recognitionRef.current.lang = updates.language_preference;
      }
      
      setFeedback({ message: 'Voice settings updated successfully', type: 'success' });
    } catch (error) {
      console.error('Failed to update voice profile:', error);
      setFeedback({ message: 'Failed to update voice settings', type: 'error' });
    }
  };

  // Load command history
  const loadCommandHistory = async () => {
    try {
      const response = await api.get('/api/voice/history?limit=50');
      setCommandHistory(response);
    } catch (error) {
      console.error('Failed to load command history:', error);
    }
  };

  return (
    <div className="voice-command-manager">
      <div className="voice-control-bar">
        <button
          className={`voice-toggle-btn ${isListening ? 'listening' : ''}`}
          onClick={toggleListening}
          disabled={isProcessing}
        >
          <i className={`fas fa-${isListening ? 'microphone-slash' : 'microphone'}`} />
          {isListening ? 'Stop' : 'Start'} Voice Commands
        </button>

        <div className="voice-controls">
          <button
            className="voice-control-btn"
            onClick={() => setShowSettings(!showSettings)}
            title="Voice Settings"
          >
            <i className="fas fa-cog" />
          </button>
          
          <button
            className="voice-control-btn"
            onClick={() => {
              setShowHistory(!showHistory);
              if (!showHistory) loadCommandHistory();
            }}
            title="Command History"
          >
            <i className="fas fa-history" />
          </button>
          
          <button
            className="voice-control-btn"
            onClick={() => setShowHelp(!showHelp)}
            title="Voice Commands Help"
          >
            <i className="fas fa-question-circle" />
          </button>
          
          <button
            className="voice-control-btn"
            onClick={() => setShowAnalytics(!showAnalytics)}
            title="Voice Analytics"
          >
            <i className="fas fa-chart-bar" />
          </button>
        </div>
      </div>

      {isListening && (
        <VoiceIndicator 
          isListening={isListening}
          isProcessing={isProcessing}
          audioLevel={audioLevel}
        />
      )}

      {feedback && (
        <VoiceFeedback
          message={feedback.message}
          type={feedback.type}
          onClose={() => setFeedback(null)}
        />
      )}

      {lastCommand && (
        <div className="last-command">
          <strong>Last command:</strong> {lastCommand.text}
          <span className="confidence">({Math.round(lastCommand.confidence * 100)}% confident)</span>
        </div>
      )}

      {showSettings && voiceProfile && (
        <VoiceSettings
          profile={voiceProfile}
          onUpdate={updateVoiceProfile}
          onClose={() => setShowSettings(false)}
        />
      )}

      {showHistory && (
        <VoiceCommandHistory
          commands={commandHistory}
          onClose={() => setShowHistory(false)}
        />
      )}

      {showHelp && (
        <VoiceCommandHelp
          onClose={() => setShowHelp(false)}
        />
      )}

      {showAnalytics && (
        <VoiceAnalytics
          onClose={() => setShowAnalytics(false)}
        />
      )}
    </div>
  );
};

export default VoiceCommandManager;