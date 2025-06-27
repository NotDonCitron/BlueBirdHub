import React, { useEffect, useState } from 'react';
import './VoiceFeedback.css';

interface VoiceFeedbackProps {
  message: string;
  type: 'success' | 'error' | 'info' | 'warning';
  onClose: () => void;
  duration?: number;
  speak?: boolean;
}

const VoiceFeedback: React.FC<VoiceFeedbackProps> = ({ 
  message, 
  type, 
  onClose, 
  duration = 5000,
  speak = false 
}) => {
  const [isVisible, setIsVisible] = useState(true);
  const [progress, setProgress] = useState(100);

  useEffect(() => {
    const startTime = Date.now();
    
    const updateProgress = () => {
      const elapsed = Date.now() - startTime;
      const remaining = Math.max(0, 100 - (elapsed / duration) * 100);
      setProgress(remaining);
      
      if (remaining > 0) {
        requestAnimationFrame(updateProgress);
      } else {
        setIsVisible(false);
        setTimeout(onClose, 300);
      }
    };
    
    requestAnimationFrame(updateProgress);
    
    // Speak the message if requested
    if (speak && 'speechSynthesis' in window) {
      const utterance = new SpeechSynthesisUtterance(message);
      utterance.rate = 1.0;
      utterance.pitch = 1.0;
      utterance.volume = 0.8;
      speechSynthesis.speak(utterance);
    }
    
    return () => {
      if (speak && 'speechSynthesis' in window) {
        speechSynthesis.cancel();
      }
    };
  }, [message, duration, onClose, speak]);

  const icons = {
    success: 'fa-check-circle',
    error: 'fa-exclamation-circle',
    info: 'fa-info-circle',
    warning: 'fa-exclamation-triangle'
  };

  const handleClick = () => {
    setIsVisible(false);
    setTimeout(onClose, 300);
  };

  return (
    <div className={`voice-feedback ${type} ${!isVisible ? 'fade-out' : ''}`} onClick={handleClick}>
      <div className="voice-feedback-content">
        <i className={`fas ${icons[type]}`} />
        <span>{message}</span>
      </div>
      <div className="voice-feedback-progress">
        <div 
          className="voice-feedback-progress-bar" 
          style={{ width: `${progress}%` }}
        />
      </div>
    </div>
  );
};

export default VoiceFeedback;