
from neo4j import GraphDatabase
import os
import time

class Database:
    _driver = None

    @classmethod
    def get_driver(cls):
        if cls._driver is None:
            uri = os.getenv("NEO4J_URI", "bolt://localhost:7687")
            user = os.getenv("NEO4J_USER", "neo4j")
            password = os.getenv("NEO4J_PASSWORD", "password")
            
            # Retry logic for container startup
            for _ in range(10):
                try:
                    cls._driver = GraphDatabase.driver(uri, auth=(user, password))
                    cls._driver.verify_connectivity()
                    print(f"Connected to Neo4j at {uri}")
                    break
                except Exception as e:
                    print(f"Waiting for Neo4j... ({e})")
                    time.sleep(2)
                    
        return cls._driver

    @classmethod
    def close(cls):
        if cls._driver:
            cls._driver.close()
