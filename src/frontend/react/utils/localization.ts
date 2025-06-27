import { format as formatDate, formatDistanceToNow, formatRelative, parseISO } from 'date-fns';
import { enUS, es, fr, de, zhCN, ja, ar, he } from 'date-fns/locale';

// Locale mapping for date-fns
const dateLocales = {
  en: enUS,
  es: es,
  fr: fr,
  de: de,
  zh: zhCN,
  ja: ja,
  ar: ar,
  he: he
};

// Currency mapping by country/language
const currencyMap: Record<string, string> = {
  en: 'USD',
  es: 'EUR',
  fr: 'EUR',
  de: 'EUR',
  zh: 'CNY',
  ja: 'JPY',
  ar: 'SAR',
  he: 'ILS'
};

// Timezone mapping
const timezoneMap: Record<string, string> = {
  en: 'America/New_York',
  es: 'Europe/Madrid',
  fr: 'Europe/Paris',
  de: 'Europe/Berlin',
  zh: 'Asia/Shanghai',
  ja: 'Asia/Tokyo',
  ar: 'Asia/Riyadh',
  he: 'Asia/Jerusalem'
};

export interface LocalizationOptions {
  locale: string;
  currency?: string;
  timezone?: string;
  numberSystem?: 'latn' | 'arab' | 'deva' | 'thai';
}

export class LocalizationFormatter {
  private locale: string;
  private currency: string;
  private timezone: string;
  private dateLocale: Locale;

  constructor(options: LocalizationOptions) {
    this.locale = options.locale || 'en';
    this.currency = options.currency || currencyMap[this.locale] || 'USD';
    this.timezone = options.timezone || timezoneMap[this.locale] || 'UTC';
    this.dateLocale = dateLocales[this.locale as keyof typeof dateLocales] || enUS;
  }

  // Date and Time Formatting
  formatDate(date: Date | string | number, style: 'short' | 'medium' | 'long' | 'full' = 'medium'): string {
    try {
      const dateObj = typeof date === 'string' ? parseISO(date) : new Date(date);
      
      const formatOptions: Intl.DateTimeFormatOptions = {
        timeZone: this.timezone
      };

      switch (style) {
        case 'short':
          formatOptions.dateStyle = 'short';
          break;
        case 'long':
          formatOptions.dateStyle = 'long';
          break;
        case 'full':
          formatOptions.dateStyle = 'full';
          break;
        default:
          formatOptions.dateStyle = 'medium';
      }

      return new Intl.DateTimeFormat(this.locale, formatOptions).format(dateObj);
    } catch (error) {
      console.error('Date formatting error:', error);
      return date.toString();
    }
  }

  formatTime(date: Date | string | number, style: 'short' | 'medium' | 'long' = 'short'): string {
    try {
      const dateObj = typeof date === 'string' ? parseISO(date) : new Date(date);
      
      const formatOptions: Intl.DateTimeFormatOptions = {
        timeZone: this.timezone
      };

      switch (style) {
        case 'medium':
          formatOptions.timeStyle = 'medium';
          break;
        case 'long':
          formatOptions.timeStyle = 'long';
          break;
        default:
          formatOptions.timeStyle = 'short';
      }

      return new Intl.DateTimeFormat(this.locale, formatOptions).format(dateObj);
    } catch (error) {
      console.error('Time formatting error:', error);
      return date.toString();
    }
  }

  formatDateTime(date: Date | string | number, dateStyle: 'short' | 'medium' | 'long' = 'medium', timeStyle: 'short' | 'medium' | 'long' = 'short'): string {
    try {
      const dateObj = typeof date === 'string' ? parseISO(date) : new Date(date);
      
      return new Intl.DateTimeFormat(this.locale, {
        dateStyle,
        timeStyle,
        timeZone: this.timezone
      }).format(dateObj);
    } catch (error) {
      console.error('DateTime formatting error:', error);
      return date.toString();
    }
  }

  formatRelativeTime(date: Date | string | number): string {
    try {
      const dateObj = typeof date === 'string' ? parseISO(date) : new Date(date);
      return formatDistanceToNow(dateObj, { 
        addSuffix: true, 
        locale: this.dateLocale 
      });
    } catch (error) {
      console.error('Relative time formatting error:', error);
      return '';
    }
  }

  formatRelativeTimeWithContext(date: Date | string | number): string {
    try {
      const dateObj = typeof date === 'string' ? parseISO(date) : new Date(date);
      return formatRelative(dateObj, new Date(), { 
        locale: this.dateLocale 
      });
    } catch (error) {
      console.error('Relative time with context formatting error:', error);
      return '';
    }
  }

  // Number Formatting
  formatNumber(number: number, options: Intl.NumberFormatOptions = {}): string {
    try {
      return new Intl.NumberFormat(this.locale, options).format(number);
    } catch (error) {
      console.error('Number formatting error:', error);
      return number.toString();
    }
  }

  formatInteger(number: number): string {
    return this.formatNumber(number, { maximumFractionDigits: 0 });
  }

  formatDecimal(number: number, decimals: number = 2): string {
    return this.formatNumber(number, { 
      minimumFractionDigits: decimals,
      maximumFractionDigits: decimals 
    });
  }

  formatPercent(number: number, decimals: number = 1): string {
    return this.formatNumber(number / 100, { 
      style: 'percent',
      minimumFractionDigits: decimals,
      maximumFractionDigits: decimals 
    });
  }

  formatFileSize(bytes: number): string {
    if (bytes === 0) return '0 B';
    
    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB', 'TB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    
    const size = bytes / Math.pow(k, i);
    return `${this.formatDecimal(size, i === 0 ? 0 : 1)} ${sizes[i]}`;
  }

  // Currency Formatting
  formatCurrency(amount: number, currency?: string, options: Intl.NumberFormatOptions = {}): string {
    try {
      const currencyCode = currency || this.currency;
      return new Intl.NumberFormat(this.locale, {
        style: 'currency',
        currency: currencyCode,
        ...options
      }).format(amount);
    } catch (error) {
      console.error('Currency formatting error:', error);
      return `${amount} ${currency || this.currency}`;
    }
  }

  formatCurrencyCompact(amount: number, currency?: string): string {
    return this.formatCurrency(amount, currency, { notation: 'compact' });
  }

  formatCurrencyAccounting(amount: number, currency?: string): string {
    return this.formatCurrency(amount, currency, { currencySign: 'accounting' });
  }

  // Address Formatting
  formatAddress(address: {
    street?: string;
    city?: string;
    state?: string;
    postalCode?: string;
    country?: string;
  }): string {
    const { street, city, state, postalCode, country } = address;
    
    // Different address formats by locale
    switch (this.locale) {
      case 'en':
        return [street, city, state, postalCode, country].filter(Boolean).join(', ');
      
      case 'de':
        return [street, `${postalCode} ${city}`, state, country].filter(Boolean).join(', ');
      
      case 'fr':
        return [street, `${postalCode} ${city}`, state, country].filter(Boolean).join(', ');
      
      case 'ja':
        return [country, state, city, postalCode, street].filter(Boolean).join(' ');
      
      case 'zh':
        return [country, state, city, street, postalCode].filter(Boolean).join(' ');
      
      case 'ar':
      case 'he':
        return [street, city, state, postalCode, country].filter(Boolean).join('، ');
      
      default:
        return [street, city, state, postalCode, country].filter(Boolean).join(', ');
    }
  }

  // Phone Number Formatting
  formatPhoneNumber(phoneNumber: string, country?: string): string {
    // Basic phone number formatting - in a real app, use a library like libphonenumber
    const cleaned = phoneNumber.replace(/\D/g, '');
    
    switch (country || this.locale) {
      case 'en':
        if (cleaned.length === 10) {
          return `(${cleaned.slice(0, 3)}) ${cleaned.slice(3, 6)}-${cleaned.slice(6)}`;
        } else if (cleaned.length === 11 && cleaned[0] === '1') {
          return `+1 (${cleaned.slice(1, 4)}) ${cleaned.slice(4, 7)}-${cleaned.slice(7)}`;
        }
        break;
      
      case 'de':
        if (cleaned.length >= 10) {
          return `+49 ${cleaned.slice(2, 4)} ${cleaned.slice(4, 8)} ${cleaned.slice(8)}`;
        }
        break;
      
      case 'fr':
        if (cleaned.length === 10) {
          return `${cleaned.slice(0, 2)} ${cleaned.slice(2, 4)} ${cleaned.slice(4, 6)} ${cleaned.slice(6, 8)} ${cleaned.slice(8)}`;
        }
        break;
      
      case 'ja':
        if (cleaned.length >= 10) {
          return `+81 ${cleaned.slice(1, 3)}-${cleaned.slice(3, 7)}-${cleaned.slice(7)}`;
        }
        break;
    }
    
    return phoneNumber; // Return original if formatting fails
  }

  // List Formatting
  formatList(items: string[], style: 'long' | 'short' | 'narrow' = 'long', type: 'conjunction' | 'disjunction' = 'conjunction'): string {
    try {
      if (!Array.isArray(items) || items.length === 0) return '';
      
      return new Intl.ListFormat(this.locale, { style, type }).format(items);
    } catch (error) {
      console.error('List formatting error:', error);
      return items.join(', ');
    }
  }

  // Unit Formatting
  formatUnit(value: number, unit: string, style: 'long' | 'short' | 'narrow' = 'short'): string {
    try {
      return new Intl.NumberFormat(this.locale, {
        style: 'unit',
        unit: unit as any,
        unitDisplay: style
      }).format(value);
    } catch (error) {
      console.error('Unit formatting error:', error);
      return `${value} ${unit}`;
    }
  }

  // Temperature
  formatTemperature(celsius: number, unit: 'celsius' | 'fahrenheit' = 'celsius'): string {
    const temp = unit === 'fahrenheit' ? (celsius * 9/5) + 32 : celsius;
    const unitSymbol = unit === 'fahrenheit' ? '°F' : '°C';
    return `${this.formatDecimal(temp, 1)}${unitSymbol}`;
  }

  // Distance
  formatDistance(meters: number, unit: 'metric' | 'imperial' = 'metric'): string {
    if (unit === 'imperial') {
      const feet = meters * 3.28084;
      if (feet < 5280) {
        return this.formatUnit(feet, 'foot');
      } else {
        return this.formatUnit(feet / 5280, 'mile');
      }
    } else {
      if (meters < 1000) {
        return this.formatUnit(meters, 'meter');
      } else {
        return this.formatUnit(meters / 1000, 'kilometer');
      }
    }
  }

  // Duration
  formatDuration(seconds: number): string {
    const hours = Math.floor(seconds / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    const remainingSeconds = Math.floor(seconds % 60);
    
    if (hours > 0) {
      return `${hours}:${minutes.toString().padStart(2, '0')}:${remainingSeconds.toString().padStart(2, '0')}`;
    } else {
      return `${minutes}:${remainingSeconds.toString().padStart(2, '0')}`;
    }
  }

  // Pluralization helper
  formatPlural(count: number, singular: string, plural?: string): string {
    const pluralRules = new Intl.PluralRules(this.locale);
    const rule = pluralRules.select(count);
    
    if (rule === 'one') {
      return `${this.formatInteger(count)} ${singular}`;
    } else {
      return `${this.formatInteger(count)} ${plural || singular + 's'}`;
    }
  }

  // Ordinal numbers
  formatOrdinal(number: number): string {
    try {
      const pr = new Intl.PluralRules(this.locale, { type: 'ordinal' });
      const rule = pr.select(number);
      
      // English ordinal suffixes
      if (this.locale.startsWith('en')) {
        const suffixes: Record<string, string> = {
          one: 'st',
          two: 'nd',
          few: 'rd',
          other: 'th'
        };
        return `${number}${suffixes[rule] || 'th'}`;
      }
      
      // For other languages, just return the number
      return this.formatInteger(number);
    } catch (error) {
      console.error('Ordinal formatting error:', error);
      return number.toString();
    }
  }

  // Get locale-specific preferences
  getLocalePreferences(): {
    firstDayOfWeek: number;
    dateFormat: string;
    timeFormat: '12h' | '24h';
    numberFormat: string;
    currencyPosition: 'before' | 'after';
  } {
    const preferences = {
      firstDayOfWeek: 0, // Sunday = 0, Monday = 1
      dateFormat: 'MM/dd/yyyy',
      timeFormat: '12h' as '12h' | '24h',
      numberFormat: '1,234.56',
      currencyPosition: 'before' as 'before' | 'after'
    };

    switch (this.locale) {
      case 'en':
        preferences.firstDayOfWeek = 0;
        preferences.dateFormat = 'MM/dd/yyyy';
        preferences.timeFormat = '12h';
        break;
      
      case 'de':
      case 'fr':
        preferences.firstDayOfWeek = 1;
        preferences.dateFormat = 'dd.MM.yyyy';
        preferences.timeFormat = '24h';
        preferences.numberFormat = '1.234,56';
        break;
      
      case 'es':
        preferences.firstDayOfWeek = 1;
        preferences.dateFormat = 'dd/MM/yyyy';
        preferences.timeFormat = '24h';
        preferences.numberFormat = '1.234,56';
        break;
      
      case 'zh':
      case 'ja':
        preferences.firstDayOfWeek = 0;
        preferences.dateFormat = 'yyyy/MM/dd';
        preferences.timeFormat = '24h';
        break;
      
      case 'ar':
      case 'he':
        preferences.firstDayOfWeek = 0;
        preferences.dateFormat = 'dd/MM/yyyy';
        preferences.timeFormat = '24h';
        preferences.currencyPosition = 'after';
        break;
    }

    return preferences;
  }
}

// Factory function to create formatter
export function createLocalizer(locale: string, options?: Partial<LocalizationOptions>): LocalizationFormatter {
  return new LocalizationFormatter({
    locale,
    ...options
  });
}

// React hook for localization
export function useLocalization(locale: string, options?: Partial<LocalizationOptions>) {
  const formatter = createLocalizer(locale, options);
  
  return {
    formatDate: formatter.formatDate.bind(formatter),
    formatTime: formatter.formatTime.bind(formatter),
    formatDateTime: formatter.formatDateTime.bind(formatter),
    formatRelativeTime: formatter.formatRelativeTime.bind(formatter),
    formatNumber: formatter.formatNumber.bind(formatter),
    formatInteger: formatter.formatInteger.bind(formatter),
    formatDecimal: formatter.formatDecimal.bind(formatter),
    formatPercent: formatter.formatPercent.bind(formatter),
    formatFileSize: formatter.formatFileSize.bind(formatter),
    formatCurrency: formatter.formatCurrency.bind(formatter),
    formatAddress: formatter.formatAddress.bind(formatter),
    formatPhoneNumber: formatter.formatPhoneNumber.bind(formatter),
    formatList: formatter.formatList.bind(formatter),
    formatUnit: formatter.formatUnit.bind(formatter),
    formatTemperature: formatter.formatTemperature.bind(formatter),
    formatDistance: formatter.formatDistance.bind(formatter),
    formatDuration: formatter.formatDuration.bind(formatter),
    formatPlural: formatter.formatPlural.bind(formatter),
    formatOrdinal: formatter.formatOrdinal.bind(formatter),
    getLocalePreferences: formatter.getLocalePreferences.bind(formatter)
  };
}