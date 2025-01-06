import os

from aiogram.filters import BaseFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery

from dotenv import load_dotenv

import database

load_dotenv()
ADMINS: list = os.getenv("ADMINS")



class IsOwnerFilter(BaseFilter):
    def __init__(self, is_owner):
        self.is_owner = is_owner

    async def __call__(self, message: Message) -> bool:
        return message.from_user.id in ADMINS


class IsRegistredFilter(BaseFilter):
    def __init__(self, reg) -> None:
        self.reg = reg

    async def __call__(self, message: Message) -> bool:
        user = await database.get_user(message.from_user.id)
        if user:
            return (user['name'] != '') == self.reg
        return (user is None) != self.reg


class ActiveSubscribeFilter(BaseFilter):
    def __init__(self, status) -> None:
        self.status = status

    async def __call__(self, message: Message) -> bool:
        user = await database.get_user(message.from_user.id)
        if user:
            return (user['subscription_status'] == 'active') == self.status
        else:
            return False


class KomponentTypeFilter(BaseFilter):
    def __init__(self, komponent_type: str, type_value: str):
        self.komponent_type = komponent_type
        self.type_value = type_value

    async def __call__(self, callback: CallbackQuery, state: FSMContext) -> bool:
        data = await state.get_data()
        aktive_state = str(await state.get_state()).split(':')[0]
        if aktive_state=='KompWorkState':
            return data[self.komponent_type] == self.type_value
        else:
            return False
