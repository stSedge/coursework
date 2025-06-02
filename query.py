# CALL gds.graph.project('myGraph', 'Entity', '*')

# CALL gds.node2vec.stream('myGraph', {
#   embeddingDimension: 64,
#   walkLength: 10,
#   iterations: 5
# })
# YIELD nodeId, embedding
# RETURN gds.util.asNode(nodeId).name AS nodeName, embedding
# LIMIT 10

# CALL gds.node2vec.write('myGraph', {
#   embeddingDimension: 64,
#   writeProperty: 'embedding'
# })
# YIELD nodePropertiesWritten
