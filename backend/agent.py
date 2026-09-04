"""
Cerebro's core agent loop.
Orchestrates: check memory -> search if needed -> extract -> save to graph -> respond.
Auto-refreshes stale knowledge and never raises — always returns a usable result.
"""
import time
from graph_store import GraphStore
from search import SearchClient
from extractor import Extractor

class CerebroAgent:
    def __init__(self):
        self.store = GraphStore()
        self.search = SearchClient()
        self.extractor = Extractor()

    def process_query(self, session_id, query_text):
        return self._process_with_auto_retry(session_id, query_text)

    def _process_with_auto_retry(self, session_id, query_text, outer_attempts=2):
        """Wraps the full pipeline with one transparent auto-retry on total failure,
        so a single transient blip doesn't surface as an error to the user at all."""
        last_result = None
        for attempt in range(outer_attempts):
            result = self._process_once(session_id, query_text)
            if not result.get("search_failed"):
                return result
            last_result = result
            if attempt < outer_attempts - 1:
                time.sleep(2)
        return last_result

    def _process_once(self, session_id, query_text):
        # Step 0: record the query — never let a DB hiccup crash the whole pipeline
        query_id = None
        try:
            query_id = self.store.create_query(session_id, query_text)
        except Exception as e:
            print(f"Failed to record query in graph (continuing without it): {e}")

        # Step 1: search the web (search.py already retries internally, skips
        # retries entirely for non-retryable errors like oversized queries)
        search_results = self.search.search(query_text, max_results=5)

        # Step 2: extract structured knowledge from results
        if search_results:
            extracted = self.extractor.extract(query_text, search_results)
        else:
            extracted = {"entities": [], "facts": [], "relationships": []}

        # Step 3: cross-session recall
        entity_names = [e["name"] for e in extracted.get("entities", [])]
        try:
            cross_session = self.store.get_cross_session_context(entity_names, session_id)
        except Exception as e:
            print(f"Cross-session lookup failed: {e}")
            cross_session = []

        # Step 4: link query to entities (only if we successfully created the query node)
        if query_id:
            for entity in extracted.get("entities", []):
                try:
                    self.store.link_query_to_entity(query_id, entity["name"], entity["type"])
                except Exception as e:
                    print(f"Failed to link entity {entity.get('name')}: {e}")

        # Step 5: save new facts
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

        # Step 6: relationships
        for rel in extracted.get("relationships", []):
            try:
                self.store.link_related_entities(rel["entity1"], rel["entity2"])
            except Exception as e:
                print(f"Failed to link relationship: {e}")

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

    def is_topic_fresh(self, entity_name):
        """Public helper: check if we have recent (non-stale) knowledge on this entity."""
        try:
            return not self.store.is_entity_stale(entity_name)
        except Exception:
            return False
