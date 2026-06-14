from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from config import ADMIN_IDS
from database import products, accounts
from keyboards import admin_menu
import aiofiles

router = Router()

@router.message(Command("admin"))
async def admin_panel(msg: Message):
    if msg.from_user.id not in ADMIN_IDS:
        return await msg.answer("🚫 Không có quyền admin!")
    await msg.answer("🛠 <b>Admin Panel</b>", reply_markup=admin_menu())

@router.message(F.document, lambda m: m.from_user.id in ADMIN_IDS)
async def upload_accounts(msg: Message):
    if not msg.caption or ":" not in msg.caption:
        return await msg.answer("❌ Format: <code>prod:capcut_7ngay</code>")

    key = msg.caption.split(":", 1)[1].strip()
    file = await msg.document.get_file()
    content = await file.download_to_memory()
    lines = [line.strip() for line in content.decode().split("\n") if line.strip()]

    await accounts.update_one({"product_key": key}, {"$push": {"accounts": {"$each": lines}}}, upsert=True)
    await products.update_one({"product_key": key}, {"$inc": {"stock": len(lines)}}, upsert=True)

    await msg.answer(f"✅ Đã upload **{len(lines)}** tài khoản cho `{key}`")
