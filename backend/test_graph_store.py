from graph_store import GraphStore

store = GraphStore()

# Simulate a session
session_id = store.create_session(topic="Testing Cerebro")
query_id = store.create_query(session_id, "What is FalkorDB?")

store.link_query_to_entity(query_id, "FalkorDB", "technology")
fact_id = store.save_fact(
    entity_name="FalkorDB",
    entity_type="technology",
    fact_text="FalkorDB is a graph database built for AI workloads",
    confidence=0.9,
    source_url="https://falkordb.com",
    session_id=session_id
)

print("Session:", session_id)
print("Query:", query_id)
print("Fact:", fact_id)
print("Known facts about FalkorDB:", store.get_known_facts("FalkorDB"))
