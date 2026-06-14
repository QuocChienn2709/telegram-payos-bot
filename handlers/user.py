from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from keyboards import main_menu, categories_kb, products_kb, payment_method_kb
from database import products, users
from bson import ObjectId

router = Router()

@router.message(Command("start"))
async def start(msg: Message):
    await users.update_one(
        {"user_id": msg.from_user.id},
        {"$setOnInsert": {"username": msg.from_user.username, "created_at": msg.date}},
        upsert=True
    )
    await msg.answer(
        "👋 <b>Chào mừng đến với cửa hàng Tài Khoản Pro!</b>\n\n"
        "Chọn chức năng bên dưới:",
        reply_markup=main_menu(),
        parse_mode="HTML"
    )

@router.callback_query(F.data == "shop")
async def shop(callback: CallbackQuery):
    categories = await products.distinct("category")
    if not categories:
        await callback.answer("Chưa có sản phẩm nào. Liên hệ admin!", show_alert=True)
        return
    await callback.message.edit_text("📂 <b>Chọn loại sản phẩm:</b>", reply_markup=categories_kb(categories), parse_mode="HTML")

@router.callback_query(F.data.startswith("cat_"))
async def show_products(callback: CallbackQuery):
    category = callback.data.split("_")[1]
    prods = await products.find({"category": category}).to_list(50)
    
    if not prods:
        await callback.answer("Không có sản phẩm trong danh mục này!")
        return
    
    await callback.message.edit_text(
        f"📦 <b>Sản phẩm {category.capitalize()}:</b>",
        reply_markup=products_kb(prods),
        parse_mode="HTML"
    )

@router.callback_query(F.data.startswith("prod_"))
async def product_detail(callback: CallbackQuery):
    try:
        prod_id = callback.data.split("_")[1]
        prod = await products.find_one({"_id": ObjectId(prod_id)})
        
        if not prod:
            await callback.answer("Sản phẩm không tồn tại!")
            return
            
        text = f"""
🛒 <b>{prod['name']}</b>

💰 Giá: <b>{prod['price']:,} đ</b>
⏳ Thời hạn: <b>{prod['duration']}</b>
📦 Tồn kho: <b>{prod.get('stock', 0)}</b> tài khoản
"""
        await callback.message.edit_text(text, reply_markup=payment_method_kb(prod_id), parse_mode="HTML")
    except:
        await callback.answer("Lỗi xử lý sản phẩm!")

@router.callback_query(F.data == "main")
async def back_to_main(callback: CallbackQuery):
    await callback.message.edit_text("Chọn chức năng:", reply_markup=main_menu())
