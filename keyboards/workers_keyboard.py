import random

from aiogram.types import (InlineKeyboardMarkup, InlineKeyboardButton, KeyboardButton, ReplyKeyboardMarkup)
from aiogram.types.keyboard_button_request_users import KeyboardButtonRequestUsers
from aiogram.utils.keyboard import InlineKeyboardBuilder, ReplyKeyboardBuilder

import database as db


get_worker_keyboard = ReplyKeyboardMarkup(
    resize_keyboard=True,
    one_time_keyboard=True,
    keyboard=[
        [
            KeyboardButton(
                text="Отправить контакт",
                request_users=KeyboardButtonRequestUsers(
                    request_id=random.randint(1, 100000),  # Уникальный идентификатор запроса
                    user_is_bot=False,  # Исключаем ботов
                    request_name=True  # Запрашиваем имя пользователя
                )
            )
        ],
        [KeyboardButton(text='Отмена')]
    ]
)


async def start_workers_keyboard(user_id):
    keyboard = InlineKeyboardBuilder()
    keyboard.add(InlineKeyboardButton(text='Отмена', callback_data='cancel'))
    keyboard.add(InlineKeyboardButton(text='Добавить', callback_data='add_worker'))
    user = await db.get_user(user_id)
    workers = await db.get_workers(user_id=user['id'])
    if workers:
        for worker in workers:
            user = await db.get_user_by_id(worker['worker_id'])
            keyboard.add(InlineKeyboardButton(text=f"{user['name']}", callback_data=f"worker_vibor_{user['id']}"))
    return keyboard.adjust(1).as_markup()


async def work_with_workers_keyboard(worker_id):
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text='удалить из сотрудников', callback_data=f'delete_worker_{worker_id}')],
        [InlineKeyboardButton(text='Отмена', callback_data='cancel')]])
    return keyboard
