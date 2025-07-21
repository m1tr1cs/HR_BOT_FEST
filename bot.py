from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from config import BOT_TOKEN
from handlers.user import user_router
from handlers.jobs import jobs_router

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(storage=MemoryStorage())

dp.include_router(user_router)
dp.include_router(jobs_router)


if __name__ == "__main__":
    import asyncio
    from utils.sheets import load_vacancies_from_sheet
    load_vacancies_from_sheet()
    try:
        asyncio.run(dp.start_polling(bot))
    except (KeyboardInterrupt, SystemExit):
        pass
#test