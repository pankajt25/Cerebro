"""
Cerebro's extraction layer.
Uses Groq to pull structured entities + facts out of search results.
"""
import os
import json
import time
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

class Extractor:
    def __init__(self):
        api_key = os.getenv("GROQ_API_KEY")
        self.client = Groq(api_key=api_key)

    def extract(self, query_text, search_results):
        """
        Given the user's query and search results, extract structured
        entities and facts as JSON. Retries on transient failures.
        Returns: {"entities": [...], "facts": [...], "relationships": [...]}
        """
        context = "\n\n".join(
            f"Source: {r['url']}\nTitle: {r['title']}\nContent: {r['content']}"
            for r in search_results
        )

        prompt = f"""You are extracting structured knowledge from search results to build a knowledge graph.

User's question: {query_text}

Search results:
{context}

Extract the key entities (people, organizations, technologies, concepts) and facts from these results.
Return ONLY valid JSON, no other text, in this exact format:

{{
  "entities": [{{"name": "...", "type": "person|organization|technology|concept|other"}}],
  "facts": [{{"entity_name": "...", "text": "...", "confidence": 0.0-1.0, "source_url": "..."}}],
  "relationships": [{{"entity1": "...", "entity2": "..."}}]
}}

Keep entity names consistent across entities/facts/relationships. Extract 3-8 facts max, only the most relevant ones."""

        last_error = None
        for attempt in range(3):
            try:
                response = self.client.chat.completions.create(
                    model="openai/gpt-oss-120b",
                    max_tokens=1500,
                    messages=[{"role": "user", "content": prompt}],
                    response_format={"type": "json_object"},
                    timeout=20
                )
                raw_text = response.choices[0].message.content.strip()
                return json.loads(raw_text)
            except json.JSONDecodeError:
                last_error = "invalid JSON returned"
                print(f"Failed to parse JSON (attempt {attempt + 1})")
                if attempt < 2:
                    time.sleep(1.0)
                    continue
            except Exception as e:
                last_error = e
                print(f"Extraction attempt {attempt + 1} failed: {e}")
                if attempt < 2:
                    time.sleep(1.5 * (attempt + 1))
                    continue

        print(f"Extraction failed after all retries: {last_error}")
        return {"entities": [], "facts": [], "relationships": []}
