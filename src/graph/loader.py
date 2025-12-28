
from src.graph.db import Database
import uuid

class GraphLoader:
    def __init__(self):
        self.driver = Database.get_driver()

    def upsert_company(self, company_data: dict):
        if not company_data: return
        ticker = company_data['ticker']
        name = company_data['name']
        sector = company_data['sector']
        summary = company_data['summary']
        query = """
        MERGE (c:Company {ticker: $ticker})
        ON CREATE SET c.name = $name, c.sector = $sector, c.summary = $summary
        ON MATCH SET c.name = $name, c.sector = $sector, c.summary = $summary
        MERGE (s:Sector {name: $sector})
        MERGE (c)-[:BELONGS_TO]->(s)
        """
        with self.driver.session() as session:
            session.run(query, ticker=ticker, name=name, sector=sector, summary=summary)
            
    def upsert_news(self, news_item: dict, ticker: str):
        query = """
        MERGE (n:News {url: $url})
        ON CREATE SET n.title = $title, n.date = $date, n.summary = $summary
        WITH n
        MATCH (c:Company {ticker: $ticker})
        MERGE (n)-[:MENTIONS]->(c)
        """
        with self.driver.session() as session:
            session.run(query, url=news_item['url'], title=news_item['title'], date=str(news_item['date']), summary=news_item['summary'], ticker=ticker)

    def upsert_signal(self, ticker: str, signal: dict, source_url: str):
        sig_id = str(uuid.uuid4())
        query = """
        MATCH (c:Company {ticker: $ticker})
        MATCH (n:News {url: $url})
        MERGE (s:Signal {id: $sig_id})
        ON CREATE SET 
            s.type = $type,
            s.summary = $summary,
            s.sentiment = $sentiment,
            s.reason = $reason,
            s.date = n.date
        MERGE (n)-[:REVEALS]->(s)
        MERGE (s)-[:AFFECTS]->(c)
        """
        with self.driver.session() as session:
             session.run(query, ticker=ticker, url=source_url, sig_id=sig_id, 
                         type=signal.get('type','기타'), summary=signal.get('summary',''), 
                         sentiment=signal.get('sentiment','NEUTRAL'), reason=signal.get('reason',''))

    def link_entities(self, source: str, target: str, rtype: str, reason: str):
        # Polymorphic linking: try to find Company by ticker or Concept by name
        # If not exists, create Concept
        query = """
        MERGE (s:Concept {name: $source})
        MERGE (t:Concept {name: $target})
        WITH s, t
        CALL apoc.create.relationship(s, $rtype, {reason: $reason}, t) YIELD rel
        RETURN rel
        """
        # Using APOC is ideal, but for standard Cypher we need dynamic Cypher which is hard.
        # Fallback to simple matching if nodes exist, or just create Concepts.
        # For this prototype we assume source/target are somewhat known or just create Concepts.
        
        # Simplified: Treat all as Concepts if not Company. 
        # But we know Source/Target might be "NVDA" (Ticker).
        # Let's try to match Company first.
        
        query_poly = f"""
        MERGE (s:Concept {{name: $source}})
        MERGE (t:Concept {{name: $target}})
        MERGE (s)-[r:{rtype}]->(t)
        SET r.reason = $reason
        """
        # Note: Cypher doesn't allow dynamic Relationship Types in MERGE without APOC.
        # So we strictly support a few types or use APOC.
        # Since user doesn't have APOC installed by default in community image maybe? 
        # Actually standard neo4j image doesn't have apoc. 
        # I will use a fallback 'RELATED_TO' with a type property if dynamic fails, 
        # OR just hardcode the most common ones.
        
        # Better approach: Just use RELATED_TO and add a property 'semantic_type'
        query_fallback = """
        MERGE (s:Concept {name: $source})
        MERGE (t:Concept {name: $target})
        MERGE (s)-[r:RELATED_TO]->(t)
        SET r.semantic_type = $rtype, r.reason = $reason
        """
        with self.driver.session() as session:
            session.run(query_fallback, source=source, target=target, rtype=rtype, reason=reason)

    def upsert_report(self, ticker: str, data: dict, year: str = "2024"):
        """
        Detailed 10-K Report Node
        """
        query = """
        MATCH (c:Company {ticker: $ticker})
        MERGE (r:Report {id: $ticker + '_10K_' + $year})
        ON CREATE SET 
            r.type = '10-K',
            r.year = $year,
            r.business_summary = $bs,
            r.detailed_business = $db,
            r.risks = $risks,
            r.competitors = $comps
        ON MATCH SET
            r.business_summary = $bs,
            r.detailed_business = $db,
            r.risks = $risks,
            r.competitors = $comps
        MERGE (c)-[:FILED]->(r)
        """
        with self.driver.session() as session:
            session.run(query, ticker=ticker, year=year, 
                        bs=data.get('business_summary', ''),
                        db=data.get('detailed_business', ''),
                        risks=data.get('risks', []),
                        comps=data.get('competitors', []))

    def upsert_financials(self, ticker: str, data: dict):
        """
        Stores latest financial metrics (Revenue, Net Income) as a Financials node.
        Properties are JSON strings for simplicity in this prototype.
        """
        import json
        query = """
        MATCH (c:Company {ticker: $ticker})
        MERGE (f:Financials {id: $ticker + '_FIN'})
        ON CREATE SET 
            f.revenues = $revenues,
            f.net_incomes = $net_incomes,
            f.updated_at = datetime()
        ON MATCH SET
            f.revenues = $revenues,
            f.net_incomes = $net_incomes,
            f.updated_at = datetime()
        MERGE (c)-[:HAS_FINANCIALS]->(f)
        """
        with self.driver.session() as session:
            session.run(query, ticker=ticker, 
                        revenues=json.dumps(data.get('revenues', [])),
                        net_incomes=json.dumps(data.get('net_incomes', [])))

    def close(self):
        self.driver.close()
