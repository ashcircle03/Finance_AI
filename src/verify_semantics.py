
from src.graph.db import Database

def verify_semantics():
    driver = Database.get_driver()
    with driver.session() as session:
        print("\n--- Relationship Types ---")
        res = session.run("MATCH ()-[r]->() RETURN type(r) as t, count(r) as c ORDER BY c DESC")
        for r in res:
            print(f"{r['t']}: {r['c']}")
            
        print("\n--- Sample Reasoning ---")
        query = """
        MATCH (s)-[r]->(t) 
        WHERE r.reason IS NOT NULL 
        RETURN s.name, type(r), t.name, r.reason 
        LIMIT 5
        """
        res = session.run(query)
        for r in res:
            # Handle cases where source/target might be Company (ticker) or Concept (name)
            # In our schema Company has `name` too. Concept has `name`.
            s_name = r[0] if r[0] else "Unknown"
            t_name = r[2] if r[2] else "Unknown"
            print(f"{s_name} --[{r[1]}]--> {t_name}")
            print(f"   Reason: {r[3]}")
            
    driver.close()

if __name__ == "__main__":
    verify_semantics()
