/**
 * Voice Accessibility Service
 * Provides accessibility features and screen reader integration for voice commands
 */

interface AccessibilitySettings {
  screenReaderEnabled: boolean;
  voiceCommandsEnabled: boolean;
  audioFeedbackEnabled: boolean;
  visualIndicatorsEnabled: boolean;
  keyboardShortcutsEnabled: boolean;
  highContrastMode: boolean;
  largeTextMode: boolean;
  reducedMotionMode: boolean;
  autoFocusEnabled: boolean;
  skipLinksEnabled: boolean;
}

interface VoiceCommandShortcut {
  command: string;
  description: string;
  category: string;
  ariaLabel: string;
  keyboardAlternative?: string;
}

class VoiceAccessibilityService {
  private settings: AccessibilitySettings;
  private isScreenReaderActive: boolean = false;
  private speechSynthesis: SpeechSynthesis | null = null;
  private voiceURI: string = '';
  private speechRate: number = 1;
  private speechPitch: number = 1;
  private speechVolume: number = 1;

  constructor() {
    this.settings = this.loadSettings();
    this.initializeSpeechSynthesis();
    this.detectScreenReader();
    this.setupKeyboardShortcuts();
    this.setupAccessibilityObserver();
  }

  private loadSettings(): AccessibilitySettings {
    const saved = localStorage.getItem('voice-accessibility-settings');
    return saved ? JSON.parse(saved) : {
      screenReaderEnabled: false,
      voiceCommandsEnabled: true,
      audioFeedbackEnabled: true,
      visualIndicatorsEnabled: true,
      keyboardShortcutsEnabled: true,
      highContrastMode: false,
      largeTextMode: false,
      reducedMotionMode: false,
      autoFocusEnabled: true,
      skipLinksEnabled: true
    };
  }

  private saveSettings(): void {
    localStorage.setItem('voice-accessibility-settings', JSON.stringify(this.settings));
  }

  private initializeSpeechSynthesis(): void {
    if ('speechSynthesis' in window) {
      this.speechSynthesis = window.speechSynthesis;
      
      // Load preferred voice
      const savedVoice = localStorage.getItem('preferred-voice');
      if (savedVoice) {
        this.voiceURI = savedVoice;
      }

      // Load speech settings
      this.speechRate = parseFloat(localStorage.getItem('speech-rate') || '1');
      this.speechPitch = parseFloat(localStorage.getItem('speech-pitch') || '1');
      this.speechVolume = parseFloat(localStorage.getItem('speech-volume') || '1');
    }
  }

  private detectScreenReader(): void {
    // Check for common screen reader indicators
    const hasScreenReader = 
      navigator.userAgent.includes('NVDA') ||
      navigator.userAgent.includes('JAWS') ||
      navigator.userAgent.includes('VoiceOver') ||
      navigator.userAgent.includes('TalkBack') ||
      window.speechSynthesis?.speaking ||
      document.querySelector('[aria-live]') !== null;

    this.isScreenReaderActive = hasScreenReader;
    
    // Also check for reduced motion preference
    const prefersReducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    if (prefersReducedMotion) {
      this.settings.reducedMotionMode = true;
    }

    // Check for high contrast preference
    const prefersHighContrast = window.matchMedia('(prefers-contrast: high)').matches;
    if (prefersHighContrast) {
      this.settings.highContrastMode = true;
    }
  }

  private setupKeyboardShortcuts(): void {
    if (!this.settings.keyboardShortcutsEnabled) return;

    document.addEventListener('keydown', (event) => {
      // Alt + V: Toggle voice commands
      if (event.altKey && event.key === 'v') {
        event.preventDefault();
        this.toggleVoiceCommands();
      }

      // Alt + H: Voice help
      if (event.altKey && event.key === 'h') {
        event.preventDefault();
        this.announceVoiceHelp();
      }

      // Alt + R: Read current page
      if (event.altKey && event.key === 'r') {
        event.preventDefault();
        this.readCurrentPage();
      }

      // Alt + S: Voice settings
      if (event.altKey && event.key === 's') {
        event.preventDefault();
        this.announceVoiceSettings();
      }

      // Escape: Stop speech
      if (event.key === 'Escape') {
        this.stopSpeech();
      }
    });
  }

  private setupAccessibilityObserver(): void {
    // Observe changes to ARIA live regions
    const observer = new MutationObserver((mutations) => {
      mutations.forEach((mutation) => {
        if (mutation.type === 'childList') {
          const target = mutation.target as Element;
          if (target.getAttribute('aria-live') === 'assertive' || 
              target.getAttribute('aria-live') === 'polite') {
            this.announceAriaLiveContent(target);
          }
        }
      });
    });

    observer.observe(document.body, {
      childList: true,
      subtree: true,
      attributes: true,
      attributeFilter: ['aria-live', 'aria-label', 'aria-describedby']
    });
  }

  public speak(text: string, priority: 'high' | 'medium' | 'low' = 'medium'): void {
    if (!this.settings.audioFeedbackEnabled || !this.speechSynthesis) return;

    // Cancel lower priority speech
    if (priority === 'high') {
      this.speechSynthesis.cancel();
    }

    const utterance = new SpeechSynthesisUtterance(text);
    utterance.rate = this.speechRate;
    utterance.pitch = this.speechPitch;
    utterance.volume = this.speechVolume;

    // Set voice if available
    if (this.voiceURI) {
      const voices = this.speechSynthesis.getVoices();
      const selectedVoice = voices.find(voice => voice.voiceURI === this.voiceURI);
      if (selectedVoice) {
        utterance.voice = selectedVoice;
      }
    }

    this.speechSynthesis.speak(utterance);
  }

  public stopSpeech(): void {
    if (this.speechSynthesis) {
      this.speechSynthesis.cancel();
    }
  }

  public announceVoiceCommand(command: string, confidence: number): void {
    if (this.isScreenReaderActive) {
      const confidenceText = confidence > 0.8 ? 'with high confidence' : 
                            confidence > 0.6 ? 'with medium confidence' : 
                            'with low confidence';
      
      this.speak(`Voice command detected: ${command}, ${confidenceText}`, 'high');
    }
  }

  public announceCommandResult(result: string, success: boolean): void {
    const prefix = success ? 'Success:' : 'Error:';
    this.speak(`${prefix} ${result}`, success ? 'medium' : 'high');
  }

  public announceNavigationChange(page: string): void {
    this.speak(`Navigated to ${page}`, 'medium');
    
    // Focus management
    if (this.settings.autoFocusEnabled) {
      setTimeout(() => {
        const mainHeading = document.querySelector('h1');
        if (mainHeading && mainHeading instanceof HTMLElement) {
          mainHeading.focus();
        }
      }, 100);
    }
  }

  public announceTaskCreated(taskTitle: string): void {
    this.speak(`Task created: ${taskTitle}`, 'medium');
  }

  public announceTaskUpdated(taskTitle: string): void {
    this.speak(`Task updated: ${taskTitle}`, 'medium');
  }

  public announceError(error: string): void {
    this.speak(`Error: ${error}`, 'high');
  }

  private announceAriaLiveContent(element: Element): void {
    const text = element.textContent?.trim();
    if (text && this.settings.audioFeedbackEnabled) {
      const priority = element.getAttribute('aria-live') === 'assertive' ? 'high' : 'medium';
      this.speak(text, priority as 'high' | 'medium');
    }
  }

  private toggleVoiceCommands(): void {
    this.settings.voiceCommandsEnabled = !this.settings.voiceCommandsEnabled;
    this.saveSettings();
    
    const status = this.settings.voiceCommandsEnabled ? 'enabled' : 'disabled';
    this.speak(`Voice commands ${status}`, 'high');
    
    // Dispatch custom event
    document.dispatchEvent(new CustomEvent('voice-commands-toggled', {
      detail: { enabled: this.settings.voiceCommandsEnabled }
    }));
  }

  private announceVoiceHelp(): void {
    const helpText = `
      Voice commands available:
      Say "Hey BlueBird" followed by your command.
      Examples:
      Create a task to review documents.
      Show me high priority tasks.
      Navigate to dashboard.
      Set priority to urgent.
      For full list, press Alt H again or visit help section.
    `;
    this.speak(helpText, 'high');
  }

  private readCurrentPage(): void {
    const mainContent = document.querySelector('main') || 
                       document.querySelector('[role="main"]') ||
                       document.body;
    
    if (mainContent) {
      const text = this.extractReadableText(mainContent);
      this.speak(text, 'medium');
    }
  }

  private announceVoiceSettings(): void {
    const settingsText = `
      Voice settings:
      Voice commands are ${this.settings.voiceCommandsEnabled ? 'enabled' : 'disabled'}.
      Audio feedback is ${this.settings.audioFeedbackEnabled ? 'enabled' : 'disabled'}.
      Speech rate is ${this.speechRate}.
      To change settings, navigate to voice settings panel.
    `;
    this.speak(settingsText, 'medium');
  }

  private extractReadableText(element: Element): string {
    // Extract text while respecting semantic structure
    const walker = document.createTreeWalker(
      element,
      NodeFilter.SHOW_TEXT | NodeFilter.SHOW_ELEMENT,
      {
        acceptNode: (node) => {
          if (node.nodeType === Node.TEXT_NODE) {
            return NodeFilter.FILTER_ACCEPT;
          }
          
          const element = node as Element;
          
          // Skip hidden elements
          if (element.hidden || 
              element.getAttribute('aria-hidden') === 'true' ||
              getComputedStyle(element).display === 'none') {
            return NodeFilter.FILTER_REJECT;
          }
          
          // Include semantic elements
          if (['H1', 'H2', 'H3', 'H4', 'H5', 'H6', 'P', 'LI', 'BUTTON', 'A'].includes(element.tagName)) {
            return NodeFilter.FILTER_ACCEPT;
          }
          
          return NodeFilter.FILTER_SKIP;
        }
      }
    );

    const textParts: string[] = [];
    let node;

    while (node = walker.nextNode()) {
      if (node.nodeType === Node.TEXT_NODE) {
        const text = node.textContent?.trim();
        if (text) {
          textParts.push(text);
        }
      } else {
        const element = node as Element;
        const ariaLabel = element.getAttribute('aria-label');
        if (ariaLabel) {
          textParts.push(ariaLabel);
        }
      }
    }

    return textParts.join(' ').replace(/\s+/g, ' ').trim();
  }

  public getVoiceCommandShortcuts(): VoiceCommandShortcut[] {
    return [
      {
        command: 'Hey BlueBird, create task',
        description: 'Create a new task',
        category: 'Task Management',
        ariaLabel: 'Voice command to create a new task',
        keyboardAlternative: 'Ctrl + N'
      },
      {
        command: 'Hey BlueBird, show tasks',
        description: 'Display task list',
        category: 'Task Management',
        ariaLabel: 'Voice command to show all tasks',
        keyboardAlternative: 'Ctrl + T'
      },
      {
        command: 'Hey BlueBird, go to dashboard',
        description: 'Navigate to dashboard',
        category: 'Navigation',
        ariaLabel: 'Voice command to navigate to dashboard',
        keyboardAlternative: 'Ctrl + D'
      },
      {
        command: 'Hey BlueBird, help',
        description: 'Show voice command help',
        category: 'Help',
        ariaLabel: 'Voice command to show help information',
        keyboardAlternative: 'Alt + H'
      },
      {
        command: 'Hey BlueBird, settings',
        description: 'Open voice settings',
        category: 'Settings',
        ariaLabel: 'Voice command to open voice settings',
        keyboardAlternative: 'Alt + S'
      }
    ];
  }

  public updateSettings(newSettings: Partial<AccessibilitySettings>): void {
    this.settings = { ...this.settings, ...newSettings };
    this.saveSettings();
    
    // Apply immediate changes
    if (newSettings.highContrastMode !== undefined) {
      document.body.classList.toggle('high-contrast', newSettings.highContrastMode);
    }
    
    if (newSettings.largeTextMode !== undefined) {
      document.body.classList.toggle('large-text', newSettings.largeTextMode);
    }
    
    if (newSettings.reducedMotionMode !== undefined) {
      document.body.classList.toggle('reduced-motion', newSettings.reducedMotionMode);
    }
  }

  public getSettings(): AccessibilitySettings {
    return { ...this.settings };
  }

  public setSpeechSettings(rate: number, pitch: number, volume: number, voiceURI?: string): void {
    this.speechRate = Math.max(0.1, Math.min(2, rate));
    this.speechPitch = Math.max(0, Math.min(2, pitch));
    this.speechVolume = Math.max(0, Math.min(1, volume));
    
    if (voiceURI) {
      this.voiceURI = voiceURI;
      localStorage.setItem('preferred-voice', voiceURI);
    }
    
    localStorage.setItem('speech-rate', this.speechRate.toString());
    localStorage.setItem('speech-pitch', this.speechPitch.toString());
    localStorage.setItem('speech-volume', this.speechVolume.toString());
  }

  public getAvailableVoices(): SpeechSynthesisVoice[] {
    return this.speechSynthesis ? this.speechSynthesis.getVoices() : [];
  }

  public isScreenReaderDetected(): boolean {
    return this.isScreenReaderActive;
  }

  public addSkipLink(targetId: string, text: string): void {
    if (!this.settings.skipLinksEnabled) return;

    const skipLink = document.createElement('a');
    skipLink.href = `#${targetId}`;
    skipLink.textContent = text;
    skipLink.className = 'skip-link';
    skipLink.style.cssText = `
      position: absolute;
      left: -9999px;
      z-index: 999;
      padding: 8px;
      background: #000;
      color: #fff;
      text-decoration: none;
      font-weight: bold;
    `;
    
    skipLink.addEventListener('focus', () => {
      skipLink.style.left = '6px';
      skipLink.style.top = '6px';
    });
    
    skipLink.addEventListener('blur', () => {
      skipLink.style.left = '-9999px';
    });
    
    document.body.insertBefore(skipLink, document.body.firstChild);
  }

  public announceLoadingState(isLoading: boolean, context?: string): void {
    const message = isLoading ? 
      `Loading ${context || 'content'}...` : 
      `${context || 'Content'} loaded successfully`;
    
    this.speak(message, 'medium');
  }

  public announceFormValidation(errors: string[]): void {
    if (errors.length > 0) {
      const message = `Form has ${errors.length} error${errors.length > 1 ? 's' : ''}: ${errors.join(', ')}`;
      this.speak(message, 'high');
    }
  }
}

export default new VoiceAccessibilityService();