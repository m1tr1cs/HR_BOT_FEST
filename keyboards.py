from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

# def back_keyboard():
#     return ReplyKeyboardMarkup(keyboard=[[KeyboardButton(text="🔙 Назад")]], resize_keyboard=True)

def phone_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📱 Поділитися номером", request_contact=True)]
        ],
        resize_keyboard=True, one_time_keyboard=True
    )

# def interest_keyboard():
#     return ReplyKeyboardMarkup(
#         keyboard=[
#             [KeyboardButton(text="Робота"), KeyboardButton(text="Про нас")]
#         ],
#         resize_keyboard=True
#     )
#New keyboard for positions
def positions_keyboard(positions: list[str]) -> ReplyKeyboardMarkup:
    buttons = [KeyboardButton(text=pos) for pos in positions]
    keyboard = [[btn] for btn in buttons] + [[KeyboardButton(text="🔙 Назад")]]
    return ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True)


#new keyboard for inline_position
def positions_inline_keyboard(positions):
    # Розбиваємо список по 2 елементи для рядів
    keyboard = []
    row = []
    for idx, pos in enumerate(positions, 1):
        row.append(InlineKeyboardButton(text=pos, callback_data=f"position_{pos}"))
        if idx % 2 == 0:
            keyboard.append(row)
            row = []
    if row:  # Додаємо останній ряд, якщо елементів непарна кількість
        keyboard.append(row)
    keyboard.append([InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_interest")])
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


#inline buttom Робота, Про нас
def interest_inline_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="Робота", callback_data="interest_job"),
            InlineKeyboardButton(text="Про нас", callback_data="interest_about")
        ]
    ])