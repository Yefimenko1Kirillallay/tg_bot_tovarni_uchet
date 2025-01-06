import os
import uuid
from datetime import datetime, timedelta, date

from yookassa import Configuration, Payment

from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, LabeledPrice, PreCheckoutQuery
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.enums import content_type

from States import *
from messages import *
from main import bot
import keyboards as kb
from filters import *
import database as db

from dotenv import load_dotenv

load_dotenv()

PAYMENT_PROVIDER_TOKEN = os.getenv("PAYMENT_PROVIDER_TOKEN")
YOOKASSA_SHOP_ID = os.getenv("YOOKASSA_SHOP_ID")  # ID магазина Юкассы
YOOKASSA_SECRET_KEY = os.getenv("YOOKASSA_SECRET_KEY")  # Секретный ключ Юкассы
CURRENCY = os.getenv("CURRENCY")
PRICE = int(os.getenv("PRICE"))

Configuration.account_id = YOOKASSA_SHOP_ID
Configuration.secret_key = YOOKASSA_SECRET_KEY

router = Router()

router.message.filter(IsRegistredFilter(reg=True))


@router.message(F.text == 'Подписка 💸')
async def payment_info(message: Message):
    user = await db.get_user(message.from_user.id)
    print(user)
    end_date = user['subscription_end_date']
    sub_status = user['subscription_status']
    if sub_status:
        mes = f"Ваша подписка закончится {end_date.strftime('%d.%m.%Y')}"
    else:
        mes = f"Ваша подписка закончена\nДля продолжения работы, продлите подписку"
    await message.answer(text=mes, reply_markup=kb.payment_keyboard)


@router.callback_query(F.data == 'pay_subscribe')
async def pay_subskribe(callback: CallbackQuery):
    prices = [LabeledPrice(label="Подписка на месяц", amount=PRICE)]
    payload = str(uuid.uuid4())  # Уникальный идентификатор заказа
    await bot.send_invoice(
        chat_id=callback.from_user.id,
        title="Подписка на месяц",
        description="Оплата подписки на 30 дней",
        payload=payload,
        provider_token=PAYMENT_PROVIDER_TOKEN,
        currency=CURRENCY,
        prices=prices,
        start_parameter="subscribe",
    )


@router.pre_checkout_query()
async def pre_checkout(pre_checkout_query: PreCheckoutQuery):
    await bot.answer_pre_checkout_query(pre_checkout_query.id, ok=True)


@router.message(F.successful_payment)
async def successful_payment(message: Message):
    user = await db.get_user(message.from_user.id)
    await db.add_subscription_time(user_id=user['id'])
    user = await db.get_user(message.from_user.id)
    end_date = user['subscription_end_date']
    await message.answer(f"Спасибо за оплату! Ваша подписка активна до {end_date.strftime('%d.%m.%Y')}.")

