from datetime import date, timedelta

from .model import async_session
from .model import User, Sklad, Grup, Tovar, Full, Owner_worker_association, Grup_tovar_association
from sqlalchemy import select, update, delete


async def get_user(tg_id):
    async with async_session() as session:
        async with session.begin():
            user = await session.scalar(select(User).where(User.tg_id == tg_id))
            if user is None:
                return None
            user = user.__dict__
            user = {'id': user['id'], 'tg_id': user['tg_id'], 'number': user['number'], 'name': user['name'],
                    'google_sheet_id': user['google_sheet_id'], 'subscription_status': user['subscription_status'],
                    'subscription_end_date': user['subscription_end_date']}
            return user


async def get_user_by_id(user_id):
    async with async_session() as session:
        async with session.begin():
            user = await session.scalar(select(User).where(User.id == user_id))
            if user is None:
                return None
            user = user.__dict__
            user = {'id': user['id'], 'tg_id': user['tg_id'], 'number': user['number'], 'name': user['name'],
                    'google_sheet_id': user['google_sheet_id'], 'subscription_status': user['subscription_status'],
                    'subscription_end_date': user['subscription_end_date']}
            return user


async def add_user(tg_id, number, name):
    async with async_session() as session:
        async with session.begin():
            user = await session.scalar(select(User).where(User.tg_id == tg_id))
            end_date = date.today() + timedelta(days=3)
            if user is None:
                session.add(User(tg_id=tg_id, number=number, name=name, google_sheet_id='',
                                 subscription_status='active', subscription_end_date=end_date))
            else:
                await session.execute(update(User).where(User.id == user.id)
                                      .values(number=number, name=name, subscription_status='active',
                                              subscription_end_date=end_date))
            await session.commit()


async def set_google_sheet_id(google_sheet_id, user_id):
    async with async_session() as session:
        async with session.begin():
            await session.execute(update(User).where(User.id == user_id).values(google_sheet_id=google_sheet_id))
            await session.commit()


async def add_subscription_time(user_id):
    async with async_session() as session:
        async with session.begin():
            user = await get_user_by_id(user_id=user_id)
            past_date = user['subscription_end_date']
            today = date.today()
            if past_date < today:
                end_date = today + timedelta(days=30)
            else:
                end_date = past_date + timedelta(days=30)
            await session.execute(update(User).where(User.id == user['id']).values(subscription_status='active',
                                                                                subscription_end_date=end_date))
            await session.commit()


# Функция для проверки статусов подписок
async def check_subscriptions():
    async with async_session() as session:
        async with session.begin():
            # Получаем всех пользователей с истёкшей подпиской
            result = await session.execute(
                select(User).where(User.subscription_end_date < date.today(), User.subscription_status == "active")
            )
            users = result.scalars().all()
            for user in users:

                user.subscription_status = "passive"  # Деактивируем подписку
            await session.commit()


async def get_owner(user_id):
    async with async_session() as session:
        async with session.begin():
            result = await session.scalars(select(Owner_worker_association)
                                           .where(Owner_worker_association.worker_id == user_id))
            if result is None:
                return None
            owners = [owner.__dict__ for owner in result]
            owner_list = []
            for owner in owners:
                owner_list.append({'id': owner['id'], 'owner_id': owner['owner_id'], 'worker_id': owner['worker_id']})
            return owner_list


async def get_workers(user_id):
    async with async_session() as session:
        async with session.begin():
            result = await session.scalars(select(Owner_worker_association)
                                           .where(Owner_worker_association.owner_id == user_id))
            if result is None:
                return None
            workers = [owner.__dict__ for owner in result]
            worker_list = []
            for worker in workers:
                worker_list.append({'id': worker['id'], 'owner_id': worker['owner_id'],
                                    'worker_id': worker['worker_id']})
            return worker_list


async def get_sklads(owner_id):
    async with async_session() as session:
        async with session.begin():
            result = await session.execute(select(Sklad).where(Sklad.owner_id == owner_id))
            if result is None:
                return None
            sklads = result.scalars().all()
            sklads_data = [sklad.__dict__ for sklad in sklads]
            sklad_list = []
            for sklad in sklads_data:
                sklad_list.append({'id': sklad['id'], 'name': sklad['name'], 'owner_id': sklad['owner_id']})
            return sklad_list


async def get_sklad_by_id(sklad_id):
    async with async_session() as session:
        async with session.begin():
            sklad = await session.scalar(select(Sklad).where(Sklad.id == sklad_id))
            if sklad is None:
                return None
            sklad = sklad.__dict__
            sklad = {'id': sklad['id'], 'name': sklad['name'], 'owner_id': sklad['owner_id']}
            return sklad


async def add_sklad(owner_id, name):
    async with async_session() as session:
        async with session.begin():
            session.add(Sklad(name=name, owner_id=owner_id))
            await session.commit()


async def change_sklad(sklad_id, name):
    async with async_session() as session:
        async with session.begin():
            await session.execute(update(Sklad).where(Sklad.id == sklad_id).values(name=name))
            await session.commit()


async def get_grups_by_sklad(sklad_id):
    async with async_session() as session:
        async with session.begin():
            result = await session.execute(select(Grup)
                                           .join(Sklad, Sklad.id == Grup.sklad_id).where(Sklad.id == sklad_id))
            grups = result.scalars().all()
            grups_data = [grup.__dict__ for grup in grups]
            grup_list = []
            for grup in grups_data:
                grup_list.append({'id': grup['id'], 'sklad_id': grup['sklad_id'], 'name': grup['name']})
            return grup_list


async def add_grup(sklad_id, name):
    async with async_session() as session:
        async with session.begin():
            session.add(Grup(sklad_id=sklad_id, name=name))
            await session.commit()


async def change_grup(grup_id, name):
    async with async_session() as session:
        async with session.begin():
            await session.execute(update(Grup).where(Grup.id == grup_id).values(name=name))
            await session.commit()


async def get_tovars(owner_id):
    async with async_session() as session:
        async with session.begin():
            result = await session.execute(select(Tovar).where(Tovar.owner_id == owner_id))
            if result is None:
                return None
            tovars = result.scalars().all()
            tovars_data = [tovar.__dict__ for tovar in tovars]
            tovar_list = []
            for tovar in tovars_data:
                tovar_list.append({'id': tovar['id'], 'owner_id': tovar['owner_id'], 'name': tovar['name'],
                                   'photo_id': tovar['photo_id'], 'description': tovar['description'],
                                   'information': tovar['information'], 'size': tovar['size'],
                                   'weight': tovar['weight'], 'izmerenie': tovar['izmerenie']})
            return tovar_list


async def get_tovar_by_id(tovar_id):
    async with async_session() as session:
        async with session.begin():
            tovar = await session.scalar(select(Tovar).where(Tovar.id == tovar_id))
            if tovar is None:
                return None
            tovar = tovar.__dict__
            tovar = {'id': tovar['id'], 'owner_id': tovar['owner_id'], 'name': tovar['name'],
                     'photo_id': tovar['photo_id'], 'description': tovar['description'],
                     'information': tovar['information'], 'size': tovar['size'], 'weight': tovar['weight'],
                     'izmerenie': tovar['izmerenie']}
            return tovar


async def get_tovar_by_grup(grup_id):
    async with async_session() as session:
        async with session.begin():
            tovars = await session.scalars(select(Tovar)
                                           .join(Grup_tovar_association, Grup_tovar_association.tovar_id == Tovar.id)
                                           .where(Grup_tovar_association.grup_id == grup_id))
            if tovars is None:
                return None
            tovars = [tovar.__dict__ for tovar in tovars]
            tovar_list = []
            for tovar in tovars:
                tovar_list.append({'id': tovar['id'], 'owner_id': tovar['owner_id'], 'name': tovar['name'],
                                   'photo_id': tovar['photo_id'], 'description': tovar['description'],
                                   'information': tovar['information'], 'size': tovar['size'],
                                   'weight': tovar['weight'],
                                   'izmerenie': tovar['izmerenie']})
            return tovar_list


async def add_tovar(grup_id, owner_id, name, photo_id, description, information, size, weight, izmerenie):
    async with async_session() as session:
        async with session.begin():
            new_tovar = Tovar(name=name, owner_id=owner_id, photo_id=photo_id, description=description,
                              information=information, size=size, weight=weight, izmerenie=izmerenie)
            session.add(new_tovar)
            await session.flush()
            if grup_id:
                session.add(Grup_tovar_association(grup_id=grup_id, tovar_id=new_tovar.id))
            await session.commit()


# async def change_tovar(tovar_id, name, photo_id, description, information, size, weight, izmerenie):
#     async with async_session() as session:
#         async with session.begin():
#             if name:
#                 await session.execute(update(Tovar).where(Tovar.id == tovar_id).values(name=name))
#                 await session.commit()
#             if photo_id:
#                 await session.execute(update(Tovar).where(Tovar.id == tovar_id).values(photo_id=photo_id))
#                 await session.commit()
#             if description:
#                 await session.execute(update(Tovar).where(Tovar.id == tovar_id).values(description=description))
#                 await session.commit()
#             if information:
#                 await session.execute(update(Tovar).where(Tovar.id == tovar_id).values(information=information))
#                 await session.commit()
#             if size:
#                 await session.execute(update(Tovar).where(Tovar.id == tovar_id).values(size=size))
#                 await session.commit()
#             if weight:
#                 await session.execute(update(Tovar).where(Tovar.id == tovar_id).values(weight=weight))
#                 await session.commit()
#             if izmerenie:
#                 await session.execute(update(Tovar).where(Tovar.id == tovar_id).values(izmerenie=izmerenie))
#                 await session.commit()
async def change_tovar(tovar_id, name, photo_id, description, information, size, weight, izmerenie):
    async with async_session() as session:
        async with session.begin():  # Открываем транзакцию
            # Подготавливаем словарь с полями для обновления
            update_values = {}
            if name:
                update_values['name'] = name
            if photo_id:
                update_values['photo_id'] = photo_id
            if description:
                update_values['description'] = description
            if information:
                update_values['information'] = information
            if size:
                update_values['size'] = size
            if weight:
                update_values['weight'] = weight
            if izmerenie:
                update_values['izmerenie'] = izmerenie

            # Выполняем обновление только если есть изменения
            if update_values:
                await session.execute(
                    update(Tovar)
                    .where(Tovar.id == tovar_id)
                    .values(**update_values)
                )
            await session.commit()


async def add_tovar_grup_assotiation(grup_id, tovar_id):
    async with async_session() as session:
        async with session.begin():
            session.add(Grup_tovar_association(grup_id=grup_id, tovar_id=tovar_id))
            await session.commit()


async def add_owner_worker_assotiation(owner_id, worker_id):
    async with async_session() as session:
        async with session.begin():
            session.add(Owner_worker_association(owner_id=owner_id, worker_id=worker_id))
            await session.commit()


async def delete_owner_worker_assotiation(owner_id, worker_id):
    async with async_session() as session:
        async with session.begin():
            session.execute(delete(Owner_worker_association).where(Owner_worker_association.owner_id == owner_id,
                                                                   Owner_worker_association.worker_id == worker_id))
            await session.commit()


async def delete_komponent(komponent, komponent_id, komponent2_id=None):
    async with async_session() as session:
        async with session.begin():
            match komponent:
                case 'sklad':
                    # Удаляем все записи из Grup_tovar_association, связанные со sklad через Grup
                    grup_ids_subquery = select(Grup.id).where(Grup.sklad_id == komponent_id)
                    await session.execute(delete(Grup_tovar_association)
                                          .where(Grup_tovar_association.grup_id.in_(grup_ids_subquery)))
                    # Удаляем все записи из Grup, связанные с sklad
                    await session.execute(delete(Grup).where(Grup.sklad_id == komponent_id))
                    # Удаляем сам sklad
                    await session.execute(delete(Sklad).where(Sklad.id == komponent_id))

                case 'grup':
                    # Удаляем все записи из Grup_tovar_association, связанные с grup
                    await session.execute(delete(Grup_tovar_association)
                                          .where(Grup_tovar_association.grup_id == komponent_id))
                    # Удаляем сам grup
                    await session.execute(delete(Grup).where(Grup.id == komponent_id))

                case 'grup_tovar_ship':
                    # Удаляем все записи из Grup_tovar_association, связанные с tovar
                    await session.execute(delete(Grup_tovar_association)
                                          .where(Grup_tovar_association.tovar_id == komponent_id,
                                                 Grup_tovar_association.grup_id == komponent2_id))

                case 'tovar':
                    # Удаляем все записи из Grup_tovar_association, связанные с tovar
                    await session.execute(delete(Grup_tovar_association)
                                          .where(Grup_tovar_association.tovar_id == komponent_id))
                    # Удаляем сам tovar
                    await session.execute(delete(Tovar).where(Tovar.id == komponent_id))


async def set_uchet(sklad_id, grup_id, action, date, tovar_id, tovar_koll, worker_id):
    async with async_session() as session:
        async with session.begin():
            sklad = await get_sklad_by_id(sklad_id=sklad_id)
            owner_id = sklad['owner_id']
            session.add(Full(owner_id=owner_id, sklad_id=sklad_id, grup_id=grup_id, action=action, date=date,
                             tovar_id=tovar_id, tovar_koll=tovar_koll, worker_id=worker_id))


async def get_full(owner_id):
    async with async_session() as session:
        async with session.begin():
            result = await session.scalars(select(Full).where(Full.owner_id == owner_id))
            if result is None:
                return None
            fulls = [full.__dict__ for full in result]
            full_list = []
            for full in fulls:
                full_list.append({'id': full['id'], 'owner_id': full['owner_id'], 'sklad_id': full['sklad_id'],
                                  'grup_id': full['grup_id'], 'date': full['date'], 'action': full['action'],
                                  'tovar_id': full['tovar_id'], 'tovar_koll': full['tovar_koll'],
                                  'worker_id': full['worker_id']})
            return full_list

