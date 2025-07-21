from aiogram import Router, F
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, ReplyKeyboardRemove
from states import Form
from keyboards import phone_keyboard, interest_keyboard
from keyboards import back_keyboard
from utils.sheets import get_vacancies
import logging

user_router = Router()

@user_router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext):
    logging.info(f"User {message.from_user.id} started bot")
    welcome_text = '''
Холдинг емоцій !FEST — це мережа креативних ресторанів та проєктів з оригінальними концепціями. Ми розпочали цей шлях у 2007 році, і з того часу наша команда зросла до понад 2000 людей, які щодня наповнюють цей світ емоціями, смаками та унікальними враженнями.
'''
    await state.clear()
    await message.answer(welcome_text, reply_markup=ReplyKeyboardRemove())
    await message.answer("👋 Привіт! Як до тебе звертатись?")
    await state.set_state(Form.waiting_for_name)

@user_router.message(Form.waiting_for_name)
async def process_name(message: Message, state: FSMContext):
    name = message.text.strip()
    if not name or len(name) < 1:
        await message.answer("❗ Будь ласка, введи своє справжнє ім’я.")
        return
    await state.update_data(name=name)
    await message.answer("📞 Тепер поділись своїм номером телефону або введи його вручну:", reply_markup=phone_keyboard())
    await state.set_state(Form.waiting_for_phone)

@user_router.message(Form.waiting_for_phone, F.contact)
async def process_phone_contact(message: Message, state: FSMContext):
    await state.update_data(phone=message.contact.phone_number)
    await message.answer("📅 Введи свій вік (лише цифри, наприклад: 25):", reply_markup=ReplyKeyboardRemove())
    await state.set_state(Form.waiting_for_age)

@user_router.message(Form.waiting_for_phone)
async def process_phone_text(message: Message, state: FSMContext):
    phone = message.text.strip()
    import re
    if not re.match(r"^\+?\d{10,15}$", phone):
        await message.answer("❗ Неправильний формат номера. Спробуй ще раз (наприклад, +380XXXXXXXXX):")
        return
    await state.update_data(phone=phone)
    await message.answer("📅 Введи свій вік (лише цифри, наприклад: 25):", reply_markup=ReplyKeyboardRemove())
    await state.set_state(Form.waiting_for_age)

@user_router.message(Form.waiting_for_age)
async def process_age(message: Message, state: FSMContext):
    if not message.text or not message.text.isdigit():
        await message.answer("❗ Будь ласка, введи вік як число (наприклад, 18, 22, 47):")
        return
    age = int(message.text)
    if not 16 <= age <= 55:
        await message.answer("🔞 На жаль, ми розглядаємо кандидатів віком від 16 до 55 років.")
        return
    await state.update_data(age=str(age))
    await message.answer("🔎 Чудово! Тепер обери, що тебе цікавить:", reply_markup=interest_keyboard())
    await state.set_state(Form.choosing_interest)

@user_router.message(Form.choosing_interest, F.text.in_(["Робота", "Про нас"]))
async def process_interest(message: Message, state: FSMContext):
    text = message.text
    if text == "Про нас":
        about_text = (
            "Тепер !FEST – уже більш ніж ресторанна компанія..."
        )
        await message.answer(about_text, reply_markup=interest_keyboard())
        return

    if text == "Робота":
        vacancies = get_vacancies()
        if not vacancies:
            await message.answer("😔 На жаль, зараз немає відкритих вакансій.", reply_markup=ReplyKeyboardRemove())
            await state.clear()
            return

        await state.update_data(vacancies=vacancies)
        unique_positions = sorted(list(set(v['position'] for v in vacancies if 'position' in v)))

        from aiogram.types import KeyboardButton, ReplyKeyboardMarkup
        position_buttons = [KeyboardButton(text=pos) for pos in unique_positions]
        kb = ReplyKeyboardMarkup(
            keyboard=[[btn] for btn in position_buttons] + [[KeyboardButton(text="🔙 Назад")]],
            resize_keyboard=True
        )
        await message.answer("Чудово! Обери категорію, яка тебе цікавить:", reply_markup=kb)
        await state.set_state(Form.choosing_position)
