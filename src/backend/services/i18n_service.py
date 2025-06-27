"""
Internationalization (i18n) service for BlueBirdHub backend.
Provides translation support for API responses and backend messages.
"""

import json
import os
from typing import Dict, Any, Optional, List
from pathlib import Path
from babel import Locale, UnknownLocaleError
from babel.dates import format_datetime, format_date, format_time
from babel.numbers import format_decimal, format_currency, format_percent
from babel.core import get_global
import logging

logger = logging.getLogger(__name__)

class I18nService:
    """Service for handling internationalization in the backend."""
    
    def __init__(self, default_locale: str = 'en', translations_dir: Optional[str] = None):
        self.default_locale = default_locale
        self.current_locale = default_locale
        
        # Set translations directory
        if translations_dir is None:
            # Default to frontend public locales directory
            base_dir = Path(__file__).parent.parent.parent
            self.translations_dir = base_dir / "frontend" / "public" / "locales"
        else:
            self.translations_dir = Path(translations_dir)
        
        # Cache for loaded translations
        self._translations_cache: Dict[str, Dict[str, Any]] = {}
        
        # Supported locales
        self.supported_locales = ['en', 'es', 'fr', 'de', 'zh', 'ja', 'ar', 'he']
        
        # Namespace mappings for backend-specific translations
        self.backend_namespaces = ['errors', 'api', 'notifications', 'email']
        
        logger.info(f"I18n service initialized with default locale: {default_locale}")

    def set_locale(self, locale: str) -> bool:
        """
        Set the current locale for the service.
        
        Args:
            locale: The locale code (e.g., 'en', 'es', 'fr')
            
        Returns:
            bool: True if locale was set successfully, False otherwise
        """
        if locale not in self.supported_locales:
            logger.warning(f"Unsupported locale: {locale}, falling back to {self.default_locale}")
            locale = self.default_locale
        
        try:
            # Validate locale with Babel
            Locale.parse(locale)
            self.current_locale = locale
            logger.debug(f"Locale set to: {locale}")
            return True
        except UnknownLocaleError:
            logger.error(f"Invalid locale: {locale}")
            return False

    def get_locale(self) -> str:
        """Get the current locale."""
        return self.current_locale

    def load_translations(self, namespace: str, locale: str) -> Dict[str, Any]:
        """
        Load translations for a specific namespace and locale.
        
        Args:
            namespace: Translation namespace (e.g., 'common', 'errors')
            locale: Locale code
            
        Returns:
            Dict containing translations
        """
        cache_key = f"{locale}:{namespace}"
        
        if cache_key in self._translations_cache:
            return self._translations_cache[cache_key]
        
        translation_file = self.translations_dir / locale / f"{namespace}.json"
        
        try:
            if translation_file.exists():
                with open(translation_file, 'r', encoding='utf-8') as f:
                    translations = json.load(f)
                    self._translations_cache[cache_key] = translations
                    logger.debug(f"Loaded translations for {locale}:{namespace}")
                    return translations
            else:
                logger.warning(f"Translation file not found: {translation_file}")
                return {}
        except Exception as e:
            logger.error(f"Error loading translations from {translation_file}: {e}")
            return {}

    def translate(self, key: str, locale: Optional[str] = None, 
                 namespace: str = 'common', **kwargs) -> str:
        """
        Translate a key to the specified locale.
        
        Args:
            key: Translation key (e.g., 'common.loading')
            locale: Target locale (defaults to current locale)
            namespace: Translation namespace
            **kwargs: Variables for interpolation
            
        Returns:
            Translated string
        """
        if locale is None:
            locale = self.current_locale
        
        # Load translations for the namespace
        translations = self.load_translations(namespace, locale)
        
        # Get nested value from translations
        value = self._get_nested_value(translations, key)
        
        # Fallback to default locale if translation not found
        if value is None and locale != self.default_locale:
            fallback_translations = self.load_translations(namespace, self.default_locale)
            value = self._get_nested_value(fallback_translations, key)
        
        # Final fallback to the key itself
        if value is None:
            logger.warning(f"Translation not found: {namespace}:{key} for locale {locale}")
            value = key
        
        # Perform interpolation if variables provided
        if kwargs and isinstance(value, str):
            try:
                value = value.format(**kwargs)
            except (KeyError, ValueError) as e:
                logger.warning(f"Interpolation error for key {key}: {e}")
        
        return str(value)

    def translate_plural(self, key: str, count: int, locale: Optional[str] = None,
                        namespace: str = 'common', **kwargs) -> str:
        """
        Translate a key with pluralization support.
        
        Args:
            key: Base translation key
            count: Number for pluralization
            locale: Target locale
            namespace: Translation namespace
            **kwargs: Additional variables for interpolation
            
        Returns:
            Translated string with proper pluralization
        """
        if locale is None:
            locale = self.current_locale
        
        # Add count to interpolation variables
        kwargs['count'] = count
        
        # Try different plural forms
        plural_keys = [
            f"{key}_plural" if count != 1 else key,
            f"{key}_{count}",
            key
        ]
        
        for plural_key in plural_keys:
            value = self.translate(plural_key, locale, namespace, **kwargs)
            if value != plural_key:  # Found a translation
                return value
        
        # Fallback: use singular form with count
        return f"{count} {self.translate(key, locale, namespace, **kwargs)}"

    def _get_nested_value(self, obj: Dict[str, Any], key: str) -> Any:
        """Get nested value from dictionary using dot notation."""
        keys = key.split('.')
        current = obj
        
        for k in keys:
            if isinstance(current, dict) and k in current:
                current = current[k]
            else:
                return None
        
        return current

    # Formatting methods using Babel
    
    def format_datetime(self, dt, format='medium', locale: Optional[str] = None) -> str:
        """Format datetime according to locale."""
        if locale is None:
            locale = self.current_locale
        
        try:
            return format_datetime(dt, format=format, locale=locale)
        except Exception as e:
            logger.error(f"Error formatting datetime: {e}")
            return str(dt)

    def format_date(self, date, format='medium', locale: Optional[str] = None) -> str:
        """Format date according to locale."""
        if locale is None:
            locale = self.current_locale
        
        try:
            return format_date(date, format=format, locale=locale)
        except Exception as e:
            logger.error(f"Error formatting date: {e}")
            return str(date)

    def format_time(self, time, format='medium', locale: Optional[str] = None) -> str:
        """Format time according to locale."""
        if locale is None:
            locale = self.current_locale
        
        try:
            return format_time(time, format=format, locale=locale)
        except Exception as e:
            logger.error(f"Error formatting time: {e}")
            return str(time)

    def format_decimal(self, number, locale: Optional[str] = None) -> str:
        """Format decimal number according to locale."""
        if locale is None:
            locale = self.current_locale
        
        try:
            return format_decimal(number, locale=locale)
        except Exception as e:
            logger.error(f"Error formatting decimal: {e}")
            return str(number)

    def format_currency(self, amount, currency='USD', locale: Optional[str] = None) -> str:
        """Format currency according to locale."""
        if locale is None:
            locale = self.current_locale
        
        try:
            return format_currency(amount, currency=currency, locale=locale)
        except Exception as e:
            logger.error(f"Error formatting currency: {e}")
            return f"{amount} {currency}"

    def format_percent(self, number, locale: Optional[str] = None) -> str:
        """Format percentage according to locale."""
        if locale is None:
            locale = self.current_locale
        
        try:
            return format_percent(number, locale=locale)
        except Exception as e:
            logger.error(f"Error formatting percent: {e}")
            return f"{number * 100}%"

    # API Response helpers
    
    def localize_error_response(self, error_code: str, locale: Optional[str] = None, 
                               **kwargs) -> Dict[str, Any]:
        """
        Create a localized error response.
        
        Args:
            error_code: Error code key
            locale: Target locale
            **kwargs: Variables for error message interpolation
            
        Returns:
            Localized error response dict
        """
        if locale is None:
            locale = self.current_locale
        
        message = self.translate(error_code, locale, namespace='errors', **kwargs)
        
        return {
            'error': True,
            'code': error_code,
            'message': message,
            'locale': locale
        }

    def localize_success_response(self, data: Any, message_key: str = 'success', 
                                 locale: Optional[str] = None, **kwargs) -> Dict[str, Any]:
        """
        Create a localized success response.
        
        Args:
            data: Response data
            message_key: Success message key
            locale: Target locale
            **kwargs: Variables for message interpolation
            
        Returns:
            Localized success response dict
        """
        if locale is None:
            locale = self.current_locale
        
        message = self.translate(message_key, locale, namespace='api', **kwargs)
        
        return {
            'success': True,
            'message': message,
            'data': data,
            'locale': locale
        }

    def get_supported_locales(self) -> List[Dict[str, str]]:
        """Get list of supported locales with their display names."""
        locales = []
        
        for locale_code in self.supported_locales:
            try:
                locale = Locale.parse(locale_code)
                locales.append({
                    'code': locale_code,
                    'name': locale.display_name,
                    'native_name': locale.get_display_name(locale)
                })
            except UnknownLocaleError:
                logger.warning(f"Could not parse locale: {locale_code}")
        
        return locales

    def clear_cache(self):
        """Clear the translations cache."""
        self._translations_cache.clear()
        logger.info("Translation cache cleared")

    def preload_translations(self, locales: Optional[List[str]] = None, 
                           namespaces: Optional[List[str]] = None):
        """
        Preload translations into cache.
        
        Args:
            locales: List of locales to preload (defaults to all supported)
            namespaces: List of namespaces to preload (defaults to backend namespaces)
        """
        if locales is None:
            locales = self.supported_locales
        
        if namespaces is None:
            namespaces = self.backend_namespaces
        
        for locale in locales:
            for namespace in namespaces:
                self.load_translations(namespace, locale)
        
        logger.info(f"Preloaded translations for {len(locales)} locales and {len(namespaces)} namespaces")


# Global instance
i18n_service = I18nService()

def get_i18n_service() -> I18nService:
    """Get the global i18n service instance."""
    return i18n_service

# Convenience functions
def t(key: str, locale: Optional[str] = None, namespace: str = 'common', **kwargs) -> str:
    """Shorthand for translate."""
    return i18n_service.translate(key, locale, namespace, **kwargs)

def tn(key: str, count: int, locale: Optional[str] = None, namespace: str = 'common', **kwargs) -> str:
    """Shorthand for translate_plural."""
    return i18n_service.translate_plural(key, count, locale, namespace, **kwargs)

def set_locale(locale: str) -> bool:
    """Set the global locale."""
    return i18n_service.set_locale(locale)

def get_locale() -> str:
    """Get the current global locale."""
    return i18n_service.get_locale()