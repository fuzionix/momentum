import yfinance as yf

class YahooFinanceService:
    @staticmethod
    def get_stock_data(ticker_symbol: str) -> dict:
        try:
            ticker = yf.Ticker(ticker_symbol)
            data = {
                'info': ticker.info,
                'history': ticker.history(period='7d').to_dict(),
                'financials': ticker.financials.to_dict()
            }
            return data
        except Exception as e:
            return {'error': str(e)}