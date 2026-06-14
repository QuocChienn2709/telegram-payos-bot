from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from keyboards import main_menu, categories_kb, products_kb, payment_method_kb
from database import products, accounts, wallets, users
from bson import ObjectId

router = Router()

@router.message(Command("start"))
async def start(msg: Message):
    await users.update_one({"user_id": msg.from_user.id}, {"$setOnInsert": {"username": msg.from_user.username}}, upsert=True)
    await msg.answer("👋 Chào mừng đến với cửa hàng tài khoản Pro!\nChọn menu bên dưới:", reply_markup=main_menu())

@router.callback_query(F.data == "shop")
async def shop(callback: CallbackQuery):
    cats = await products.distinct("category")
    await callback.message.edit_text("📂 Chọn loại sản phẩm:", reply_markup=categories_kb(cats))

@router.callback_query(F.data.startswith("cat_"))
async def show_products(callback: CallbackQuery):
    category = callback.data.split("_")[1]
    prods = await products.find({"category": category}).to_list(50)
    if not prods:
        await callback.answer("Không có sản phẩm nào!")
        return
    await callback.message.edit_text(f"📦 Sản phẩm {category.capitalize()}:", reply_markup=products_kb(prods))

@router.callback_query(F.data.startswith("prod_"))
async def product_detail(callback: CallbackQuery):
    prod_id = callback.data.split("_")[1]
    prod = await products.find_one({"_id": ObjectId(prod_id)})
    if not prod:
        await callback.answer("Sản phẩm không tồn tại!")
        return
    text = f"🛒 <b>{prod['name']}</b>\nGiá: <b>{prod['price']:,}đ</b>\nThời hạn: {prod['duration']}\nTồn kho: <b>{prod['stock']}</b>"
    await callback.message.edit_text(text, parse_mode="HTML", reply_markup=payment_method_kb(prod_id))