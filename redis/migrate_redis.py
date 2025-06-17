from redis.commands.search.field import TextField, VectorField
from redis.commands.search.index_definition import IndexDefinition, IndexType

import os
import redis

REDIS_HOST = os.getenv("REDIS_HOST", "redis")
REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))
REDIS_PASSWORD = os.getenv("REDIS_PASSWORD")

r = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, password=REDIS_PASSWORD, decode_responses=False)

VECTOR_DIM = 128
INDEX_NAME = "idx:vectors"
VECTOR_FIELD = "vector"
VECTOR_TYPE = "FLOAT32"
VECTOR_METRIC = "COSINE"

def create_index():
    try:
        r.ft(INDEX_NAME).info()
        print("Индекс уже существует")
    except Exception:
        schema = (
            TextField("id"),
            VectorField(
                "vector",
                "FLAT",
                {
                    "TYPE": "FLOAT32",
                    "DIM": 128,
                    "DISTANCE_METRIC": "COSINE",
                    "INITIAL_CAP": 1000,
                }
            )
        )

        definition = IndexDefinition(prefix=["doc:"], index_type=IndexType.HASH)
        r.ft(INDEX_NAME).create_index(schema, definition=definition)
        print("Индекс создан")


if __name__ == "__main__":
    create_index()

    # for _ in range(10):
    #     doc_id = str(uuid.uuid4())
    #     vector = np.random.rand(128)
    #     add_vector_doc(doc_id, vector)
