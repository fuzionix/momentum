from typing import Dict
from datetime import datetime
from utils.formatters import format_large_number
from services.llm.prompts.prompt_base import BasePrompt

class StockAnalysisPrompt(BasePrompt):
    '''Prompt generator for stock analysis'''

    def build_prompt(stock_data: Dict) -> str:
        stock_info = stock_data['stock_info']
        historical_data = stock_data['historical_data']
        news = stock_data['news']

        financial_summary = f'''
- Current Price: ${stock_info['current_price']}
- Market Cap: {format_large_number(stock_info['market_cap'])}
- P/E Ratio: {stock_info['pe_ratio']}
- Forward P/E: {stock_info['forward_pe']}
- EPS: ${stock_info['eps']}
- Forward EPS: ${stock_info['forward_eps']}
- Revenue: {format_large_number(stock_info['revenue'])}
- Dividend Yield: {stock_info['dividend_yield']}%
- Target Mean Price: ${stock_info['target_mean_price']}
- Analyst Recommendation: {stock_info['recommendation'].capitalize()}
- Analyst Count: {stock_info['num_analyst_opinions']}
'''

        price_history_text = f'''
- Date Range: {historical_data['start_date']} to {historical_data['end_date']}
- Starting Price: ${historical_data['start_price']}
- Current Price: ${historical_data['end_price']}
- Change: ${historical_data['price_change']} ({historical_data['percent_change']}%)
- 1-Month Range: ${historical_data['min_price']} - ${historical_data['max_price']}
- Average Volume: {format_large_number(historical_data['avg_volume'])}
- 52-Week Range: ${stock_info['fifty_two_week_low']} - ${stock_info['fifty_two_week_high']}
- 50-Day Moving Average: ${stock_info['fifty_day_average']}
- 200-Day Moving Average: ${stock_info['two_hundred_day_average']}
'''
        
        technical_analysis_section = f'''
- RSI (14): {historical_data['current_indicators']['rsi']} ({'Overbought' if historical_data['technical_signals']['rsi_overbought'] else 'Oversold' if historical_data['technical_signals']['rsi_oversold'] else 'Neutral'})
- MACD: {historical_data['current_indicators']['macd']} (Signal: {historical_data['current_indicators']['macd_signal']})
- MACD Signal: {'Bullish' if historical_data['technical_signals']['macd_bullish'] else 'Bearish'}
- 20-Day SMA: ${historical_data['current_indicators']['sma20']}
- Price vs 20-Day SMA: {'Above' if historical_data['technical_signals']['price_above_sma20'] else 'Below'}
- Bollinger Bands: Upper ${historical_data['current_indicators']['upper_bollinger']} / Lower ${historical_data['current_indicators']['lower_bollinger']}
- ATR: ${historical_data['current_indicators']['atr']}
- 1-Month Volatility: {historical_data['volatility']}
'''
        
        financial_health_section = f'''
- Profit Margin: {f"{float(stock_info['profit_margins']) * 100:.2f}%" if stock_info['profit_margins'] != 'N/A' else 'N/A'}
- Operating Margin: {f"{float(stock_info['operating_margins']) * 100:.2f}%" if stock_info['operating_margins'] != 'N/A' else 'N/A'}
- Gross Margin: {f"{float(stock_info['gross_margins']) * 100:.2f}%" if stock_info['gross_margins'] != 'N/A' else 'N/A'}
- Return on Equity: {f"{float(stock_info['return_on_equity']) * 100:.2f}%" if stock_info['return_on_equity'] != 'N/A' else 'N/A'}
- Return on Assets: {f"{float(stock_info['return_on_assets']) * 100:.2f}%" if stock_info['return_on_assets'] != 'N/A' else 'N/A'}
- Debt to Equity: {stock_info['debt_to_equity']}
- Current Ratio: {stock_info['current_ratio']}
- Quick Ratio: {stock_info['quick_ratio']}
- Operating Cash Flow: {format_large_number(stock_info['operating_cash_flow'])}
- Free Cash Flow: {format_large_number(stock_info['free_cash_flow'])}
- Total Cash: {format_large_number(stock_info['total_cash'])}
- Total Debt: {format_large_number(stock_info['total_debt'])}
- PEG Ratio: {stock_info['peg_ratio']}
- Price to Book: {stock_info['price_to_book']}
- Price to Sales: {stock_info['price_to_sales']}
'''
        
        news_items = []
        for i, news_item in enumerate(news[:5]):  # Limit to 5 most recent news items
            content = news_item['content']
            date_str = datetime.strptime(content['pubDate'], '%Y-%m-%dT%H:%M:%SZ').strftime('%Y-%m-%d')
            news_items.append(f"{date_str}: {content['title']}")

        news_section = "\n".join(news_items)

        # Create the prompt
        prompt = f'''
You are a financial analyst providing insights on stock {stock_data['ticker']} ({stock_info['name']}).

COMPANY INFORMATION:
- Symbol: {stock_data['ticker']}
- Company: {stock_info['name']}
- Sector: {stock_info['sector']}
- Industry: {stock_info['industry']}
- Business Summary: {stock_info['business_summary']}

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
[Ticker] | [Current Price] | [🔺(Increase)/🔻(Decrease)] [Percent Change %]

<b>Company Overview</b>
[Provide a brief strategic assessment of the company's market position, recent business developments, and key competitive advantages or challenges.]

<b>Key Signals</b>
[List exactly 8 key signals, with a mix of positive and negative indicators, prioritizing the most impactful factors for investors]
✅ [Positive signal with brief explanation]
✅ [Positive signal with brief explanation]
❎ [Negative signal with brief explanation]
[etc.]

<b>Market Insights</b>
[Paragraph 1: Analyze price action in relation to broader market trends, sector performance, and technical indicators. Include specific numbers and timeframes.]
[Paragraph 2: Connect recent news to price movements, evaluate how market sentiment is affecting the stock, and identify potential catalysts. Reference specific news items from the provided data.]
[Paragraph 3: Provide advanced strategic insights by analyzing competitive positioning, identifying market inefficiencies or misunderstood aspects of the business model, and evaluating the company's strategic advantage within evolving industry dynamics. Consider how macroeconomic factors, regulatory changes, or structural trends might specifically impact this company's trajectory in ways the market hasn't fully priced in. If possible, identify a contrarian view or overlooked opportunity that sophisticated investors should consider.]

<b>Recommendation: [Buy/Sell/Hold] [🟢/🔴/🟡]</b>
[Provide a clear recommendation based on the analysis, including a target price and timeframe for the recommendation in 2-3 sentences.]

<b>Risk Level: [Low/Medium/High] [⚪/🟠/🔴]</b>
[Assess the risk level associated with the investment recommendation, considering factors such as volatility, market conditions, and company-specific risks in 2-3 sentences.]

---

Example output format:
# ACME | $123.45 | 🔺 1.92%
    
<b>Company Overview</b>
ACME Corp is a leading player in the tech sector, specializing in AI-driven solutions. The company has recently expanded its product line and secured several high-profile contracts, positioning itself for robust growth in the coming quarters.

<b>Key Signals</b>
✅ Strong profit margin (23.4%) outperforming sector average by 7.2%
✅ Recent price momentum with 5.2% gain over 7 days
✅ Analyst consensus is 'buy' with target price 15% above current levels
❎ High debt-to-equity ratio (1.8) indicates significant leverage
❎ Forward P/E of 25.3 suggests premium valuation compared to peers

<b>Market Insights</b>
[Paragraph 1]
[Paragraph 2]
[Paragraph 3]

<b>Recommendation: Buy 🟢</b>
[]

<b>Risk Level: Medium 🟠</b>
[]

Keep your response concise and focused on the most important insights. If certain data points are missing, acknowledge the limitations of your analysis.
        '''
        return prompt