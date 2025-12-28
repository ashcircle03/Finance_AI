
from src.collectors.stock import StockCollector
from src.collectors.news import NewsCollector
from src.collectors.disclosure import DisclosureCollector
from src.processing.extractor import LLMProcessor
from src.graph.loader import GraphLoader
import time

def run_stock_pipeline():
    print("Starting Stock Pipeline...")
    collector = StockCollector()
    news_collector = NewsCollector()
    disc_collector = DisclosureCollector()
    llm = LLMProcessor()
    
    loader = GraphLoader()
    
    tickers = collector.get_market_leaders()
    
    for ticker in tickers:
        print(f"Processing {ticker}...")
        info = collector.get_company_info(ticker)
        if info:
            loader.upsert_company(info)
            
            # --- News Section ---
            print(f"  Fetching news for {ticker}...")
            articles = news_collector.get_latest_news(ticker)
            for article in articles:
                # 1. Store News Node
                loader.upsert_news(article, ticker)
                # 2. Extract Event Signals
                extracted = llm.extract_graph_data(article['summary'])
                # 3. Store Signals
                for sig in extracted.get('signals', []):
                    try:
                        loader.upsert_signal(ticker, sig, article['url'])
                    except Exception as e:
                        print(f"    Error storing signal: {e}")

            # --- 10-K Section (New) ---
            print(f"  Fetching 10-K for {ticker} (SEC)...")
            text_10k = disc_collector.get_latest_10k_text(ticker)
            if text_10k:
                print(f"    Analyzing 10-K ({len(text_10k)} chars)...")
                fundamentals = llm.extract_fundamentals(text_10k)
                if fundamentals:
                    loader.upsert_report(ticker, fundamentals, "2024")
                    print("    10-K Analysis Stored.")
            else:
                print("    No 10-K found or failed to fetch.")

            # --- Financials Section (New) ---
            print(f"  Fetching Financial Facts for {ticker} (SEC XBRL)...")
            financials = disc_collector.get_financial_facts(ticker)
            if financials:
                loader.upsert_financials(ticker, financials)
                print(f"    Financials Stored (Rev: {len(financials.get('revenues',[]))} qtrs).")
            
            time.sleep(1) 
            
    loader.close()
    print("Stock Pipeline Complete.")

if __name__ == "__main__":
    run_stock_pipeline()
