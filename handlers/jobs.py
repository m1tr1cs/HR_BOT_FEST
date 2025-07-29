from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from states import Form
from utils.db import save_candidate, has_applied, get_admin_chat_ids
from keyboards import positions_inline_keyboard, interest_inline_keyboard

jobs_router = Router()


@jobs_router.callback_query(F.data.startswith("position_"), Form.choosing_position)
async def process_position_callback(callback: CallbackQuery, state: FSMContext):
    chosen_position = callback.data.replace("position_", "")
    data = await state.get_data()
    vacancies = data.get("vacancies", [])
    unique_positions = sorted(list(set(v['position'] for v in vacancies if 'position' in v)))
    if chosen_position not in unique_positions:
        await callback.answer("Будь ласка, обери категорію за допомогою кнопок.")
        return

    filtered_vacancies = [v for v in vacancies if v.get('position') == chosen_position]
    vacancy_message_ids = []
    for vacancy in filtered_vacancies:
        vacancy_text = (
            f"🏢 Посада: {vacancy.get('position', 'Не вказано')}\n"
            f"🏢 Заклад: {vacancy.get('market', 'Не вказано')}\n"
            f"📍 Місто: {vacancy.get('city', 'Не вказано')}\n"
            f"🗺️ Адреса: {vacancy.get('location', 'Не вказано')}\n"
            f"📝 Опис: {vacancy.get('description', 'Без опису')}"
        )
        buttons = []
        if not has_applied(callback.from_user.id, vacancy["vacancy_id"]):
            buttons.append([InlineKeyboardButton(text="Цікавить ✨", callback_data=f"apply_{vacancy['vacancy_id']}")])
        msg = await callback.message.answer(vacancy_text,
                                            reply_markup=InlineKeyboardMarkup(
                                                inline_keyboard=buttons) if buttons else None)
        vacancy_message_ids.append(msg.message_id)

    # Відправляємо кнопку "Назад" окремим повідомленням і теж зберігаємо його id
    back_msg = await callback.message.answer(
        "Щоб повернутися до вибору категорії — натисни 'Назад'.",
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=[[InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_positions")]]
        )
    )
    await state.update_data(vacancy_message_ids=vacancy_message_ids, vacancy_back_message_id=back_msg.message_id)


# handler inline button back
@jobs_router.callback_query(F.data == "back_to_positions")
async def process_back_to_positions(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    vacancies = data.get("vacancies", [])
    unique_positions = sorted(list(set(v['position'] for v in vacancies if 'position' in v)))
    await callback.message.edit_text(
        "Чудово! Обери категорію, яка тебе цікавить:",
        reply_markup=positions_inline_keyboard(unique_positions)
    )

    await state.set_state(Form.choosing_position)
    await callback.answer()


@jobs_router.callback_query(F.data == "back_to_interest")
async def process_back_to_interest(callback: CallbackQuery, state: FSMContext):
    from utils.db import is_admin
    data = await state.get_data()
    show_edit = all(data.get(k) for k in ["name", "phone", "age"])
    is_admin_user = is_admin(callback.from_user.id)

    from keyboards import interest_inline_keyboard
    await callback.message.answer(
        "🔎 Чудово! Обери, що тебе цікавить:",
        reply_markup=interest_inline_keyboard(
            show_edit_button=show_edit,
            show_feedback_button=True,
            show_admin_button=is_admin_user
        )
    )
    await state.set_state(Form.choosing_interest)
    await callback.answer()


@jobs_router.callback_query(F.data.startswith("apply_"))
async def process_vacancy_callback(callback: CallbackQuery, state: FSMContext):
    vacancy_id = int(callback.data.split("_")[1])
    user_data = await state.get_data()
    all_vacancies = user_data.get("vacancies")
    if not all_vacancies:
        await callback.answer("❗ Немає доступних вакансій. Почніть з /start", show_alert=True)
        return

    # ВИДАЛЯЄМО всі вакансії та "Назад"
    vacancy_message_ids = user_data.get("vacancy_message_ids", [])
    for msg_id in vacancy_message_ids:
        try:
            await callback.bot.delete_message(callback.message.chat.id, msg_id)
        except Exception:
            pass
    back_message_id = user_data.get("vacancy_back_message_id")
    if back_message_id:
        try:
            await callback.bot.delete_message(callback.message.chat.id, back_message_id)
        except Exception:
            pass

    selected_vacancy = next((v for v in all_vacancies if v.get('vacancy_id') == vacancy_id), None)
    if not selected_vacancy or not all(k in user_data for k in ['name', 'phone', 'age']):
        await callback.answer("Помилка! Сесія застаріла або дані неповні. Спробуйте почати з /start", show_alert=True)
        return
    name = user_data.get('name')
    phone = user_data.get('phone')
    age = user_data.get('age')
    chat_id = callback.from_user.id
    resume_link = user_data.get('resume_link')
    save_candidate(name, phone, age, chat_id, selected_vacancy, resume_link)
    # ----- НОВЕ! -----
    from utils.db import get_admin_chat_ids
    admins = get_admin_chat_ids()
    vacancy_text = (
        f"🆕 Новий відгук!\n"
        f"👤 Імʼя: {name}\n"
        f"📱 Телефон: {phone}\n"
        f"🎂 Вік: {age}\n"
        f"📌 Вакансія: {selected_vacancy.get('position', '')} - {selected_vacancy.get('market', '')} ({selected_vacancy.get('location', '')})"
    )

    buttons = []
    if resume_link:
        if resume_link.startswith("BQAC"):
            # callback на відкриття файла саме для цього відгуку (id треба дістати!)
            # Треба зберегти id запису кандидата після save_candidate. Найпростіше — дістати max(id):
            from utils.db import get_last_candidate_id_by_user
            candidate_id = get_last_candidate_id_by_user(chat_id)
            buttons.append([
                InlineKeyboardButton(
                    text="📄 Переглянути файл",
                    callback_data=f"admin_open_resume_{candidate_id}"
                )
            ])
        else:
            buttons.append([
                InlineKeyboardButton(
                    text="🔗 Переглянути лінк",
                    url=resume_link
                )
            ])

    markup = InlineKeyboardMarkup(inline_keyboard=buttons) if buttons else None

    for admin_chat in admins:
        try:
            await callback.bot.send_message(admin_chat, vacancy_text, reply_markup=markup)
        except Exception as e:
            print(f"Не вдалося надіслати сповіщення адміну: {e}")
    # ----- Кінець нового -----

    await callback.answer("✅ Твій відгук успішно надіслано!", show_alert=False)
    # Відправляємо підтвердження лише для обраної вакансії!
    await callback.message.answer(
        f"🎉 **Дякуємо! Ваш відгук на цю вакансію надіслано.**\n\n"
        f"🏢 Посада: {selected_vacancy.get('position', 'Не вказано')}\n"
        f"🏢 Заклад: {selected_vacancy.get('market', 'Не вказано')}\n"
        f"📍 Місто: {selected_vacancy.get('city', 'Не вказано')}\n"
        f"🗺️ Адреса: {selected_vacancy.get('location', 'Не вказано')}\n"
        f"📝 Опис: {selected_vacancy.get('description', 'Без опису')}",
        parse_mode="Markdown",
        reply_markup=None
    )
    await state.update_data(vacancies=None)
    from keyboards import main_menu_keyboard
    await callback.message.answer("🔧 Обери дію:", reply_markup=main_menu_keyboard())
