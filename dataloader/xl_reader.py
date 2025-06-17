import pandas as pd
import uuid
from storage.models import Product

def load_products_from_excel(file_path: str = 'input.xlsx'):
    df = pd.read_excel(file_path, header=None, names=['name', 'description', 'price'])
    products = []
    prev_name = ''
    for _, row in df.iterrows():
        if pd.notna(row['name']):
            prev_name = row['name']
        if pd.isna(row['price']) or pd.isna(row['description']):
            continue
        print('name:', row['name'], ' price:', row['price'], flush=True)
        price_str = str(row['price']).replace('от ', '').replace(' ₽', '')
        product = Product(
            id=uuid.uuid4(),
            name=str(prev_name),
            description=str(row['description']),
            price=int(price_str)
        )
        products.append(product)
    return products
