from pprint import pprint

from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.enums import content_type

import States
from messages import *
from keyboards import *
import database as db
import filters

router = Router()


@router.message(CommandStart(), filters.IsRegistredFilter(reg=False))
async def send_welcome(message: Message):
    await message.answer(text=start_msg.format(message.from_user.first_name)+'\n'+reg_message,
                         reply_markup=reg_keyboard)


@router.message(filters.IsRegistredFilter(reg=False), F.content_type == "contact")
async def not_reg_user_message(message: Message):
    await db.add_user(tg_id=message.from_user.id, number=message.contact.phone_number,
                      name=message.from_user.first_name)
    await message.answer(text=sucsess_reg_msg, reply_markup=base_keyboard)


@router.message(filters.IsRegistredFilter(reg=False))
async def not_reg_user_message(message: Message):
    await message.answer(text=reg_message, reply_markup=reg_keyboard)


@router.message(CommandStart(), filters.IsRegistredFilter(reg=True))
async def send_welcome(message: Message):
    await message.answer(text=start_msg.format(message.from_user.first_name),
                         reply_markup=base_keyboard)


@router.message(filters.IsRegistredFilter(reg=True), filters.ActiveSubscribeFilter(status=False))
async def not_active_status(message: Message):
    await message.answer(text="Ваша подписка закончена\nДля продолжения работы, продлите подписку",
                         reply_markup=payment_keyboard)


@router.callback_query(F.data == 'cancel')
async def cancel(callback: CallbackQuery, state: FSMContext):
    await callback.answer('cansel')
    await state.clear()
    await callback.message.edit_text(text='Ваши действия отменены')


@router.message(F.text.lower() == 'отмена', filters.IsRegistredFilter(reg=True))
async def cancel(message: Message, state: FSMContext):
    await state.clear()
    await message.answer(text='Ваши действия отменены', reply_markup=base_keyboard)
