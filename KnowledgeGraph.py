from env import uri, user, password, db_name
from Neo4jConnection import Neo4jConnection
import spacy

class KnowledgeGraph: 
    def __init__(self, text):
        self.text = text
        self.nlp = spacy.load("en_core_web_sm")
        self.doc = self.nlp(self.text)

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
        conn.query("CALL gds.graph.project('myGraph', 'Entity', '*')")
        q = '''
            CALL gds.node2vec.stream('myGraph', {
            embeddingDimension: 64,
            walkLength: 10,
            iterations: 5
            })
            YIELD nodeId, embedding
            '''
        conn.query(q)
        q = '''
            CALL gds.node2vec.write('myGraph', {
            embeddingDimension: 64,
            writeProperty: 'embedding'
            })
            YIELD nodePropertiesWritten
            '''
        conn.query()
        conn.close()

    def create_knowledge_graph(self):
        triplets = self.get_triplets()
        conn = Neo4jConnection(uri=uri, user=user, password=password)
        conn.query(f"CREATE OR REPLACE DATABASE {db_name}")
        for subj, pred, obj in triplets:
            self.insert_triplet(conn, subj, pred, obj)
        self.add_embedding()
        conn.close()
