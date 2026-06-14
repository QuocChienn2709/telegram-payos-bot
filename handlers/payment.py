from aiogram import Router, F
from aiogram.types import CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
import time
from bson import ObjectId
from database import products, orders, wallets
from config import PAYOS_CLIENT_ID, PAYOS_API_KEY, PAYOS_CHECKSUM_KEY
from payos import PayOS

router = Router()

class PaymentState(StatesGroup):
    waiting = State()

@router.callback_query(F.data.startswith("pay_qr_"))
async def pay_qr(callback: CallbackQuery):
    prod_id = callback.data.split("_")[2]
    prod = await products.find_one({"_id": ObjectId(prod_id)})
    if not prod or prod.get('stock', 0) <= 0:
        return await callback.answer("❌ Hết hàng!", show_alert=True)

    order_code = int(time.time())
    payos = PayOS(PAYOS_CLIENT_ID, PAYOS_API_KEY, PAYOS_CHECKSUM_KEY)

    payment = payos.payment_requests.create({
        "orderCode": order_code,
        "amount": prod['price'],
        "description": f"Mua {prod['name']}",
        "cancelUrl": "https://t.me/yourbot",
        "returnUrl": "https://t.me/yourbot",
    })

    await orders.insert_one({
        "order_code": order_code,
        "user_id": callback.from_user.id,
        "product_id": ObjectId(prod_id),
        "product_key": prod['product_key'],
        "product_name": prod['name'],
        "amount": prod['price'],
        "status": "pending"
    })

    await callback.message.edit_text(f"🔗 Thanh toán QR:\n{payment['checkoutUrl']}")

@router.callback_query(F.data.startswith("pay_wallet_"))
async def pay_wallet(callback: CallbackQuery):
    prod_id = callback.data.split("_")[2]
    prod = await products.find_one({"_id": ObjectId(prod_id)})
    wallet = await wallets.find_one({"user_id": callback.from_user.id})

    if not wallet or wallet.get('balance', 0) < prod['price']:
        return await callback.answer("💰 Số dư ví không đủ!", show_alert=True)

    # Trừ tiền ví
    await wallets.update_one({"user_id": callback.from_user.id}, {"$inc": {"balance": -prod['price']}})
    
    # Tạo order paid
    await orders.insert_one({
        "user_id": callback.from_user.id,
        "product_id": ObjectId(prod_id),
        "product_key": prod['product_key'],
        "product_name": prod['name'],
        "amount": prod['price'],
        "status": "paid",
        "payment_method": "wallet"
    })

    await callback.answer("✅ Thanh toán bằng ví thành công!", show_alert=True)
    # Gọi hàm gửi tài khoản
    await process_successful_order({"user_id": callback.from_user.id, "product_key": prod['product_key'], "product_name": prod['name']})
