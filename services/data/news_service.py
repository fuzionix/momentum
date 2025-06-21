import os
from typing import List, Dict
from newsapi import NewsApiClient

class NewsService:
    def __init__(self):
        self.api_key = os.getenv('NEWS_API_KEY')
        self.newsapi = NewsApiClient(api_key=self.api_key)
    
    def get_highlighted_news(self, limit: int = 5) -> List[Dict]:
        """
        Fetch top financial and business headlines
        
        Args:
            limit: Number of news articles to return
            
        Returns:
            List of news articles
        """
        try:
            # Get headlines from business category
            business_news = self.newsapi.get_top_headlines(
                category='business',
                language='en',
                page_size=limit
            )
            
            # Format the results
            articles = []
            if business_news['status'] == 'ok':
                for article in business_news['articles'][:limit]:
                    articles.append({
                        'title': article['title'],
                        'description': article['description'],
                        'url': article['url'],
                        'source': article['source']['name'],
                        'published_at': article['publishedAt'],
                        'content': article['content']
                    })
            
            return articles
        except Exception as e:
            print(f"Error fetching news: {e}")
            return []