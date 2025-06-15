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
- 當前價格：${stock_info['current_price']}
- 市值：{format_large_number(stock_info['market_cap'])}
- 市盈率：{stock_info['pe_ratio']}
- 預期市盈率：{stock_info['forward_pe']}
- 每股收益：${stock_info['eps']}
- 預期每股收益：${stock_info['forward_eps']}
- 營業收入：{format_large_number(stock_info['revenue'])}
- 股息收益率：{stock_info['dividend_yield']}%
- 目標均價：${stock_info['target_mean_price']}
- 分析師建議：{stock_info['recommendation'].capitalize()}
- 分析師人數：{stock_info['num_analyst_opinions']}
'''

        price_history_text = f'''
- 日期範圍：{historical_data['start_date']} 至 {historical_data['end_date']}
- 起始價格：${historical_data['start_price']}
- 當前價格：${historical_data['end_price']}
- 變動：${historical_data['price_change']} ({historical_data['percent_change']}%)
- 一個月範圍：${historical_data['min_price']} - ${historical_data['max_price']}
- 平均成交量：{format_large_number(historical_data['avg_volume'])}
- 52 週範圍：${stock_info['fifty_two_week_low']} - ${stock_info['fifty_two_week_high']}
- 50 日移動平均線：${stock_info['fifty_day_average']}
- 200 日移動平均線：${stock_info['two_hundred_day_average']}
'''
        
        technical_analysis_section = f'''
- RSI (14)：{historical_data['current_indicators']['rsi']} ({'超買' if historical_data['technical_signals']['rsi_overbought'] else '超賣' if historical_data['technical_signals']['rsi_oversold'] else '中性'})
- MACD：{historical_data['current_indicators']['macd']} (訊號線：{historical_data['current_indicators']['macd_signal']})
- MACD 訊號：{'看漲' if historical_data['technical_signals']['macd_bullish'] else '看跌'}
- 20 日簡單移動平均線：${historical_data['current_indicators']['sma20']}
- 價格與 20 日均線關係：{'Above' if historical_data['technical_signals']['price_above_sma20'] else 'Below'}
- 布林帶：上軌 ${historical_data['current_indicators']['upper_bollinger']} / 下軌 ${historical_data['current_indicators']['lower_bollinger']}
- ATR：${historical_data['current_indicators']['atr']}
- 一個月波動率：{historical_data['volatility']}
'''
        
        financial_health_section = f'''
- 利潤率：{f"{float(stock_info['profit_margins']) * 100:.2f}%" if stock_info['profit_margins'] != 'N/A' else 'N/A'}
- 營運利潤率：{f"{float(stock_info['operating_margins']) * 100:.2f}%" if stock_info['operating_margins'] != 'N/A' else 'N/A'}
- 毛利率：{f"{float(stock_info['gross_margins']) * 100:.2f}%" if stock_info['gross_margins'] != 'N/A' else 'N/A'}
- 股本回報率：{f"{float(stock_info['return_on_equity']) * 100:.2f}%" if stock_info['return_on_equity'] != 'N/A' else 'N/A'}
- 資產回報率：{f"{float(stock_info['return_on_assets']) * 100:.2f}%" if stock_info['return_on_assets'] != 'N/A' else 'N/A'}
- 負債權益比：{stock_info['debt_to_equity']}
- 流動比率：{stock_info['current_ratio']}
- 速動比率：{stock_info['quick_ratio']}
- 營運現金流：{format_large_number(stock_info['operating_cash_flow'])}
- 自由現金流：{format_large_number(stock_info['free_cash_flow'])}
- 總現金：{format_large_number(stock_info['total_cash'])}
- 總負債：{format_large_number(stock_info['total_debt'])}
- PEG 比率：{stock_info['peg_ratio']}
- 市淨率：{stock_info['price_to_book']}
- 市銷率：{stock_info['price_to_sales']}
'''
        
        news_items = []
        for i, news_item in enumerate(news[:5]):  # Limit to 5 most recent news items
            content = news_item['content']
            date_str = datetime.strptime(content['pubDate'], '%Y-%m-%dT%H:%M:%SZ').strftime('%Y-%m-%d')
            news_items.append(f"{date_str}: {content['title']}")

        news_section = "\n".join(news_items)

        # Create the prompt
        prompt = f'''
你是一位金融分析師，正在為股票 {stock_data['ticker']} ({stock_info['name']}) 提供見解。

公司資料：
- 股票代號：{stock_data['ticker']}
- 公司名稱：{stock_info['name']}
- 行業：{stock_info['sector']}
- 產業：{stock_info['industry']}
- 業務概要：{stock_info['business_summary']}

財務指標：
{financial_summary}

市場數據：
{price_history_text}

技術分析：
{technical_analysis_section}
    
財務健康：
{financial_health_section}

最新消息：
{news_section}

根據這些資料，請按照以下結構提供財務分析：
[股票代號] | [當前價格] | [🔺(上升)/🔻(下降)] [百分比變動 %]

<b>公司概覽</b>
[提供公司市場地位、近期業務發展以及主要競爭優勢或挑戰的簡要戰略評估。]

<b>關鍵訊號</b>
[列出恰好8個關鍵訊號，混合正面和負面指標，優先考慮對投資者最有影響力的因素]
✅ [正面訊號及簡短解釋]
✅ [正面訊號及簡短解釋]
❎ [負面訊號及簡短解釋]
[等等]

<b>市場洞察</b>
[第1段]：[分析價格走勢與更廣泛的市場趨勢、行業表現和技術指標的關係。包括具體數字和時間框架。]
[第2段]：[將近期新聞與價格變動聯繫起來，評估市場情緒如何影響股票，並識別潛在催化劑。引用提供數據中的具體新聞項目。]
[第3段]：[通過分析競爭定位、識別市場低效率或被誤解的業務模式方面，以及評估公司在不斷演變的行業動態中的戰略優勢，提供高級戰略洞察。考慮宏觀經濟因素、監管變化或結構性趨勢如何特別影響這家公司的軌跡，以市場尚未充分定價的方式。如果可能，識別資深投資者應考慮的反向觀點或被忽視的機會。]

<b>建議：[買入/賣出/持有] [🟢/🔴/🟡]</b>
[根據分析提供明確的建議，包括目標價格和建議的時間框架，使用2-3句話。]

<b>風險級別：[低/中/高] [⚪/🟠/🔴]</b>
[評估與投資建議相關的風險水平，考慮波動性、市場條件和公司特定風險等因素，使用2-3句話。]

---

輸出格式示例：
# ACME | $123.45 | 🔺 1.92%
    
<b>公司概覽</b>
ACME公司是科技行業的領先企業，專注於AI驅動的解決方案。該公司最近擴展了產品線並獲得了幾個高知名度的合約，為未來幾個季度的強勁增長奠定了基礎。

<b>關鍵訊號</b>
✅ 強勁的利潤率(23.4%)，超過行業平均水平7.2%
✅ 最近7天價格勢頭強勁，漲幅達5.2%
✅ 分析師一致給予「買入」評級，目標價格高於當前水平15%
❎ 高負債權益比(1.8)表明顯著槓桿
❎ 預期市盈率25.3，相比同行估值偏高

<b>市場洞察</b>
[]
[]
[]

<b>建議：買入 🟢</b>
[]

<b>風險級別：中等 🟠</b>
[]

請保持回應簡潔，專注於最重要的見解。如果某些數據點缺失，請確認分析的局限性。
        '''
        return prompt