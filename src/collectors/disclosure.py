
import requests
import json
from bs4 import BeautifulSoup
import time

class DisclosureCollector:
    def __init__(self):
        self.headers = {
            "User-Agent": "FinGraphProject student@fingraph.com",
            "Accept-Encoding": "gzip, deflate",
            "Host": "www.sec.gov"
        }
        self.data_headers = {
            "User-Agent": "FinGraphProject student@fingraph.com",
            "Accept-Encoding": "gzip, deflate",
            "Host": "data.sec.gov"
        }
        self.tickers_url = "https://www.sec.gov/files/company_tickers.json"
        
        # Cache mapping
        self.ticker_to_cik = self._load_ticker_map()

    def _load_ticker_map(self):
        try:
            print("Fetching SEC Ticker Map...")
            resp = requests.get(self.tickers_url, headers=self.headers)
            if resp.status_code != 200:
                print(f"Failed to fetch tickers: {resp.status_code}")
                return {}
            
            data = resp.json()
            # data is dict of dicts: "0": {"cik_str": 320193, "ticker": "AAPL", ...}
            mapping = {}
            for item in data.values():
                mapping[item['ticker']] = item['cik_str']
            return mapping
        except Exception as e:
            print(f"Error loading ticker map: {e}")
            return {}

    def get_latest_10k_text(self, ticker: str) -> str:
        cik = self.ticker_to_cik.get(ticker.upper())
        if not cik:
            print(f"CIK not found for {ticker}")
            return None
            
        # CIK must be 10 digits zero-padded for API URLs
        cik_str = f"{cik:010d}"
        
        submissions_url = f"https://data.sec.gov/submissions/CIK{cik_str}.json"
        
        try:
            print(f"Fetching submissions for {ticker} (CIK: {cik_str})...")
            # Rate limit politeness
            time.sleep(0.1)
            resp = requests.get(submissions_url, headers=self.data_headers)
            if resp.status_code != 200:
                print(f"Failed to fetch submissions: {resp.status_code}")
                return None
                
            data = resp.json()
            filings = data.get('filings', {}).get('recent', {})
            
            # Find latest 10-K
            forms = filings.get('form', [])
            accession_nums = filings.get('accessionNumber', [])
            primary_docs = filings.get('primaryDocument', [])
            
            for i, form in enumerate(forms):
                if form == '10-K':
                    acc = accession_nums[i]
                    doc = primary_docs[i]
                    # Format: https://www.sec.gov/Archives/edgar/data/{cik}/{acc_no_dash}/{doc}
                    acc_no_dash = acc.replace("-", "")
                    doc_url = f"https://www.sec.gov/Archives/edgar/data/{cik}/{acc_no_dash}/{doc}"
                    
                    print(f"Found 10-K URL: {doc_url}")
                    return self._fetch_and_clean_text(doc_url)
                    
            print(f"No 10-K found for {ticker}")
            return None
            
        except Exception as e:
            print(f"Error fetching 10-K: {e}")
            return None

    def _fetch_and_clean_text(self, url: str) -> str:
        try:
            # Archives are on www.sec.gov
            resp = requests.get(url, headers=self.headers)
            if resp.status_code != 200:
                print(f"Failed to download 10-K: {resp.status_code}")
                return ""
                
            soup = BeautifulSoup(resp.content, 'html.parser')
            # Extract text
            text = soup.get_text(separator=' ', strip=True)
            
            # Very basic cleanup
            return text
        except Exception as e:
            print(f"Error parsing document: {e}")
            return ""

    def get_financial_facts(self, ticker: str) -> dict:
        """
        Fetches quantitative financial data (Revenue, Net Income) from SEC XBRL API.
        Returns a dictionary with 'revenues' and 'net_incomes' lists (Quarterly).
        """
        cik = self.ticker_to_cik.get(ticker.upper())
        if not cik:
            print(f"CIK not found for {ticker}")
            return {}
            
        cik_str = f"{cik:010d}"
        facts_url = f"https://data.sec.gov/api/xbrl/companyfacts/CIK{cik_str}.json"
        
        try:
            print(f"Fetching company facts for {ticker}...")
            time.sleep(0.1)
            resp = requests.get(facts_url, headers=self.data_headers)
            if resp.status_code != 200:
                print(f"Failed to fetch facts: {resp.status_code}")
                return {}
                
            data = resp.json()
            us_gaap = data.get('facts', {}).get('us-gaap', {})
            
            # Extract Revenue
            # Strategy: Iterate through potential tags. Use the first one that returns RECENT data.
            revenue_data = []
            rev_tags = ['RevenueFromContractWithCustomerExcludingAssessedTax', 'Revenues', 'SalesRevenueNet']
            
            for tag_name in rev_tags:
                tag = us_gaap.get(tag_name)
                if not tag: continue
                
                temp_data = []
                units = tag.get('units', {}).get('USD', [])
                for u in units:
                    # Filter for recent data (e.g. > 2023) and 10-Q/10-K forms
                    if u.get('year', 0) >= 2023 and 'frame' in u: 
                         temp_data.append({
                             "period": u['frame'],
                             "value": u['val'],
                             "date": u['end']
                         })
                
                if temp_data:
                    revenue_data = temp_data
                    print(f"  Using Revenue Tag: {tag_name} ({len(revenue_data)} records)")
                    break # Found valid recent data
            
            # Extract Net Income (NetIncomeLoss)
            income_data = []
            inc_tags = ['NetIncomeLoss', 'ProfitLoss']
            
            for tag_name in inc_tags:
                tag = us_gaap.get(tag_name)
                if not tag: continue
                
                temp_data = []
                units = tag.get('units', {}).get('USD', [])
                for u in units:
                    if u.get('year', 0) >= 2023 and 'frame' in u:
                         temp_data.append({
                             "period": u['frame'],
                             "value": u['val'],
                             "date": u['end']
                         })
                
                if temp_data:
                    income_data = temp_data
                    print(f"  Using Income Tag: {tag_name} ({len(income_data)} records)")
                    break

            # Sort by period
            revenue_data.sort(key=lambda x: x['period'])
            income_data.sort(key=lambda x: x['period'])
            
            return {
                "revenues": revenue_data[-8:], # Last 8 quarters/periods
                "net_incomes": income_data[-8:]
            }
            
        except Exception as e:
            print(f"Error fetching facts: {e}")
            return {}

if __name__ == "__main__":
    c = DisclosureCollector()
    # facts = c.get_financial_facts("AAPL")
    # print(json.dumps(facts, indent=2))
    text = c.get_latest_10k_text("AAPL")
    if text:
        print(f"Excerpt: {text[:500]}...")
