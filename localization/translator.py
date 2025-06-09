from typing import Dict, Optional
from localization.translations.en import TRANSLATIONS as EN_TRANSLATIONS
from localization.translations.zh_hk import TRANSLATIONS as ZH_HK_TRANSLATIONS

class Translator:
    """Handles translations for the bot"""
    
    LANGUAGES = {
        "en": "English",
        "zh-hk": "繁體中文"
    }
    
    _translations = {
        "en": EN_TRANSLATIONS,
        "zh-hk": ZH_HK_TRANSLATIONS
    }
    
    @classmethod
    def get(cls, key: str, lang: str = "en", **kwargs) -> str:
        """
        Get a translation for a key in the specified language
        
        Args:
            key: The translation key
            lang: The language code (defaults to English)
            **kwargs: Format parameters for the translation string
            
        Returns:
            The translated string
        """
        # Default to English if language not supported
        if lang not in cls._translations:
            lang = "en"
            
        translation = cls._translations[lang].get(key, cls._translations["en"].get(key, key))
        
        if kwargs:
            try:
                return translation.format(**kwargs)
            except KeyError:
                return translation
        return translation
    
    @classmethod
    def get_language_name(cls, lang_code: str) -> str:
        """Get the display name of a language from its code"""
        return cls.LANGUAGES.get(lang_code, "English")