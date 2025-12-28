
import yfinance as yf
import pandas as pd
from typing import List, Dict

class StockCollector:
    def __init__(self):
        self.market_leaders = [
            "NVDA", "AAPL", "MSFT", "GOOGL", "AMZN", "TSLA", "META"
        ]

    def get_market_leaders(self) -> List[str]:
        return self.market_leaders

    def get_company_info(self, ticker: str) -> Dict:
        """
        Fetches basic company info and sector from yfinance.
        """
        try:
            stock = yf.Ticker(ticker)
            info = stock.info
            
            return {
                "ticker": ticker,
                "name": info.get("longName", ticker),
                "sector": info.get("sector", "Unknown"),
                "summary": info.get("longBusinessSummary", "No summary available.")[:500] + "..." # Truncate for demo
            }
        except Exception as e:
            print(f"Error fetching data for {ticker}: {e}")
            return None

if __name__ == "__main__":
    collector = StockCollector()
    data = collector.get_company_info("NVDA")
    print(data)
