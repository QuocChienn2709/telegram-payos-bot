from pymongo import MongoClient
from datetime import datetime

client = MongoClient(MONGO_URI)
db = client['payos_bot']

users = db.users
products = db.products  # {category, name, price, duration, stock}
orders = db.orders
wallets = db.wallets  # {user_id, balance}
accounts = db.accounts  # {product_id, account_data}  # or separate collection per type