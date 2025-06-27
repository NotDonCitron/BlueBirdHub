import i18n from 'i18next';
import { initReactI18next } from 'react-i18next';
import Backend from 'i18next-http-backend';
import LanguageDetector from 'i18next-browser-languagedetector';
import ChainedBackend from 'i18next-chained-backend';
import LocalStorageBackend from 'i18next-localstorage-backend';
import MultiloadBackendAdapter from 'i18next-multiload-backend-adapter';
import sprintf from 'i18next-sprintf-postprocessor';

// Supported languages configuration
export const supportedLanguages = {
  en: { name: 'English', nativeName: 'English', rtl: false },
  es: { name: 'Spanish', nativeName: 'Español', rtl: false },
  fr: { name: 'French', nativeName: 'Français', rtl: false },
  de: { name: 'German', nativeName: 'Deutsch', rtl: false },
  zh: { name: 'Chinese', nativeName: '中文', rtl: false },
  ja: { name: 'Japanese', nativeName: '日本語', rtl: false },
  ar: { name: 'Arabic', nativeName: 'العربية', rtl: true },
  he: { name: 'Hebrew', nativeName: 'עברית', rtl: true }
};

export const defaultLanguage = 'en';
export const fallbackLanguages = ['en'];

// RTL languages
export const rtlLanguages = ['ar', 'he'];

// Language detector configuration
const languageDetectorOptions = {
  // Order and from where user language should be detected
  order: ['localStorage', 'navigator', 'htmlTag', 'path', 'subdomain'],
  
  // Keys or params to lookup language from
  lookupLocalStorage: 'i18nextLng',
  lookupFromPathIndex: 0,
  lookupFromSubdomainIndex: 0,
  
  // Cache user language on
  caches: ['localStorage'],
  excludeCacheFor: ['cimode'], // Languages to not persist (i.e. dev mode)
  
  // Optional expire and versions
  cookieMinutes: 10080, // 7 days
  cookieDomain: 'myDomain',
  
  // Optional htmlTag with lang attribute
  htmlTag: document.documentElement,
  
  // Optional set cookie options
  cookieOptions: { path: '/', sameSite: 'strict' }
};

// Backend configuration for loading translations
const backendOptions = {
  backends: [
    LocalStorageBackend,  // Primary: use localStorage
    MultiloadBackendAdapter // Fallback: load from HTTP
  ],
  backendOptions: [
    {
      // LocalStorageBackend options
      expirationTime: 7 * 24 * 60 * 60 * 1000, // 7 days
      defaultVersion: 'v1.0.0'
    },
    {
      // HTTP Backend options wrapped in MultiloadBackendAdapter
      backend: Backend,
      backendOption: {
        loadPath: '/locales/{{lng}}/{{ns}}.json',
        allowMultiLoading: true,
        crossDomain: false,
        withCredentials: false,
        // Custom headers
        customHeaders: {
          'Cache-Control': 'no-cache'
        },
        // Request timeout
        requestOptions: {
          cache: 'default'
        }
      }
    }
  ]
};

// Initialize i18next
i18n
  .use(ChainedBackend)
  .use(LanguageDetector)
  .use(sprintf) // Enable sprintf postprocessor for advanced formatting
  .use(initReactI18next)
  .init({
    // Language configuration
    lng: defaultLanguage,
    fallbackLng: fallbackLanguages,
    supportedLngs: Object.keys(supportedLanguages),
    
    // Namespace configuration
    ns: ['common', 'navigation', 'dashboard', 'workspace', 'tasks', 'files', 'ai', 'settings', 'auth', 'errors'],
    defaultNS: 'common',
    
    // Backend configuration
    backend: backendOptions,
    
    // Language detection
    detection: languageDetectorOptions,
    
    // Development configuration
    debug: process.env.NODE_ENV === 'development',
    
    // Translation options
    keySeparator: '.',
    nsSeparator: ':',
    
    // Interpolation options
    interpolation: {
      escapeValue: false, // React already does escaping
      formatSeparator: ',',
      format: function(value, format, lng, options) {
        if (format === 'uppercase') return value.toUpperCase();
        if (format === 'lowercase') return value.toLowerCase();
        if (format === 'capitalize') return value.charAt(0).toUpperCase() + value.slice(1);
        
        // Date formatting
        if (format.startsWith('date')) {
          const dateFormat = format.split(':')[1] || 'medium';
          return new Intl.DateTimeFormat(lng, {
            dateStyle: dateFormat as any
          }).format(new Date(value));
        }
        
        // Number formatting
        if (format.startsWith('number')) {
          const numberFormat = format.split(':')[1] || 'decimal';
          return new Intl.NumberFormat(lng, {
            style: numberFormat === 'currency' ? 'currency' : 'decimal',
            currency: numberFormat === 'currency' ? 'USD' : undefined
          }).format(value);
        }
        
        return value;
      }
    },
    
    // Pluralization
    pluralSeparator: '_',
    contextSeparator: '_',
    
    // Post processing
    postProcess: ['sprintf'],
    
    // React specific options
    react: {
      useSuspense: false, // Disable suspense for better error handling
      bindI18n: 'languageChanged',
      bindI18nStore: 'added removed',
      transEmptyNodeValue: '',
      transSupportBasicHtmlNodes: true,
      transKeepBasicHtmlNodesFor: ['br', 'strong', 'i', 'em', 'span'],
      transWrapTextNodes: ''
    },
    
    // Performance options
    load: 'languageOnly', // Load only language code, not region
    preload: [defaultLanguage], // Preload default language
    
    // Caching
    updateMissing: process.env.NODE_ENV === 'development',
    saveMissing: process.env.NODE_ENV === 'development',
    
    // Retry configuration
    retryOptions: {
      retries: 3,
      retryDelay: function(attempt: number) {
        return Math.pow(2, attempt) * 100; // Exponential backoff
      }
    }
  });

// Language change handler
i18n.on('languageChanged', (lng) => {
  // Update document direction for RTL languages
  const isRTL = rtlLanguages.includes(lng);
  document.documentElement.dir = isRTL ? 'rtl' : 'ltr';
  document.documentElement.lang = lng;
  
  // Store language preference
  localStorage.setItem('i18nextLng', lng);
  
  // Emit custom event for other components to listen
  window.dispatchEvent(new CustomEvent('languageChanged', { detail: { language: lng, isRTL } }));
});

// Utility functions
export const getCurrentLanguage = () => i18n.language;
export const isRTL = () => rtlLanguages.includes(i18n.language);
export const changeLanguage = (lng: string) => i18n.changeLanguage(lng);

// Translation validation utility
export const validateTranslationKey = (key: string, ns?: string): boolean => {
  return i18n.exists(key, { ns });
};

// Get missing translations for development
export const getMissingTranslations = (): Record<string, any> => {
  return (i18n as any).store?.data || {};
};

// Preload specific namespace
export const preloadNamespace = (ns: string, lng?: string) => {
  return i18n.loadNamespaces(ns, lng);
};

// Get available languages
export const getAvailableLanguages = () => {
  return Object.entries(supportedLanguages).map(([code, info]) => ({
    code,
    ...info
  }));
};

// Format currency for current locale
export const formatCurrency = (amount: number, currency = 'USD') => {
  return new Intl.NumberFormat(i18n.language, {
    style: 'currency',
    currency
  }).format(amount);
};

// Format date for current locale
export const formatDate = (date: Date | string, style: 'short' | 'medium' | 'long' | 'full' = 'medium') => {
  return new Intl.DateTimeFormat(i18n.language, {
    dateStyle: style
  }).format(new Date(date));
};

// Format relative time
export const formatRelativeTime = (date: Date | string) => {
  const rtf = new Intl.RelativeTimeFormat(i18n.language, { numeric: 'auto' });
  const diff = Date.now() - new Date(date).getTime();
  const days = Math.floor(diff / (1000 * 60 * 60 * 24));
  
  if (days === 0) return rtf.format(0, 'day');
  if (days < 7) return rtf.format(-days, 'day');
  if (days < 30) return rtf.format(-Math.floor(days / 7), 'week');
  if (days < 365) return rtf.format(-Math.floor(days / 30), 'month');
  return rtf.format(-Math.floor(days / 365), 'year');
};

export default i18n;