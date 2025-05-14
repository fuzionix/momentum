import json
import numpy as np
import pandas as pd
import yfinance as yf

class YahooFinanceService:
    '''Fetch and process stock data from Yahoo Finance'''

    @staticmethod
    def get_stock_data(ticker: str, period: str = '1mo') -> dict:
        '''Get basic information about a stock.'''

        try:
            stock = yf.Ticker(ticker)
            info = stock.info
            hist = stock.history(period=period)

            data_info = YahooFinanceService.get_stock_info(info)
            data_hist = YahooFinanceService.get_historical_data(hist)
            data = {
                'ticker': ticker,
                'period': period,
                'stock_info': data_info,
                'historical_data': data_hist,
                'news': stock.news,
            }

            data_serialized = json.loads(json.dumps(data, cls=JSONEncoder))        
            return format_float_values(data_serialized)
        except Exception as e:
            return {'error': f"Error retrieving information for {ticker}: {str(e)}"}
        
    @staticmethod
    def get_stock_info(info: dict) -> dict:
        '''Get stock information for a given ticker.'''
        analysis_info = {
            # Basic Information
            'name': info.get('longName', 'N/A'),
            'sector': info.get('sector', 'N/A'),
            'industry': info.get('industry', 'N/A'),
            
            # Price Information
            'current_price': info.get('currentPrice', 'N/A'),
            'previous_close': info.get('previousClose', 'N/A'),
            'open': info.get('open', 'N/A'),
            'day_low': info.get('dayLow', 'N/A'),
            'day_high': info.get('dayHigh', 'N/A'),
            'fifty_two_week_low': info.get('fiftyTwoWeekLow', 'N/A'),
            'fifty_two_week_high': info.get('fiftyTwoWeekHigh', 'N/A'),
            'fifty_day_average': info.get('fiftyDayAverage', 'N/A'),
            'two_hundred_day_average': info.get('twoHundredDayAverage', 'N/A'),
            
            # Volume and Market Information
            'volume': info.get('volume', 'N/A'),
            'average_volume': info.get('averageVolume', 'N/A'),
            'average_volume_10d': info.get('averageVolume10days', 'N/A'),
            'market_cap': info.get('marketCap', 'N/A'),
            'beta': info.get('beta', 'N/A'),
            'shares_outstanding': info.get('sharesOutstanding', 'N/A'),
            'float_shares': info.get('floatShares', 'N/A'),
            
            # Value Metrics
            'pe_ratio': info.get('trailingPE', 'N/A'),
            'forward_pe': info.get('forwardPE', 'N/A'),
            'eps': info.get('trailingEps', 'N/A'),
            'forward_eps': info.get('forwardEps', 'N/A'),
            'price_to_book': info.get('priceToBook', 'N/A'),
            'price_to_sales': info.get('priceToSalesTrailing12Months', 'N/A'),
            'peg_ratio': info.get('trailingPegRatio', 'N/A'),
            
            # Income Statement Metrics
            'revenue': info.get('totalRevenue', 'N/A'),
            'revenue_per_share': info.get('revenuePerShare', 'N/A'),
            'gross_margins': info.get('grossMargins', 'N/A'),
            'operating_margins': info.get('operatingMargins', 'N/A'),
            'profit_margins': info.get('profitMargins', 'N/A'),
            'ebitda': info.get('ebitda', 'N/A'),
            'ebitda_margins': info.get('ebitdaMargins', 'N/A'),
            
            # Balance Sheet Metrics
            'total_cash': info.get('totalCash', 'N/A'),
            'total_cash_per_share': info.get('totalCashPerShare', 'N/A'),
            'total_debt': info.get('totalDebt', 'N/A'),
            'debt_to_equity': info.get('debtToEquity', 'N/A'),
            'current_ratio': info.get('currentRatio', 'N/A'),
            'quick_ratio': info.get('quickRatio', 'N/A'),
            'book_value': info.get('bookValue', 'N/A'),
            
            # Cash Flow Metrics
            'operating_cash_flow': info.get('operatingCashflow', 'N/A'),
            'free_cash_flow': info.get('freeCashflow', 'N/A'),
            
            # Performance Metrics
            'return_on_assets': info.get('returnOnAssets', 'N/A'),
            'return_on_equity': info.get('returnOnEquity', 'N/A'),
            'earnings_growth': info.get('earningsGrowth', 'N/A'),
            'revenue_growth': info.get('revenueGrowth', 'N/A'),
            'year_to_date_change': info.get('52WeekChange', 'N/A'),
            
            # Dividend Information
            'dividend_rate': info.get('dividendRate', 'N/A'),
            'dividend_yield': info.get('dividendYield', 'N/A'),
            'payout_ratio': info.get('payoutRatio', 'N/A'),
            'ex_dividend_date': info.get('exDividendDate', 'N/A'),
            
            # Analyst Information
            'target_mean_price': info.get('targetMeanPrice', 'N/A'),
            'target_high_price': info.get('targetHighPrice', 'N/A'),
            'target_low_price': info.get('targetLowPrice', 'N/A'),
            'recommendation': info.get('recommendationKey', 'N/A'),
            'num_analyst_opinions': info.get('numberOfAnalystOpinions', 'N/A'),
            
            # Short Interest
            'shares_short': info.get('sharesShort', 'N/A'),
            'short_ratio': info.get('shortRsatio', 'N/A'),
            'short_percent_of_float': info.get('shortPercentOfFloat', 'N/A'),
            
            # Business Summary
            'business_summary': info.get('longBusinessSummary', 'N/A')[:300] + '...' if info.get('longBusinessSummary', 'N/A') else 'N/A',
        }
        
        return analysis_info
        
    @staticmethod
    def get_historical_data(hist: dict) -> dict:
        '''Get historical price data for a stock with analysis metrics.'''
        try:
            if hist.empty:
                return {'error': f"No historical data available"}
            
            # Calculate price changes
            price_change = hist['Close'].iloc[-1] - hist['Close'].iloc[0]
            percent_change = (price_change / hist['Close'].iloc[0]) * 100
            
            # Calculate moving averages
            hist['SMA_20'] = hist['Close'].rolling(window=20).mean()
            hist['SMA_50'] = hist['Close'].rolling(window=50).mean()
            hist['SMA_200'] = hist['Close'].rolling(window=200).mean()
            
            # Calculate RSI
            delta = hist['Close'].diff()
            gain = delta.where(delta > 0, 0).rolling(window=14).mean()
            loss = -delta.where(delta < 0, 0).rolling(window=14).mean()
            rs = gain / loss
            hist['RSI'] = 100 - (100 / (1 + rs))
            
            # Calculate Bollinger Bands
            hist['BB_Middle'] = hist['Close'].rolling(window=20).mean()
            hist['BB_Std'] = hist['Close'].rolling(window=20).std()
            hist['BB_Upper'] = hist['BB_Middle'] + (hist['BB_Std'] * 2)
            hist['BB_Lower'] = hist['BB_Middle'] - (hist['BB_Std'] * 2)
            
            # Calculate Average True Range (ATR)
            high_low = hist['High'] - hist['Low']
            high_close = abs(hist['High'] - hist['Close'].shift())
            low_close = abs(hist['Low'] - hist['Close'].shift())
            ranges = pd.concat([high_low, high_close, low_close], axis=1)
            true_range = ranges.max(axis=1)
            hist['ATR'] = true_range.rolling(14).mean()
            
            # Calculate MACD
            hist['EMA_12'] = hist['Close'].ewm(span=12, adjust=False).mean()
            hist['EMA_26'] = hist['Close'].ewm(span=26, adjust=False).mean()
            hist['MACD'] = hist['EMA_12'] - hist['EMA_26']
            hist['MACD_Signal'] = hist['MACD'].ewm(span=9, adjust=False).mean()
            hist['MACD_Hist'] = hist['MACD'] - hist['MACD_Signal']
            
            # Get recent values for key indicators
            current_price = hist['Close'].iloc[-1]
            current_sma20 = hist['SMA_20'].iloc[-1] if not pd.isna(hist['SMA_20'].iloc[-1]) else None
            current_sma50 = hist['SMA_50'].iloc[-1] if not pd.isna(hist['SMA_50'].iloc[-1]) else None
            current_sma200 = hist['SMA_200'].iloc[-1] if not pd.isna(hist['SMA_200'].iloc[-1]) else None
            current_rsi = hist['RSI'].iloc[-1] if not pd.isna(hist['RSI'].iloc[-1]) else None
            current_macd = hist['MACD'].iloc[-1] if not pd.isna(hist['MACD'].iloc[-1]) else None
            current_macd_signal = hist['MACD_Signal'].iloc[-1] if not pd.isna(hist['MACD_Signal'].iloc[-1]) else None
            
            # Calculate volatility
            daily_returns = hist['Close'].pct_change()
            volatility = daily_returns.std() * np.sqrt(252)  # Annualized volatility
            
            # Prepare monthly data
            if len(hist) > 30:
                monthly = hist.resample('M').agg({
                    'Open': 'first',
                    'High': 'max',
                    'Low': 'min',
                    'Close': 'last',
                    'Volume': 'sum'
                })
                monthly_data = [{
                    'date': idx.strftime('%Y-%m'),
                    'open': row['Open'],
                    'high': row['High'],
                    'low': row['Low'],
                    'close': row['Close'],
                    'volume': row['Volume']
                } for idx, row in monthly.iterrows()]
            else:
                monthly_data = []
            
            # Prepare weekly data
            if len(hist) > 7:
                weekly = hist.resample('W').agg({
                    'Open': 'first',
                    'High': 'max',
                    'Low': 'min',
                    'Close': 'last',
                    'Volume': 'sum'
                })
                weekly_data = [{
                    'date': idx.strftime('%Y-%m-%d'),
                    'open': row['Open'],
                    'high': row['High'],
                    'low': row['Low'],
                    'close': row['Close'],
                    'volume': row['Volume']
                } for idx, row in weekly.iterrows()]
            else:
                weekly_data = []
            
            # Create return dictionary with analysis data
            analysis_data = {
                'start_date': hist.index[0].strftime('%Y-%m-%d'),
                'end_date': hist.index[-1].strftime('%Y-%m-%d'),
                'start_price': hist['Close'].iloc[0],
                'end_price': hist['Close'].iloc[-1],
                'price_change': price_change,
                'percent_change': percent_change,
                'max_price': hist['High'].max(),
                'min_price': hist['Low'].min(),
                'avg_volume': hist['Volume'].mean(),
                'max_volume': hist['Volume'].max(),
                'volatility': volatility,
                'data_points': len(hist),
                
                # Technical indicators
                'current_indicators': {
                    'price': current_price,
                    'sma20': current_sma20,
                    'sma50': current_sma50,
                    'sma200': current_sma200,
                    'rsi': current_rsi,
                    'macd': current_macd,
                    'macd_signal': current_macd_signal,
                    'upper_bollinger': hist['BB_Upper'].iloc[-1] if not pd.isna(hist['BB_Upper'].iloc[-1]) else None,
                    'lower_bollinger': hist['BB_Lower'].iloc[-1] if not pd.isna(hist['BB_Lower'].iloc[-1]) else None,
                    'atr': hist['ATR'].iloc[-1] if not pd.isna(hist['ATR'].iloc[-1]) else None,
                },
                
                # Signal analysis
                'technical_signals': {
                    'price_above_sma20': bool(current_price > current_sma20) if current_sma20 is not None else None,
                    'price_above_sma50': bool(current_price > current_sma50) if current_sma50 is not None else None,
                    'price_above_sma200': bool(current_price > current_sma200) if current_sma200 is not None else None,
                    'sma20_above_sma50': bool(current_sma20 > current_sma50) if (current_sma20 is not None and current_sma50 is not None) else None,
                    'rsi_overbought': bool(current_rsi > 70) if current_rsi is not None else None,
                    'rsi_oversold': bool(current_rsi < 30) if current_rsi is not None else None,
                    'macd_bullish': bool(current_macd > current_macd_signal) if (current_macd is not None and current_macd_signal is not None) else None,
                },
                
                # Historical data summaries
                'monthly_data': monthly_data,
                'weekly_data': weekly_data,
                
                # Last 5 days
                'recent_days': [{
                    'date': idx.strftime('%Y-%m-%d'),
                    'open': row['Open'],
                    'high': row['High'],
                    'low': row['Low'],
                    'close': row['Close'],
                    'volume': row['Volume']
                } for idx, row in hist.tail(5).iterrows()]
            }
            
            return analysis_data
            
        except Exception as e:
            return {'error': f"Error retrieving historical data: {str(e)}"}
        
class JSONEncoder(json.JSONEncoder):
    '''Custom JSON encoder for NumPy types.'''
    def default(self, obj):
        if isinstance(obj, (np.integer, np.int64, np.int32)):
            return int(obj)
        elif pd.isna(obj):
            return None
        return super().default(obj)
    
def format_float_values(data):
    '''Recursively format all float values in a dictionary/list structure to 2 decimal places.'''
    if isinstance(data, dict):
        return {k: format_float_values(v) for k, v in data.items()}
    elif isinstance(data, list):
        return [format_float_values(item) for item in data]
    elif isinstance(data, float):
        return round(data, 2)
    else:
        return data
