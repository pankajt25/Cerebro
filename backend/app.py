"""
Cerebro — Streamlit frontend.
A research agent with persistent memory, powered by FalkorDB.
"""
import streamlit as st
from graph_store import GraphStore
from agent import CerebroAgent

st.set_page_config(page_title="Cerebro", page_icon="🧠", layout="wide")

@st.cache_resource
def get_agent():
    return CerebroAgent()

@st.cache_resource
def get_store():
    return GraphStore()

agent = get_agent()
store = get_store()

if "session_id" not in st.session_state:
    st.session_state.session_id = None
if "messages" not in st.session_state:
    st.session_state.messages = []

with st.sidebar:
    st.title("🧠 Cerebro")
    st.caption("A research agent with persistent memory")

    if st.session_state.session_id is None:
        topic = st.text_input("What are you researching today?", placeholder="e.g. Graph databases")
        if st.button("Start Session", type="primary", use_container_width=True):
            if topic.strip():
                st.session_state.session_id = store.create_session(topic)
                st.session_state.messages = []
                st.rerun()
    else:
        st.success("Session active")
        st.caption(f"Session ID: `{st.session_state.session_id[:8]}...`")
        if st.button("End Session & Start New", use_container_width=True):
            st.session_state.session_id = None
            st.session_state.messages = []
            st.rerun()

    st.divider()
    st.markdown("**How it works:**")
    st.caption(
        "Every question you ask gets researched live and stored as a "
        "knowledge graph in FalkorDB. Come back later and ask something "
        "related — Cerebro will recall what it learned before."
    )

if st.session_state.session_id is None:
    st.info("👈 Start a session in the sidebar to begin researching.")
    st.stop()

st.title("Research Chat")

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])
        if msg["role"] == "assistant" and msg.get("cross_session"):
            with st.expander("🔗 Recalled from a previous session"):
                for item in msg["cross_session"]:
                    st.markdown(f"- *\"{item[2]}\"* — asked on a past session ({item[1][:10]})")

if user_input := st.chat_input("Ask something to research..."):
    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.markdown(user_input)

    with st.chat_message("assistant"):
        with st.spinner("Researching..."):
            try:
                result = agent.process_query(st.session_state.session_id, user_input)
            except Exception as e:
                st.error("Something went wrong while researching that. Please try again or rephrase your question.")
                st.caption(f"Details: {e}")
                st.stop()

        if result.get("search_failed"):
            answer = "I couldn't reach the search service just now — this is usually temporary. Please try again in a moment."
        elif result["new_facts"]:
            answer_lines = ["Here's what I found:\n"]
            for fact in result["new_facts"]:
                answer_lines.append(f"- {fact['text']}")
            answer = "\n".join(answer_lines)
        elif result.get("raw_snippets"):
            answer_lines = ["I couldn't structure this into clean facts, but here's what I found:\n"]
            for snippet in result["raw_snippets"]:
                answer_lines.append(f"- {snippet}")
            answer = "\n".join(answer_lines)
        else:
            answer = "I searched but couldn't find anything useful — try rephrasing?"

        st.markdown(answer)

        if result.get("cross_session_context"):
            with st.expander("🔗 Recalled from a previous session", expanded=True):
                for item in result["cross_session_context"]:
                    st.markdown(f"- *\"{item[2]}\"* — asked on a past session ({item[1][:10]})")

        if result.get("entities"):
            st.caption("Entities: " + ", ".join(e["name"] for e in result["entities"]))

    st.session_state.messages.append({
        "role": "assistant",
        "content": answer,
        "cross_session": result.get("cross_session_context", [])
    })
