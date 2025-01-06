from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext

from aiogram.enums import content_type

from States import *
from messages import *
import keyboards as kb
from filters import *
import database as db

router = Router()

router.message.filter(IsRegistredFilter(reg=True), ActiveSubscribeFilter(status=True))


@router.message(F.text == 'Сотрудники 👷‍♂️')
async def start_workers(message: Message):
    await message.answer(text="️⬇️Выберите сотрудника или добавьте нового⬇️",
                         reply_markup=await kb.start_workers_keyboard(message.from_user.id))


@router.callback_query(F.data.startswith('worker_vibor_'))
async def worker_vibor(callback: CallbackQuery):
    await callback.answer()
    worker_id = int(callback.data.split('_')[2])
    await callback.message.answer(text='⬇️Выберите функции⬇️',
                                  reply_markup=await kb.work_with_workers_keyboard(worker_id))


@router.callback_query(F.data.startswith('delete_worker_'))
async def delete_worker(callback: CallbackQuery):
    await callback.answer()
    worker_id = int(callback.data.split('_')[2])
    await db.delete_owner_worker_assotiation(owner_id=callback.from_user.id, worker_id=worker_id)
    await callback.message.answer(text='Работник удалён из списка',
                                  reply_markup=await kb.start_workers_keyboard(callback.from_user.id))


@router.callback_query(F.data == 'add_worker')
async def add_worker(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    await callback.message.answer("Пожалуйста, отправьте контакт другого человека, нажав кнопку ниже.",
                                  reply_markup=kb.get_worker_keyboard)
    await state.set_state(AddWorkerState.get_worker)


# Хэндлер для обработки контакта
@router.message(AddWorkerState.get_worker, F.user_shared)
async def process_contact(message: Message, state: FSMContext):
    worker = message.user_shared
    if worker is None:
        await message.answer(text="Пожалуйста, отправьте контакт с помощью кнопки.",
                             reply_markup=kb.get_worker_keyboard)
        return
    user_id = worker.user_id

    await state.clear()
    owner = await db.get_user(message.from_user.id)
    user = await db.get_user(user_id)
    if user is None:
        await db.add_user(tg_id=user_id, number='', name='')
        user = await db.get_user(user_id)
    try:
        await db.add_owner_worker_assotiation(owner_id=owner['id'], worker_id=user['id'])
        await message.answer(text=f"Сотрудник добавлен:\nUser ID: {user_id}", reply_markup=kb.base_keyboard)
    except:
        await message.answer(text=f"Произошла ошибка", reply_markup=kb.base_keyboard)
