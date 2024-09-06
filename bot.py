import asyncio
from aiogram import Bot, Dispatcher, F
from aiogram.filters import CommandStart, Command
from aiogram.types import Message, FSInputFile
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
import requests
from config import TOKEN
import sqlite3
import aiohttp
import logging
import random
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import ReplyKeyboardBuilder, InlineKeyboardBuilder

# Создаем экземпляр бота и диспетчера
bot = Bot(token=TOKEN)
dp = Dispatcher()

logging.basicConfig(level=logging.INFO)

button_registr = KeyboardButton(text="Регистрация в телеграм боте")
button_exchange_rates = KeyboardButton(text="Курс валют")
button_tips = KeyboardButton(text="Советы по экономии")
button_finances = KeyboardButton(text="Личные финансы")

keyboards = ReplyKeyboardMarkup(keyboard=[
    [button_registr, button_exchange_rates],
    [button_tips, button_finances]
], resize_keyboard=True)  # one_time_keyboard=True)

conn = sqlite3.connect('users.db')
cursor = conn.cursor()
cursor.execute('''CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    telegram_id INTEGER UNIQUE,
                    username TEXT NOT NULL,
                    name TEXT NOT NULL,
                    category1 TEXT,
                    category2 TEXT,
                    category3 TEXT,
                    expenses1 REAL,
                    expenses2 REAL,
                    expenses3 REAL
                )''')
conn.commit()


class FinancesForm(StatesGroup):
    category1 = State()
    expenses1 = State()
    category2 = State()
    expenses2 = State()
    category3 = State()
    expenses3 = State()


@dp.message(Command("start"))
async def send_start(message: Message):
    await message.answer("Привет! Я ваш личный финансовый помощник. Выберите одну из опций в меню:",
                         reply_markup=keyboards)


@dp.message(F.text == "Регистрация в телеграм боте")
async def registration(message: Message):
    telegram_id = message.from_user.id
    name = message.from_user.full_name
    username = message.from_user.username  # Assuming this is the correct way to get the username
    cursor.execute('''SELECT * FROM users WHERE telegram_id = ?''', (telegram_id,))
    user = cursor.fetchone()
    if user:
        await message.answer("Вы уже зарегистрированы")
    else:
        cursor.execute('''INSERT INTO users (telegram_id, name, username) VALUES (?, ?, ?)''',
                       (telegram_id, name, username))
        conn.commit()
        await message.answer("Вы успешно зарегистрированы!")


@dp.message(F.text == "Курс валют")
async def exchange_rates(message: Message):
    url = "https://v6.exchangerate-api.com/v6/09edf8b2bb246e1f801cbfba/latest/USD"
    try:
        response = requests.get(url)
        data = response.json()
        if response.status_code != 200:
            await message.answer("Не удалось получить курс валют")
            return
        usd_to_rub = data['conversion_rates']['RUB']
        eur_to_usd = data['conversion_rates']['EUR']
        eur_to_rub = eur_to_usd * usd_to_rub
        await message.answer(f"Курс доллара к рублю: {usd_to_rub:.2f}\nКурс евро к рублю: {eur_to_rub:.2f}")
    except:
        await message.answer("Произошла ошибка при получении курса валют")


@dp.message(F.text == "Советы по экономии")
async def send_tips(message: Message):
    tips = [
        "Совет 1: Ведите бюджет и следите за своими расходами.",
        "Совет 2: Откладывайте часть доходов на сбережения.",
        "Совет 3: Покупайте товары по скидкам и распродажам."
    ]
    tip = random.choice(tips)
    await message.answer(tip)

    #     response = await aiohttp.ClientSession().get(url)
    #     data = await response.json()
    #     rates = data['conversion_rates']
    #     rates_str = "\n".join([f"{currency}: {rate:.2f}" for currency, rate in rates.items()])
    #     await message.answer(f"Курс валют:\n{rates_str}")
    # except Exception as e:
    #     await message.answer(f"Произошла ошибка: {e}")


@dp.message(F.text == "Личные финансы")
async def finances(message: Message, state: FSMContext):
    await state.set_state(FinancesForm.category1)
    await message.reply("Выберите первую категорию расходов:")


@dp.message(FinancesForm.category1)
async def process_category1(message: Message, state: FSMContext):
    await state.update_data(category1=message.text)
    await state.set_state(FinancesForm.expenses1)
    await message.reply("Введите сумму расходов по первой категории:")


@dp.message(FinancesForm.expenses1)
async def process_expenses1(message: Message, state: FSMContext):
    await state.update_data(expenses1=float(message.text))
    await state.set_state(FinancesForm.category2)
    await message.reply("Выберите вторую категорию расходов:")


@dp.message(FinancesForm.category2)
async def process_category2(message: Message, state: FSMContext):
    await state.update_data(category2=message.text)
    await state.set_state(FinancesForm.expenses2)
    await message.reply("Введите сумму расходов по второй категории:")


@dp.message(FinancesForm.expenses2)
async def process_expenses2(message: Message, state: FSMContext):
    await state.update_data(expenses2=float(message.text))
    await state.set_state(FinancesForm.category3)
    await message.reply("Выберите третью категорию расходов:")


@dp.message(FinancesForm.category3)
async def process_category3(message: Message, state: FSMContext):
    await state.update_data(category3=message.text)
    await state.set_state(FinancesForm.expenses3)
    await message.reply("Введите сумму расходов по третьей категории:")


@dp.message(FinancesForm.expenses3)
async def process_expenses3(message: Message, state: FSMContext):
    data = await state.get_data()  # Получаем данные из состояния
    telegram_id = message.from_user.id
    cursor.execute(
        '''UPDATE users SET category1 = ?, expenses1 = ?, category2 = ?, expenses2 = ?, category3 = ?, expenses3 = ? WHERE telegram_id = ?''',
        (data['category1'], data['expenses1'], data['category2'], data['expenses2'], data['category3'],
         float(message.text), telegram_id))
    conn.commit()
    await state.clear()
    await message.reply("Данные сохранены. Вы можете добавить новые данные или выйти в главное меню.")


async def main():
    await dp.start_polling(bot)


if __name__ == '__main__':
    asyncio.run(main())