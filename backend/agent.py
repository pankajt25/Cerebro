"""
Cerebro's core agent loop.
Orchestrates: check memory -> search if needed -> extract -> save to graph -> respond.
Designed to never raise — always returns a usable result, even on upstream failures.
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
        query_id = self.store.create_query(session_id, query_text)

        # Step 1: search the web (never crashes — returns [] on failure after retries)
        search_results = self.search.search(query_text, max_results=5)

        # Step 2: extract structured knowledge from results
        if search_results:
            extracted = self.extractor.extract(query_text, search_results)
        else:
            extracted = {"entities": [], "facts": [], "relationships": []}

        # Step 3: check what we already knew BEFORE this search (cross-session recall)
        entity_names = [e["name"] for e in extracted.get("entities", [])]
        try:
            cross_session = self.store.get_cross_session_context(entity_names, session_id)
        except Exception as e:
            print(f"Cross-session lookup failed: {e}")
            cross_session = []

        # Step 4: link query to entities mentioned
        for entity in extracted.get("entities", []):
            try:
                self.store.link_query_to_entity(query_id, entity["name"], entity["type"])
            except Exception as e:
                print(f"Failed to link entity {entity.get('name')}: {e}")

        # Step 5: save new facts to the graph
        saved_facts = []
        entity_type_map = {e["name"]: e["type"] for e in extracted.get("entities", [])}
        for fact in extracted.get("facts", []):
            try:
                entity_type = entity_type_map.get(fact["entity_name"], "other")
                self.store.save_fact(
                    entity_name=fact["entity_name"],
                    entity_type=entity_type,
                    fact_text=fact["text"],
                    confidence=fact.get("confidence", 0.7),
                    source_url=fact.get("source_url", ""),
                    session_id=session_id
                )
                saved_facts.append(fact)
            except Exception as e:
                print(f"Failed to save fact: {e}")

        # Step 6: save relationships between entities
        for rel in extracted.get("relationships", []):
            try:
                self.store.link_related_entities(rel["entity1"], rel["entity2"])
            except Exception as e:
                print(f"Failed to link relationship: {e}")

        # Fallback: if extraction produced no facts, surface raw search snippets
        raw_snippets = []
        if not saved_facts and search_results:
            raw_snippets = [r["content"][:300] for r in search_results[:3] if r.get("content")]

        return {
            "query_id": query_id,
            "new_facts": saved_facts,
            "cross_session_context": cross_session,
            "entities": extracted.get("entities", []),
            "raw_snippets": raw_snippets,
            "search_failed": not search_results
        }
