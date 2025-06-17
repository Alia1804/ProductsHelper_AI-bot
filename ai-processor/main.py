import os
from fastapi import FastAPI
from pydantic import BaseModel
from vectorizer import model
from redis_client import VectorStorage
from classifier import Classifier

classifier = Classifier(model)

app = FastAPI()

REDIS_HOST = os.getenv('REDIS_HOST', 'redis')
REDIS_PORT = int(os.getenv('REDIS_PORT', 6379))
REDIS_PASSWORD = os.getenv('REDIS_PASSWORD', None)

class MessageRequest(BaseModel):
    text: str
    user_id: str

@app.post('/process')
async def process_message(request: MessageRequest):
    answer = {'outputs': {}}

    answer['action'] = classifier.get_class(request.text)

    for ent in classifier.get_ents(request.text):

        vector = model.generate_embedding(ent)
        results = await VectorStorage.search_vectors_within_threshold(vector, 0.5, 10 if answer['action'] else 1)

        results = [i for i, _ in results]
        if results:
            answer['outputs'][ent] = results

    return answer


@app.post('/add_vector')
async def process_message(request: MessageRequest):

    vector = model.generate_embedding(request.text)
    await VectorStorage.add_vector_doc(request.user_id, vector)

