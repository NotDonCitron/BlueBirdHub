import React, { createContext, useContext, useEffect, useState, ReactNode } from 'react';
import { useTranslation } from 'react-i18next';
import { 
  supportedLanguages, 
  rtlLanguages, 
  getCurrentLanguage, 
  changeLanguage, 
  getAvailableLanguages,
  formatCurrency,
  formatDate,
  formatRelativeTime,
  preloadNamespace
} from '../config/i18n';

// Types
export interface Language {
  code: string;
  name: string;
  nativeName: string;
  rtl: boolean;
}

export interface I18nContextType {
  // Current language state
  currentLanguage: string;
  isRTL: boolean;
  availableLanguages: Language[];
  
  // Language management
  changeLanguage: (lng: string) => Promise<void>;
  getCurrentLanguage: () => string;
  
  // Translation functions
  t: (key: string, options?: any) => string;
  
  // Formatting functions
  formatCurrency: (amount: number, currency?: string) => string;
  formatDate: (date: Date | string, style?: 'short' | 'medium' | 'long' | 'full') => string;
  formatRelativeTime: (date: Date | string) => string;
  formatNumber: (number: number, options?: Intl.NumberFormatOptions) => string;
  
  // Namespace management
  loadNamespace: (ns: string) => Promise<void>;
  
  // Pluralization helpers
  getPlural: (key: string, count: number, options?: any) => string;
  
  // Validation
  isKeyExists: (key: string, ns?: string) => boolean;
  
  // Gender support
  getGenderedText: (key: string, gender: 'male' | 'female' | 'neutral', options?: any) => string;
  
  // Loading state
  isLoading: boolean;
  
  // Error handling
  translationError: string | null;
}

const I18nContext = createContext<I18nContextType | undefined>(undefined);

interface I18nProviderProps {
  children: ReactNode;
  defaultLanguage?: string;
}

export const I18nProvider: React.FC<I18nProviderProps> = ({ 
  children, 
  defaultLanguage 
}) => {
  const { t, i18n, ready } = useTranslation();
  const [currentLanguage, setCurrentLanguage] = useState<string>(getCurrentLanguage());
  const [isRTL, setIsRTL] = useState<boolean>(rtlLanguages.includes(getCurrentLanguage()));
  const [isLoading, setIsLoading] = useState<boolean>(!ready);
  const [translationError, setTranslationError] = useState<string | null>(null);
  
  const availableLanguages = getAvailableLanguages();

  // Language change handler
  const handleLanguageChange = async (lng: string): Promise<void> => {
    try {
      setIsLoading(true);
      setTranslationError(null);
      
      // Validate language
      if (!supportedLanguages[lng as keyof typeof supportedLanguages]) {
        throw new Error(`Unsupported language: ${lng}`);
      }
      
      // Change language
      await changeLanguage(lng);
      
      // Update state
      setCurrentLanguage(lng);
      setIsRTL(rtlLanguages.includes(lng));
      
      // Update document attributes
      document.documentElement.lang = lng;
      document.documentElement.dir = rtlLanguages.includes(lng) ? 'rtl' : 'ltr';
      
      // Store preference
      localStorage.setItem('preferredLanguage', lng);
      
    } catch (error) {
      setTranslationError(`Failed to change language: ${error}`);
      console.error('Language change error:', error);
    } finally {
      setIsLoading(false);
    }
  };

  // Format number with current locale
  const formatNumber = (number: number, options: Intl.NumberFormatOptions = {}): string => {
    try {
      return new Intl.NumberFormat(currentLanguage, options).format(number);
    } catch (error) {
      console.warn('Number formatting error:', error);
      return number.toString();
    }
  };

  // Load additional namespace
  const loadNamespace = async (ns: string): Promise<void> => {
    try {
      setIsLoading(true);
      await preloadNamespace(ns, currentLanguage);
    } catch (error) {
      setTranslationError(`Failed to load namespace: ${ns}`);
      console.error('Namespace loading error:', error);
    } finally {
      setIsLoading(false);
    }
  };

  // Get plural form
  const getPlural = (key: string, count: number, options: any = {}): string => {
    return t(key, { count, ...options });
  };

  // Check if translation key exists
  const isKeyExists = (key: string, ns?: string): boolean => {
    return i18n.exists(key, { ns });
  };

  // Get gendered text
  const getGenderedText = (key: string, gender: 'male' | 'female' | 'neutral', options: any = {}): string => {
    const genderedKey = `${key}_${gender}`;
    if (isKeyExists(genderedKey)) {
      return t(genderedKey, options);
    }
    // Fallback to neutral or base key
    return t(key, options);
  };

  // Listen for language changes
  useEffect(() => {
    const handleI18nLanguageChange = (lng: string) => {
      setCurrentLanguage(lng);
      setIsRTL(rtlLanguages.includes(lng));
    };

    i18n.on('languageChanged', handleI18nLanguageChange);
    
    return () => {
      i18n.off('languageChanged', handleI18nLanguageChange);
    };
  }, [i18n]);

  // Initialize default language
  useEffect(() => {
    if (defaultLanguage && defaultLanguage !== currentLanguage) {
      handleLanguageChange(defaultLanguage);
    }
  }, [defaultLanguage]);

  // Listen for i18n ready state
  useEffect(() => {
    setIsLoading(!ready);
  }, [ready]);

  // Context value
  const contextValue: I18nContextType = {
    currentLanguage,
    isRTL,
    availableLanguages,
    changeLanguage: handleLanguageChange,
    getCurrentLanguage: () => currentLanguage,
    t,
    formatCurrency,
    formatDate,
    formatRelativeTime,
    formatNumber,
    loadNamespace,
    getPlural,
    isKeyExists,
    getGenderedText,
    isLoading,
    translationError
  };

  return (
    <I18nContext.Provider value={contextValue}>
      {children}
    </I18nContext.Provider>
  );
};

// Custom hook to use I18n context
export const useI18n = (): I18nContextType => {
  const context = useContext(I18nContext);
  if (context === undefined) {
    throw new Error('useI18n must be used within an I18nProvider');
  }
  return context;
};

// HOC for class components
export const withI18n = <P extends object>(Component: React.ComponentType<P>) => {
  return React.forwardRef<any, P>((props, ref) => {
    const i18nContext = useI18n();
    return <Component {...props} ref={ref} i18n={i18nContext} />;
  });
};

// Custom hooks for specific use cases
export const useTranslationWithNamespace = (namespace: string) => {
  const { t, loadNamespace } = useI18n();
  
  useEffect(() => {
    loadNamespace(namespace);
  }, [namespace, loadNamespace]);
  
  return (key: string, options?: any) => t(`${namespace}:${key}`, options);
};

export const useRTL = () => {
  const { isRTL } = useI18n();
  return isRTL;
};

export const useLanguageDirection = () => {
  const { isRTL } = useI18n();
  return isRTL ? 'rtl' : 'ltr';
};

export const useLocalizedFormatting = () => {
  const { formatCurrency, formatDate, formatRelativeTime, formatNumber } = useI18n();
  
  return {
    currency: formatCurrency,
    date: formatDate,
    relativeTime: formatRelativeTime,
    number: formatNumber
  };
};

export default I18nContext;