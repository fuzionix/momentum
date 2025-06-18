import re
from typing import Tuple

class Validation:
    def validate_ticker(self, ticker: str) -> tuple[bool, str]:
        """
        Validate ticker symbol format
        Returns (is_valid, error_message)
        """
        if not ticker or len(ticker) == 0:
            return False, "股票代碼不能為空"
        
        ticker = ticker.strip()
        if len(ticker) > 20:
            return False, "股票代碼太長"
            
        return True, ""
    
    def format_ticker(self, ticker: str) -> str:
        """
        Format ticker according to exchange rules:
        - Digit-only tickers are assumed to be Hong Kong stocks
        - Already formatted tickers (with a dot) are left as is
        - Letter-only tickers are assumed to be US stocks
        """
        ticker = ticker.strip().upper()
        
        # If ticker already contains a dot (like "0700.HK"), leave it as is
        if '.' in ticker:
            return ticker
            
        # If ticker is digit-only, assume it's a Hong Kong stock
        if ticker.isdigit():
            # Pad with leading zeros to 4 digits for HK stocks
            padded_ticker = ticker.zfill(4)
            return f"{padded_ticker}.HK"
            
        # Otherwise assume it's a US stock (return as is)
        return ticker
        
    def format_telegram_message(self, message: str) -> str:
        """
        Format message for Telegram's MarkdownV2 format
        Escapes special characters
        """
        escape_chars = ['_', '*', '[', ']', '(', ')', '~', '`', '>', '#', '+', '-', '=', '|', '{', '}', '.', '!']
        for char in escape_chars:
            message = message.replace(char, f'\\{char}')
        return message