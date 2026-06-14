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

# Khởi tạo Bot
bot = Bot(
    token=BOT_TOKEN,
    default=DefaultBotProperties(parse_mode="HTML")
)

dp = Dispatcher(storage=MemoryStorage())

dp.include_router(user_router)
dp.include_router(payment_router)
dp.include_router(admin_router)


async def payos_webhook(request):
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
                    "✅ <b>Thanh toán thành công!</b>\nĐang xử lý và gửi tài khoản..."
                )
                # TODO: Thêm logic gửi tài khoản tự động sau
    except Exception as e:
        logging.error(f"Webhook error: {e}")
    
    return web.Response(text="OK")


async def main():
    logging.basicConfig(level=logging.INFO)
    
    # ================== WEBHOOK SERVER ==================
    app = web.Application()
    app.router.add_post("/webhook", payos_webhook)
    
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, '0.0.0.0', 8080)
    await site.start()
    
    logging.info(f"Webhook server started on port 8080")
    logging.info(f"Webhook URL: {WEBHOOK_URL}")
    
    # Không dùng polling khi deploy trên Render (tránh conflict)
    # await dp.start_polling(bot)   ← Đã comment
    
    # Giữ process chạy
    await asyncio.Event().wait()  # Giữ bot chạy vô hạn


if __name__ == "__main__":
    asyncio.run(main())
