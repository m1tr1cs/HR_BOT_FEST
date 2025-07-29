from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from config import BOT_TOKEN
from handlers.user import user_router
from handlers.jobs import jobs_router
from utils.db import init_db

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(storage=MemoryStorage())

dp.include_router(user_router)
dp.include_router(jobs_router)

if __name__ == "__main__":
    import asyncio


    async def main():
        init_db()
        await dp.start_polling(bot)


    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        pass
