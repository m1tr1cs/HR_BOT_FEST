from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

def back_keyboard():
    return ReplyKeyboardMarkup(keyboard=[[KeyboardButton(text="🔙 Назад")]], resize_keyboard=True)

def phone_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📱 Поділитися номером", request_contact=True)]
        ],
        resize_keyboard=True, one_time_keyboard=True
    )

def interest_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Робота"), KeyboardButton(text="Про нас")]
        ],
        resize_keyboard=True
    )
