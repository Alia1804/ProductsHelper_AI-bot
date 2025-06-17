from sqlalchemy.orm import Session
from postgres import SessionLocal
import os
import httpx
import asyncio
from xl_reader import load_products_from_excel

PROCESSOR_URL = os.getenv("PROCESSOR_URL")

async def wait_for_processor(url: str, timeout: int = 60, interval: int = 3):
    async with httpx.AsyncClient() as client:
        total_wait = 0
        while total_wait < timeout:
            try:
                await client.get(url)
                return
            except (httpx.RequestError, httpx.ConnectError):
                pass
            print(f"Ожидание доступности Processor на {url}... {total_wait}s")
            await asyncio.sleep(interval)
            total_wait += interval
    raise TimeoutError(f"Processor не стал доступен за {timeout} секунд")

async def load_test_products(session: Session):
    test_products = load_products_from_excel()

    async with httpx.AsyncClient() as client:
        for product in test_products:
            session.add(product)
            await client.post(
                f"{PROCESSOR_URL}/add_vector",
                json={"text": product.name + ': ' + product.description, "user_id": str(product.id)}
            )
    session.commit()
    print(f"Добавлено {len(test_products)} тестовых товаров.")

async def main():
    session = SessionLocal()
    try:
        await load_test_products(session)
    finally:
        session.close()

if __name__ == "__main__":
    async def runner():
        await wait_for_processor(PROCESSOR_URL)
        await main()
    asyncio.run(runner())
