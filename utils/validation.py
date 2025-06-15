import re
from typing import Tuple

class Validation:
    # Characters that need to be escaped in MarkdownV2 format
    SPECIAL_CHARS = ['_', '*', '[', ']', '(', ')', '~', '`', '>', '#', '+', 
                     '-', '=', '|', '{', '}', '.', '!']
    
    @staticmethod
    def validate_ticker(ticker: str) -> Tuple[bool, str]:
        '''
        Validate ticker symbol.
        Returns (is_valid, error_message)
        '''
        # Check if ticker is empty
        if not ticker or ticker.strip() == '':
            return False, '股票代碼不能為空'
            
        # Check ticker length
        if len(ticker) > 10:
            return False, '股票代碼過長（最多 10 個字符）'
            
        # Check for valid characters (letters, numbers, some special characters)
        if not re.match(r'^[A-Za-z0-9\.\-]+$', ticker):
            return False, '股票代碼包含無效字符'

        return True, ''
    
    @staticmethod
    def escape_markdown(text: str) -> str:
        '''
        Escape special characters for MarkdownV2 format in Telegram
        '''
        escaped_text = text
        for char in Validation.SPECIAL_CHARS:
            escaped_text = escaped_text.replace(char, f'\\{char}')
        return escaped_text
    
    @staticmethod
    def format_telegram_message(message: str, parse_mode: str = 'MarkdownV2') -> str:
        '''
        Format message for Telegram based on parse mode
        '''
        if parse_mode.lower() == 'markdownv2':
            return Validation.escape_markdown(message)
        # For HTML or other modes, no escaping needed
        return message