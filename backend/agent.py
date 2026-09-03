"""
Cerebro's core agent loop.
Orchestrates: check memory -> search if needed -> extract -> save to graph -> respond.
"""
from graph_store import GraphStore
from search import SearchClient
from extractor import Extractor

class CerebroAgent:
    def __init__(self):
        self.store = GraphStore()
        self.search = SearchClient()
        self.extractor = Extractor()

    def process_query(self, session_id, query_text):
        """
        Main entry point: handles one user query end-to-end.
        Returns a dict with the answer context (known facts, new facts, cross-session recall).
        """
        query_id = self.store.create_query(session_id, query_text)

        # Step 1: search the web for this query
        search_results = self.search.search(query_text, max_results=5)

        # Step 2: extract structured knowledge from results
        extracted = self.extractor.extract(query_text, search_results)

        # Step 3: check what we already knew BEFORE this search (cross-session recall)
        entity_names = [e["name"] for e in extracted.get("entities", [])]
        cross_session = self.store.get_cross_session_context(entity_names, session_id)

        # Step 4: link query to entities mentioned
        for entity in extracted.get("entities", []):
            self.store.link_query_to_entity(query_id, entity["name"], entity["type"])

        # Step 5: save new facts to the graph
        saved_facts = []
        entity_type_map = {e["name"]: e["type"] for e in extracted.get("entities", [])}
        for fact in extracted.get("facts", []):
            entity_type = entity_type_map.get(fact["entity_name"], "other")
            fact_id = self.store.save_fact(
                entity_name=fact["entity_name"],
                entity_type=entity_type,
                fact_text=fact["text"],
                confidence=fact.get("confidence", 0.7),
                source_url=fact.get("source_url", ""),
                session_id=session_id
            )
            saved_facts.append(fact)

        # Step 6: save relationships between entities
        for rel in extracted.get("relationships", []):
            self.store.link_related_entities(rel["entity1"], rel["entity2"])

        return {
            "query_id": query_id,
            "new_facts": saved_facts,
            "cross_session_context": cross_session,
            "entities": extracted.get("entities", [])
        }
