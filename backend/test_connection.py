from falkordb import FalkorDB

db = FalkorDB(host='localhost', port=6379)
graph = db.select_graph('cerebro')

result = graph.query("CREATE (n:TestNode {name: 'Cerebro is alive'}) RETURN n")
print("Write successful:", result.result_set)

result = graph.query("MATCH (n:TestNode) RETURN n.name")
print("Read back:", result.result_set)
