from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


def phone_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📱 Поділитися номером", request_contact=True)]
        ],
        resize_keyboard=True, one_time_keyboard=True
    )


def main_menu_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🏠 Головне меню", callback_data="back_to_interest")],
        [InlineKeyboardButton(text="📝 Редагувати дані", callback_data="edit_user_data")]
    ])


def positions_keyboard(positions: list[str]) -> ReplyKeyboardMarkup:
    buttons = [KeyboardButton(text=pos) for pos in positions]
    keyboard = [[btn] for btn in buttons] + [[KeyboardButton(text="🔙 Назад")]]
    return ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True)


# new keyboard for inline_position
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


def interest_inline_keyboard(show_edit_button=False, show_feedback_button=False, show_admin_button=False):
    buttons = [
        [
            InlineKeyboardButton(text="Робота", callback_data="interest_job"),
            InlineKeyboardButton(text="Про нас", callback_data="interest_about")
        ]
    ]
    if show_edit_button:
        buttons.append([InlineKeyboardButton(text="📝 Редагувати дані", callback_data="edit_user_data")])
    if show_feedback_button:
        buttons.append([InlineKeyboardButton(text="📄 Мої відгуки", callback_data="view_feedback")])
    if show_admin_button:
        buttons.append([InlineKeyboardButton(text="🛠 HR-панель", callback_data="admin_panel")])

    return InlineKeyboardMarkup(inline_keyboard=buttons)


def cancel_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="❌ Скасувати")]],
        resize_keyboard=True,
        one_time_keyboard=True
    )


def back_to_interest_keyboard(show_edit=False, show_feedback=False):
    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

    buttons = [
        [InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_interest")]
    ]

    if show_edit:
        buttons.insert(0, [InlineKeyboardButton(text="📝 Редагувати дані", callback_data="edit_user_data")])
    if show_feedback:
        buttons.insert(0, [InlineKeyboardButton(text="📄 Мої відгуки", callback_data="view_feedback")])

    return InlineKeyboardMarkup(inline_keyboard=buttons)


def admin_panel_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✏️ Редагувати «Про нас»", callback_data="admin_edit_about")],
        [InlineKeyboardButton(text="🗂 Редагувати вакансії", callback_data="admin_edit_vacancies")],
        [InlineKeyboardButton(text="📄 Всі відгуки", callback_data="admin_view_feedbacks")],
        [InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_interest")]
    ])
