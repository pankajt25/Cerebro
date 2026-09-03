"""
Cerebro's web search layer using Tavily.
"""
import os
from tavily import TavilyClient
from dotenv import load_dotenv

load_dotenv()

class SearchClient:
    def __init__(self):
        api_key = os.getenv("TAVILY_API_KEY")
        self.client = TavilyClient(api_key=api_key)

    def search(self, query, max_results=5):
        """Returns list of {title, url, content} dicts."""
        response = self.client.search(
            query=query,
            max_results=max_results,
            search_depth="basic"
        )
        return [
            {"title": r["title"], "url": r["url"], "content": r["content"]}
            for r in response.get("results", [])
        ]
