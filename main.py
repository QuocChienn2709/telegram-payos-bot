import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from aiohttp import web
from config import BOT_TOKEN, WEBHOOK_URL
from database import db
from handlers.user import router as user_router
from handlers.payment import router as payment_router
from handlers.admin import router as admin_router

bot = Bot(token=BOT_TOKEN, parse_mode="HTML")
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
        
        if webhook_data.get('success') and webhook_data['data'].get('status') == "PAID":
            order_code = webhook_data['data']['orderCode']
            order = await db.orders.find_one_and_update(
                {"order_code": order_code, "status": "pending"},
                {"$set": {"status": "paid"}}
            )
            if order:
                # TODO: Gửi tài khoản (sẽ bổ sung sau)
                await bot.send_message(order['user_id'], "✅ Thanh toán thành công!\nTài khoản đang được gửi...")
    except Exception as e:
        logging.error(f"Webhook error: {e}")
    return web.Response(text="OK")

async def main():
    logging.basicConfig(level=logging.INFO)
    
    app = web.Application()
    app.router.add_post("/webhook", payos_webhook)
    
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, '0.0.0.0', 8080)
    await site.start()
    
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
