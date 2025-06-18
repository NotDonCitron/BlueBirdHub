import { useCallback } from 'react';
import { errorLogger } from '../utils/errorLogger';

interface ErrorContext {
  component?: string;
  action?: string;
  userId?: string;
  metadata?: Record<string, any>;
}

export const useErrorHandler = (defaultContext?: ErrorContext) => {
  const handleError = useCallback((error: Error | unknown, context?: ErrorContext) => {
    const errorContext = {
      ...defaultContext,
      ...context,
      timestamp: new Date().toISOString(),
      userAgent: navigator.userAgent,
      url: window.location.href
    };

    if (error instanceof Error) {
      errorLogger.logError(error, errorContext);
    } else {
      // Handle non-Error objects
      const wrappedError = new Error(
        typeof error === 'string' ? error : JSON.stringify(error)
      );
      errorLogger.logError(wrappedError, errorContext);
    }

    // Return user-friendly message
    return getUserFriendlyMessage(error);
  }, [defaultContext]);

  return { handleError };
};

function getUserFriendlyMessage(error: Error | unknown): string {
  if (error instanceof Error) {
    // Network errors
    if (error.message.includes('fetch')) {
      return 'Verbindungsfehler. Bitte überprüfen Sie Ihre Internetverbindung.';
    }
    
    // API errors
    if (error.message.includes('401') || error.message.includes('Unauthorized')) {
      return 'Sitzung abgelaufen. Bitte melden Sie sich erneut an.';
    }
    
    if (error.message.includes('403') || error.message.includes('Forbidden')) {
      return 'Sie haben keine Berechtigung für diese Aktion.';
    }
    
    if (error.message.includes('404') || error.message.includes('Not Found')) {
      return 'Die angeforderte Ressource wurde nicht gefunden.';
    }
    
    if (error.message.includes('500') || error.message.includes('Internal Server')) {
      return 'Serverfehler. Bitte versuchen Sie es später erneut.';
    }
    
    // Validation errors
    if (error.message.includes('validation') || error.message.includes('invalid')) {
      return 'Bitte überprüfen Sie Ihre Eingaben.';
    }
  }
  
  return 'Ein unerwarteter Fehler ist aufgetreten. Bitte versuchen Sie es erneut.';
}