
from fastapi import FastAPI, HTTPException
from src.graph.db import Database
from pydantic import BaseModel
from typing import List, Optional, Any

app = FastAPI(title="FinGraph API")

class Node(BaseModel):
    id: str
    label: str
    type: str

class Edge(BaseModel):
    source: str
    target: str
    relation: str
    reason: Optional[str] = None

class NewsItem(BaseModel):
    title: str
    url: str
    date: str

class SignalItem(BaseModel):
    type: str
    summary: str
    sentiment: str
    reason: str
    date: str
    
class ReportItem(BaseModel):
    type: str     # 10-K
    year: str
    business_summary: str
    detailed_business: str
    risks: List[str]
    competitors: List[str]

class GraphResponse(BaseModel):
    nodes: List[Node]
    edges: List[Edge]
    news: List[NewsItem]
    signals: List[SignalItem]
    report: Optional[ReportItem] = None
    financials: Optional[dict] = None # Added Financials

@app.get("/search/{ticker}", response_model=GraphResponse)
def search_ticker(ticker: str):
    driver = Database.get_driver()
    nodes_dict = {}
    edges = []
    news_list = []
    signals_list = []
    report_item = None
    financials_data = None
    
    import json
    
    # 1. Fetch Company & Sector
    query_graph = """
    MATCH (c:Company {ticker: $ticker})
    OPTIONAL MATCH (c)-[:BELONGS_TO]->(s:Sector)
    RETURN c, s
    """
    
    # 2. Fetch Signals
    query_signals = """
    MATCH (s:Signal)-[:AFFECTS]->(c:Company {ticker: $ticker})
    RETURN s
    ORDER BY s.date DESC LIMIT 10
    """
    
    # 3. Fetch Report
    query_report = """
    MATCH (c:Company {ticker: $ticker})-[:FILED]->(r:Report)
    RETURN r
    ORDER BY r.year DESC LIMIT 1
    """
    
    # 4. Fetch Financials
    query_fin = """
    MATCH (c:Company {ticker: $ticker})-[:HAS_FINANCIALS]->(f:Financials)
    RETURN f
    """
    
    # 5. Fetch News
    query_news = """
    MATCH (c:Company {ticker: $ticker})<-[:MENTIONS]-(n:News)
    RETURN n
    ORDER BY n.date DESC LIMIT 5
    """

    with driver.session() as session:
        # Graph Query
        result = session.run(query_graph, ticker=ticker)
        record = result.single()
        
        if not record or not record['c']:
             raise HTTPException(status_code=404, detail="Ticker not found")

        c = record['c']
        nodes_dict[c['ticker']] = Node(id=c['ticker'], label=c.get('name', ticker), type="Company")

        s = record['s']
        if s:
            nodes_dict[s['name']] = Node(id=s['name'], label=s['name'], type="Sector")
            edges.append(Edge(source=c['ticker'], target=s['name'], relation="BELONGS_TO"))
            
        # Signal Query
        result_sig = session.run(query_signals, ticker=ticker)
        for r in result_sig:
            sig = r['s']
            signals_list.append(SignalItem(
                type=sig.get('type', '기타'),
                summary=sig.get('summary', ''),
                sentiment=sig.get('sentiment', 'NEUTRAL'),
                reason=sig.get('reason', ''),
                date=str(sig.get('date', ''))
            ))
            
            type_label = sig.get('type', 'Event')
            nodes_dict[type_label] = Node(id=type_label, label=type_label, type="Event")
            edges.append(Edge(source=type_label, target=c['ticker'], relation="AFFECTS", reason=sig.get('summary')))
            
        # Report Query
        result_rep = session.run(query_report, ticker=ticker)
        rep_record = result_rep.single()
        if rep_record:
            r = rep_record['r']
            report_item = ReportItem(
                type=r.get('type', '10-K'),
                year=r.get('year', '2024'),
                business_summary=r.get('business_summary', ''),
                detailed_business=r.get('detailed_business', ''),
                risks=r.get('risks', []),
                competitors=r.get('competitors', [])
            )
            
        # Financials Query
        result_fin = session.run(query_fin, ticker=ticker)
        fin_record = result_fin.single()
        if fin_record:
            f = fin_record['f']
            financials_data = {
                "revenues": json.loads(f.get("revenues", "[]")),
                "net_incomes": json.loads(f.get("net_incomes", "[]"))
            }
        
        # News Query
        result_news = session.run(query_news, ticker=ticker)
        for record in result_news:
             n = record['n']
             news_list.append(NewsItem(
                 title=n.get('title', 'No Title'),
                 url=n.get('url', '#'),
                 date=str(n.get('date', ''))
             ))
        
    return GraphResponse(
        nodes=list(nodes_dict.values()), 
        edges=edges,
        news=news_list,
        signals=signals_list,
        report=report_item,
        financials=financials_data
    )

@app.get("/leaders")
def get_market_leaders():
    driver = Database.get_driver()
    with driver.session() as session:
        result = session.run("MATCH (c:Company) RETURN c.ticker, c.name LIMIT 20")
        return [{"ticker": r[0], "name": r[1]} for r in result]
