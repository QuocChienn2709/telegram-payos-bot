import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.client.default import DefaultBotProperties
from aiohttp import web

from config import BOT_TOKEN, WEBHOOK_URL
from database import db
from handlers.user import router as user_router
from handlers.payment import router as payment_router
from handlers.admin import router as admin_router

# ================== KHỞI TẠO BOT ==================
bot = Bot(
    token=BOT_TOKEN,
    default=DefaultBotProperties(parse_mode="HTML")
)

dp = Dispatcher(storage=MemoryStorage())

dp.include_router(user_router)
dp.include_router(payment_router)
dp.include_router(admin_router)


# ================== PAYOS WEBHOOK ==================
async def payos_webhook(request):
    # Hỗ trợ GET để test
    if request.method == "GET":
        return web.Response(text="✅ Webhook PayOS is active and running!")

    from payos import PayOS
    from config import PAYOS_CLIENT_ID, PAYOS_API_KEY, PAYOS_CHECKSUM_KEY
    
    try:
        data = await request.json()
        payos = PayOS(PAYOS_CLIENT_ID, PAYOS_API_KEY, PAYOS_CHECKSUM_KEY)
        webhook_data = payos.webhooks.verify(data)
        
        if webhook_data.get('success') and webhook_data.get('data', {}).get('status') == "PAID":
            order_code = webhook_data['data']['orderCode']
            
            order = await db.orders.find_one_and_update(
                {"order_code": order_code, "status": "pending"},
                {"$set": {"status": "paid"}}
            )
            
            if order:
                await bot.send_message(
                    order['user_id'],
                    "✅ <b>Thanh toán thành công!</b>\nĐang xử lý và gửi tài khoản cho bạn..."
                )
                # Logic gửi tài khoản sẽ được bổ sung sau
                logging.info(f"Payment success for order {order_code}")
                
    except Exception as e:
        logging.error(f"Webhook error: {e}")
    
    return web.Response(text="OK")


# ================== MAIN FUNCTION ==================
async def main():
    logging.basicConfig(level=logging.INFO)
    
    # Start Webhook Server
    app = web.Application()
    app.router.add_get("/webhook", payos_webhook)   # Test GET
    app.router.add_post("/webhook", payos_webhook)  # PayOS POST
    
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, '0.0.0.0', 8080)
    await site.start()
    
    logging.info("🚀 Bot started successfully!")
    logging.info(f"Webhook URL: {WEBHOOK_URL}")
    
    # Giữ process chạy (không dùng polling khi deploy trên Render)
    await asyncio.Event().wait()


if __name__ == "__main__":
    asyncio.run(main())
