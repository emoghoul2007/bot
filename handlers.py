import asyncio
from typing import Any
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, LabeledPrice, PreCheckoutQuery
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from aiocryptopay import AioCryptoPay, Networks
from config import BOT_TOKEN, CRYPTO_PAY_TOKEN, ADMIN_ID, PRODUCT_PRICES_CRYPTO, PRODUCT_PRICES_STARS
from database import Database
from keyboards import (
    get_language_keyboard, get_main_menu_keyboard, 
    get_product_selection_keyboard, get_product_detail_keyboard,
    get_upload_photos_keyboard, get_payment_methods_keyboard,
    get_check_payment_keyboard, get_back_to_products_keyboard
)
from texts import TEXTS

router = Router()
db = Database()

class OrderStates(StatesGroup):
    waiting_for_photos = State()
    choosing_payment = State()
    waiting_for_crypto_payment = State()

@router.message(F.text == '/start')
async def cmd_start(message: Message, state: FSMContext):
    await state.clear()
    
    user_id = message.from_user.id
    lang = db.get_user_language(user_id)
    
    # Show language selection
    await message.answer(TEXTS['language_prompt'][lang], reply_markup=get_language_keyboard())

@router.callback_query(F.data.startswith('lang_'))
async def process_language_change(callback: CallbackQuery, state: FSMContext):
    lang = callback.data.split('_')[1]
    user_id = callback.from_user.id
    
    db.set_user_language(user_id, lang)
    
    await callback.message.edit_text(
        TEXTS['start_message'][lang],
        reply_markup=get_main_menu_keyboard(lang)
    )
    await callback.answer()

@router.callback_query(F.data == 'select_pack')
async def show_product_selection(callback: CallbackQuery):
    user_id = callback.from_user.id
    lang = db.get_user_language(user_id)
    
    await callback.message.edit_text(
        TEXTS['product_selection'][lang],
        reply_markup=get_product_selection_keyboard(lang)
    )
    await callback.answer()

@router.callback_query(F.data.startswith('product_'))
async def show_product_detail(callback: CallbackQuery):
    product_type = callback.data.split('_')[1]
    user_id = callback.from_user.id
    lang = db.get_user_language(user_id)
    
    text_key = f'{product_type}_pack'
    text = TEXTS[text_key][lang]
    
    await callback.message.edit_text(
        text,
        reply_markup=get_product_detail_keyboard(lang, product_type)
    )
    await callback.answer()

@router.callback_query(F.data.startswith('upload_photo_'))
async def start_upload_photos(callback: CallbackQuery, state: FSMContext):
    product_type = callback.data.split('_')[2]
    user_id = callback.from_user.id
    lang = db.get_user_language(user_id)
    
    await state.update_data(product_type=product_type)
    await state.set_state(OrderStates.waiting_for_photos)
    
    await callback.message.edit_text(
        TEXTS['upload_photos'][lang],
        reply_markup=get_upload_photos_keyboard(lang)
    )
    await callback.answer()

@router.message(OrderStates.waiting_for_photos, F.photo)
async def process_photo_upload(message: Message, state: FSMContext):
    data = await state.get_data()
    photos = data.get('photos', [])
    
    # Add the new photo to the list
    photos.append(message.photo[-1].file_id)
    await state.update_data(photos=photos)
    
    user_id = message.from_user.id
    lang = db.get_user_language(user_id)
    
    # Inform user that photo was received
    await message.answer(f"Photo {len(photos)} uploaded. Total: {len(photos)}/3")
    
    # If 3 photos uploaded, automatically show payment options
    if len(photos) >= 3:
        await state.set_state(OrderStates.choosing_payment)
        product_type = data['product_type']
        await message.answer(
            "Photos uploaded! Now choose payment method:",
            reply_markup=get_payment_methods_keyboard(lang, product_type)
        )

@router.callback_query(F.data == 'pay_pack', OrderStates.waiting_for_photos)
async def prompt_payment_method_from_photos(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    photos = data.get('photos', [])
    
    if not photos:
        await callback.answer("Please upload at least one photo first!", show_alert=True)
        return
    
    user_id = callback.from_user.id
    lang = db.get_user_language(user_id)
    product_type = data['product_type']
    
    await state.set_state(OrderStates.choosing_payment)
    await callback.message.edit_text(
        "Choose payment method:",
        reply_markup=get_payment_methods_keyboard(lang, product_type)
    )
    await callback.answer()

@router.callback_query(F.data.startswith('crypto_pay_'))
async def process_crypto_payment(callback: CallbackQuery, state: FSMContext):
    product_type = callback.data.split('_')[2]
    user_id = callback.from_user.id
    lang = db.get_user_language(user_id)
    
    # Get price for the selected product
    price = PRODUCT_PRICES_CRYPTO[product_type]
    
    # Initialize CryptoBot client
    crypto = AioCryptoPay(token=CRYPTO_PAY_TOKEN, network=Networks.MAIN_NET)
    
    try:
        # Create invoice
        invoice = await crypto.create_invoice(
            asset='USDT',
            amount=price,
            description=f'Payment for {product_type} pack',
            payload=f'crypto_{user_id}_{product_type}'
        )
        
        # Save order to DB
        order_id = db.add_order(user_id, product_type, 0, crypto_invoice_id=invoice.invoice_id)
        
        # Store invoice ID in state
        await state.update_data(invoice_id=invoice.invoice_id)
        
        # Send payment info to user
        await callback.message.edit_text(
            f"Pay {price}$ USDT via CryptoBot:\n\nInvoice ID: {invoice.invoice_id}\n\n{invoice.pay_url}",
            reply_markup=get_check_payment_keyboard(str(invoice.invoice_id), lang)
        )
        
        # Notify admin
        await callback.bot.send_message(
            ADMIN_ID,
            f"New crypto payment order #{order_id} from user {user_id} for {product_type} pack"
        )

        data = await state.get_data()
        photos = data.get('photos', [])

for photo in photos:
    await callback.bot.send_photo(
        ADMIN_ID,
        photo=photo,
        caption=f"Order #{order_id}\nUser: {user_id}"
    )
    
        await state.set_state(OrderStates.waiting_for_crypto_payment)
    except Exception as e:
        await callback.message.answer(f"Error creating invoice: {str(e)}")
    
    await callback.answer()

@router.callback_query(F.data.startswith('stars_pay_'))
async def process_stars_payment(callback: CallbackQuery, state: FSMContext):
    product_type = callback.data.split('_')[2]
    user_id = callback.from_user.id
    lang = db.get_user_language(user_id)
    
    # Get price for the selected product
    price = PRODUCT_PRICES_STARS[product_type]
    
    # Generate a unique payload for this transaction
    import uuid
    payload = f"stars_{uuid.uuid4()}_{user_id}_{product_type}"
    
    # Save order to DB
    order_id = db.add_order(user_id, product_type, 0, stars_invoice_payload=payload)
    
    # Send invoice to user
    await callback.bot.send_invoice(
        chat_id=user_id,
        title=f"{product_type.capitalize()} Pack",
        description=f"Payment for {product_type} pack with Telegram Stars",
        payload=payload,
        provider_token='',  # Empty for Telegram Stars
        currency='XTR',  # Telegram Stars
        prices=[LabeledPrice(label='Total', amount=price)]
    )
    
    # Notify admin
    await callback.bot.send_message(
        ADMIN_ID,
        f"New stars payment order #{order_id} from user {user_id} for {product_type} pack"
    )
    
    await callback.answer()

@router.pre_checkout_query()
async def process_pre_checkout_query(pre_checkout_query: PreCheckoutQuery):
    # Always approve the checkout
    await pre_checkout_query.answer(ok=True)

@router.message(F.successful_payment)
async def process_successful_payment(message: Message):
    user_id = message.from_user.id
    lang = db.get_user_language(user_id)
    
    # Find the order by payload
    payload = message.successful_payment.invoice_payload
    order_info = db.get_order_by_stars_payload(payload)
    
    if order_info:
        order_id, _, product_type = order_info
        # Update order status
        db.update_order_status(order_id, 'completed')
        
        # Send success message
        await message.answer(TEXTS['payment_success'][lang])
        
        # Notify admin
        await message.bot.send_message(
            ADMIN_ID,
            f"Stars payment successful for order #{order_id} from user {user_id}, product: {product_type}"
        )
    else:
        await message.answer("Payment processed but couldn't find order information.")

@router.callback_query(F.data.startswith('check_payment_'))
async def check_crypto_payment(callback: CallbackQuery):
    invoice_id = callback.data.split('_', 2)[2]
    user_id = callback.from_user.id
    lang = db.get_user_language(user_id)
    
    # Initialize CryptoBot client
    crypto = AioCryptoPay(token=CRYPTO_PAY_TOKEN, network=Networks.MAIN_NET)
    
    try:
        # Check invoice status
        invoice = await crypto.get_invoices(invoice_ids=[int(invoice_id)])
        if invoice and invoice[0].status == 'paid':
            # Update order status in DB
            order_info = db.get_pending_crypto_orders(user_id)
            if order_info:
                order_id, _, _ = order_info
                db.update_order_status(order_id, 'completed')
                
                # Send success message
                await callback.message.edit_text(TEXTS['payment_success'][lang])
                
                # Notify admin
                await callback.bot.send_message(
                    ADMIN_ID,
                    f"Crypto payment successful for order #{order_id} from user {user_id}"
                )
            else:
                await callback.message.answer("Order not found.")
        else:
            await callback.answer("Payment not detected yet. Please wait or check again later.", show_alert=True)
    except Exception as e:
        await callback.message.answer(f"Error checking payment: {str(e)}")

@router.callback_query(F.data == 'select_pack')
async def back_to_product_selection(callback: CallbackQuery, state: FSMContext):
    # Clear state and return to product selection
    await state.clear()
    user_id = callback.from_user.id
    lang = db.get_user_language(user_id)
    
    await callback.message.edit_text(
        TEXTS['product_selection'][lang],
        reply_markup=get_product_selection_keyboard(lang)
    )
    await callback.answer()


@router.callback_query(F.data == 'pay_pack')
async def start_payment_process(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    photos = data.get('photos', [])
    
    if not photos:
        user_id = callback.from_user.id
        lang = db.get_user_language(user_id)
        await callback.answer("Please upload at least one photo first!", show_alert=True)
        return
    
    user_id = callback.from_user.id
    lang = db.get_user_language(user_id)
    product_type = data['product_type']
    
    await state.set_state(OrderStates.choosing_payment)
    await callback.message.edit_text(
        "Choose payment method:",
        reply_markup=get_payment_methods_keyboard(lang, product_type)
    )
    await callback.answer()
