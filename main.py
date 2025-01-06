import datetime
import os
import asyncio
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

from handlers import *

from dotenv import load_dotenv

from database.model import db_main
import database as db

load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")

bot = Bot(token=BOT_TOKEN,
          default=DefaultBotProperties(parse_mode=ParseMode.HTML))

# Настраиваем APScheduler
scheduler = AsyncIOScheduler()

# Запускаем задачу каждый день в 00:01
scheduler.add_job(db.check_subscriptions, CronTrigger(hour=0, minute=1))


async def main():
    await db_main()

    dp = Dispatcher()
    dp.startup.register(startup)
    dp.shutdown.register(shutdown)

    dp.include_router(payment_router)
    dp.include_router(base_router)
    dp.include_router(otchet_router)
    dp.include_router(komponent_router)
    dp.include_router(workers_router)
    dp.include_router(support_router)

    # Запуск планировщика
    scheduler.start()

    await dp.start_polling(bot)


async def startup(dispatcher: Dispatcher):
    print('Starting up...')


async def shutdown(dispatcher: Dispatcher):
    print('Shutting down...')


if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
