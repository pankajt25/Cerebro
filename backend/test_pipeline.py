from search import SearchClient
from extractor import Extractor

search = SearchClient()
extractor = Extractor()

query = "What is FalkorDB used for?"

print("Searching...")
results = search.search(query, max_results=3)
for r in results:
    print("-", r["title"], r["url"])

print("\nExtracting...")
extracted = extractor.extract(query, results)
print(extracted)
