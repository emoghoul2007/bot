from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

def get_language_keyboard():
    keyboard = InlineKeyboardBuilder()
    keyboard.add(
        InlineKeyboardButton(text="English", callback_data="lang_en"),
        InlineKeyboardButton(text="Русский", callback_data="lang_ru")
    )
    return keyboard.as_markup()

def get_main_menu_keyboard(lang_code='en'):
    keyboard = InlineKeyboardBuilder()
    
    if lang_code == 'en':
        keyboard.add(InlineKeyboardButton(text="Select Pack 🔥", callback_data="select_pack"))
    else:
        keyboard.add(InlineKeyboardButton(text="Выбрать пак 🔥", callback_data="select_pack"))
    
    return keyboard.as_markup()

def get_product_selection_keyboard(lang_code='en'):
    keyboard = InlineKeyboardBuilder()
    
    if lang_code == 'en':
        keyboard.row(
            InlineKeyboardButton(text="Date — $5 😮‍💨💦", callback_data="product_date"),
            InlineKeyboardButton(text="Undress — $5 🔥👙", callback_data="product_undress")
        )
        keyboard.row(
            InlineKeyboardButton(text="Sex — $5 🍆💦", callback_data="product_sex"),
            InlineKeyboardButton(text="3-in-1 Everything — $12.99 🔥💦", callback_data="product_combo")
        )
    else:
        keyboard.row(
            InlineKeyboardButton(text="Дата — 5$ 😮‍💨💦", callback_data="product_date"),
            InlineKeyboardButton(text="Раздеть — 5$ 🔥👙", callback_data="product_undress")
        )
        keyboard.row(
            InlineKeyboardButton(text="Секс — 5$ 🍆💦", callback_data="product_sex"),
            InlineKeyboardButton(text="3в1 ВСЁ + БОНУС — 12.99$ 🔥💦", callback_data="product_combo")
        )
    
    return keyboard.as_markup()

def get_product_detail_keyboard(lang_code='en', product_type='date'):
    keyboard = InlineKeyboardBuilder()
    
    if lang_code == 'en':
        keyboard.row(
            InlineKeyboardButton(text="Upload a photo", callback_data=f"upload_photo_{product_type}"),
            InlineKeyboardButton(text="Back", callback_data="select_pack")
        )
    else:
        keyboard.row(
            InlineKeyboardButton(text="Загрузить фото", callback_data=f"upload_photo_{product_type}"),
            InlineKeyboardButton(text="Назад", callback_data="select_pack")
        )
    
    return keyboard.as_markup()

def get_upload_photos_keyboard(lang_code='en'):
    keyboard = InlineKeyboardBuilder()
    
    if lang_code == 'en':
        keyboard.row(
            InlineKeyboardButton(text="Pay for the pack 💸", callback_data="pay_pack"),
            InlineKeyboardButton(text="Choose another pack 👀", callback_data="select_pack")
        )
    else:
        keyboard.row(
            InlineKeyboardButton(text="Перейти к оплате 💸", callback_data="pay_pack"),
            InlineKeyboardButton(text="Выбрать другой пак 👀", callback_data="select_pack")
        )
    
    return keyboard.as_markup()

def get_payment_methods_keyboard(lang_code='en', product_type='date'):
    keyboard = InlineKeyboardBuilder()
    
    if lang_code == 'en':
        keyboard.row(
            InlineKeyboardButton(text="Crypto (USDT)", callback_data=f"crypto_pay_{product_type}"),
            InlineKeyboardButton(text="Telegram Stars", callback_data=f"stars_pay_{product_type}")
        )
    else:
        keyboard.row(
            InlineKeyboardButton(text="Криптовалюта (USDT)", callback_data=f"crypto_pay_{product_type}"),
            InlineKeyboardButton(text="Звёзды Telegram", callback_data=f"stars_pay_{product_type}")
        )
    
    return keyboard.as_markup()

def get_check_payment_keyboard(invoice_id: str, lang_code='en'):
    keyboard = InlineKeyboardBuilder()
    
    if lang_code == 'en':
        keyboard.add(InlineKeyboardButton(text="Check Payment ✅", callback_data=f"check_payment_{invoice_id}"))
    else:
        keyboard.add(InlineKeyboardButton(text="Проверить оплату ✅", callback_data=f"check_payment_{invoice_id}"))
    
    return keyboard.as_markup()

def get_back_to_products_keyboard(lang_code='en'):
    keyboard = InlineKeyboardBuilder()
    
    if lang_code == 'en':
        keyboard.add(InlineKeyboardButton(text="Back to products", callback_data="select_pack"))
    else:
        keyboard.add(InlineKeyboardButton(text="Вернуться к продуктам", callback_data="select_pack"))
    
    return keyboard.as_markup()