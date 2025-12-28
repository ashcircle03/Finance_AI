
import feedparser
import datetime
from typing import List, Dict
import urllib.parse

class NewsCollector:
    def __init__(self):
        self.base_url = "https://news.google.com/rss/search?q={query}&hl=en-US&gl=US&ceid=US:en"

    def get_latest_news(self, ticker: str, limit: int = 3) -> List[Dict]:
        """
        Fetches real news from Google News RSS for the given ticker.
        """
        # Search query: ticker + "stock" to filter relevant news
        query = urllib.parse.quote(f"{ticker} stock")
        url = self.base_url.format(query=query)
        
        print(f"    Fetching RSS: {url}")
        feed = feedparser.parse(url)
        
        news_items = []
        for entry in feed.entries[:limit]:
            # Use description as summary (often contains HTML, LLM can handle it or we strip it)
            # For simplicity, we pass the title + snippet to LLM
            
            item = {
                "url": entry.link,
                "title": entry.title,
                "summary": f"{entry.title} - {entry.description}", # Combine for better context extraction
                "date": entry.published if 'published' in entry else str(datetime.date.today())
            }
            news_items.append(item)
            
        return news_items

if __name__ == "__main__":
    collector = NewsCollector()
    print(collector.get_latest_news("NVDA"))
