from aiogram.fsm.state import StatesGroup, State


class Form(StatesGroup):
    waiting_for_name = State()
    waiting_for_phone = State()
    waiting_for_age = State()
    choosing_interest = State()
    choosing_position = State()
    waiting_for_about_text = State()

    # Для HR-панелі
    choosing_city = State()
    choosing_market = State()
    choosing_vacancy = State()
    editing_vacancy = State()

    # Нові стани для перегляду всіх вакансій
    choosing_all_cities = State()
    choosing_markets = State()

    # Для пагінації відгуків
    admin_feedback_page = State()
    waiting_for_resume = State()
