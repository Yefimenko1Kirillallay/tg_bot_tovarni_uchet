from sqlalchemy import ForeignKey, String, BigInteger, Boolean, Integer, Date
from sqlalchemy.ext.asyncio import AsyncAttrs, async_sessionmaker, create_async_engine
from sqlalchemy.orm import Mapped, mapped_column, DeclarativeBase, relationship
import os
import logging
import asyncio
import datetime
from datetime import date
import aiosqlite
import greenlet

from dotenv import load_dotenv

# Включаем логирование
logging.basicConfig()
logging.getLogger('sqlalchemy.engine').setLevel(logging.INFO)

load_dotenv()

DB_URL = os.getenv('DB_URL')

engine = create_async_engine(url=DB_URL, echo=False)
async_session = async_sessionmaker(engine)


class Base(AsyncAttrs, DeclarativeBase):
    pass


class User(Base):
    __tablename__ = 'users'
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    tg_id: Mapped[int] = mapped_column(BigInteger, nullable=False, unique=True)
    number: Mapped[str] = mapped_column(String(13))
    name: Mapped[str] = mapped_column(String(20))
    google_sheet_id: Mapped[str] = mapped_column()
    subscription_status: Mapped[str] = mapped_column(String(7), nullable=False)
    subscription_end_date: Mapped[date] = mapped_column(Date, nullable=False)

    # Используем back_populates для связи с ассоциацией Sklad_user_association
    user_sklad_ship = relationship('Sklad', back_populates='sklad_user_ship')
    owner_worker_ship = relationship('Owner_worker_association',
                                     back_populates='worker_owner_ship',
                                     foreign_keys='Owner_worker_association.worker_id')
    owner_tovar_ship = relationship('Tovar', back_populates='tovar_owner_ship')
    F_user_ship = relationship('Full', back_populates='user_full_ship')


class Owner_worker_association(Base):
    __tablename__ = 'owner_worker_associations'
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    owner_id: Mapped[int] = mapped_column(ForeignKey('users.id'), nullable=False)
    worker_id: Mapped[int] = mapped_column(ForeignKey('users.id'), nullable=False)

    worker_owner_ship = relationship('User',
                                     back_populates='owner_worker_ship',
                                     foreign_keys=[worker_id])
    owner_user_ship = relationship('User',
                                   foreign_keys=[owner_id])


class Sklad(Base):
    __tablename__ = 'sklads'
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(20), nullable=False, unique=True)
    owner_id: Mapped[int] = mapped_column(ForeignKey('users.id'), nullable=False)

    # Используем back_populates для связи с ассоциацией Sklad_user_association
    sklad_user_ship = relationship('User', back_populates='user_sklad_ship')
    sklad_grup_ship = relationship('Grup', back_populates='grup_sklad_ship')
    full_sklad_ship = relationship('Full', back_populates='sklad_full_ship', primaryjoin="Sklad.id == Full.sklad_id")


class Grup(Base):
    __tablename__ = 'grups'
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    sklad_id: Mapped[int] = mapped_column(ForeignKey('sklads.id'), nullable=False)
    name: Mapped[str] = mapped_column(String(20), nullable=False, unique=True)

    grup_sklad_ship = relationship("Sklad", back_populates="sklad_grup_ship")
    grup_associations_ship = relationship('Grup_tovar_association', back_populates='associations_grup_ship',
                                          primaryjoin="Grup.id == Grup_tovar_association.grup_id")
    full_grup_ship = relationship("Full", back_populates="grup_full_ship",
                                  primaryjoin="Grup.id == Full.grup_id")


class Tovar(Base):
    __tablename__ = 'tovars'
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    owner_id: Mapped[int] = mapped_column(ForeignKey('users.id'), nullable=False)
    name: Mapped[str] = mapped_column(String(20), nullable=False)
    photo_id: Mapped[int] = mapped_column()
    description: Mapped[str] = mapped_column(String(20))
    information: Mapped[str] = mapped_column(String(20))
    size: Mapped[str] = mapped_column(String(10))
    weight: Mapped[str] = mapped_column(String(10))
    izmerenie: Mapped[str] = mapped_column(String(20))
    
    tovar_owner_ship = relationship('User', back_populates='owner_tovar_ship')
    full_tovar_ship = relationship("Full", back_populates="tovar_full_ship",
                                   primaryjoin="Tovar.id == Full.tovar_id")
    tovar_associations_ship = relationship('Grup_tovar_association', back_populates='associations_tovar_ship',
                                           primaryjoin="Tovar.id == Grup_tovar_association.tovar_id")


class Grup_tovar_association(Base):
    __tablename__ = 'grup_tovar_associations'
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    grup_id: Mapped[int] = mapped_column(ForeignKey('grups.id'), nullable=False)
    tovar_id: Mapped[int] = mapped_column(ForeignKey('tovars.id'), nullable=False)

    associations_grup_ship = relationship('Grup', back_populates='grup_associations_ship',
                                          primaryjoin="Grup.id == Grup_tovar_association.grup_id")
    associations_tovar_ship = relationship('Tovar', back_populates='tovar_associations_ship',
                                           primaryjoin="Tovar.id == Grup_tovar_association.tovar_id")


class Full(Base):
    __tablename__ = "fulls"
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    owner_id: Mapped[int] = mapped_column(ForeignKey('users.id'), nullable=False)
    sklad_id: Mapped[int] = mapped_column(ForeignKey('sklads.id'), nullable=False)
    grup_id: Mapped[int] = mapped_column(ForeignKey('grups.id'), nullable=False)
    date: Mapped[str] = mapped_column(String(12), nullable=False)
    action: Mapped[str] = mapped_column(String(12), nullable=False)
    tovar_id: Mapped[int] = mapped_column(ForeignKey('tovars.id'), nullable=False)
    tovar_koll: Mapped[int] = mapped_column(nullable=False)
    worker_id: Mapped[int] = mapped_column(nullable=False)

    user_full_ship = relationship('User', back_populates='F_user_ship')
    sklad_full_ship = relationship('Sklad', back_populates='full_sklad_ship', primaryjoin="Sklad.id == Full.sklad_id")
    grup_full_ship = relationship('Grup', back_populates='full_grup_ship', primaryjoin="Grup.id == Full.grup_id")
    tovar_full_ship = relationship('Tovar', back_populates='full_tovar_ship')


async def db_main():
    async with engine.begin() as conn:
        # Попробуйте явно создать таблицы
        await conn.run_sync(Base.metadata.create_all)
