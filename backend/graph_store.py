"""
Cerebro's graph memory layer.
Wraps FalkorDB Cypher queries into clean Python functions.
"""
from falkordb import FalkorDB
import uuid
import os
from datetime import datetime, timezone
from dotenv import load_dotenv

load_dotenv()

class GraphStore:
    def __init__(self, host=None, port=None, username=None, password=None, graph_name='cerebro'):
        # Fall back to env vars, then to local defaults if nothing is set
        host = host or os.getenv("FALKORDB_HOST", "localhost")
        port = int(port or os.getenv("FALKORDB_PORT", 6379))
        username = username or os.getenv("FALKORDB_USERNAME")
        password = password or os.getenv("FALKORDB_PASSWORD")

        if username and password:
            self.db = FalkorDB(host=host, port=port, username=username, password=password)
        else:
            self.db = FalkorDB(host=host, port=port)

        self.graph = self.db.select_graph(graph_name)

    def create_session(self, topic):
        session_id = str(uuid.uuid4())
        timestamp = datetime.now(timezone.utc).isoformat()
        self.graph.query(
            "CREATE (s:Session {id: $id, timestamp: $ts, topic: $topic})",
            {"id": session_id, "ts": timestamp, "topic": topic}
        )
        return session_id

    def create_query(self, session_id, query_text):
        query_id = str(uuid.uuid4())
        timestamp = datetime.now(timezone.utc).isoformat()
        self.graph.query(
            """
            MATCH (s:Session {id: $session_id})
            CREATE (q:Query {id: $query_id, text: $text, timestamp: $ts})
            CREATE (s)-[:CONTAINS]->(q)
            """,
            {"session_id": session_id, "query_id": query_id, "text": query_text, "ts": timestamp}
        )
        return query_id

    def get_known_facts(self, entity_name):
        """Check if we already know something about this entity."""
        result = self.graph.query(
            """
            MATCH (e:Entity {name: $name})<-[:ABOUT]-(f:Fact)
            OPTIONAL MATCH (f)-[:SOURCED_FROM]->(src:Source)
            RETURN f.text, f.confidence, src.url
            """,
            {"name": entity_name}
        )
        return result.result_set

    def get_cross_session_context(self, entity_names, current_session_id):
        """Recall what we discussed about these entities in OTHER sessions."""
        if not entity_names:
            return []
        result = self.graph.query(
            """
            MATCH (e:Entity)<-[:MENTIONS]-(q:Query)<-[:CONTAINS]-(s:Session)
            WHERE e.name IN $names AND s.id <> $current_session
            RETURN DISTINCT s.id, s.timestamp, q.text
            ORDER BY s.timestamp DESC
            LIMIT 10
            """,
            {"names": entity_names, "current_session": current_session_id}
        )
        return result.result_set

    def get_related_entities(self, entity_name, hops=2):
        """Multi-hop: find entities connected to this one."""
        result = self.graph.query(
            f"""
            MATCH (e1:Entity {{name: $name}})-[:RELATED_TO*1..{hops}]-(e2:Entity)
            RETURN DISTINCT e2.name, e2.type
            """,
            {"name": entity_name}
        )
        return result.result_set

    def link_query_to_entity(self, query_id, entity_name, entity_type):
        self.graph.query(
            """
            MERGE (e:Entity {name: $name})
            ON CREATE SET e.type = $type
            WITH e
            MATCH (q:Query {id: $query_id})
            CREATE (q)-[:MENTIONS]->(e)
            """,
            {"name": entity_name, "type": entity_type, "query_id": query_id}
        )

    def save_fact(self, entity_name, entity_type, fact_text, confidence, source_url, session_id):
        fact_id = str(uuid.uuid4())
        self.graph.query(
            """
            MERGE (e:Entity {name: $entity_name})
            ON CREATE SET e.type = $entity_type
            CREATE (f:Fact {id: $fact_id, text: $fact_text, confidence: $confidence})
            CREATE (f)-[:ABOUT]->(e)
            MERGE (src:Source {url: $source_url})
            CREATE (f)-[:SOURCED_FROM]->(src)
            WITH f
            MATCH (s:Session {id: $session_id})
            CREATE (f)-[:LEARNED_IN]->(s)
            """,
            {
                "entity_name": entity_name, "entity_type": entity_type,
                "fact_id": fact_id, "fact_text": fact_text, "confidence": confidence,
                "source_url": source_url, "session_id": session_id
            }
        )
        return fact_id

    def link_related_entities(self, entity1, entity2):
        self.graph.query(
            """
            MATCH (e1:Entity {name: $e1}), (e2:Entity {name: $e2})
            MERGE (e1)-[:RELATED_TO]->(e2)
            """,
            {"e1": entity1, "e2": entity2}
        )
