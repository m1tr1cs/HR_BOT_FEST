from aiogram import Router, F
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, ReplyKeyboardRemove, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from states import Form
import logging
import re
from keyboards import interest_inline_keyboard, phone_keyboard, cancel_keyboard, back_to_interest_keyboard, \
    admin_panel_keyboard
from utils.db import  is_admin, get_chat_id_by_phone, remove_admin, get_user_profile
from aiogram.filters import Command
from utils.db import set_admin

user_router = Router()


@user_router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext):
    logging.info(f"User {message.from_user.id} started bot")

    await state.clear()

    chat_id = message.from_user.id
    user_data = get_user_profile(chat_id)  # <--- замість get_candidate_by_chat_id

    if user_data:
        await state.update_data(**user_data)

    if user_data:
        await state.update_data(**user_data)
        await message.answer(
            f"""👋 Привіт знову, {user_data['name']}!

Твої поточні дані:
👤 Ім'я: {user_data['name']}
📱 Телефон: {user_data['phone']}
🎂 Вік: {user_data['age']}
""", reply_markup=ReplyKeyboardRemove())
        is_admin_user = is_admin(chat_id)
        await message.answer(
            "🔎 Обери, що тебе цікавить:",
            reply_markup=interest_inline_keyboard(
                show_edit_button=True,
                show_feedback_button=True,
                show_admin_button=is_admin_user
            )
        )
        await state.set_state(Form.choosing_interest)
        return

    # якщо користувача ще немає в базі
    await message.answer("👋 Привіт! Як до тебе звертатись?", reply_markup=ReplyKeyboardRemove())
    await state.set_state(Form.waiting_for_name)


@user_router.message(Form.waiting_for_name)
async def process_name_or_cancel(message: Message, state: FSMContext):
    text = message.text.strip()

    if text == "❌ Скасувати":
        data = await state.get_data()
        show_edit = all(data.get(k) for k in ["name", "phone", "age"])

        await message.answer("🔎 Чудово! Обери, що тебе цікавить:",
                             reply_markup=ReplyKeyboardRemove())
        await message.answer("⬇️ Обери дію:",
                             reply_markup=interest_inline_keyboard(show_edit_button=show_edit))

        await state.set_state(Form.choosing_interest)
        return

    # якщо не "Скасувати" — обробляємо як ім’я
    if not re.match(r"^[A-Za-zА-Яа-яІіЇїЄєҐґʼ'\- ]+$", text):
        await message.answer(
            "❗ Будь ласка, введи ім’я лише літерами (українською або латиницею), без цифр та спеціальних символів.")
        return

    await state.update_data(name=text)
    await message.answer(
        "📞 Тепер поділись своїм номером телефону або введи його вручну:",
        reply_markup=phone_keyboard()
    )
    await state.set_state(Form.waiting_for_phone)


@user_router.message(Form.waiting_for_phone, F.contact)
async def process_phone_contact(message: Message, state: FSMContext):
    await state.update_data(phone=message.contact.phone_number)
    await message.answer(
        "📅 Введи свій вік (лише цифри, наприклад: 25):",
        reply_markup=ReplyKeyboardRemove()
    )
    await state.set_state(Form.waiting_for_age)


@user_router.message(Form.waiting_for_phone)
async def process_phone_text(message: Message, state: FSMContext):
    phone = message.text.strip()
    import re
    if not re.match(r"^\+?\d{10,15}$", phone):
        await message.answer("❗ Неправильний формат номера. Спробуй ще раз (наприклад, +380XXXXXXXXX):")
        return
    await state.update_data(phone=phone)
    await message.answer(
        "📅 Введи свій вік (лише цифри, наприклад: 25):",
        reply_markup=ReplyKeyboardRemove()
    )
    await state.set_state(Form.waiting_for_age)


@user_router.message(Form.waiting_for_resume)
async def process_resume(message: Message, state: FSMContext):
    data = await state.get_data()
    resume_link = None

    if message.document:
        resume_link = message.document.file_id
    elif message.text and (message.text.startswith("http://") or message.text.startswith("https://")):
        resume_link = message.text.strip()
    elif message.text and message.text.lower() == "пропустити":
        resume_link = data.get("resume_link")
    else:
        await message.answer("Будь ласка, надішли файл (pdf/docx) або лінк (Google Drive/Docs), або напиши 'Пропустити'.")
        return

    await state.update_data(resume_link=resume_link)

    # !!! ЗБЕРІГАЄМО В USERS:
    from utils.db import update_resume_link
    update_resume_link(message.from_user.id, resume_link)

    await message.answer(
        "🔎 Чудово! Обери, що тебе цікавить:",
        reply_markup=interest_inline_keyboard()
    )
    await state.set_state(Form.choosing_interest)



# @user_router.message(Form.waiting_for_age)
# async def process_age(message: Message, state: FSMContext):
#     if not message.text or not message.text.isdigit():
#         await message.answer("📅 Введи свій вік (лише цифри, наприклад: 25):")
#         return
#     age = int(message.text)
#     if not 16 <= age <= 55:
#         await message.answer("Нажаль, ми розглядаємо кандидатів віком від 16 до 55 років.")
#         return
#     await state.update_data(age=str(age))
#     # *** Додаємо новий етап ***
#     await message.answer(
#         "🔗 Надішли файл резюме (pdf, docx) або посилання на Google Drive/Docs:",
#         reply_markup=ReplyKeyboardRemove()
#     )
#     await state.set_state(Form.waiting_for_resume)
#
#
# from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


@user_router.callback_query(F.data == "edit_user_data")
async def edit_user_data(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    resume_link = data.get("resume_link")
    resume_text = ""
    buttons = [[InlineKeyboardButton(text="❌ Скасувати", callback_data="back_to_interest")]]

    # Якщо прикріплений файл резюме — додати кнопку для перегляду
    if resume_link:
        if resume_link.startswith("BQAC"):
            resume_text = "\n📄 Поточний файл резюме прикріплений."
            buttons.insert(0,
                           [InlineKeyboardButton(text="👁 Переглянути файл резюме", callback_data="view_resume_file")])
        else:
            resume_text = f"\n🔗 Поточне резюме: {resume_link}"

    await callback.message.answer(
        f"""Твої поточні дані:
👤 Ім'я: {data.get('name')}
📱 Телефон: {data.get('phone')}
🎂 Вік: {data.get('age')}
{resume_text}

✏️ Введи нове ім’я (або натисни “❌ Скасувати”):""",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons)
    )
    await state.set_state(Form.waiting_for_name)
    await callback.answer()


@user_router.callback_query(F.data == "view_resume_file")
async def view_resume_file(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    resume_link = data.get("resume_link")
    if resume_link and resume_link.startswith("BQAC"):
        await callback.message.answer_document(resume_link)
    else:
        await callback.message.answer("Файл не знайдено.")
    await callback.answer()


@user_router.callback_query(F.data.in_(["interest_job", "interest_about"]), Form.choosing_interest)
async def process_interest_inline(callback: CallbackQuery, state: FSMContext):
    text = callback.data

    data = await state.get_data()
    show_edit = all(data.get(k) for k in ["name", "phone", "age"])
    show_feedback = True

    if text == "interest_about":
        from utils.db import get_setting
        about_text = get_setting("about_text") or "🤷‍♀️ Розділ «Про нас» ще не заповнений."
        is_admin_user = is_admin(callback.from_user.id)

        # Генеруємо власну клаву з кнопкою Назад
        buttons = [
            [InlineKeyboardButton(text="⬅️ Назад", callback_data="back_to_interest")]
        ]

        await callback.message.answer(
            about_text,
            reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons)
        )
        await callback.answer()
        return

    if text == "interest_job":
        from utils.db import get_vacancies_for_age
        age = int(data.get("age", 0))
        vacancies = get_vacancies_for_age(age)

        if not vacancies:
            await callback.message.edit_text("😔 На жаль, зараз немає відкритих вакансій для вашої вікової категорії.",
                                             reply_markup=None)
            await state.clear()
            await callback.answer()
            return

        await state.update_data(vacancies=vacancies)
        unique_positions = sorted(list(set(v['position'] for v in vacancies if 'position' in v)))

        from keyboards import positions_inline_keyboard
        await callback.message.edit_text(
            "Чудово! Обери посаду, яка тебе цікавить:",
            reply_markup=positions_inline_keyboard(unique_positions)
        )
        await state.set_state(Form.choosing_position)
        await callback.answer()


@user_router.callback_query(F.data == "view_feedback")
async def view_user_feedback(callback: CallbackQuery, state: FSMContext):
    from utils.db import get_user_feedbacks
    feedbacks = get_user_feedbacks(callback.from_user.id)

    if not feedbacks:
        await callback.message.answer("😔 Ви ще не надсилали жодного відгуку.")
        await callback.answer()
        return

    for row in feedbacks:
        record_id, job_description, created_at = row
        await callback.message.answer(
            f"📌 {job_description}\n🕒 {created_at}",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[[
                InlineKeyboardButton(text="❌ Скасувати відгук", callback_data=f"cancel_feedback_{record_id}")
            ]])
        )
    await callback.message.answer("⬅️ Повернутись назад:",
                                  reply_markup=back_to_interest_keyboard(show_edit=False, show_feedback=True))


@user_router.callback_query(F.data.startswith("cancel_feedback_"))
async def cancel_feedback(callback: CallbackQuery, state: FSMContext):
    record_id = int(callback.data.split("_")[-1])
    from utils.db import delete_feedback
    delete_feedback(record_id, callback.from_user.id)
    await callback.message.edit_text("✅ Відгук успішно скасовано.")
    await callback.answer()

    # ID розробника, хто має право призначати адмінів


DEVELOPER_ID = 494176019  # 🔁 заміни на свій Telegram ID


@user_router.message(Command("makeadmin"))
async def handle_makeadmin_command(message: Message):
    # Перевірка, чи ти сам адмін
    from utils.db import is_admin
    if not is_admin(message.from_user.id):
        await message.answer("⛔️ У вас немає прав доступу до цієї команди.")
        return

    parts = message.text.strip().split()
    if len(parts) != 2:
        await message.answer("❗ Використання: /makeadmin +380XXXXXXXXX")
        return

    phone = parts[1]
    chat_id = get_chat_id_by_phone(phone)
    if not chat_id:
        await message.answer("😔 Користувача з таким номером не знайдено в базі.")
        return

    set_admin(chat_id)
    await message.answer(f"✅ Користувача з номером {phone} призначено адміністратором.")


@user_router.message(Command("removeadmin"))
async def handle_removeadmin_command(message: Message):
    from utils.db import is_admin
    if not is_admin(message.from_user.id):
        await message.answer("⛔️ У вас немає прав доступу до цієї команди.")
        return

    parts = message.text.strip().split()
    if len(parts) != 2:
        await message.answer("❗ Використання: /removeadmin +380XXXXXXXXX")
        return

    phone = parts[1]
    chat_id = get_chat_id_by_phone(phone)
    if not chat_id:
        await message.answer("😔 Користувача з таким номером не знайдено в базі.")
        return

    remove_admin(chat_id)
    await message.answer(f"✅ Роль адміністратора з номера {phone} успішно знято.")


# @user_router.message(Command("makeadmin"))


# async def make_admin_command(message: Message):
#     if message.from_user.id != DEVELOPER_ID:
#         await message.answer("❌ У вас немає прав для цієї команди.")
#         return
#
#     parts = message.text.split()
#     if len(parts) != 2 or not parts[1].isdigit():
#         await message.answer("🔧 Використання: /makeadmin <chat_id>")
#         return
#
#     chat_id = parts[1]
#     set_admin(chat_id)
#     await message.answer(f"✅ Користувач {chat_id} тепер адміністратор.")

@user_router.callback_query(F.data == "admin_panel")
async def admin_panel(callback: CallbackQuery, state: FSMContext):
    from utils.db import is_admin
    if not is_admin(callback.from_user.id):
        await callback.answer("У вас немає доступу до HR-панелі", show_alert=True)
        return

    await callback.message.answer("🛠 HR-панель — оберіть дію:", reply_markup=admin_panel_keyboard())
    await callback.answer()


@user_router.callback_query(F.data == "admin_edit_about")
async def admin_edit_about(callback: CallbackQuery, state: FSMContext):
    await callback.message.answer("✏️ Надішліть новий текст «Про нас».")
    await state.set_state(Form.waiting_for_about_text)
    await callback.answer()


@user_router.message(Form.waiting_for_about_text)
async def save_about_text(message: Message, state: FSMContext):
    text = message.text.strip()
    from utils.db import set_setting
    set_setting("about_text", text)

    await message.answer("✅ Опис «Про нас» оновлено.")
    await state.set_state(Form.choosing_interest)


@user_router.callback_query(F.data == "admin_view_feedbacks")
async def admin_view_feedbacks(callback: CallbackQuery, state: FSMContext):
    from utils.db import get_all_feedbacks
    feedbacks = get_all_feedbacks()

    if not feedbacks:
        await callback.message.answer("😔 Відгуків ще немає.")
        await callback.answer()
        return

    await state.update_data(feedbacks=feedbacks, feedback_page=0)
    await show_feedback_page(callback.message, state)
    await state.set_state(Form.admin_feedback_page)
    await callback.answer()


async def show_feedback_page(message: Message, state: FSMContext):
    data = await state.get_data()
    feedbacks = data.get("feedbacks", [])
    page = data.get("feedback_page", 0)
    per_page = 5

    start = page * per_page
    end = start + per_page
    page_feedbacks = feedbacks[start:end]

    if not page_feedbacks:
        await message.answer("📭 Більше відгуків немає.")
        return

    for fb in page_feedbacks:
        fid, name, phone, age, chat_id, job, created, checked, resume_link = fb
        status = "✅ Опрацьовано" if checked else "🕓 Не опрацьовано"

        msg = (
            f"👤 {name}, {age} років\n"
            f"📱 {phone}\n"
            f"📌 {job}\n"
            f"🕒 {created}\n"
            f"🆔 Chat ID: {chat_id}\n"
            f"📍 Статус: {status}"
        )

        buttons = []
        # ОНОВЛЕНО: кнопка на відкриття файлу через callback, а не url
        if resume_link:
            if resume_link.startswith('BQAC'):
                buttons.append(InlineKeyboardButton(
                    text="📄 Відкрити файл",
                    callback_data=f"admin_open_resume_{fid}"
                ))
            else:
                msg += f"\n🔗 Резюме: {resume_link}"

        if not checked:
            buttons.append(InlineKeyboardButton(text="✅ Опрацювати", callback_data=f"mark_checked_{fid}"))
        buttons.append(InlineKeyboardButton(text="❌ Видалити", callback_data=f"admin_delete_feedback_{fid}"))

        await message.answer(msg, reply_markup=InlineKeyboardMarkup(inline_keyboard=[buttons]))

    # Навігація
    nav_buttons = []
    if page > 0:
        nav_buttons.append(InlineKeyboardButton(text="⬅️ Назад", callback_data="feedback_prev"))
    if end < len(feedbacks):
        nav_buttons.append(InlineKeyboardButton(text="➡️ Далі", callback_data="feedback_next"))

    if nav_buttons:
        await message.answer("📄 Навігація по відгуках:",
                             reply_markup=InlineKeyboardMarkup(inline_keyboard=[nav_buttons]))

    # Додаємо кнопку Назад
    await message.answer(
        "⬅️ Повернутись в HR-панель:",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="⬅️ Назад", callback_data="back_to_admin")]
        ])
    )


@user_router.callback_query(F.data.in_(["feedback_next", "feedback_prev"]), Form.admin_feedback_page)
async def paginate_feedback(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    page = data.get("feedback_page", 0)

    if callback.data == "feedback_next":
        page += 1
    elif callback.data == "feedback_prev":
        page = max(0, page - 1)

    await state.update_data(feedback_page=page)
    await show_feedback_page(callback.message, state)
    await callback.answer()


@user_router.callback_query(F.data.startswith("mark_checked_"))
async def mark_checked(callback: CallbackQuery, state: FSMContext):
    record_id = int(callback.data.split("_")[-1])
    from utils.db import mark_feedback_checked
    mark_feedback_checked(record_id)
    await callback.message.edit_text("✅ Відгук позначено як опрацьований.")
    await callback.answer()


@user_router.callback_query(F.data == "admin_edit_vacancies")
async def admin_edit_vacancies(callback: CallbackQuery, state: FSMContext):
    from utils.db import get_all_cities
    cities = get_all_cities()

    buttons = [[InlineKeyboardButton(text=city, callback_data=f"admin_city_{city}")] for city in cities]
    buttons.append([InlineKeyboardButton(text="🔙 Назад", callback_data="admin_panel")])

    await callback.message.answer("🏙 Обери місто:", reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons))
    await state.set_state(Form.choosing_city)
    await callback.answer()


@user_router.callback_query(F.data.startswith("admin_city_"), Form.choosing_city)
async def admin_choose_market(callback: CallbackQuery, state: FSMContext):
    city = callback.data.replace("admin_city_", "")
    from utils.db import get_markets_by_city
    markets = get_markets_by_city(city)

    # Генеруємо короткі ключі
    market_keys = {}
    for idx, market in enumerate(markets):
        key = f"m_{idx}"
        market_keys[key] = market

    await state.update_data(selected_city=city, market_keys=market_keys)

    # Кнопки з безпечними ключами
    buttons = [
        [InlineKeyboardButton(text=market, callback_data=f"admin_market_{key}")]
        for key, market in market_keys.items()
    ]
    buttons.append([InlineKeyboardButton(text="🔙 Назад", callback_data="admin_edit_vacancies")])

    await callback.message.answer(f"🏢 Обери заклад у місті «{city}»:",
                                  reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons))
    await state.set_state(Form.choosing_market)
    await callback.answer()


@user_router.callback_query(F.data.startswith("admin_market_"), Form.choosing_market)
async def admin_choose_vacancy(callback: CallbackQuery, state: FSMContext):
    key = callback.data.replace("admin_market_", "")
    data = await state.get_data()
    market_keys = data.get("market_keys", {})
    market = market_keys.get(key)

    if not market:
        await callback.answer("⛔️ Не знайдено заклад.")
        return

    city = data.get("selected_city")
    from utils.db import get_vacancies_by_market
    vacancies = get_vacancies_by_market(city, market)

    if not vacancies:
        await callback.message.answer("😕 У цьому закладі поки немає вакансій.")
        await callback.answer()
        return

    for v in vacancies:
        vid, position, location, age_range, description = v
        text = f"📌 {position}\n📍 {location}\n📝 {description or '—'}"
        await callback.message.answer(
            text,
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="✏️ Редагувати", callback_data=f"edit_vacancy_{vid}")],
                [InlineKeyboardButton(text="❌ Видалити", callback_data=f"delete_vacancy_{vid}")],
                [InlineKeyboardButton(text="🙈 Приховати", callback_data=f"hide_vacancy_{vid}")]
            ])
        )

    await callback.message.answer(
        "➕ Додати нову вакансію:",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="➕ Додати вакансію", callback_data="add_vacancy")],
            [InlineKeyboardButton(text="🔙 Назад", callback_data="admin_edit_vacancies")]
        ])
    )

    await callback.answer()


@user_router.callback_query(F.data.startswith("delete_vacancy_"))
async def admin_delete_vacancy(callback: CallbackQuery, state: FSMContext):
    vacancy_id = int(callback.data.split("_")[-1])
    from utils.db import delete_vacancy
    delete_vacancy(vacancy_id)
    await callback.message.edit_text("🗑 Вакансію успішно видалено.")
    await callback.answer()


@user_router.callback_query(F.data.startswith("edit_vacancy_"))
async def admin_start_edit_vacancy(callback: CallbackQuery, state: FSMContext):
    vacancy_id = int(callback.data.split("_")[-1])
    await state.update_data(editing_vacancy_id=vacancy_id)

    # Витягуємо поточні дані з БД:
    from utils.db import get_vacancies_by_id
    vacancy = get_vacancies_by_id(vacancy_id)  # зроби таку функцію у db.py!

    if vacancy:
        position, market, city, location, age_range, description = vacancy
        await callback.message.answer(
            f"Поточна вакансія:\n\n"
            f"Позиція: {position}\n"
            f"Заклад: {market}\n"
            f"Місто: {city}\n"
            f"Адреса: {location}\n"
            f"Вік: {age_range}\n"
            f"Опис: {description}"
        )

    await callback.message.answer(
        "✏️ Надішліть новий опис вакансії у форматі:\n\n"
        "Позиція\nЗаклад\nМісто\nАдреса\nВік\nОпис\n\n"
        "(кожне поле — окремий рядок)",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="❌ Скасувати", callback_data="cancel_edit_vacancy")]
        ])
    )

    await state.set_state(Form.editing_vacancy)
    await callback.answer()


@user_router.callback_query(F.data == "cancel_edit_vacancy")
async def cancel_edit_vacancy(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_text("✏️ Редагування вакансії скасовано.")
    await callback.message.answer(
        "⬅️ Повернутись назад:",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="⬅️ Назад", callback_data="admin_edit_vacancies")]
        ])
    )
    await state.set_state(Form.choosing_interest)
    await callback.answer()


@user_router.callback_query(F.data.startswith("hide_vacancy_"))
async def admin_hide_vacancy(callback: CallbackQuery, state: FSMContext):
    vacancy_id = int(callback.data.split("_")[-1])
    from utils.db import hide_vacancy
    hide_vacancy(vacancy_id)
    await callback.message.edit_text("🙈 Вакансію приховано.")
    await callback.answer()


@user_router.message(Form.editing_vacancy)
async def save_edited_vacancy(message: Message, state: FSMContext):
    parts = [p.strip() for p in message.text.strip().split("\n") if p.strip()]
    if len(parts) < 6:
        await message.answer(
            "⚠️ Формат неправильний. Має бути 6 рядків:\nПозиція\nЗаклад\nМісто\nАдреса\nВік\nОпис"
        )
        return

    position, market, city, location, age_range, description = parts[:6]
    data = await state.get_data()
    vacancy_id = data.get("editing_vacancy_id")

    if vacancy_id:  # редагування
        from utils.db import update_vacancy
        update_vacancy(vacancy_id, position, market, city, location, age_range, description)
        await message.answer("✅ Вакансію оновлено.")
    else:  # додавання
        from utils.db import add_vacancy
        add_vacancy(position, market, city, location, age_range, description)
        await message.answer(
            "✅ Нову вакансію додано.",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="⬅️ Назад", callback_data="admin_edit_vacancies")]
            ])
        )
        await state.set_state(Form.choosing_interest)


@user_router.callback_query(F.data == "back_to_admin")
async def back_to_admin(callback: CallbackQuery, state: FSMContext):
    await callback.message.answer("🛠 HR-панель — оберіть дію:", reply_markup=admin_panel_keyboard())
    await state.set_state(Form.choosing_interest)
    await callback.answer()


@user_router.message(Form.waiting_for_age)
async def process_age(message: Message, state: FSMContext):
    if not message.text or not message.text.isdigit():
        await message.answer("📅 Введи свій вік (лише цифри, наприклад: 25):")
        return
    age = int(message.text)
    if not 16 <= age <= 55:
        await message.answer("Нажаль, ми розглядаємо кандидатів віком від 16 до 55 років.")
        return
    await state.update_data(age=str(age))

    # Витягуємо поточне резюме з state
    data = await state.get_data()
    resume_link = data.get("resume_link")
    msg = "🔗 Надішли файл резюме (pdf, docx) або посилання на Google Drive/Docs.\nЯкщо не хочеш змінювати — напиши 'Пропустити'."
    if resume_link:
        if resume_link.startswith("BQAC"):
            msg += "\n📄 Поточний файл резюме вже прикріплений."
        else:
            msg += f"\n🔗 Поточне резюме: {resume_link}"

    await message.answer(
        msg,
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=[[InlineKeyboardButton(text="❌ Скасувати", callback_data="back_to_interest")]]
        )
    )
    await state.set_state(Form.waiting_for_resume)


@user_router.callback_query(F.data.startswith("admin_open_resume_"))
async def admin_open_resume(callback: CallbackQuery, state: FSMContext):
    fid = int(callback.data.split("_")[-1])
    from utils.db import get_all_feedbacks
    feedbacks = get_all_feedbacks()
    resume_link = None
    for fb in feedbacks:
        if fb[0] == fid:
            resume_link = fb[-1]  # resume_link має бути останній у tuple
            break

    if resume_link and resume_link.startswith("BQAC"):
        await callback.message.answer_document(resume_link)
    elif resume_link:
        await callback.message.answer(f"🔗 Резюме: {resume_link}")
    else:
        await callback.message.answer("❗️ Файл резюме не знайдено або він не файл Telegram.")

    await callback.answer()


@user_router.callback_query(F.data.startswith("admin_delete_feedback_"))
async def admin_delete_feedback(callback: CallbackQuery, state: FSMContext):
    record_id = int(callback.data.split("_")[-1])
    from utils.db import delete_feedback
    delete_feedback(record_id)
    await callback.message.edit_text("🗑 Відгук успішно видалено.")
    await callback.answer()


@user_router.callback_query(F.data == "add_vacancy")
async def admin_add_vacancy(callback: CallbackQuery, state: FSMContext):
    await callback.message.answer(
        "Введіть нову вакансію у форматі:\n\nПозиція | Заклад | Місто | Адреса | Вік | Опис"
    )
    await state.set_state(Form.editing_vacancy)
    await state.update_data(editing_vacancy_id=None)  # None, бо це нова вакансія
    await callback.answer()
