from graph_store import GraphStore
from agent import CerebroAgent

store = GraphStore()
agent = CerebroAgent()

# Session 1: ask about FalkorDB
session1 = store.create_session(topic="Learning about graph databases")
print("=== SESSION 1 ===")
result1 = agent.process_query(session1, "What is FalkorDB used for?")
print("New facts found:", len(result1["new_facts"]))
print("Entities:", [e["name"] for e in result1["entities"]])

# Session 2 (simulating a NEW/different session): ask something related
session2 = store.create_session(topic="Exploring GraphRAG")
print("\n=== SESSION 2 (should recall session 1) ===")
result2 = agent.process_query(session2, "How does GraphRAG relate to FalkorDB?")
print("New facts found:", len(result2["new_facts"]))
print("Cross-session recall:", result2["cross_session_context"])
