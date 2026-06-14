from aiogram import Router, F
from aiogram.types import CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
import time
from bson import ObjectId
from config import PAYOS_CLIENT_ID, PAYOS_API_KEY, PAYOS_CHECKSUM_KEY
from database import products, orders, db
from payos import PayOS

router = Router()

class PaymentState(StatesGroup):
    waiting = State()

payos_client = PayOS(client_id=PAYOS_CLIENT_ID, api_key=PAYOS_API_KEY, checksum_key=PAYOS_CHECKSUM_KEY)

@router.callback_query(F.data.startswith("pay_qr_"))
async def pay_qr(callback: CallbackQuery, state: FSMContext):
    try:
        prod_id = callback.data.split("_")[2]
        prod = await products.find_one({"_id": ObjectId(prod_id)})
        
        if not prod or prod.get('stock', 0) <= 0:
            await callback.answer("❌ Hết hàng!", show_alert=True)
            return

        order_code = int(time.time() * 1000) % 1000000000
        
        payment_data = {
            "orderCode": order_code,
            "amount": prod['price'],
            "description": f"Mua {prod['name']}",
            "cancelUrl": "https://t.me/yourbot",
            "returnUrl": "https://t.me/yourbot",
        }
        
        payment = payos_client.payment_requests.create(payment_data)
        
        await orders.insert_one({
            "order_code": order_code,
            "user_id": callback.from_user.id,
            "product_id": ObjectId(prod_id),
            "product_name": prod['name'],
            "amount": prod['price'],
            "status": "pending",
            "created_at": time.time()
        })
        
        await callback.message.edit_text(
            f"✅ Đơn hàng tạo thành công!\n\n"
            f"💰 Số tiền: <b>{prod['price']:,}đ</b>\n"
            f"🛒 Sản phẩm: {prod['name']}\n\n"
            f"🔗 Thanh toán tại đây:\n{payment['checkoutUrl']}",
            parse_mode="HTML",
            disable_web_page_preview=True
        )
        await state.set_state(PaymentState.waiting)
        await callback.answer()
    except Exception as e:
        await callback.answer(f"Lỗi: {str(e)}", show_alert=True)
