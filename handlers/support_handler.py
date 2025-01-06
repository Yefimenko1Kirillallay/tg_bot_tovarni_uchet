import os

from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.enums import content_type

from main import bot

from States import *
from messages import *
import keyboards as kb
from filters import *
import database as db

ADMIN_CHAT_ID = int(os.getenv("ADMIN_CHAT_ID"))

router = Router()

router.message.filter(IsRegistredFilter(reg=True), ActiveSubscribeFilter(status=True))


@router.message(F.text == 'Поддержка 🛎')  # lambda message: message.chat.id != ADMIN_CHAT_ID
async def start_support(message: Message, state: FSMContext):
    await state.set_state(SupportState.get_text)
    await message.answer(text='Введите вопрос, который вы хотите задать у поддержки.', reply_markup=kb.cancel_keyboard)


@router.message(SupportState.get_text)
async def get_text(message: Message, state: FSMContext):
    await state.clear()
    await message.answer('Ваш вопрос отправлен в поддержку.')
    mes = f"Новое сообщение от пользователя:\nИмя: <code>{message.from_user.full_name}</code>\n" \
          f"ID: <code>{message.from_user.id}</code>\nUsername: <code>@{message.from_user.username}</code>\n" \
          f"Чтобы ответить пользователю, ответьте на это сообщение\n\nТекст сообщения:\n<code>{message.text}</code>"
    await bot.send_message(ADMIN_CHAT_ID, mes)
    forwarded = await bot.forward_message(ADMIN_CHAT_ID, from_chat_id=message.chat.id, message_id=message.message_id)


# Хэндлер для ответа администратора
@router.message(lambda message: message.chat.id == ADMIN_CHAT_ID)
async def reply_to_user(message: Message):
    if message.reply_to_message and "ID:" in message.reply_to_message.text:
        # Извлекаем ID пользователя из текста сообщения
        try:
            user_id_text = message.reply_to_message.text.split("ID:")[1].split("\n")[0].strip()
            user_id = int(user_id_text)  # Преобразуем в целое число
            reply_text = message.text

            # Отправляем ответ пользователю
            await bot.send_message(user_id, f"Ответ поддержки: {reply_text}")
            await message.answer("Ответ отправлен пользователю.")
        except ValueError:
            print("Не удалось извлечь ID пользователя из текста.")
            await message.answer("Ошибка: не удалось определить ID пользователя.")
    else:
        await message.answer("Ответьте на пересланное сообщение пользователя, чтобы отправить ему ответ.")
