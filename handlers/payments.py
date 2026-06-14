from aiogram import Router, F
from aiogram.types import CallbackQuery, Message
from payos import PayOS
from payos.types import CreatePaymentLinkRequest
import time
from config import PAYOS_CLIENT_ID, PAYOS_API_KEY, PAYOS_CHECKSUM_KEY, WEBHOOK_URL
from database import products, accounts, orders, wallets
from bson import ObjectId
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

payos_client = PayOS(client_id=PAYOS_CLIENT_ID, api_key=PAYOS_API_KEY, checksum_key=PAYOS_CHECKSUM_KEY)

router = Router()

class PaymentState(StatesGroup):
    waiting = State()

@router.callback_query(F.data.startswith("pay_qr_"))
async def pay_qr(callback: CallbackQuery, state: FSMContext):
    prod_id = callback.data.split("_")[2]
    prod = await products.find_one({"_id": ObjectId(prod_id)})
    
    order_code = int(time.time())
    payment_data = CreatePaymentLinkRequest(
        orderCode=order_code,
        amount=prod['price'],
        description=f"Mua {prod['name']}",
        cancelUrl="https://t.me/yourbot",
        returnUrl="https://t.me/yourbot",
        items=[{"name": prod['name'], "quantity": 1, "price": prod['price']}]
    )
    
    payment = payos_client.payment_requests.create(payment_data)
    
    await orders.insert_one({
        "order_code": order_code,
        "user_id": callback.from_user.id,
        "product_id": prod_id,
        "status": "pending",
        "amount": prod['price']
    })
    
    await callback.message.edit_text(
        f"🔗 Thanh toán qua PayOS:\n\n{payment['checkoutUrl']}\n\nHoặc quét QR trong link trên.",
        disable_web_page_preview=True
    )
    await state.set_state(PaymentState.waiting)

# Webhook sẽ xử lý sau
