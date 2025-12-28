
from src.graph.db import Database

def verify():
    driver = Database.get_driver()
    with driver.session() as session:
        print("\n--- Summary ---")
        res = session.run("MATCH (n) RETURN labels(n) as l, count(n) as c")
        for r in res:
            print(f"{r['l']}: {r['c']}")
            
        print("\n--- Sample Linkages ---")
        res = session.run("MATCH (c:Company)-[:RELATED_TO]->(t:Concept) RETURN c.ticker, t.name LIMIT 5")
        for r in res:
            print(f"{r['c.ticker']} -> {r['t.name']}")
            
    driver.close()

if __name__ == "__main__":
    verify()
