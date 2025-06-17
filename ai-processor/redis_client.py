import os
import redis.asyncio as redis
import struct
import numpy as np
from typing import List, Tuple, Optional

class RedisManager:
    _client: Optional[redis.Redis] = None

    @classmethod
    async def get_redis(cls) -> redis.Redis:
        if cls._client is None:
            cls._client = redis.Redis.from_url(
                os.getenv("REDIS_URL", f"redis://{os.getenv('REDIS_HOST','redis')}:{os.getenv('REDIS_PORT','6379')}"),
                password=os.getenv("REDIS_PASSWORD"),
                decode_responses=False,
                max_connections=10,
                socket_timeout=5
            )
        return cls._client

class VectorStorage:
    VECTOR_FIELD = "vector"
    VECTOR_DIM = int(os.getenv("VECTOR_DIM", 128))

    @staticmethod
    def float_vector_to_bytes(vector: np.ndarray) -> bytes:
        return vector.astype(np.float32).tobytes()

    @staticmethod
    def bytes_to_float_vector(b: bytes) -> np.ndarray:
        expected_len = VectorStorage.VECTOR_DIM * 4  # 4 байта на float32
        if b is None:
            raise ValueError("Получен None вместо байтов вектора")
        if len(b) != expected_len:
            raise ValueError(f"Неверная длина байтов вектора: ожидалось {expected_len}, получено {len(b)}")
        return np.array(struct.unpack(f'{VectorStorage.VECTOR_DIM}f', b), dtype=np.float32)


    @classmethod
    async def add_vector_doc(cls, doc_id: str, vector: np.ndarray):
        redis_client = await RedisManager.get_redis()
        key = f"{VectorStorage.VECTOR_FIELD}:{doc_id}"
        await redis_client.hset(
            key,
            mapping={
                "vector": vector.astype(np.float32).tobytes(),
                "id": doc_id
            }
        )
        print(f"Добавлен документ {doc_id}")


    @staticmethod
    def cosine_similarity(a: np.ndarray, b: np.ndarray) -> float:
        """Вычисление косинусного сходства"""
        dot_product = np.dot(a, b)
        norm_a = np.linalg.norm(a)
        norm_b = np.linalg.norm(b)
        return (dot_product / (norm_a * norm_b)).item()

    @classmethod
    async def search_vectors_within_threshold(
        cls,
        query_vector: np.ndarray,
        threshold: float = 0,
        k: int = 100
    ) -> List[Tuple[str, float]]:
        redis_client = await RedisManager.get_redis()
        
        keys = await redis_client.keys(f"{VectorStorage.VECTOR_FIELD}*")
        results = []
        query = query_vector.astype(np.float32).flatten()
        
        for key in keys:
            data = await redis_client.hgetall(key)

            vector = np.frombuffer(data[b"vector"], dtype=np.float32)
            similarity = VectorStorage.cosine_similarity(query, vector)
            
            if similarity >= threshold:
                results.append((data[b"id"].decode(), similarity))

        results.sort(key=lambda x: x[1], reverse=True)

        if not results:
            return []
        
        results = results[:k]

        max_sim = results[0][1]
        min_allowed = max(threshold, max_sim - 0.03)

        filtered = [r for r in results if r[1] >= min_allowed]

        return filtered


