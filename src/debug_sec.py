
import requests
import json
import time

headers = {
    "User-Agent": "FinGraphProject student@fingraph.com",
    "Accept-Encoding": "gzip, deflate",
    "Host": "data.sec.gov"
}

def check_aapl():
    # AAPL CIK: 0000320193
    url = "https://data.sec.gov/api/xbrl/companyfacts/CIK0000320193.json"
    print(f"Fetching {url}...")
    resp = requests.get(url, headers=headers)
    if resp.status_code != 200:
        print(f"Error: {resp.status_code}")
        return
        
    data = resp.json()
    us_gaap = data.get('facts', {}).get('us-gaap', {})
    
    print("Available US-GAAP Tags (first 50):")
    keys = list(us_gaap.keys())
    print(keys[:50])
    
    # Check specific tags
    for tag in ['Revenues', 'SalesRevenueNet', 'RevenueFromContractWithCustomerExcludingAssessedTax', 'NetIncomeLoss']:
        if tag in us_gaap:
            print(f"\nTag Found: {tag}")
            units = us_gaap[tag].get('units', {})
            print(f"  Units: {list(units.keys())}")
            if 'USD' in units:
                print(f"  First 3 records for USD:")
                print(json.dumps(units['USD'][-3:], indent=2))
        else:
            print(f"\nTag NOT Found: {tag}")

if __name__ == "__main__":
    check_aapl()
