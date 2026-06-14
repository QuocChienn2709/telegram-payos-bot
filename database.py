from motor.motor_asyncio import AsyncIOMotorClient
from config import MONGO_URI

client = AsyncIOMotorClient(MONGO_URI)
db = client['telegram_payos_bot']

users = db.users
wallets = db.wallets
products = db.products
accounts = db.accounts  # {product_key: [list of accounts]}
orders = db.orders