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
from payos import PayOS
from config import PAYOS_CLIENT_ID, PAYOS_API_KEY, PAYOS_CHECKSUM_KEY

bot = Bot(token=BOT_TOKEN, parse_mode="HTML")
storage = MemoryStorage()
dp = Dispatcher(storage=storage)

dp.include_router(user_router)
dp.include_router(payment_router)
dp.include_router(admin_router)

payos_client = PayOS(PAYOS_CLIENT_ID, PAYOS_API_KEY, PAYOS_CHECKSUM_KEY)

async def payos_webhook(request):
    try:
        data = await request.json()
        webhook_data = payos_client.webhooks.verify(data)
        
        if webhook_data['success'] and webhook_data['data']['status'] == "PAID":
            order_code = webhook_data['data']['orderCode']
            order = await db.orders.find_one_and_update(
                {"order_code": order_code, "status": "pending"},
                {"$set": {"status": "paid"}}
            )
            
            if order:
                prod = await db.products.find_one({"_id": order['product_id']})
                # Lấy 1 account
                acc_doc = await db.accounts.find_one({"product_key": prod['product_key']})
                if acc_doc and acc_doc['accounts']:
                    account = acc_doc['accounts'].pop(0)
                    await db.accounts.update_one({"product_key": prod['product_key']}, {"$set": {"accounts": acc_doc['accounts']}})
                    await db.products.update_one({"_id": order['product_id']}, {"$inc": {"stock": -1}})
                    
                    user_id = order['user_id']
                    await bot.send_message(user_id, f"✅ Thanh toán thành công!\n\nTài khoản của bạn:\n<code>{account}</code>")
    except Exception as e:
        logging.error(e)
    return web.Response(text="OK")

async def main():
    logging.basicConfig(level=logging.INFO)
    
    # Webhook server
    app = web.Application()
    app.router.add_post("/webhook", payos_webhook)
    
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, '0.0.0.0', 8080)
    await site.start()
    
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())