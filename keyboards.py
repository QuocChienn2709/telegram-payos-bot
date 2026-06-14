from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

def main_menu():
    kb = [
        [InlineKeyboardButton(text="🛒 Mua Tài Khoản", callback_data="shop")],
        [InlineKeyboardButton(text="💰 Ví của tôi", callback_data="wallet")],
        [InlineKeyboardButton(text="📜 Lịch sử mua", callback_data="history")],
    ]
    return InlineKeyboardMarkup(inline_keyboard=kb)

def categories_kb(categories):
    kb = [[InlineKeyboardButton(text=cat.capitalize(), callback_data=f"cat_{cat}")] for cat in categories]
    kb.append([InlineKeyboardButton(text="🔙 Quay lại", callback_data="main")])
    return InlineKeyboardMarkup(inline_keyboard=kb)

def products_kb(products_list):
    kb = []
    for p in products_list:
        stock = p.get('stock', 0)
        kb.append([InlineKeyboardButton(
            text=f"{p['name']} - {p['price']:,}đ ({stock} còn)",
            callback_data=f"prod_{str(p['_id'])}"
        )])
    kb.append([InlineKeyboardButton(text="🔙 Quay lại", callback_data="shop")])
    return InlineKeyboardMarkup(inline_keyboard=kb)

def payment_method_kb(product_id):
    kb = [
        [InlineKeyboardButton(text="💳 Thanh toán QR PayOS", callback_data=f"pay_qr_{product_id}")],
        [InlineKeyboardButton(text="💰 Thanh toán bằng Ví", callback_data=f"pay_wallet_{product_id}")],
        [InlineKeyboardButton(text="🔙 Quay lại", callback_data="shop")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=kb)

def admin_menu():
    kb = [
        [InlineKeyboardButton(text="📤 Upload Tài Khoản TXT", callback_data="admin_upload")],
        [InlineKeyboardButton(text="🛠 Quản lý Sản phẩm", callback_data="admin_products")],
    ]
    return InlineKeyboardMarkup(inline_keyboard=kb)
