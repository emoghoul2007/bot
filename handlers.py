from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from aiocryptopay import AioCryptoPay, Networks

from config import ADMIN_ID, CRYPTO_PAY_TOKEN, PRODUCT_PRICES_CRYPTO
from database import Database
from keyboards import *
from texts import TEXTS

router = Router()
db = Database()


class OrderStates(StatesGroup):
    waiting_for_photos = State()
    choosing_payment = State()
    waiting_for_crypto_payment = State()


@router.message(F.text == "/start")
async def start(message: Message, state: FSMContext):
    await state.clear()

    user_id = message.from_user.id
    lang = db.get_user_language(user_id)

    await message.answer(
        TEXTS["start_message"][lang],
        reply_markup=get_main_menu_keyboard(lang)
    )


@router.callback_query(F.data == "select_pack")
async def select_pack(callback: CallbackQuery):

    user_id = callback.from_user.id
    lang = db.get_user_language(user_id)

    await callback.message.edit_text(
        TEXTS["product_selection"][lang],
        reply_markup=get_product_selection_keyboard(lang)
    )

    await callback.answer()


@router.callback_query(F.data.startswith("product_"))
async def product_detail(callback: CallbackQuery):

    product_type = callback.data.split("_")[1]

    user_id = callback.from_user.id
    lang = db.get_user_language(user_id)

    text = TEXTS[f"{product_type}_pack"][lang]

    await callback.message.edit_text(
        text,
        reply_markup=get_product_detail_keyboard(lang, product_type)
    )

    await callback.answer()


@router.callback_query(F.data.startswith("upload_photo_"))
async def upload_photo(callback: CallbackQuery, state: FSMContext):

    product_type = callback.data.split("_")[2]

    await state.update_data(product_type=product_type, photos=[])
    await state.set_state(OrderStates.waiting_for_photos)

    user_id = callback.from_user.id
    lang = db.get_user_language(user_id)

    await callback.message.edit_text(
        TEXTS["upload_photos"][lang],
        reply_markup=get_upload_photos_keyboard(lang)
    )

    await callback.answer()


@router.message(OrderStates.waiting_for_photos, F.photo)
async def receive_photo(message: Message, state: FSMContext):

    data = await state.get_data()
    photos = data.get("photos", [])

    file_id = message.photo[-1].file_id

    photos.append(file_id)

    await state.update_data(photos=photos)

    await message.answer(f"Photo received ({len(photos)}/3)")

    if len(photos) >= 3:

        user_id = message.from_user.id
        lang = db.get_user_language(user_id)

        product_type = data["product_type"]

        await state.set_state(OrderStates.choosing_payment)

        await message.answer(
            "Photos uploaded. Choose payment:",
            reply_markup=get_payment_methods_keyboard(lang, product_type)
        )


@router.callback_query(F.data.startswith("crypto_pay_"))
async def crypto_payment(callback: CallbackQuery, state: FSMContext):

    product_type = callback.data.split("_")[2]

    user_id = callback.from_user.id
    lang = db.get_user_language(user_id)

    data = await state.get_data()
    photos = data.get("photos", [])

    price = PRODUCT_PRICES_CRYPTO[product_type]

    crypto = AioCryptoPay(
        token=CRYPTO_PAY_TOKEN,
        network=Networks.MAIN_NET
    )

    invoice = await crypto.create_invoice(
        asset="USDT",
        amount=price,
        description=f"{product_type} pack",
        payload=f"{user_id}_{product_type}"
    )

    order_id = db.add_order(
        user_id,
        product_type,
        0,
        crypto_invoice_id=invoice.invoice_id
    )

    await state.update_data(invoice_id=invoice.invoice_id)

    await callback.message.edit_text(
        f"Pay {price}$ via CryptoBot\n\n{invoice.pay_url}",
        reply_markup=get_check_payment_keyboard(str(invoice.invoice_id), lang)
    )

    await callback.bot.send_message(
        ADMIN_ID,
        f"🆕 New order #{order_id}\nUser: {user_id}\nPack: {product_type}"
    )

    for photo in photos:

        await callback.bot.send_photo(
            ADMIN_ID,
            photo=photo,
            caption=f"Order #{order_id}\nUser {user_id}"
        )

    await state.set_state(OrderStates.waiting_for_crypto_payment)

    await callback.answer()


@router.callback_query(F.data.startswith("check_payment_"))
async def check_payment(callback: CallbackQuery):

    invoice_id = callback.data.split("_")[2]

    crypto = AioCryptoPay(
        token=CRYPTO_PAY_TOKEN,
        network=Networks.MAIN_NET
    )

    invoices = await crypto.get_invoices(invoice_ids=[invoice_id])

    if invoices[0].status == "paid":

        await callback.message.edit_text("✅ Payment received!")

        await callback.bot.send_message(
            ADMIN_ID,
            f"💰 Payment confirmed for invoice {invoice_id}"
        )

    else:

        await callback.answer("Payment not found yet", show_alert=True)
