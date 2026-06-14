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

bot = Bot(
    token=BOT_TOKEN,
    default=DefaultBotProperties(parse_mode="HTML")
)

dp = Dispatcher(storage=MemoryStorage())

dp.include_router(user_router)
dp.include_router(payment_router)
dp.include_router(admin_router)


async def payos_webhook(request):
    if request.method == "GET":
        return web.Response(text="✅ Webhook PayOS is active!")

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
                await process_successful_order(order)
    except Exception as e:
        logging.error(f"Webhook error: {e}")
    return web.Response(text="OK")


async def process_successful_order(order):
    """Gửi tài khoản tự động sau thanh toán"""
    try:
        prod_key = order.get("product_key")
        acc_doc = await db.accounts.find_one({"product_key": prod_key})
        
        if acc_doc and acc_doc.get("accounts"):
            account = acc_doc["accounts"].pop(0)
            await db.accounts.update_one({"product_key": prod_key}, {"$set": {"accounts": acc_doc["accounts"]}})
            await db.products.update_one({"product_key": prod_key}, {"$inc": {"stock": -1}})

            await bot.send_message(
                order['user_id'],
                f"✅ <b>Thanh toán thành công!</b>\n\n"
                f"🛒 Sản phẩm: {order['product_name']}\n"
                f"🔑 Tài khoản:\n<code>{account}</code>\n\n"
                f"Cảm ơn bạn đã mua hàng!",
                parse_mode="HTML"
            )
        else:
            await bot.send_message(order['user_id'], "✅ Thanh toán thành công!\nNhưng hiện tại hết hàng. Admin sẽ liên hệ sớm.")
    except Exception as e:
        logging.error(f"Error sending account: {e}")


async def main():
    logging.basicConfig(level=logging.INFO)
    app = web.Application()
    app.router.add_get("/webhook", payos_webhook)
    app.router.add_post("/webhook", payos_webhook)

    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, '0.0.0.0', 8080)
    await site.start()

    logging.info("🚀 Bot + Webhook started!")
    await asyncio.Event().wait()


if __name__ == "__main__":
    asyncio.run(main())
