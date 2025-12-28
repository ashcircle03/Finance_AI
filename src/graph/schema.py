
from src.graph.db import Database

def initialize_schema():
    driver = Database.get_driver()
    with driver.session() as session:
        # Unique Constraints
        constraints = [
            "CREATE CONSTRAINT IF NOT EXISTS FOR (c:Company) REQUIRE c.ticker IS UNIQUE",
            "CREATE CONSTRAINT IF NOT EXISTS FOR (s:Sector) REQUIRE s.name IS UNIQUE",
            "CREATE CONSTRAINT IF NOT EXISTS FOR (n:News) REQUIRE n.url IS UNIQUE",
            "CREATE CONSTRAINT IF NOT EXISTS FOR (c:Concept) REQUIRE c.name IS UNIQUE"
        ]
        
        for query in constraints:
            session.run(query)
            print(f"Executed: {query}")
            
    print("Schema Initialization Complete.")

if __name__ == "__main__":
    initialize_schema()
