from typing import List, Dict
from services.llm.prompts.prompt_base import BasePrompt

class NewsSummaryPrompt(BasePrompt):
    """Prompt generator for news summarization and translation"""
    
    @staticmethod
    def build_prompt(news_articles: List[Dict]) -> str:
        """
        Build a prompt for summarizing and translating news articles
        
        Args:
            news_articles: List of news articles with title, description, source, and published_at
            
        Returns:
            Prompt string
        """
        articles_text = ""
        
        for i, article in enumerate(news_articles, 1):
            articles_text += f"""
文章 {i}:
標題: {article['title']}
描述: {article['description'] or 'N/A'}
來源: {article['source']}
發布時間: {article['published_at']}
URL: {article['url']}
內容摘要: {article['content'][:500] if article['content'] else 'N/A'}

"""
        
        prompt = f"""
你是一位資深商業和財經新聞編輯，請將以下英文財經新聞翻譯並總結成繁體中文。

以下是新聞文章:
{articles_text}

請執行以下任務：
一：翻譯每篇文章的標題為繁體中文
二：為每篇文章撰寫一段簡短但信息豐富的摘要（繁體中文）
三：在摘要中包含文章的關鍵財務數據、市場影響和背景（如果有的話）
四：按照重要性排序，將最具市場影響力的新聞放在前面
五：確保保留每篇文章的來源信息

請按照以下格式輸出:

<b>本週環球要聞</b>

<b>1. [翻譯後的標題]</b>
[原始來源] | [發布日期]
[簡潔但全面的繁體中文摘要，包含關鍵財務數據和市場影響]

<b>2. [翻譯後的標題]</b>
...

請確保所有內容翻譯成地道、專業的繁體中文，適合香港和臺灣的讀者閱讀。

注意：標題中的來源可以移除。
"""
        
        return prompt