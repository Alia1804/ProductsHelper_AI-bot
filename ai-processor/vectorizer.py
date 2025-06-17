from sentence_transformers import SentenceTransformer
import os

MODEL_PATH = './models/rubert'


class Vectorizer:
    def __init__(self):
        if not os.path.exists(MODEL_PATH):
            model = SentenceTransformer('DeepPavlov/rubert-base-cased-sentence')
            model.save(MODEL_PATH)
        self.model = SentenceTransformer(MODEL_PATH)

    def generate_embedding(self, description: str):
        return self.model.encode(description)
    

model = Vectorizer()
