from aiogram.types import (InlineKeyboardMarkup, InlineKeyboardButton, KeyboardButton, ReplyKeyboardMarkup)
from aiogram.utils.keyboard import InlineKeyboardBuilder, ReplyKeyboardBuilder

import database as db

cancel_button = InlineKeyboardButton(text='Отмена', callback_data='cancel')
create_komponent_button = InlineKeyboardButton(text='Добавить', callback_data='create_komponent')
change_komponent_button = InlineKeyboardButton(text='Изменить', callback_data='change_komponent')
delete_komponent_button = InlineKeyboardButton(text='Удалить', callback_data='delete_komponent')

cancel_keyboard = InlineKeyboardMarkup(inline_keyboard=[[cancel_button]])

reg_keyboard = ReplyKeyboardMarkup(keyboard=[
    [KeyboardButton(text='Пройти регистрацию', request_contact=True)]], resize_keyboard=True)

base_keyboard = ReplyKeyboardMarkup(
    keyboard=[[KeyboardButton(text='Работа с учётом 👨‍💻'), KeyboardButton(text='Отчёт 📃')],
              [KeyboardButton(text='Сотрудники 👷‍♂️'), KeyboardButton(text='Обучение 🧠')],
              [KeyboardButton(text='Поддержка 🛎'), KeyboardButton(text='Подписка 💸')]],
    resize_keyboard=True)

start_work_keyboard = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text='Вести учёт', callback_data='sklad_list')],
    [InlineKeyboardButton(text='Все товары', callback_data='all_tovar_list')],
    [cancel_button]
])

sklad_work_keyboard = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text='Группы', callback_data='grup_list')],
    [change_komponent_button],
    [delete_komponent_button],
    [cancel_button]
])

grup_work_keyboard = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text='Товары', callback_data='tovar_grup_list')],
    [change_komponent_button],
    [delete_komponent_button],
    [cancel_button]
])

tovar_work_keyboard = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text='Посмотреть товар', callback_data='watch_tovar')],
    [change_komponent_button],
    [delete_komponent_button],
    [cancel_button]
])

tovar_in_grup_keyboard = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text='Вести учёт', callback_data='tovar_uchet')],
    [change_komponent_button],
    [InlineKeyboardButton(text='Удалить со списка', callback_data='delete_tovar_from_grup')],
    [cancel_button]
])

tovar_grup_work_keyboard = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text='Добавить в список', callback_data='tovar_grup_list')],
    [InlineKeyboardButton(text='Товары', callback_data='tovar_grup_list')],
    [cancel_button]
])

propusk_tovar_data_keyboard = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text='Пропустить', callback_data='next_tovar_data')],
    [cancel_button]])

tovar_uchet_keyboard = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text='Поступление', callback_data='uchet_postuplenie')],
    [InlineKeyboardButton(text='Списание', callback_data='uchet_spisanie')],
    [cancel_button]
])


async def sklad_list_keyboard(tg_id):
    keyboard = InlineKeyboardBuilder()
    keyboard.add(create_komponent_button)
    user = await db.get_user(tg_id)
    sklads = await db.get_sklads(user['id'])
    if sklads:
        for sklad in sklads:
            keyboard.add(InlineKeyboardButton(text=f'{sklad["name"]}',
                                              callback_data=f'sklad_vibor_{sklad["id"]}'))

    owners = await db.get_owner(user['id'])
    if owners:
        for owner in owners:
            sklads = await db.get_sklads(owner["id"])
            if sklads:
                for sklad in sklads:
                    keyboard.add(InlineKeyboardButton(text=f'{sklad["name"]}',
                                                      callback_data=f'sklad_vibor_{sklad["id"]}'))

    keyboard.add(cancel_button)
    return keyboard.adjust(1).as_markup()


async def grup_list_keyboard(sklad_id):
    keyboard = InlineKeyboardBuilder()
    keyboard.add(create_komponent_button)
    grups = await db.get_grups_by_sklad(sklad_id)
    for grup in grups:
        keyboard.add(InlineKeyboardButton(text=f'{grup["name"]}',
                                          callback_data=f'grup_vibor_{grup["id"]}'))
    keyboard.add(cancel_button)
    return keyboard.adjust(1).as_markup()


async def all_tovar_list_keyboard(user_id):
    keyboard = InlineKeyboardBuilder()
    keyboard.add(create_komponent_button)

    user = await db.get_user(user_id)
    tovars = await db.get_tovars(user["id"])
    if tovars:
        for tovar in tovars:
            keyboard.add(InlineKeyboardButton(text=f'{tovar["name"]}', callback_data=f'tovar_vibor_{tovar["id"]}'))

    owners = await db.get_owner(user['id'])
    if owners:
        for owner in owners:
            tovars = await db.get_tovars(owner["id"])
            if tovars:
                for tovar in tovars:
                    keyboard.add(InlineKeyboardButton(text=f'{tovar["name"]}',
                                                      callback_data=f'tovar_vibor_{tovar["id"]}'))
    keyboard.add(cancel_button)
    return keyboard.adjust(1).as_markup()


async def tovar_grup_list_keyboard(grup_id):
    keyboard = InlineKeyboardBuilder()
    keyboard.add(InlineKeyboardButton(text=f'Добавить товар в список', callback_data=f'add_tovar_to_grup'))
    tovars = await db.get_tovar_by_grup(grup_id)
    if tovars:
        for tovar in tovars:
            keyboard.add(InlineKeyboardButton(text=f'{tovar["name"]}', callback_data=f'tovar_vibor_{tovar["id"]}'))
    keyboard.add(cancel_button)
    return keyboard.adjust(1).as_markup()


async def add_tovar_to_grup_list_keyboard(user_id, grup_id):
    keyboard = InlineKeyboardBuilder()
    tovar_in_grup = await db.get_tovar_by_grup(grup_id)

    all_tovars = []
    user = await db.get_user(user_id)
    tovars = await db.get_tovars(user["id"])
    if tovars:
        all_tovars += tovars

    owners = await db.get_owner(user['id'])
    if owners:
        for owner in owners:
            tovars = await db.get_tovars(owner["id"])
            if tovars:
                all_tovars += tovars

    keyboard.add(create_komponent_button)
    if tovar_in_grup:
        for tovar in all_tovars:
            if tovar:
                if not tovar in tovar_in_grup:
                    keyboard.add(InlineKeyboardButton(text=f'{tovar["name"]}',
                                                      callback_data=f'add_tovar_to_grup_{tovar["id"]}'))
    else:
        for tovar in all_tovars:
            keyboard.add(InlineKeyboardButton(text=f'{tovar["name"]}',
                                              callback_data=f'add_tovar_to_grup_{tovar["id"]}'))

    keyboard.add(cancel_button)
    return keyboard.adjust(1).as_markup()


async def get_owner(user_id):
    user = await db.get_user(user_id)
    keyboard = InlineKeyboardBuilder()
    keyboard.add(InlineKeyboardButton(text=f'{user["name"]}', callback_data=f'get_owner_{user["id"]}'))
    owners = await db.get_owner(user['id'])
    if owners:
        for owner in owners:
            user = await db.get_user_by_id(owner["owner_id"])
            keyboard.add(InlineKeyboardButton(text=f'{user["name"]}', callback_data=f'get_owner_{user["id"]}'))
    keyboard.add(cancel_button)
    return keyboard.adjust(1).as_markup()

othet_keyboard = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text='Создать отчёт', callback_data='create_othet')],
    [InlineKeyboardButton(text='Изменить id таблицы', callback_data='set_sheet_id')],
    [cancel_button]
])

payment_keyboard = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text='Продлить', callback_data='pay_subscribe')],
    [cancel_button]
])
