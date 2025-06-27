import React, { useState, useRef, useEffect } from 'react';
import { useI18n } from '../../contexts/I18nContext';
import './LanguageSwitcher.css';

interface LanguageSwitcherProps {
  className?: string;
  variant?: 'compact' | 'full' | 'icon-only';
  showFlags?: boolean;
  placement?: 'top' | 'bottom' | 'left' | 'right';
}

const LanguageSwitcher: React.FC<LanguageSwitcherProps> = ({
  className = '',
  variant = 'compact',
  showFlags = true,
  placement = 'bottom'
}) => {
  const { 
    currentLanguage, 
    availableLanguages, 
    changeLanguage, 
    isLoading, 
    t,
    isRTL
  } = useI18n();
  
  const [isOpen, setIsOpen] = useState(false);
  const dropdownRef = useRef<HTMLDivElement>(null);
  
  // Flag emoji mapping
  const flagMap: Record<string, string> = {
    en: '🇺🇸',
    es: '🇪🇸', 
    fr: '🇫🇷',
    de: '🇩🇪',
    zh: '🇨🇳',
    ja: '🇯🇵',
    ar: '🇸🇦',
    he: '🇮🇱'
  };

  // Close dropdown when clicking outside
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        setIsOpen(false);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
    };
  }, []);

  // Handle language change
  const handleLanguageChange = async (languageCode: string) => {
    setIsOpen(false);
    
    if (languageCode !== currentLanguage) {
      try {
        await changeLanguage(languageCode);
      } catch (error) {
        console.error('Failed to change language:', error);
      }
    }
  };

  // Get current language info
  const currentLang = availableLanguages.find(lang => lang.code === currentLanguage);
  
  // Keyboard navigation
  const handleKeyDown = (event: React.KeyboardEvent, languageCode?: string) => {
    if (event.key === 'Enter' || event.key === ' ') {
      event.preventDefault();
      if (languageCode) {
        handleLanguageChange(languageCode);
      } else {
        setIsOpen(!isOpen);
      }
    } else if (event.key === 'Escape') {
      setIsOpen(false);
    }
  };

  const renderCurrentLanguage = () => {
    if (!currentLang) return null;

    switch (variant) {
      case 'icon-only':
        return (
          <span className="language-flag" aria-label={currentLang.nativeName}>
            {showFlags && flagMap[currentLanguage]}
          </span>
        );
      
      case 'full':
        return (
          <div className="language-current-full">
            {showFlags && (
              <span className="language-flag">{flagMap[currentLanguage]}</span>
            )}
            <span className="language-name">{currentLang.nativeName}</span>
            <span className="language-code">({currentLanguage.toUpperCase()})</span>
          </div>
        );
      
      case 'compact':
      default:
        return (
          <div className="language-current-compact">
            {showFlags && (
              <span className="language-flag">{flagMap[currentLanguage]}</span>
            )}
            <span className="language-name">{currentLang.nativeName}</span>
          </div>
        );
    }
  };

  return (
    <div 
      className={`language-switcher ${className} ${isRTL ? 'rtl' : 'ltr'}`}
      ref={dropdownRef}
    >
      <button
        className={`language-button ${variant} ${isOpen ? 'open' : ''}`}
        onClick={() => setIsOpen(!isOpen)}
        onKeyDown={(e) => handleKeyDown(e)}
        aria-label={t('common.language')}
        aria-expanded={isOpen}
        aria-haspopup="listbox"
        disabled={isLoading}
      >
        {renderCurrentLanguage()}
        <span className={`dropdown-arrow ${isOpen ? 'open' : ''}`}>
          {isRTL ? '◂' : '▸'}
        </span>
      </button>

      {isOpen && (
        <div 
          className={`language-dropdown ${placement}`}
          role="listbox"
          aria-label={t('common.language')}
        >
          {availableLanguages.map((language) => (
            <button
              key={language.code}
              className={`language-option ${language.code === currentLanguage ? 'selected' : ''}`}
              onClick={() => handleLanguageChange(language.code)}
              onKeyDown={(e) => handleKeyDown(e, language.code)}
              role="option"
              aria-selected={language.code === currentLanguage}
              disabled={isLoading}
            >
              <div className="language-option-content">
                {showFlags && (
                  <span className="language-flag">{flagMap[language.code]}</span>
                )}
                <div className="language-text">
                  <span className="language-native">{language.nativeName}</span>
                  <span className="language-english">({language.name})</span>
                </div>
                {language.code === currentLanguage && (
                  <span className="checkmark" aria-hidden="true">✓</span>
                )}
              </div>
            </button>
          ))}
        </div>
      )}

      {isLoading && (
        <div className="language-loading" aria-live="polite">
          {t('common.loading')}
        </div>
      )}
    </div>
  );
};

export default LanguageSwitcher;