from datetime import datetime
from utils.formatters import format_large_number
from services.llm.prompts.prompt_base import BasePrompt

class StockAnalysisPrompt(BasePrompt):
    '''Prompt generator for stock analysis'''

    def format_data(stock_data: dict) -> dict:
        # Extract basic information
        info = stock_data.get('info', {})

        # Extract company information
        symbol = info.get('symbol', 'Unknown')
        company_name = info.get('shortName', info.get('longName', 'Unknown Company'))
        sector = info.get('sector', 'Unknown')
        industry = info.get('industry', 'Unknown')
        business_summary = info.get('longBusinessSummary', 'No business summary available')

        # Truncate business summary if too long
        if len(business_summary) > 300:
            business_summary = business_summary[:297] + '...'

        # Create a summary of available financial metrics
        financial_metrics = []
        metrics_to_check = [
            ('currentPrice', 'Current Price', lambda x: f'${x:.2f}'),
            ('marketCap', 'Market Cap', lambda x: format_large_number(x)),
            ('trailingPE', 'P/E Ratio', lambda x: f'{x:.2f}'),
            ('forwardPE', 'Forward P/E', lambda x: f'{x:.2f}'),
            ('trailingEps', 'EPS (TTM)', lambda x: f'${x:.2f}'),
            ('dividendYield', 'Dividend Yield', lambda x: f'{x*100:.2f}%'),
            ('revenueGrowth', 'Revenue Growth', lambda x: f'{x*100:.2f}%'),
            ('profitMargins', 'Profit Margin', lambda x: f'{x*100:.2f}%'),
            ('operatingMargins', 'Operating Margin', lambda x: f'{x*100:.2f}%'),
            ('returnOnEquity', 'Return on Equity', lambda x: f'{x*100:.2f}%'),
            ('debtToEquity', 'Debt to Equity', lambda x: f'{x:.2f}'),
            ('quickRatio', 'Quick Ratio', lambda x: f'{x:.2f}'),
            ('targetMeanPrice', 'Target Price', lambda x: f'${x:.2f}'),
        ]

        for key, label, formatter in metrics_to_check:
            if key in info and info[key] is not None:
                try:
                    formatted_value = formatter(info[key])
                    financial_metrics.append(f'- {label}: {formatted_value}')
                except (TypeError, ValueError):
                    financial_metrics.append(f'- {label}: {info[key]}')

        # Extract price history
        price_history_section = ['- Recent Prices: No data available']
        price_change = None
        percent_change = None
        
        try:
            history = stock_data.get('history', {})
            if isinstance(history, dict) and 'Close' in history:
                close_data = history['Close']
                if isinstance(close_data, dict) and close_data:
                    prices = list(close_data.values())[-30:]
                    
                    if prices:
                        price_history_section = [f"- Recent Prices(30 Days): {', '.join([f'${float(p):.2f}' for p in prices])}"]
                        
                        # Calculate price change
                        price_change = float(prices[-1]) - float(prices[0])
                        percent_change = (price_change / float(prices[0])) * 100
                        price_history_section.append(f'- Price Change: ${price_change:.2f} ({percent_change:.2f}%)')
                        
                        # Add trading volume if available
                        if 'Volume' in history:
                            volume_data = history['Volume']
                            if isinstance(volume_data, dict) and volume_data:
                                avg_volume = sum(list(volume_data.values())[-30:]) / 30
                                price_history_section.append(f'- Avg Daily Volume: {int(avg_volume):,}')
        except Exception:
            price_history_section.append('- Note: Error processing price history data')

        # Extract technical indicators
        technical_indicators = stock_data.get('technical_indicators', {})
        tech_analysis = []

        if technical_indicators:
            # Get the most recent values
            try:
                latest = {}
                for indicator, values in technical_indicators.items():
                    if values and isinstance(values, dict):
                        latest_date = max(values.keys())
                        latest[indicator] = values[latest_date]
                
                # Add formatted technical indicators
                if 'RSI' in latest:
                    rsi_value = latest['RSI']
                    tech_analysis.append(f'- RSI (14): {rsi_value:.2f}')
                    
                if 'SMA_50' in latest and 'SMA_200' in latest and latest['SMA_50'] and latest['SMA_200']:
                    sma_50 = latest['SMA_50']
                    sma_200 = latest['SMA_200']
                    golden_cross = sma_50 > sma_200
                    tech_analysis.append(f'- 50-day SMA: ${sma_50:.2f}')
                    tech_analysis.append(f'- 200-day SMA: ${sma_200:.2f}')
                    tech_analysis.append(f'- MA Signal: {"Bullish (Golden Cross)" if golden_cross else "Bearish (Death Cross)"}')
                    
                if 'MACD' in latest and 'MACD_Signal' in latest:
                    macd = latest['MACD']
                    macd_signal = latest['MACD_Signal']
                    macd_hist = macd - macd_signal if macd and macd_signal else None
                    if macd_hist is not None:
                        tech_analysis.append(f'- MACD Histogram: {macd_hist:.3f} ({"Bullish" if macd_hist > 0 else "Bearish"})')
            except Exception as e:
                tech_analysis.append(f'- Technical analysis error: {str(e)}')

        # Extract financial health indicators
        financial_health = []

        # Extract and format news
        news_items = []
        news_data = stock_data.get('news', [])
        if news_data and isinstance(news_data, list):
            recent_news = news_data[:5]
            for item in recent_news:
                if isinstance(item, dict):
                    content = item.get('content', {})
                    if isinstance(content, dict):
                        title = content.get('title', 'No title')
                    
                    pub_date = ''
                    if 'content' in item and isinstance(item['content'], dict):
                        pub_date = item['content'].get('pubDate', '')
                        
                    if pub_date:
                        try:
                            date_obj = datetime.strptime(pub_date, '%Y-%m-%dT%H:%M:%SZ')
                            formatted_date = date_obj.strftime('%b %d, %Y')
                            news_items.append(f'- {title} ({formatted_date})')
                        except Exception:
                            news_items.append(f'- {title}')
                    else:
                        news_items.append(f'- {title}')
                    
                    summary = ''
                    if 'content' in item and isinstance(item['content'], dict):
                        summary = item['content'].get('summary', '')
                        
                    if summary and len(summary) > 20:
                        if len(summary) > 200:
                            summary = summary[:197] + '...'
                        news_items.append(f'  Summary: {summary}')
        
        # Return formatted data as a dictionary
        return {
            'company': {
                'symbol': symbol,
                'name': company_name,
                'sector': sector,
                'industry': industry,
                'business_summary': business_summary
            },
            'financial_metrics': financial_metrics,
            'price_history': price_history_section,
            'technical_analysis': tech_analysis,
            'financial_health': financial_health,
            'price_change': price_change,
            'percent_change': percent_change,
            'news': news_items
        }
    
    def build_prompt(formatted_data: dict) -> str:
        company = formatted_data['company']
        financial_metrics = formatted_data['financial_metrics']
        price_history = formatted_data['price_history']
        tech_analysis = formatted_data['technical_analysis']
        financial_health = formatted_data['financial_health']
        news = formatted_data.get('news', [])
        
        financial_summary = '\n'.join(financial_metrics) if financial_metrics else 'Financial data not available'
        price_history_text = '\n'.join(price_history)
        technical_analysis_section = '\n'.join(tech_analysis) if tech_analysis else 'Technical indicators not available'
        financial_health_section = '\n'.join(financial_health) if financial_health else 'Financial health data not available'
        news_section = '\n'.join(news) if news else 'No recent news available'

        # Create the prompt
        prompt = f'''
You are a financial analyst providing insights on stock {company['symbol']} ({company['name']}).

COMPANY INFORMATION:
- Symbol: {company['symbol']}
- Company: {company['name']}
- Sector: {company['sector']}
- Industry: {company['industry']}
- Business Summary: {company['business_summary']}

FINANCIAL METRICS:
{financial_summary}

MARKET DATA:
{price_history_text}

TECHNICAL ANALYSIS:
{technical_analysis_section}
    
FINANCIAL HEALTH:
{financial_health_section}

RECENT NEWS:
{news_section}

Based on this information, provide a financial analysis using the following structure:
[Ticker] | [Price Change] [🔺(Increase)/🔻(Decrease)]

<b>Company Overview</b>
[Provide a brief 2-3 sentence overview of the company's current financial situation and market position]

<b>Key Signals</b>
[List 6-8 key signals from the data using the format below]
✅ [Positive signal with brief explanation]
✅ [Positive signal with brief explanation]
❎ [Negative signal with brief explanation]
[etc.]

<b>Market Insights</b>
[Think deeply and provide precise insights on recent market trends with related news and other relevant factors in 2 paragraphs]
[Paragraph 1 - Market trend analysis]
[Paragraph 2 - News impact and market outlook]

<b>Recommendation: [Buy/Sell/Neutral] [🟢/🔴/🟡]</b>
[1-2 sentences explaining the final recommendation]

<b>Risk Level: [Low/Medium/High] [⚪/🟠/🔴]</b>
[Brief explanation of risk assessment]

---

Example output format:
ACME | 🔺$152.33 (+5.34%)
    
<b>Company Overview</b>
ACME Inc. currently trades at $152.33 with a market cap of $2.3B, showing a recent uptrend of 5.2%. The company maintains solid profit margins in a competitive industry despite recent market volatility.

<b>Key Signals</b>
✅ Strong profit margin (23.4%) outperforming sector average by 7.2%
✅ Recent price momentum with 5.2% gain over 7 days
✅ Analyst consensus is 'buy' with target price 15% above current levels
❎ High debt-to-equity ratio (1.8) indicates significant leverage
❎ Forward P/E of 25.3 suggests premium valuation compared to peers

<b>Market Insights</b>

<b>Recommendation: Buy 🟢</b>
Strong fundamentals and positive momentum outweigh valuation concerns, making this a compelling entry point for investors with medium to long-term horizons.

<b>Risk Level: Medium 🟠</b>
While fundamentals are solid, high valuation and debt levels create vulnerability to market downturns or interest rate changes.

Keep your response concise and focused on the most important insights. If certain data points are missing, acknowledge the limitations of your analysis.
        '''
        return prompt