"""
Cerebro's extraction layer.
Uses Groq (free tier, Llama 3.3 70B) to pull structured entities + facts
out of search results.
"""
import os
import json
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
        entities and facts as JSON.
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

        response = self.client.chat.completions.create(
            model="openai/gpt-oss-120b",
            max_tokens=1500,
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"}
        )

        raw_text = response.choices[0].message.content.strip()

        try:
            return json.loads(raw_text)
        except json.JSONDecodeError:
            print("Failed to parse JSON:", raw_text)
            return {"entities": [], "facts": [], "relationships": []}
