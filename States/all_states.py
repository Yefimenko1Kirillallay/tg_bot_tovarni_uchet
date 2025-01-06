from aiogram.fsm.state import State, StatesGroup


class KompWorkState(StatesGroup):
    sklad = State()
    grup = State()
    tovar = State()
    uchet = State()
    action = State()
    type = State()
    name = State()
    description = State()
    information = State()
    size = State()
    weight = State()
    izmerenie = State()
    photo = State()
    date = State()


class SupportState(StatesGroup):
    get_text = State()


class AddWorkerState(StatesGroup):
    get_worker = State()


class OtchetState(StatesGroup):
    get_owner_othet = State()
    get_sheet_id = State()

