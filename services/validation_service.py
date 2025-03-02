import re
from typing import Tuple

class ValidationService:
    # Characters that need to be escaped in MarkdownV2 format
    SPECIAL_CHARS = ['_', '*', '[', ']', '(', ')', '~', '`', '>', '#', '+', 
                     '-', '=', '|', '{', '}', '.', '!']
    
    @staticmethod
    def validate_ticker(ticker: str) -> Tuple[bool, str]:
        """
        Validate ticker symbol.
        Returns (is_valid, error_message)
        """
        # Check if ticker is empty
        if not ticker or ticker.strip() == "":
            return False, "Ticker symbol cannot be empty"
            
        # Check ticker length
        if len(ticker) > 10:
            return False, "Ticker symbol is too long (max 10 characters)"
            
        # Check for valid characters (letters, numbers, some special characters)
        if not re.match(r'^[A-Za-z0-9\.\-]+$', ticker):
            return False, "Ticker contains invalid characters"
            
        return True, ""
    
    @staticmethod
    def escape_markdown(text: str) -> str:
        """
        Escape special characters for MarkdownV2 format in Telegram
        """
        escaped_text = text
        for char in ValidationService.SPECIAL_CHARS:
            escaped_text = escaped_text.replace(char, f"\\{char}")
        return escaped_text
    
    @staticmethod
    def format_telegram_message(message: str, parse_mode: str = "MarkdownV2") -> str:
        """
        Format message for Telegram based on parse mode
        """
        if parse_mode.lower() == "markdownv2":
            return ValidationService.escape_markdown(message)
        # For HTML or other modes, no escaping needed
        return message