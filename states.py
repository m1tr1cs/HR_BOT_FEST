from aiogram.fsm.state import StatesGroup, State

class Form(StatesGroup):
    waiting_for_name = State()
    waiting_for_phone = State()
    waiting_for_age = State()
    choosing_interest = State()
    choosing_position = State()
    waiting_for_about_text = State()
    choosing_city = State()
    choosing_market = State()
    choosing_vacancy = State()
    editing_vacancy = State()