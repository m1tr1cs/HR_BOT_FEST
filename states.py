from aiogram.fsm.state import StatesGroup, State

class Form(StatesGroup):
    waiting_for_name = State()
    waiting_for_phone = State()
    waiting_for_age = State()
    choosing_interest = State()
    choosing_position = State()
