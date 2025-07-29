from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from states import Form
from utils.db import save_candidate
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
    # await callback.message.answer(
    #    f"Знайдено {len(filtered_vacancies)} вакансій за посадою «{chosen_position}». Натисни «Цікавить» під тією, що сподобалась."
    # )
    for vacancy in filtered_vacancies:
        vacancy_text = (
            f"🏢 Посада: {vacancy.get('position', 'Не вказано')}\n"
            f"🏢 Заклад: {vacancy.get('market', 'Не вказано')}\n"
            f"📍 Місто: {vacancy.get('city', 'Не вказано')}\n"
            f"🗺️ Адреса: {vacancy.get('location', 'Не вказано')}\n"
            f"👥 Вік: {vacancy.get('age_range', 'Не вказано')}\n"
            f"📝 Опис: {vacancy.get('description', 'Без опису')}"
        )
        inline_kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="Цікавить ✨", callback_data=f"apply_{vacancy['vacancy_id']}")]
        ])
        await callback.message.answer(vacancy_text, reply_markup=inline_kb)
    # inline button "Back" ----- testing
    await callback.message.answer(
        "Щоб повернутися до вибору категорії — натисни 'Назад'.",
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=[[InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_positions")]]
        )
    )


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
    # await callback.message.answer("\u200B", reply_markup=ReplyKeyboardRemove())
    await state.set_state(Form.choosing_position)
    await callback.answer()


@jobs_router.callback_query(F.data == "back_to_interest")
async def process_back_to_interest(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    show_edit = all(data.get(k) for k in ["name", "phone", "age"])

    from utils.db import is_admin
    is_admin_user = is_admin(callback.from_user.id)

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
    all_vacancies = user_data.get("vacancies", [])
    selected_vacancy = next((v for v in all_vacancies if v.get('vacancy_id') == vacancy_id), None)
    if not selected_vacancy or not all(k in user_data for k in ['name', 'phone', 'age']):
        await callback.answer("Помилка! Сесія застаріла або дані неповні. Спробуйте почати з /start", show_alert=True)
        return
    name = user_data.get('name')
    phone = user_data.get('phone')
    age = user_data.get('age')
    chat_id = callback.from_user.id
    save_candidate(name, phone, age, chat_id, selected_vacancy)
    await callback.answer("✅ Твій відгук успішно надіслано!", show_alert=False)
    await callback.message.answer(f"🎉 **Дякуємо! Ваш відгук на цю вакансію надіслано.**\n\n{callback.message.text}",
                                  parse_mode="Markdown", reply_markup=None)
    await state.update_data(vacancies=None)
    # await callback.message.answer("Якщо захочеш переглянути інші вакансії або почати знову, просто напиши /start.",
    #                              reply_markup=ReplyKeyboardRemove())
    main_menu_kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🏠 Головне меню", callback_data="back_to_interest")]
        ]
    )
    from keyboards import main_menu_keyboard
    await callback.message.answer("🔧 Обери дію:", reply_markup=main_menu_keyboard())
