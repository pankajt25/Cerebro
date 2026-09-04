"""
Cerebro's web search layer using Tavily.
"""
import os
import time
from tavily import TavilyClient
from dotenv import load_dotenv

load_dotenv()

class SearchClient:
    def __init__(self):
        api_key = os.getenv("TAVILY_API_KEY")
        self.client = TavilyClient(api_key=api_key)

    def search(self, query, max_results=5, retries=3):
        """Returns list of {title, url, content} dicts. Retries on transient network errors."""
        last_error = None
        for attempt in range(retries + 1):
            try:
                response = self.client.search(
                    query=query,
                    max_results=max_results,
                    search_depth="basic",
                    timeout=15
                )
                return [
                    {"title": r["title"], "url": r["url"], "content": r["content"]}
                    for r in response.get("results", [])
                ]
            except Exception as e:
                last_error = e
                if attempt < retries:
                    time.sleep(1.5 * (attempt + 1))  # increasing backoff
                    continue
        # All retries exhausted — return empty instead of crashing the app
        print(f"Search failed after {retries + 1} attempts: {last_error}")
        return []
