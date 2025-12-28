
import kuzu

def verify_graph():
    db = kuzu.Database("./data/fingraph_db")
    conn = kuzu.Connection(db)
    
    print("\n--- Companies ---")
    results = conn.execute("MATCH (c:Company) RETURN c.name, c.ticker LIMIT 5")
    while results.has_next():
        print(results.get_next())
        
    print("\n--- Concepts Linked to Companies ---")
    results = conn.execute("MATCH (c:Company)-[:RELATED_TO]->(t:Concept) RETURN c.ticker, t.name")
    while results.has_next():
        print(results.get_next())

if __name__ == "__main__":
    verify_graph()
