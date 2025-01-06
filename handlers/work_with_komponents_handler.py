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


@router.callback_query(F.data == 'cancel')
async def cancel(callback: CallbackQuery, state: FSMContext):
    await callback.answer('cansel')
    await state.clear()
    await callback.message.edit_text(text='Ваши действия отменены')


@router.message(F.text == 'Работа с учётом 👨‍💻')
async def start_uchet(message: Message, state: FSMContext):
    await message.answer(text="⬇️Выберите с чем будете работать⬇️", reply_markup=kb.start_work_keyboard)


@router.callback_query(F.data == 'sklad_list')
async def sklad_list(callback: CallbackQuery, state: FSMContext):
    await state.set_state(KompWorkState.sklad)
    await callback.message.edit_text(text="️⬇️Выберите склад или создайте новый⬇️",
                                     reply_markup=await kb.sklad_list_keyboard(callback.from_user.id))


@router.callback_query(F.data == 'delete_komponent')
async def delete_komponent(callback: CallbackQuery, state: FSMContext):
    await callback.answer('Произошло удаление')
    aktive_state = str(await state.get_state()).split(':')[1]
    state_data = await state.get_data()
    aktive_state_data = state_data[aktive_state]
    await db.delete_komponent(komponent=aktive_state, komponent_id=aktive_state_data)
    match aktive_state:
        case 'sklad':
            await callback.message.edit_text(text="️⬇️Ваши склады⬇️",
                                             reply_markup=await kb.sklad_list_keyboard(callback.from_user.id))
        case 'grup':
            await callback.message.edit_text(text="️⬇️Группы⬇️",
                                             reply_markup=await kb.grup_list_keyboard(state_data["sklad"]))
        case 'tovar':
            await callback.message.edit_text(text="️⬇️Товары⬇️",
                                             reply_markup=await kb.sklad_list_keyboard(callback.from_user.id))


@router.callback_query(F.data == 'change_komponent')
async def change_komponent(callback: CallbackQuery, state: FSMContext):
    await state.update_data(action='change')
    await state.update_data(type='get_name')
    aktive_state = str(await state.get_state()).split(':')[1]
    state_data = await state.get_data()
    action = state_data[aktive_state]
    await callback.answer()
    if aktive_state == 'tovar':
        await callback.message.edit_text(text="Начинаем изменение.\nВведите название:",
                                         reply_markup=kb.propusk_tovar_data_keyboard)
    else:
        await callback.message.edit_text(text="Начинаем изменение.\nВведите название:", reply_markup=kb.cancel_keyboard)


@router.callback_query(F.data == 'create_komponent')
async def create_sklad(callback: CallbackQuery, state: FSMContext):
    await state.update_data(action='create')
    await state.update_data(type='get_name')
    await callback.answer()
    await callback.message.edit_text(text="Начинаем создание.\nВведите название:", reply_markup=kb.cancel_keyboard)


@router.message(F.text, KomponentTypeFilter("type", "get_name"))
async def get_komponent_name(message: Message, state: FSMContext):
    aktive_state = str(await state.get_state()).split(':')[1]
    state_data = await state.get_data()
    action = state_data["action"]

    if aktive_state == 'tovar':
        await state.update_data(type="get_description")
        await state.update_data(name=message.text)
        await message.answer(text="Введите описание:", reply_markup=kb.propusk_tovar_data_keyboard)

    elif aktive_state == 'sklad':
        if action == 'create':
            await state.update_data(name=message.text)
            await message.answer(text='На кого будет создан товар?',
                                 reply_markup=await kb.get_owner(message.from_user.id))
        elif action == 'change':
            sklad_id = state_data["sklad"]
            await db.change_sklad(sklad_id=sklad_id, name=message.text)
            await message.answer(text=f"Вы изменили имя склада на - " + message.text,
                                 reply_markup=await kb.sklad_list_keyboard(message.from_user.id))
        await state.update_data(action=None)
        await state.update_data(type=None)

    elif aktive_state == 'grup':
        if action == 'create':
            sklad_id = state_data["sklad"]
            await db.add_grup(sklad_id=sklad_id, name=message.text)
            await message.answer(text=f"Вы создали группу с именем - " + message.text,
                                 reply_markup=await kb.grup_list_keyboard(sklad_id))
        elif action == 'change':
            grup_id = state_data["grup"]
            sklad_id = state_data["sklad"]
            await db.change_grup(grup_id=grup_id, name=message.text)
            await message.answer(text=f"Вы изменили имя группы на - " + message.text,
                                 reply_markup=await kb.grup_list_keyboard(sklad_id))
        await state.update_data(action=None)
        await state.update_data(type=None)


@router.callback_query(F.data.startswith("get_owner_"), KompWorkState.sklad)
async def add_sclad(callback: CallbackQuery, state: FSMContext):
    await callback.answer(callback.data)
    owner_id = callback.data.split('_')[2]
    state_data = await state.get_data()
    name = state_data["name"]

    await db.add_sklad(owner_id=owner_id, name=name)

    await callback.message.answer(text=f"Вы создали склад с именем - " + name,
                                  reply_markup=await kb.sklad_list_keyboard(callback.message.from_user.id))


@router.message(F.photo, KompWorkState.tovar, KomponentTypeFilter("type", "get_photo"))
async def get_tovar_photo(message: Message, state: FSMContext):
    photo = message.photo[-1]
    await state.update_data(photo=photo.file_id)
    state_data = await state.get_data()
    action = state_data["action"]
    if action == 'change':
        tovar_id = state_data['tovar']
        name = state_data["name"]
        photo_id = state_data["photo"]
        description = state_data["description"]
        information = state_data["information"]
        size = state_data["size"]
        weight = state_data["weight"]
        izmerenie = state_data["izmerenie"]
        tovar = await db.get_tovar_by_id(tovar_id=tovar_id)
        mes = f"ТОВАР ИЗМЕНЁН\n\n"
        if name:
            mes += f"<b>Название:</b> {name} <s>{tovar['name']}</s>\n"
        else:
            mes += f"<b>Название:</b> {tovar['name']}\n"

        if description:
            mes += f"<b>Описание:</b> {description} <s>{tovar['description']}</s>\n"
        else:
            mes += f"<b>Описание:</b> {tovar['description']}\n"

        if information:
            mes += f"<b>Информация:</b> {information} <s>{tovar['information']}</s>\n"
        else:
            mes += f"<b>Информация:</b> {tovar['information']}\n"

        if size:
            mes += f"<b>Габариты:</b> {size} <s>{tovar['size']}</s>\n"
        else:
            mes += f"<b>Габариты:</b> {tovar['size']}\n"

        if weight:
            mes += f"<b>Вес:</b> {weight} <s>{tovar['weight']}</s>\n"
        else:
            mes += f"<b>Вес:</b> {tovar['weight']}\n"

        if izmerenie:
            mes += f"<b>Измерение:</b> {izmerenie} <s>{tovar['izmerenie']}</s>\n"
        else:
            mes += f"<b>Измерение:</b> {tovar['izmerenie']}\n"

        await db.change_tovar(tovar_id=tovar_id, name=name, photo_id=photo_id, description=description,
                              information=information, size=size, weight=weight, izmerenie=izmerenie)
        if photo_id:
            await message.answer_photo(photo=photo_id, caption=mes)
        elif tovar['photo']:
            await message.answer_photo(photo=tovar['photo'], caption=mes)
        else:
            await message.answer(text=mes)
    else:
        await message.answer(text='На кого будет создан товар?',
                             reply_markup=await kb.get_owner(message.from_user.id))


@router.callback_query(F.data.startswith("get_owner_"), KompWorkState.tovar)
async def add_tovar(callback: CallbackQuery, state: FSMContext):
    await callback.answer(callback.data)
    owner_id = callback.data.split('_')[2]
    state_data = await state.get_data()
    grup_id = state_data["grup"]
    name = state_data["name"]
    photo_id = state_data["photo"]
    description = state_data["description"]
    information = state_data["information"]
    size = state_data["size"]
    weight = state_data["weight"]
    izmerenie = state_data["izmerenie"]

    await db.add_tovar(grup_id=grup_id, owner_id=owner_id, name=name, photo_id=photo_id, description=description,
                       information=information, size=size, weight=weight, izmerenie=izmerenie)

    mess = f"ТОВАР СОЗДАН\n\n<b>Название:</b> {name}\n<b>Описание:</b> {description}\n<b>Информация</b> {information}" \
           f"\n<b>Габариты:</b> {size}\n<b>Вес:</b> {weight}\n<b>Измерение</b> {izmerenie}"
    if photo_id:
        await callback.message.answer_photo(photo=photo_id, caption=mess)
    else:
        await callback.message.answer(text=mess)


@router.message(F.text, KompWorkState.tovar)
async def get_tovar_dopolnitelno(message: Message, state: FSMContext):
    state_data = await state.get_data()
    action_type = state_data["type"]
    match action_type:
        case "get_description":
            await state.update_data(type="get_information")
            await state.update_data(description=message.text)
            await message.answer(text="Введите дополнительную информацию:", reply_markup=kb.propusk_tovar_data_keyboard)
        case "get_information":
            await state.update_data(type="get_size")
            await state.update_data(information=message.text)
            await message.answer(text="Введите габариты:", reply_markup=kb.propusk_tovar_data_keyboard)
        case "get_size":
            await state.update_data(type="get_izmerenie")
            await state.update_data(size=message.text)
            await message.answer(text="Введите измерение:", reply_markup=kb.propusk_tovar_data_keyboard)
        case "get_izmerenie":
            await state.update_data(type="get_weight")
            await state.update_data(izmerenie=message.text)
            await message.answer(text="Введите вес (кг):", reply_markup=kb.propusk_tovar_data_keyboard)
        case "get_weight":
            await state.update_data(type="get_photo")
            await state.update_data(weight=message.text)
            await message.answer(text="Пришлите фото:", reply_markup=kb.propusk_tovar_data_keyboard)


@router.callback_query(F.data == 'next_tovar_data', KompWorkState.tovar)
async def propusk_vvod(callback: CallbackQuery, state: FSMContext):
    await callback.answer(callback.data)
    state_data = await state.get_data()
    action = state_data['action']
    action_type = state_data["type"]
    match action_type:
        case "get_description":
            await state.update_data(type="get_information")
            await state.update_data(description='')
            await callback.message.edit_text(text="Введите дополнительную информацию:",
                                             reply_markup=kb.propusk_tovar_data_keyboard)
        case "get_information":
            await state.update_data(type="get_size")
            await state.update_data(information='')
            await callback.message.edit_text(text="Введите габариты:", reply_markup=kb.propusk_tovar_data_keyboard)
        case "get_size":
            await state.update_data(type="get_izmerenie")
            await state.update_data(size='')
            await callback.message.edit_text(text="Введите измерение:", reply_markup=kb.propusk_tovar_data_keyboard)
        case "get_izmerenie":
            await state.update_data(type="get_weight")
            await state.update_data(izmerenie='')
            await callback.message.edit_text(text="Введите вес (кг):", reply_markup=kb.propusk_tovar_data_keyboard)
        case "get_weight":
            await state.update_data(type="get_photo")
            await state.update_data(weight='')
            await callback.message.edit_text(text="Пришлите фото:", reply_markup=kb.propusk_tovar_data_keyboard)
        case "get_photo":
            await state.update_data(photo='')
            state_data = await state.get_data()
            action = state_data['action']
            if action == 'change':
                tovar_id = state_data['tovar']
                name = state_data["name"]
                photo_id = state_data["photo"]
                description = state_data["description"]
                information = state_data["information"]
                size = state_data["size"]
                weight = state_data["weight"]
                izmerenie = state_data["izmerenie"]

                tovar = await db.get_tovar_by_id(tovar_id=tovar_id)
                mes = f"ТОВАР ИЗМЕНЁН\n\n"
                if name:
                    mes += f"<b>Название:</b> {name} <s>{tovar['name']}</s>\n"
                else:
                    mes += f"<b>Название:</b> {tovar['name']}\n"

                if description:
                    mes += f"<b>Описание:</b> {description} <s>{tovar['description']}</s>\n"
                else:
                    mes += f"<b>Описание:</b> {tovar['description']}\n"

                if information:
                    mes += f"<b>Информация:</b> {information} <s>{tovar['information']}</s>\n"
                else:
                    mes += f"<b>Информация:</b> {tovar['information']}\n"

                if size:
                    mes += f"<b>Габариты:</b> {size} <s>{tovar['size']}</s>\n"
                else:
                    mes += f"<b>Габариты:</b> {tovar['size']}\n"

                if weight:
                    mes += f"<b>Вес:</b> {weight} <s>{tovar['weight']}</s>\n"
                else:
                    mes += f"<b>Вес:</b> {tovar['weight']}\n"

                if izmerenie:
                    mes += f"<b>Измерение:</b> {izmerenie} <s>{tovar['izmerenie']}</s>\n"
                else:
                    mes += f"<b>Измерение:</b> {tovar['izmerenie']}\n"

                await db.change_tovar(tovar_id=tovar_id, name=name, photo_id=photo_id, description=description,
                                      information=information, size=size, weight=weight, izmerenie=izmerenie)
                if photo_id:
                    await callback.message.answer_photo(photo=photo_id, caption=mes)
                elif tovar['photo_id']:
                    await callback.message.answer_photo(photo=tovar['photo_id'], caption=mes)
                else:
                    await callback.message.answer(text=mes)
            else:
                await callback.message.edit_text(text='На кого будет создан товар?',
                                                 reply_markup=await kb.get_owner(callback.from_user.id))


@router.callback_query(F.data.startswith('sklad_vibor_'), KompWorkState.sklad)
async def work_vibor_in_sklad(callback: CallbackQuery, state: FSMContext):
    await callback.answer(callback.data)
    sklad_id = callback.data.split('_')[2]
    await state.update_data(sklad=sklad_id)
    await callback.message.edit_text(text='⬇️Выберите функции⬇️', reply_markup=kb.sklad_work_keyboard)


@router.callback_query(F.data == 'grup_list', KompWorkState.sklad)
async def group_vibor_list(callback: CallbackQuery, state: FSMContext):
    await callback.answer(callback.data)
    await state.set_state(KompWorkState.grup)
    state_data = await state.get_data()
    sklad_id = state_data["sklad"]
    await callback.message.edit_text(text='⬇️Выберите групп или создайте новую⬇️',
                                     reply_markup=await kb.grup_list_keyboard(sklad_id=sklad_id))


@router.callback_query(F.data.startswith('grup_vibor_'), KompWorkState.grup)
async def work_vibor_in_grup(callback: CallbackQuery, state: FSMContext):
    await callback.answer(callback.data)
    grup_id = callback.data.split('_')[2]
    await state.update_data(grup=grup_id)
    await callback.message.edit_text(text='⬇️Выберите функции⬇️', reply_markup=kb.grup_work_keyboard)


@router.callback_query(F.data.startswith('tovar_vibor_'), KompWorkState.tovar)
async def work_vibor_in_grup(callback: CallbackQuery, state: FSMContext):
    await callback.answer(callback.data)
    tovar_id = callback.data.split('_')[2]
    await state.update_data(tovar=tovar_id)
    state_data = await state.get_data()
    grup_id = state_data['grup']
    if grup_id:
        await callback.message.edit_text(text='⬇️Выберите функции⬇️', reply_markup=kb.tovar_in_grup_keyboard)
    else:
        await callback.message.edit_text(text='⬇️Выберите функции⬇️', reply_markup=kb.tovar_work_keyboard)


@router.callback_query(F.data == 'watch_tovar', KompWorkState.tovar)
async def work_vibor_in_grup(callback: CallbackQuery, state: FSMContext):
    await callback.answer(callback.data)
    state_data = await state.get_data()
    tovar_id = state_data['tovar']
    tovar = await db.get_tovar_by_id(tovar_id=tovar_id)
    name = tovar["name"]
    photo_id = tovar["photo_id"]
    description = tovar["description"]
    information = tovar["information"]
    size = tovar["size"]
    weight = tovar["weight"]
    izmerenie = tovar["izmerenie"]
    mes = f"ТОВАР\n\n<b>Название:</b> {name}\n<b>Описание:</b> {description}\n<b>Информация</b> {information}" \
           f"\n<b>Габариты:</b> {size}\n<b>Вес:</b> {weight}\n<b>Измерение</b> {izmerenie}"
    if photo_id:
        await callback.message.answer_photo(photo=photo_id, caption=mes)
    else:
        await callback.message.answer(text=mes)

@router.callback_query(F.data.startswith('add_tovar_to_grup_'), KompWorkState.tovar)
async def work_vibor_in_grup(callback: CallbackQuery, state: FSMContext):
    await callback.answer(callback.data)
    tovar_id = callback.data.split('_')[4]
    await state.update_data(tovar=tovar_id)
    state_data = await state.get_data()
    grup_id = state_data['grup']
    await db.add_tovar_grup_assotiation(grup_id=grup_id, tovar_id=tovar_id)
    await callback.message.edit_text(text='⬇️Выберите функции⬇️', reply_markup=kb.tovar_in_grup_keyboard)


@router.callback_query(F.data == 'all_tovar_list')
async def tovar_vibor_list(callback: CallbackQuery, state: FSMContext):
    await callback.answer(callback.data)
    await state.set_state(KompWorkState.tovar)
    await state.update_data(grup=None)
    await state.update_data(sklad=None)
    await callback.message.edit_text(text='⬇️Выберите товар или создайте новую⬇️',
                                     reply_markup=await kb.all_tovar_list_keyboard(user_id=callback.from_user.id))


@router.callback_query(F.data == 'tovar_grup_list', KompWorkState.grup)
async def tovar_grup_vibor_list(callback: CallbackQuery, state: FSMContext):
    await callback.answer(callback.data)
    await state.set_state(KompWorkState.tovar)
    state_data = await state.get_data()
    grup_id = state_data['grup']
    await callback.message.edit_text(text='⬇️Выберите товар или создайте новую⬇️',
                                     reply_markup=await kb.tovar_grup_list_keyboard(grup_id))


@router.callback_query(F.data == 'add_tovar_to_grup', KompWorkState.tovar)
async def add_tovar_to_grup_list(callback: CallbackQuery, state: FSMContext):
    await callback.answer(callback.data)
    state_data = await state.get_data()
    grup_id = state_data['grup']
    user_id = callback.from_user.id
    await callback.message.edit_text(text='⬇️Выберите товар или создайте новый⬇️',
                                     reply_markup=await kb.add_tovar_to_grup_list_keyboard(user_id=user_id,
                                                                                           grup_id=grup_id))


@router.callback_query(F.data == 'delete_tovar_from_grup', KompWorkState.tovar)
async def delete_tovar_from_grup(callback: CallbackQuery, state: FSMContext):
    await callback.answer(callback.data)
    state_data = await state.get_data()
    grup_id = state_data['grup']
    tovar_id = state_data['tovar']
    await db.delete_komponent(komponent='grup_tovar_ship', komponent_id=tovar_id, komponent2_id=grup_id)
    await callback.message.edit_text(text='Товар удалён из списка',
                                     reply_markup=await kb.tovar_grup_list_keyboard(grup_id))


@router.callback_query(F.data == 'tovar_uchet', KompWorkState.tovar)
async def tovar_uchet(callback: CallbackQuery, state: FSMContext):
    await callback.answer(callback.data)
    await state.set_state(KompWorkState.uchet)
    await callback.message.edit_text(text='Выберите тип действия',
                                     reply_markup=kb.tovar_uchet_keyboard)


@router.callback_query(F.data.startswith('uchet_'), KompWorkState.uchet)
async def tovar_uchet(callback: CallbackQuery, state: FSMContext):
    await callback.answer(callback.data)
    u_type = callback.data.split('_')[1]
    await state.update_data(uchet=u_type)
    await state.update_data(type='get_date')
    await callback.message.edit_text(text='Введите дату и время',
                                     reply_markup=kb.cancel_keyboard)


@router.message(F.text, KompWorkState.uchet, KomponentTypeFilter('type', 'get_date'))
async def get_datetime_uchet(message: Message, state: FSMContext):
    await state.update_data(date=message.text)
    await state.update_data(type='get_koll_tovar')
    await message.answer(text='Введите количество товара', reply_markup=kb.cancel_keyboard)


@router.message(F.text, KompWorkState.uchet, KomponentTypeFilter('type', 'get_koll_tovar'))
async def get_koll_uchet(message: Message, state: FSMContext):
    koll = message.text
    if koll.isdigit():
        state_data = await state.get_data()
        sklad_id = state_data['sklad']
        grup_id = state_data['grup']
        tovar_id = state_data['tovar']
        uchet_type = state_data['uchet']
        datetime = state_data['date']
        user = await db.get_user(message.from_user.id)
        await state.clear()
        await state.set_state(KompWorkState.tovar)
        await state.update_data(sklad=sklad_id, grup=grup_id)
        await db.set_uchet(sklad_id=sklad_id, grup_id=grup_id, tovar_id=tovar_id, action=uchet_type, tovar_koll=koll,
                           date=datetime, worker_id=user['id'])

        await message.answer(text=f'Произошёл учёт', reply_markup=await kb.tovar_grup_list_keyboard(grup_id))
