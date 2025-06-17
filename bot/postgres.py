from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy import select, create_engine
import os
from storage.models import Product

DATABASE_URL = f"postgresql+psycopg2://{os.environ.get('POSTGRES_USER')}:{os.environ.get('POSTGRES_PASSWORD')}@{os.environ.get('POSTGRES_HOST')}:{os.environ.get('POSTGRES_PORT')}/{os.environ.get('POSTGRES_DB')}"

engine = create_engine(DATABASE_URL, echo=True)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_products_info(session: Session, ids: list[str]):
    stmt = select(Product.id, Product.name, Product.description, Product.price).where(Product.id.in_(ids))
    result = session.execute(stmt)
    products = result.all()  # список кортежей (id, name, price)
    return products
