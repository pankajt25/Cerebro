"""
Cerebro — Streamlit frontend.
A research agent with persistent memory, powered by FalkorDB.
"""
import streamlit as st
from graph_store import GraphStore
from agent import CerebroAgent

st.set_page_config(page_title="Cerebro | FalkorDB Hackathon", page_icon="🧠", layout="wide")

# --- Custom styling ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;500;600;700&display=swap');

    html, body, [class*="css"] {
        font-family: 'Space Grotesk', sans-serif;
    }

    .stApp {
        background: radial-gradient(circle at 20% 0%, #1a0b2e 0%, #0d0518 45%, #060209 100%);
    }

    section[data-testid="stSidebar"] {
        background: linear-gradient(180deg, #150a28 0%, #0d0518 100%);
        border-right: 1px solid rgba(168, 85, 247, 0.25);
    }

    .cerebro-hero {
        padding: 0.5rem 0 1.5rem 0;
    }
    .cerebro-hero h1 {
        font-size: 2.8rem;
        font-weight: 700;
        background: linear-gradient(90deg, #c084fc, #818cf8, #a855f7);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0;
        letter-spacing: -1px;
    }
    .cerebro-hero p {
        color: #a78bfa;
        font-size: 1rem;
        margin-top: 0.2rem;
        opacity: 0.85;
    }
    .cerebro-badge {
        display: inline-block;
        background: rgba(168, 85, 247, 0.15);
        border: 1px solid rgba(168, 85, 247, 0.4);
        color: #d8b4fe;
        padding: 3px 12px;
        border-radius: 20px;
        font-size: 0.75rem;
        font-weight: 500;
        margin-top: 0.6rem;
    }

    div[data-testid="stChatMessage"] {
        background: rgba(168, 85, 247, 0.06);
        border: 1px solid rgba(168, 85, 247, 0.15);
        border-radius: 14px;
        padding: 0.5rem 0.2rem;
        margin-bottom: 0.6rem;
    }

    .stButton button {
        background: linear-gradient(90deg, #7c3aed, #a855f7);
        color: white;
        border: none;
        border-radius: 10px;
        font-weight: 600;
        transition: all 0.2s ease;
    }
    .stButton button:hover {
        box-shadow: 0 0 20px rgba(168, 85, 247, 0.6);
        transform: translateY(-1px);
    }

    .stTextInput input, .stChatInput textarea {
        background: rgba(255,255,255,0.04) !important;
        border: 1px solid rgba(168, 85, 247, 0.3) !important;
        border-radius: 10px !important;
        color: #f3e8ff !important;
    }

    div[data-testid="stExpander"] {
        border: 1px solid rgba(129, 140, 248, 0.4) !important;
        border-radius: 12px !important;
        background: rgba(129, 140, 248, 0.08) !important;
    }

    div[data-testid="stAlert"] {
        border-radius: 12px;
    }

    .cerebro-caption {
        color: #c4b5fd;
        font-size: 0.85rem;
    }

    .session-pill {
        display: inline-flex;
        align-items: center;
        gap: 6px;
        background: rgba(34, 197, 94, 0.12);
        border: 1px solid rgba(34, 197, 94, 0.4);
        color: #86efac;
        padding: 6px 14px;
        border-radius: 20px;
        font-size: 0.85rem;
        font-weight: 500;
    }
    .session-pill::before {
        content: "●";
        color: #22c55e;
        font-size: 0.7rem;
    }
</style>
""", unsafe_allow_html=True)

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

# --- Sidebar ---
with st.sidebar:
    st.markdown("""
    <div style="text-align:center; padding: 1rem 0;">
        <div style="font-size:2.5rem;">🧠</div>
        <div style="font-size:1.4rem; font-weight:700; background: linear-gradient(90deg, #c084fc, #a855f7); -webkit-background-clip: text; -webkit-text-fill-color: transparent;">Cerebro</div>
        <div style="font-size:0.8rem; color:#a78bfa; margin-top:2px;">Memory that survives sessions</div>
    </div>
    """, unsafe_allow_html=True)

    st.divider()

    if st.session_state.session_id is None:
        st.markdown("**🔎 What are you researching today?**")
        topic = st.text_input("Topic", placeholder="e.g. Graph databases", label_visibility="collapsed")
        if st.button("🚀 Start Session", type="primary", use_container_width=True):
            if topic.strip():
                st.session_state.session_id = store.create_session(topic)
                st.session_state.messages = []
                st.rerun()
            else:
                st.warning("Give it a topic first!")
    else:
        st.markdown('<div class="session-pill">Session active</div>', unsafe_allow_html=True)
        st.markdown(f'<p class="cerebro-caption" style="margin-top:8px;">ID: <code>{st.session_state.session_id[:8]}...</code></p>', unsafe_allow_html=True)
        if st.button("🔁 End Session & Start New", use_container_width=True):
            st.session_state.session_id = None
            st.session_state.messages = []
            st.rerun()

    st.divider()
    st.markdown("**⚡ How it works**")
    st.markdown(
        '<p class="cerebro-caption">Every question gets researched live and stored as a '
        'knowledge graph in <b>FalkorDB</b>. Come back later and ask something related — '
        'Cerebro recalls what it learned before, across sessions.</p>',
        unsafe_allow_html=True
    )

    st.divider()
    st.markdown(
        '<p class="cerebro-caption">🏆 Built for <b>Graph Hacks</b> — Best Agentic AI Use Case<br>'
        'Powered by FalkorDB · Groq · Tavily</p>',
        unsafe_allow_html=True
    )

# --- Main area ---
if st.session_state.session_id is None:
    st.markdown("""
    <div class="cerebro-hero">
        <h1>🧠 Cerebro</h1>
        <p>A research agent that remembers what it learns — across sessions, not just within one.</p>
        <span class="cerebro-badge">Powered by FalkorDB Graph Memory</span>
    </div>
    """, unsafe_allow_html=True)
    st.info("👈 Start a session in the sidebar to begin researching.")
    st.stop()

st.markdown("""
<div class="cerebro-hero">
    <h1>Research Chat</h1>
    <p>Ask anything — Cerebro searches, learns, and remembers.</p>
</div>
""", unsafe_allow_html=True)

for msg in st.session_state.messages:
    avatar = "🧑‍💻" if msg["role"] == "user" else "🧠"
    with st.chat_message(msg["role"], avatar=avatar):
        st.markdown(msg["content"])
        if msg["role"] == "assistant" and msg.get("cross_session"):
            with st.expander("🔗 Recalled from a previous session"):
                for item in msg["cross_session"]:
                    st.markdown(f"- *\"{item[2]}\"* — asked on a past session ({item[1][:10]})")

if user_input := st.chat_input("Ask something to research..."):
    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.chat_message("user", avatar="🧑‍💻"):
        st.markdown(user_input)

    with st.chat_message("assistant", avatar="🧠"):
        with st.spinner("🔮 Researching and building the knowledge graph..."):
            try:
                result = agent.process_query(st.session_state.session_id, user_input)
            except Exception as e:
                st.error("Something went wrong while researching that. Please try again or rephrase your question.")
                st.caption(f"Details: {e}")
                st.stop()

        if result.get("search_failed"):
            answer = "I couldn't reach the search service just now — this is usually temporary. Please try again in a moment."
        elif result["new_facts"]:
            answer_lines = ["**Here's what I found:**\n"]
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
            entity_tags = " ".join(f"`{e['name']}`" for e in result["entities"])
            st.markdown(f'<p class="cerebro-caption">🏷️ Entities: {entity_tags}</p>', unsafe_allow_html=True)

    st.session_state.messages.append({
        "role": "assistant",
        "content": answer,
        "cross_session": result.get("cross_session_context", [])
    })
