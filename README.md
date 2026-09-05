# 🧠 Cerebro

**A personal research agent with persistent memory, powered by FalkorDB.**

Cerebro remembers what you've researched across sessions. Every question is researched live via web search, structured into entities and facts by an LLM, and stored as a knowledge graph — so when you come back later and ask something related, Cerebro recalls and connects what it learned before, instead of starting cold.

🔗 **Live demo**: [cerebro-hackathon.streamlit.app](https://cerebro-hackathon.streamlit.app)

## Track
**Best Agentic AI Use Case** — WeMakeDevs x FalkorDB Graph Hacks

## Why FalkorDB does real work here
FalkorDB isn't a bolt-on visualization — it's the agent's actual memory. Every query the agent handles:
1. Checks the graph for prior knowledge on relevant entities
2. Writes newly discovered facts, entities, and relationships back into the graph
3. Runs a multi-hop cross-session query to surface what was learned in *previous, separate sessions*

Remove FalkorDB, and the agent has no memory at all — it becomes a stateless search-and-summarize tool.

## Architecture
                 ┌─────────────┐
                 │  User query │
                 └──────┬──────┘
                        │
                        ▼
              ┌───────────────────┐
              │ Tavily web search │
              └─────────┬─────────┘
                        │
                        ▼
    ┌───────────────────────────────────┐
    │ Groq LLM extraction               │
    │ (entities, facts, relationships)  │
    └───────────────┬───────────────────┘
                     │
                     ▼
            ┌─────────────────────┐
            │ FalkorDB write      │
            │ (nodes + edges)     │
            └──────────┬──────────┘
                       │
                       ▼
          ┌─────────────────────────────┐
          │ FalkorDB cross-session query│
          └──────────────┬──────────────┘
                          │
                          ▼
             ┌─────────────────────────┐
             │ Recalled context surfaced│
             │ in the UI                │
             └──────────────────────────┘

## Graph Data Model

**Nodes**
| Node | Properties |
|---|---|
| `Session` | id, timestamp, topic |
| `Query` | id, text, timestamp |
| `Entity` | name, type |
| `Fact` | id, text, confidence, last_updated |
| `Source` | url |

**Relationships**
| Relationship | Meaning |
|---|---|
| `(Session)-[:CONTAINS]->(Query)` | Session included this query |
| `(Query)-[:MENTIONS]->(Entity)` | Query touched this entity |
| `(Fact)-[:ABOUT]->(Entity)` | Fact describes this entity |
| `(Fact)-[:LEARNED_IN]->(Session)` | Fact was discovered in this session |
| `(Fact)-[:SOURCED_FROM]->(Source)` | Fact traces to this source |
| `(Entity)-[:RELATED_TO]->(Entity)` | Two entities are connected |

## Core Cypher Queries

**Cross-session recall** — the heart of the product:
```cypher
MATCH (e:Entity)<-[:MENTIONS]-(q:Query)<-[:CONTAINS]-(s:Session)
WHERE e.name IN $names AND s.id <> $current_session
RETURN DISTINCT s.id, s.timestamp, q.text
ORDER BY s.timestamp DESC
LIMIT 10
```

**Multi-hop related entities:**
```cypher
MATCH (e1:Entity {name: $name})-[:RELATED_TO*1..2]-(e2:Entity)
RETURN DISTINCT e2.name, e2.type
```

**Writing new knowledge:**
```cypher
MERGE (e:Entity {name: $entity_name})
ON CREATE SET e.type = $entity_type
CREATE (f:Fact {id: $fact_id, text: $fact_text, confidence: $confidence, last_updated: $ts})
CREATE (f)-[:ABOUT]->(e)
MERGE (src:Source {url: $source_url})
CREATE (f)-[:SOURCED_FROM]->(src)
WITH f
MATCH (s:Session {id: $session_id})
CREATE (f)-[:LEARNED_IN]->(s)
```

## Tech Stack
- **Graph DB**: FalkorDB (Cloud)
- **LLM (extraction)**: Groq (`openai/gpt-oss-120b`)
- **Web search**: Tavily API
- **Frontend**: Streamlit
- **Backend**: Python

## Local Setup

```bash
# Clone the repo
git clone https://github.com/pankajt25/Cerebro.git
cd Cerebro

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # WSL/Linux/Mac

# Install dependencies
pip install -r requirements.txt

# Set up environment variables
cp .env.example .env
# Edit .env with your own API keys (Groq, Tavily) and FalkorDB connection details

# Run FalkorDB locally via Docker (alternative to FalkorDB Cloud)
docker run -d --name cerebro-falkordb -p 6379:6379 -p 3000:3000 -v falkordb_data:/data falkordb/falkordb:latest

# Run the app
cd backend
streamlit run app.py
```

## Environment Variables

| Variable | Description |
|---|---|
| `GROQ_API_KEY` | Free tier at console.groq.com |
| `TAVILY_API_KEY` | Free tier at tavily.com |
| `FALKORDB_HOST` | FalkorDB host (localhost for Docker, or your FalkorDB Cloud endpoint) |
| `FALKORDB_PORT` | FalkorDB port |
| `FALKORDB_USERNAME` | Only needed for FalkorDB Cloud |
| `FALKORDB_PASSWORD` | Only needed for FalkorDB Cloud |

## Resilience Features
- Automatic retry with exponential backoff on transient search/extraction failures
- Oversized queries are truncated before hitting search API limits
- Graph write failures are isolated per-step so one failure doesn't block the rest of the pipeline
- Manual retry button in the UI when a query genuinely can't be completed
- Fact staleness tracking (7-day threshold) so knowledge refreshes naturally over time

## AI Coding Assistant Disclosure
This project was built with assistance from **Claude** (Anthropic) for code scaffolding, debugging, and architectural guidance. All code was reviewed, tested, and is understood by the participant. The graph data model, query design, and product decisions were made and validated by the participant throughout development.

## Demo
[Demo video link — to be added]
