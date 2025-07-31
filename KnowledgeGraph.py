from env import uri, user, password, db_name
from Neo4jConnection import Neo4jConnection
from sentence_transformers import SentenceTransformer
import re
import spacy
import textacy.extract

class KnowledgeGraph: 
    def __init__(self, text):
        self.text = text
        self.nlp = spacy.load("en_core_web_trf")
        self.doc = self.nlp(self.text)

    # def get_triplets(self):
    #     triplets = list(textacy.extract.triples.subject_verb_object_triples(self.doc))
    #     t = []
    #     for triple in triplets:
    #         node_subject = " ".join(map(str, triple.subject))
    #         node_object  = " ".join(map(str, triple.object))
    #         relation = " ".join(map(str, triple.verb))
    #         t.append([node_subject, relation, node_object])
    #     return t

    def get_span(self, token):
        subtree = list(token.subtree)
        return token.doc[subtree[0].i : subtree[-1].i + 1].text

    def get_triplets(self):
        triplets = []
        prev = None
        for sentence in self.doc.sents:
            for token in sentence:
                if token.pos_ == "VERB" or token.dep_ == "ROOT":
                    subjects = [w for w in token.children if w.dep_  in ("nsubj", "nsubjpass")]
                    objects  = [w for w in token.children if w.dep_ in ("dobj", "pobj", "obj", "attr")]
                    if not objects:
                        objects  = [w for w in sentence if w.dep_ in ("dobj", "pobj", "obj", "attr")]
                    if subjects and objects:
                        if subjects[0].pos_ == "PRON" and prev:
                            subj_text = prev
                        else:
                            subj_text = self.get_span(subjects[0])
                            prev = subj_text
                        obj_text = objects[0].lemma_
                        pred = token.text
                        triplets.append((subj_text, pred, obj_text))
        return triplets
    
    def insert_triplet(self, conn: Neo4jConnection, subject: str, predicate: str, object_: str):
        query = f"""
        MERGE (s:Entity {{name: "{subject}"}})
        MERGE (o:Entity {{name: "{object_}"}})
        MERGE (s)-[:{predicate}]->(o)
        """
        conn.query(query)

    def add_embedding(self):
        conn = Neo4jConnection(uri=uri, user=user, password=password)
        conn.query("CALL gds.graph.drop('myGraph', false) YIELD graphName")
        conn.query("CALL gds.graph.project('myGraph', 'Entity', '*')")
        q = '''
            CALL gds.node2vec.stream('myGraph', {
            embeddingDimension: 384,
            walkLength: 10,
            iterations: 5
            })
            YIELD nodeId, embedding
            '''
        conn.query(q)
        q = '''
            CALL gds.node2vec.write('myGraph', {
            embeddingDimension: 384,
            writeProperty: 'embedding'
            })
            YIELD nodePropertiesWritten
            '''
        conn.query(q)
        conn.close()

    def add_embeddings1(self, conn):
        query = "MATCH (e:Entity) RETURN e.name AS name"
        result = conn.query(query)
        nodes = [{"name": record["name"]} for record in result]

        names = [node["name"] for node in nodes]
        embedder = SentenceTransformer("all-MiniLM-L6-v2")
        embeddings = embedder.encode(names)

        for node, emb in zip(nodes, embeddings):
            query = """
                    MATCH (e:Entity) WHERE e.name = $name
                    SET e.embedding = $embedding
                    """
            conn.query(query, {
                "name": node["name"],
                "embedding": emb.tolist()
            })


    def create_knowledge_graph(self):
        triplets = self.get_triplets()
        conn = Neo4jConnection(uri=uri, user=user, password=password)
        #conn.query(f"CREATE OR REPLACE DATABASE {db_name}")
        conn.query("MATCH (n) DETACH DELETE n")
        for subj, pred, obj in triplets:
            print(subj, pred, obj)
            self.insert_triplet(conn, subj, pred, obj)
        self.add_embeddings1(conn)
        print("ok")
        conn.close()
