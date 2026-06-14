from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from config import ADMIN_IDS
from database import products, accounts
from keyboards import admin_menu
import aiofiles
from bson import ObjectId

router = Router()

@router.message(Command("admin"))
async def admin_panel(msg: Message):
    if msg.from_user.id not in ADMIN_IDS:
        return await msg.answer("🚫 Bạn không có quyền admin!")
    await msg.answer("🛠 Admin Panel", reply_markup=admin_menu())

@router.message(F.document, lambda m: m.from_user.id in ADMIN_IDS)
async def upload_accounts(msg: Message):
    if not msg.caption or not msg.caption.startswith("prod:"):
        return await msg.answer("❌ Dùng format: prod:category_product_duration")
    
    try:
        _, key = msg.caption.split(":")
        file = await msg.document.get_file()
        content = await file.download_to_memory()
        lines = content.decode().strip().split("\n")
        
        await accounts.update_one({"product_key": key}, {"$push": {"accounts": {"$each": lines}}}, upsert=True)
        
        # Cập nhật stock
        count = len(lines)
        await products.update_one({"product_key": key}, {"$inc": {"stock": count}})
        
        await msg.answer(f"✅ Đã upload {count} tài khoản cho {key}")
    except Exception as e:
        await msg.answer(f"Lỗi: {e}")