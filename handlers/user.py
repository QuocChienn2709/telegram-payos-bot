from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from keyboards import main_menu, categories_kb, products_kb, payment_method_kb
from database import products, users
from bson import ObjectId

router = Router()

@router.message(Command("start"))
async def start(msg: Message):
    await users.update_one({"user_id": msg.from_user.id},
                           {"$setOnInsert": {"username": msg.from_user.username}}, upsert=True)
    await msg.answer("👋 <b>Chào mừng đến Cửa hàng Tài Khoản Pro!</b>", reply_markup=main_menu())

@router.callback_query(F.data == "shop")
async def shop(callback: CallbackQuery):
    cats = await products.distinct("category")
    await callback.message.edit_text("📂 <b>Chọn loại sản phẩm:</b>", reply_markup=categories_kb(cats))

@router.callback_query(F.data.startswith("cat_"))
async def show_products(callback: CallbackQuery):
    cat = callback.data.split("_")[1]
    prods = await products.find({"category": cat}).to_list(30)
    await callback.message.edit_text(f"📦 <b>{cat.capitalize()}</b>", reply_markup=products_kb(prods))

@router.callback_query(F.data.startswith("prod_"))
async def product_detail(callback: CallbackQuery):
    prod_id = callback.data.split("_")[1]
    prod = await products.find_one({"_id": ObjectId(prod_id)})
    if not prod:
        return await callback.answer("Sản phẩm không tồn tại!")
    
    text = f"""
🛒 <b>{prod['name']}</b>
💰 Giá: <b>{prod['price']:,}đ</b>
⏳ Thời hạn: <b>{prod['duration']}</b>
📦 Tồn kho: <b>{prod.get('stock', 0)}</b>
"""
    await callback.message.edit_text(text, reply_markup=payment_method_kb(str(prod['_id'])))
