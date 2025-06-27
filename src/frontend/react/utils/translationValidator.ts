import { supportedLanguages } from '../config/i18n';

export interface ValidationResult {
  isValid: boolean;
  errors: ValidationError[];
  warnings: ValidationWarning[];
  stats: ValidationStats;
}

export interface ValidationError {
  type: 'missing_key' | 'invalid_format' | 'syntax_error' | 'circular_reference';
  key: string;
  language: string;
  message: string;
  severity: 'error' | 'warning';
}

export interface ValidationWarning {
  type: 'unused_key' | 'inconsistent_pluralization' | 'length_mismatch' | 'formatting_inconsistency';
  key: string;
  language: string;
  message: string;
}

export interface ValidationStats {
  totalKeys: number;
  translatedKeys: Record<string, number>;
  completionPercentage: Record<string, number>;
  missingKeys: Record<string, string[]>;
  extraKeys: Record<string, string[]>;
}

export interface TranslationData {
  [namespace: string]: {
    [language: string]: Record<string, any>;
  };
}

export class TranslationValidator {
  private data: TranslationData;
  private supportedLangs: string[];

  constructor(data: TranslationData) {
    this.data = data;
    this.supportedLangs = Object.keys(supportedLanguages);
  }

  validate(): ValidationResult {
    const errors: ValidationError[] = [];
    const warnings: ValidationWarning[] = [];
    
    // Get all unique keys across all languages and namespaces
    const allKeys = this.getAllKeys();
    
    // Check for missing translations
    errors.push(...this.validateMissingTranslations(allKeys));
    
    // Check for format consistency
    warnings.push(...this.validateFormatConsistency(allKeys));
    
    // Check for interpolation syntax
    errors.push(...this.validateInterpolationSyntax(allKeys));
    
    // Check for pluralization consistency
    warnings.push(...this.validatePluralizationConsistency(allKeys));
    
    // Check for unused keys
    warnings.push(...this.validateUnusedKeys(allKeys));
    
    // Check for length consistency (for UI elements)
    warnings.push(...this.validateLengthConsistency(allKeys));
    
    // Generate statistics
    const stats = this.generateStats(allKeys);
    
    return {
      isValid: errors.length === 0,
      errors,
      warnings,
      stats
    };
  }

  private getAllKeys(): Set<string> {
    const keys = new Set<string>();
    
    Object.keys(this.data).forEach(namespace => {
      Object.keys(this.data[namespace]).forEach(language => {
        this.extractKeys(this.data[namespace][language], '', keys, namespace);
      });
    });
    
    return keys;
  }

  private extractKeys(obj: any, prefix: string, keys: Set<string>, namespace: string): void {
    Object.keys(obj).forEach(key => {
      const fullKey = prefix ? `${namespace}:${prefix}.${key}` : `${namespace}:${key}`;
      
      if (typeof obj[key] === 'string') {
        keys.add(fullKey);
      } else if (typeof obj[key] === 'object' && obj[key] !== null) {
        this.extractKeys(obj[key], prefix ? `${prefix}.${key}` : key, keys, namespace);
      }
    });
  }

  private validateMissingTranslations(allKeys: Set<string>): ValidationError[] {
    const errors: ValidationError[] = [];
    
    allKeys.forEach(key => {
      const [namespace, ...keyParts] = key.split(':');
      const actualKey = keyParts.join(':');
      
      this.supportedLangs.forEach(language => {
        if (!this.data[namespace] || !this.data[namespace][language]) {
          errors.push({
            type: 'missing_key',
            key: actualKey,
            language,
            message: `Missing translation for key "${actualKey}" in language "${language}"`,
            severity: 'error'
          });
          return;
        }
        
        const value = this.getNestedValue(this.data[namespace][language], actualKey);
        if (value === undefined || value === '') {
          errors.push({
            type: 'missing_key',
            key: actualKey,
            language,
            message: `Empty or missing translation for key "${actualKey}" in language "${language}"`,
            severity: 'error'
          });
        }
      });
    });
    
    return errors;
  }

  private validateInterpolationSyntax(allKeys: Set<string>): ValidationError[] {
    const errors: ValidationError[] = [];
    const interpolationRegex = /\{\{([^}]+)\}\}/g;
    
    allKeys.forEach(key => {
      const [namespace, ...keyParts] = key.split(':');
      const actualKey = keyParts.join(':');
      
      // Get all interpolation variables from all languages
      const variablesByLanguage: Record<string, Set<string>> = {};
      
      this.supportedLangs.forEach(language => {
        if (this.data[namespace] && this.data[namespace][language]) {
          const value = this.getNestedValue(this.data[namespace][language], actualKey);
          if (typeof value === 'string') {
            const variables = new Set<string>();
            let match;
            while ((match = interpolationRegex.exec(value)) !== null) {
              variables.add(match[1].trim());
            }
            variablesByLanguage[language] = variables;
          }
        }
      });
      
      // Check for consistency across languages
      const languagesWithTranslations = Object.keys(variablesByLanguage);
      if (languagesWithTranslations.length > 1) {
        const referenceVars = variablesByLanguage[languagesWithTranslations[0]];
        
        languagesWithTranslations.slice(1).forEach(language => {
          const currentVars = variablesByLanguage[language];
          
          // Check for missing variables
          referenceVars.forEach(variable => {
            if (!currentVars.has(variable)) {
              errors.push({
                type: 'syntax_error',
                key: actualKey,
                language,
                message: `Missing interpolation variable "{{${variable}}}" in language "${language}"`,
                severity: 'error'
              });
            }
          });
          
          // Check for extra variables
          currentVars.forEach(variable => {
            if (!referenceVars.has(variable)) {
              errors.push({
                type: 'syntax_error',
                key: actualKey,
                language,
                message: `Extra interpolation variable "{{${variable}}}" in language "${language}"`,
                severity: 'error'
              });
            }
          });
        });
      }
    });
    
    return errors;
  }

  private validateFormatConsistency(allKeys: Set<string>): ValidationWarning[] {
    const warnings: ValidationWarning[] = [];
    
    allKeys.forEach(key => {
      const [namespace, ...keyParts] = key.split(':');
      const actualKey = keyParts.join(':');
      
      const formats: Record<string, { hasHTML: boolean; hasLineBreaks: boolean; hasSpecialChars: boolean }> = {};
      
      this.supportedLangs.forEach(language => {
        if (this.data[namespace] && this.data[namespace][language]) {
          const value = this.getNestedValue(this.data[namespace][language], actualKey);
          if (typeof value === 'string') {
            formats[language] = {
              hasHTML: /<[^>]*>/g.test(value),
              hasLineBreaks: /\n|\r\n/.test(value),
              hasSpecialChars: /[<>&"']/.test(value)
            };
          }
        }
      });
      
      // Check for formatting inconsistencies
      const languages = Object.keys(formats);
      if (languages.length > 1) {
        const reference = formats[languages[0]];
        
        languages.slice(1).forEach(language => {
          const current = formats[language];
          
          if (reference.hasHTML !== current.hasHTML) {
            warnings.push({
              type: 'formatting_inconsistency',
              key: actualKey,
              language,
              message: `HTML formatting inconsistency in key "${actualKey}" for language "${language}"`
            });
          }
          
          if (reference.hasLineBreaks !== current.hasLineBreaks) {
            warnings.push({
              type: 'formatting_inconsistency',
              key: actualKey,
              language,
              message: `Line break formatting inconsistency in key "${actualKey}" for language "${language}"`
            });
          }
        });
      }
    });
    
    return warnings;
  }

  private validatePluralizationConsistency(allKeys: Set<string>): ValidationWarning[] {
    const warnings: ValidationWarning[] = [];
    
    // Find plural keys (ending with _plural, _0, _1, _2, etc.)
    const pluralGroups: Record<string, string[]> = {};
    
    allKeys.forEach(key => {
      const [namespace, ...keyParts] = key.split(':');
      const actualKey = keyParts.join(':');
      
      // Check if it's a plural form
      const pluralMatch = actualKey.match(/^(.+)(_plural|_\d+)$/);
      if (pluralMatch) {
        const baseKey = pluralMatch[1];
        const fullBaseKey = `${namespace}:${baseKey}`;
        
        if (!pluralGroups[fullBaseKey]) {
          pluralGroups[fullBaseKey] = [];
        }
        pluralGroups[fullBaseKey].push(key);
      }
    });
    
    // Validate each plural group
    Object.keys(pluralGroups).forEach(baseKey => {
      const pluralKeys = pluralGroups[baseKey];
      
      this.supportedLangs.forEach(language => {
        const translatedKeys = pluralKeys.filter(key => {
          const [namespace, ...keyParts] = key.split(':');
          const actualKey = keyParts.join(':');
          const value = this.getNestedValue(this.data[namespace]?.[language], actualKey);
          return value !== undefined && value !== '';
        });
        
        // Check if all plural forms are translated consistently
        if (translatedKeys.length > 0 && translatedKeys.length < pluralKeys.length) {
          warnings.push({
            type: 'inconsistent_pluralization',
            key: baseKey.split(':')[1],
            language,
            message: `Incomplete plural forms for key "${baseKey}" in language "${language}"`
          });
        }
      });
    });
    
    return warnings;
  }

  private validateUnusedKeys(allKeys: Set<string>): ValidationWarning[] {
    const warnings: ValidationWarning[] = [];
    
    // This would require scanning the codebase for key usage
    // For now, we'll just flag keys that seem like they might be unused
    // In a real implementation, you'd scan your source code files
    
    allKeys.forEach(key => {
      const [namespace, ...keyParts] = key.split(':');
      const actualKey = keyParts.join(':');
      
      // Simple heuristic: keys with 'test', 'temp', 'debug' might be unused
      if (/\b(test|temp|debug|unused)\b/i.test(actualKey)) {
        warnings.push({
          type: 'unused_key',
          key: actualKey,
          language: 'all',
          message: `Potentially unused key "${actualKey}" (contains test/temp/debug)`
        });
      }
    });
    
    return warnings;
  }

  private validateLengthConsistency(allKeys: Set<string>): ValidationWarning[] {
    const warnings: ValidationWarning[] = [];
    
    allKeys.forEach(key => {
      const [namespace, ...keyParts] = key.split(':');
      const actualKey = keyParts.join(':');
      
      // Check if this is likely a UI element (button, menu, etc.)
      const isUIElement = /\b(button|menu|title|label|heading|nav)\b/i.test(actualKey);
      
      if (isUIElement) {
        const lengths: Record<string, number> = {};
        
        this.supportedLangs.forEach(language => {
          if (this.data[namespace] && this.data[namespace][language]) {
            const value = this.getNestedValue(this.data[namespace][language], actualKey);
            if (typeof value === 'string') {
              lengths[language] = value.length;
            }
          }
        });
        
        const lengthValues = Object.values(lengths);
        if (lengthValues.length > 1) {
          const minLength = Math.min(...lengthValues);
          const maxLength = Math.max(...lengthValues);
          
          // Flag if there's a significant length difference (>50% variation)
          if (maxLength > minLength * 1.5) {
            warnings.push({
              type: 'length_mismatch',
              key: actualKey,
              language: 'multiple',
              message: `Significant length variation in UI element "${actualKey}" (${minLength}-${maxLength} chars)`
            });
          }
        }
      }
    });
    
    return warnings;
  }

  private generateStats(allKeys: Set<string>): ValidationStats {
    const stats: ValidationStats = {
      totalKeys: allKeys.size,
      translatedKeys: {},
      completionPercentage: {},
      missingKeys: {},
      extraKeys: {}
    };
    
    this.supportedLangs.forEach(language => {
      let translatedCount = 0;
      const missingKeys: string[] = [];
      
      allKeys.forEach(key => {
        const [namespace, ...keyParts] = key.split(':');
        const actualKey = keyParts.join(':');
        
        if (this.data[namespace] && this.data[namespace][language]) {
          const value = this.getNestedValue(this.data[namespace][language], actualKey);
          if (value !== undefined && value !== '') {
            translatedCount++;
          } else {
            missingKeys.push(actualKey);
          }
        } else {
          missingKeys.push(actualKey);
        }
      });
      
      stats.translatedKeys[language] = translatedCount;
      stats.completionPercentage[language] = allKeys.size > 0 ? Math.round((translatedCount / allKeys.size) * 100) : 0;
      stats.missingKeys[language] = missingKeys;
    });
    
    return stats;
  }

  private getNestedValue(obj: any, path: string): any {
    return path.split('.').reduce((current, key) => {
      return current && current[key] !== undefined ? current[key] : undefined;
    }, obj);
  }

  // Static method to validate a single translation file
  static async validateTranslationFile(filePath: string): Promise<ValidationResult> {
    try {
      const response = await fetch(filePath);
      const data = await response.json();
      
      // Wrap single file in expected structure
      const wrappedData: TranslationData = {
        common: {
          en: data // Assume it's English, adjust as needed
        }
      };
      
      const validator = new TranslationValidator(wrappedData);
      return validator.validate();
    } catch (error) {
      return {
        isValid: false,
        errors: [{
          type: 'syntax_error',
          key: 'file',
          language: 'unknown',
          message: `Failed to parse translation file: ${error}`,
          severity: 'error'
        }],
        warnings: [],
        stats: {
          totalKeys: 0,
          translatedKeys: {},
          completionPercentage: {},
          missingKeys: {},
          extraKeys: {}
        }
      };
    }
  }

  // Export validation report
  exportReport(result: ValidationResult): string {
    const report = [];
    
    report.push('# Translation Validation Report');
    report.push(`Generated: ${new Date().toISOString()}`);
    report.push('');
    
    // Summary
    report.push('## Summary');
    report.push(`- Status: ${result.isValid ? '✅ Valid' : '❌ Invalid'}`);
    report.push(`- Total Keys: ${result.stats.totalKeys}`);
    report.push(`- Errors: ${result.errors.length}`);
    report.push(`- Warnings: ${result.warnings.length}`);
    report.push('');
    
    // Completion stats
    report.push('## Completion Statistics');
    Object.keys(result.stats.completionPercentage).forEach(language => {
      const percentage = result.stats.completionPercentage[language];
      const translated = result.stats.translatedKeys[language];
      const total = result.stats.totalKeys;
      report.push(`- ${language}: ${percentage}% (${translated}/${total})`);
    });
    report.push('');
    
    // Errors
    if (result.errors.length > 0) {
      report.push('## Errors');
      result.errors.forEach(error => {
        report.push(`- **${error.type}** [${error.language}] ${error.key}: ${error.message}`);
      });
      report.push('');
    }
    
    // Warnings
    if (result.warnings.length > 0) {
      report.push('## Warnings');
      result.warnings.forEach(warning => {
        report.push(`- **${warning.type}** [${warning.language}] ${warning.key}: ${warning.message}`);
      });
      report.push('');
    }
    
    // Missing keys by language
    report.push('## Missing Keys by Language');
    Object.keys(result.stats.missingKeys).forEach(language => {
      const missing = result.stats.missingKeys[language];
      if (missing.length > 0) {
        report.push(`### ${language} (${missing.length} missing)`);
        missing.forEach(key => {
          report.push(`- ${key}`);
        });
        report.push('');
      }
    });
    
    return report.join('\n');
  }
}

// Helper function to load and validate all translations
export async function validateAllTranslations(): Promise<ValidationResult> {
  const data: TranslationData = {};
  const namespaces = ['common', 'navigation', 'dashboard', 'workspace', 'tasks', 'files', 'ai', 'settings', 'auth', 'errors'];
  const languages = Object.keys(supportedLanguages);
  
  try {
    // Load all translation files
    for (const namespace of namespaces) {
      data[namespace] = {};
      
      for (const language of languages) {
        try {
          const response = await fetch(`/locales/${language}/${namespace}.json`);
          if (response.ok) {
            data[namespace][language] = await response.json();
          }
        } catch (error) {
          console.warn(`Failed to load ${namespace}.json for ${language}:`, error);
        }
      }
    }
    
    const validator = new TranslationValidator(data);
    return validator.validate();
    
  } catch (error) {
    return {
      isValid: false,
      errors: [{
        type: 'syntax_error',
        key: 'global',
        language: 'all',
        message: `Failed to validate translations: ${error}`,
        severity: 'error'
      }],
      warnings: [],
      stats: {
        totalKeys: 0,
        translatedKeys: {},
        completionPercentage: {},
        missingKeys: {},
        extraKeys: {}
      }
    };
  }
}