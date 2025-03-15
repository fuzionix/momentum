import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

class YahooFinanceService:
    @staticmethod
    def get_stock_data(ticker_symbol: str) -> dict:
        try:
            ticker = yf.Ticker(ticker_symbol)

            # Get historical data for technical analysis
            end_date = datetime.now()
            start_date = end_date - timedelta(days=365)  # 1 year of data
            hist = ticker.history(start=start_date, end=end_date)

            # Calculate technical indicators
            technical_indicators = YahooFinanceService.calculate_technical_indicators(hist)

            # Get news
            news = ticker.news

            # Get basic data
            data = {
                'info': ticker.info,
                'history': hist.to_dict(),
                'technical_indicators': technical_indicators,
                'financials': ticker.financials.to_dict(),
                'quarterly_financials': ticker.quarterly_financials.to_dict(),
                'balance_sheet': ticker.balance_sheet.to_dict(),
                'cash_flow': ticker.cashflow.to_dict(),
                'news': news,
            }
            return data
        except Exception as e:
            return {'error': str(e)}
        
    @staticmethod
    def calculate_technical_indicators(hist_df):
        '''Calculate technical indicators from historical price data'''
        if hist_df.empty:
            return {}
        
        df = hist_df.copy()
        
        try:
            # Simple Moving Averages
            df['SMA_50'] = df['Close'].rolling(window=50).mean()
            df['SMA_200'] = df['Close'].rolling(window=200).mean()
            
            # Exponential Moving Averages
            df['EMA_12'] = df['Close'].ewm(span=12, adjust=False).mean()
            df['EMA_26'] = df['Close'].ewm(span=26, adjust=False).mean()
            
            # MACD
            df['MACD'] = df['EMA_12'] - df['EMA_26']
            df['MACD_Signal'] = df['MACD'].ewm(span=9, adjust=False).mean()
            
            # RSI (14-period)
            delta = df['Close'].diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
            rs = gain / loss
            df['RSI'] = 100 - (100 / (1 + rs))
            
            # Bollinger Bands
            df['BB_Middle'] = df['Close'].rolling(window=20).mean()
            std_dev = df['Close'].rolling(window=20).std()
            df['BB_Upper'] = df['BB_Middle'] + (std_dev * 2)
            df['BB_Lower'] = df['BB_Middle'] - (std_dev * 2)
            
            # Average True Range (ATR)
            high_low = df['High'] - df['Low']
            high_close = (df['High'] - df['Close'].shift()).abs()
            low_close = (df['Low'] - df['Close'].shift()).abs()
            ranges = pd.concat([high_low, high_close, low_close], axis=1)
            true_range = ranges.max(axis=1)
            df['ATR'] = true_range.rolling(14).mean()
            
            # On-Balance Volume
            df['OBV'] = (np.sign(df['Close'].diff()) * df['Volume']).fillna(0).cumsum()
            
            # Price momentum (rate of change)
            df['ROC_10'] = df['Close'].pct_change(periods=10) * 100

            # Convert NaN values to None for JSON serialization
            return df[['SMA_50', 'SMA_200', 'MACD', 'MACD_Signal', 'RSI', 'BB_Upper', 'BB_Middle', 'BB_Lower', 'ATR', 'OBV', 'ROC_10']].tail(30).to_dict()
            
        except Exception as e:
            print(f'Error calculating technical indicators: {e}')
            return {}