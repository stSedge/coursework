from env import uri, user, password
from Neo4jConnection import Neo4jConnection
import spacy
from sentence_transformers import SentenceTransformer

class Embedding:
    def __init__(self):
        self.nlp = spacy.load("en_core_web_sm")
        self.embedder = SentenceTransformer("all-MiniLM-L6-v2")

    def query_embedding(self, query_text):
        return self.embedder.encode([query_text])[0].tolist()

    def query_similar_nodes(self, embedding, top_k=5):
        conn = Neo4jConnection(uri=uri, user=user, password=password)
        cypher = """
        MATCH (e:Entity)
        WHERE e.embedding IS NOT NULL
        WITH e, gds.similarity.cosine($embedding, e.embedding) AS score
        RETURN e.name AS name, score
        ORDER BY score DESC
        LIMIT $topK
        """
        params = {
            "embedding": embedding,
            "topK": top_k
        }
        result = conn.query(cypher, params=params)
        conn.close()
        if result is None:
            return []
        return [{"name": record["name"], "score": record["score"]} for record in result]

    def get_related_triplets(self, node_name):
        conn = Neo4jConnection(uri=uri, user=user, password=password)
        cypher = f"""
        MATCH (s:Entity)-[r]->(o:Entity)
        WHERE s.name = '{node_name}' OR o.name = '{node_name}'
        RETURN s.name AS subject, type(r) AS relation, o.name AS object
        """
        result = conn.query(cypher)
        conn.close()
        return [(r["subject"], r["relation"], r["object"]) for r in result]
    
    def get_triplets(self, query):
        query_emb = self.query_embedding(query)
        similar_nodes = self.query_similar_nodes(query_emb)
        triplets = []
        seen = set()
        for node in similar_nodes:
            name = node["name"]
            for triplet in self.get_related_triplets(name):
                if triplet not in seen:
                    seen.add(triplet)
                    triplets.append(triplet)
        return triplets[:40]


