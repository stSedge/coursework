import ollama

from Embedding import Embedding


class Model:
    def __init__(self):
        self.client = ollama.Client()
        self.model = "graphrag"

    def get_answer(self, query):
        context = Embedding().get_triplets(query)
        promt = query + "context: " + context
        return self.client.generate(model=self.model, prompt=promt)