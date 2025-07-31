import ollama

from Embedding import Embedding


class Model:
    def __init__(self):
        self.client = ollama.Client()
        self.model = "phi"

    def get_answer(self, query):
        context = Embedding().get_triplets(query)
        context_str = "\n".join([f"{s} {p} {o}" for s, p, o in context])
        prompt = query + "\ncontext:\n" + context_str
        return self.client.generate(model=self.model, prompt=prompt, stream=False)["response"]