import React, { useEffect, useRef } from 'react';
import './VoiceIndicator.css';

interface VoiceIndicatorProps {
  isListening: boolean;
  isProcessing: boolean;
  audioLevel: number;
}

const VoiceIndicator: React.FC<VoiceIndicatorProps> = ({ 
  isListening, 
  isProcessing, 
  audioLevel 
}) => {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const animationRef = useRef<number | null>(null);
  
  useEffect(() => {
    if (!canvasRef.current) return;
    
    const canvas = canvasRef.current;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;
    
    // Set canvas size
    canvas.width = 200;
    canvas.height = 200;
    
    const centerX = canvas.width / 2;
    const centerY = canvas.height / 2;
    const baseRadius = 40;
    
    let animationTime = 0;
    
    const animate = () => {
      ctx.clearRect(0, 0, canvas.width, canvas.height);
      
      if (isProcessing) {
        // Processing animation - spinning dots
        const dotCount = 8;
        const dotRadius = 4;
        const orbitRadius = 30;
        
        for (let i = 0; i < dotCount; i++) {
          const angle = (i / dotCount) * Math.PI * 2 + animationTime * 0.05;
          const x = centerX + Math.cos(angle) * orbitRadius;
          const y = centerY + Math.sin(angle) * orbitRadius;
          const opacity = 0.3 + (Math.sin(animationTime * 0.1 + i) + 1) * 0.35;
          
          ctx.fillStyle = `rgba(79, 70, 229, ${opacity})`;
          ctx.beginPath();
          ctx.arc(x, y, dotRadius, 0, Math.PI * 2);
          ctx.fill();
        }
      } else if (isListening) {
        // Listening animation - pulsing circles based on audio level
        const maxRings = 3;
        
        for (let i = 0; i < maxRings; i++) {
          const ringDelay = i * 0.3;
          const ringTime = (animationTime * 0.02 - ringDelay) % 1;
          
          if (ringTime > 0) {
            const radius = baseRadius + (audioLevel * 30) + (ringTime * 50);
            const opacity = (1 - ringTime) * (0.3 + audioLevel * 0.4);
            
            ctx.strokeStyle = `rgba(79, 70, 229, ${opacity})`;
            ctx.lineWidth = 2;
            ctx.beginPath();
            ctx.arc(centerX, centerY, radius, 0, Math.PI * 2);
            ctx.stroke();
          }
        }
        
        // Center circle
        const centerRadius = baseRadius + (audioLevel * 10);
        const gradient = ctx.createRadialGradient(centerX, centerY, 0, centerX, centerY, centerRadius);
        gradient.addColorStop(0, 'rgba(79, 70, 229, 0.8)');
        gradient.addColorStop(1, 'rgba(79, 70, 229, 0.4)');
        
        ctx.fillStyle = gradient;
        ctx.beginPath();
        ctx.arc(centerX, centerY, centerRadius, 0, Math.PI * 2);
        ctx.fill();
        
        // Audio level bars
        const barCount = 20;
        const barWidth = 3;
        const maxBarHeight = 30;
        
        for (let i = 0; i < barCount; i++) {
          const angle = (i / barCount) * Math.PI * 2;
          const barHeight = audioLevel * maxBarHeight * (0.5 + Math.random() * 0.5);
          const x1 = centerX + Math.cos(angle) * (centerRadius + 5);
          const y1 = centerY + Math.sin(angle) * (centerRadius + 5);
          const x2 = centerX + Math.cos(angle) * (centerRadius + 5 + barHeight);
          const y2 = centerY + Math.sin(angle) * (centerRadius + 5 + barHeight);
          
          ctx.strokeStyle = `rgba(79, 70, 229, ${0.6 + audioLevel * 0.4})`;
          ctx.lineWidth = barWidth;
          ctx.beginPath();
          ctx.moveTo(x1, y1);
          ctx.lineTo(x2, y2);
          ctx.stroke();
        }
      }
      
      // Microphone icon in center
      ctx.fillStyle = 'white';
      ctx.font = '24px Font Awesome 5 Free';
      ctx.textAlign = 'center';
      ctx.textBaseline = 'middle';
      ctx.fillText('\uf130', centerX, centerY);
      
      animationTime++;
      animationRef.current = requestAnimationFrame(animate);
    };
    
    animate();
    
    return () => {
      if (animationRef.current) {
        cancelAnimationFrame(animationRef.current);
      }
    };
  }, [isListening, isProcessing, audioLevel]);
  
  return (
    <div className="voice-indicator">
      <canvas ref={canvasRef} className="voice-canvas" />
      <div className="voice-status">
        {isProcessing ? 'Processing...' : isListening ? 'Listening...' : 'Ready'}
      </div>
      {isListening && !isProcessing && (
        <div className="voice-hint">
          Say "Hey BlueBird" followed by your command
        </div>
      )}
    </div>
  );
};

export default VoiceIndicator;