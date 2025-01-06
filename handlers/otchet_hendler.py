import traceback
import os
import pandas as pd
import gspread
from gspread_dataframe import set_with_dataframe

from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.enums import content_type

from google.auth.exceptions import GoogleAuthError

from States import *
from messages import *
import keyboards as kb
from filters import *
import database as db

router = Router()

router.message.filter(IsRegistredFilter(reg=True), ActiveSubscribeFilter(status=True))

SHEET_NAME = 'Лист1'
GOOGLE_CREDENTIALS_JSON = os.getenv("GOOGLE_CREDENTIALS_JSON")
gc = gspread.service_account(filename=GOOGLE_CREDENTIALS_JSON)


async def make_otchet(owner_id, google_sheet_id):
    try:
        sh = gc.open_by_key(google_sheet_id)
        worksheet = sh.worksheet(SHEET_NAME)

        data = await db.get_full(owner_id=owner_id)
        if data:
            dataframe = pd.DataFrame(data)

            worksheet.clear()
            set_with_dataframe(worksheet, dataframe)

            return f"Отчёт сделан\nВы можете его посмотреть по ссылке: " \
                   f"https://docs.google.com/spreadsheets/d/{google_sheet_id}/edit#gid=0"
        else:
            return "У вас нет данных для создания отчёта"

    except gspread.exceptions.SpreadsheetNotFound:
        return "Ошибка: таблица с таким ID не найдена. Проверьте что вы дали рабочий id и, " \
                      "что таблица имеет открытый доступ"

    except gspread.exceptions.APIError as api_error:
        return f"Ошибка: {api_error}\nУбедитесь, что API Google Sheets включен для вашего проекта, " \
               f"и сервисный аккаунт имеет доступ к таблице."

    except GoogleAuthError:
        # Ошибка аутентификации, если что-то не так с учетными данными
        return "Ошибка: проблема с учетными данными Google. Сообщите о проблеме поддержке."

    except Exception as e:
        error_details = traceback.format_exc()
        print('---e---- ', error_details)
        # Ловим другие возможные ошибки
        return f"Произошла ошибка: {error_details}\n Сообщите о проблеме поддержке."


@router.message(F.text == 'Отчёт 📃')
async def start_otchet(message: Message, state: FSMContext):
    await message.answer(text='⬇️Выберите функцию⬇️', reply_markup=kb.othet_keyboard)


@router.callback_query(F.data == 'create_othet')
async def get_otchet_owner(callback: CallbackQuery, state: FSMContext):
    await state.set_state(OtchetState.get_owner_othet)
    await callback.message.edit_text(text="⬇️Выберите, по какому какому складскому учёту вы хотите получить отчёт ⬇️",
                                     reply_markup=await kb.get_owner(callback.from_user.id))


@router.callback_query(F.data.startswith('get_owner_'), OtchetState.get_owner_othet)
async def get_otchet_owner(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    owner_id = callback.data.split('_')[2]
    await state.update_data(get_owner_othet=owner_id)
    user = await db.get_user(callback.from_user.id)
    if user['google_sheet_id']:
        mes = await make_otchet(owner_id=owner_id, google_sheet_id=user['google_sheet_id'])
        await callback.message.edit_text(text=mes)
    else:
        await state.set_state(OtchetState.get_sheet_id)
        await callback.message.edit_text(text='Пришлите id своей гугл таблицы\n' \
                                              'где её взять можно посмотреть в обучении',
                                         reply_markup=kb.cancel_keyboard)


@router.callback_query(F.data == 'set_sheet_id')
async def get_otchet_owner(callback: CallbackQuery, state: FSMContext):
    await state.set_state(OtchetState.get_sheet_id)
    await callback.message.edit_text(text='Пришлите id своей гугл таблицы\nГде её взять можно посмотреть в обучении',
                                     reply_markup=kb.cancel_keyboard)


@router.message(F.text, OtchetState.get_sheet_id)
async def get_sheet_id(message: Message, state: FSMContext):
    google_sheet_id = message.text
    user = await db.get_user(message.from_user.id)
    await db.set_google_sheet_id(user_id=user['id'], google_sheet_id=google_sheet_id)
    await message.answer(text='id получен')
    state_data = await state.get_data()
