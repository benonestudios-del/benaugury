import json
import random
import re
from aiogram import Bot, Dispatcher, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import CommandStart, Command
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
import asyncio

import os
API_TOKEN = os.getenv('API_TOKEN')
ADMIN_ID = 6382960258  # Например: 123456789

bot = Bot(token=API_TOKEN)
dp = Dispatcher()

# Загружаем фанфики
try:
    with open("fanfics.json", "r", encoding="utf-8") as f:
        FANFICS = json.load(f)
except FileNotFoundError:
    FANFICS = {}

def save_fanfics():
    with open("fanfics.json", "w", encoding="utf-8") as f:
        json.dump(FANFICS, f, ensure_ascii=False, indent=2)

# FSM для добавления фанфика
class AddFanfic(StatesGroup):
    waiting_for_title = State()
    waiting_for_text = State()

# Команда /start
@dp.message(CommandStart())
async def cmd_start(message: Message):
    await message.answer("📚 Выбери рассказ:", reply_markup=get_fanfic_keyboard())

# Генерация кнопок по фанфикам
def get_fanfic_keyboard():
    keyboard = [
        [InlineKeyboardButton(text=title, callback_data=f"fanfic:{i}")]
        for i, title in enumerate(FANFICS)
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

# Обработка выбора фанфика
@dp.callback_query(F.data.startswith("fanfic:"))
async def handle_fanfic_selection(callback: CallbackQuery):
    index = int(callback.data.split(":")[1])
    title = list(FANFICS.keys())[index]
    phrase = random.choice(FANFICS[title])
    await callback.message.answer(
        f"📖 *{title}*\n\n_{phrase}_",
        parse_mode="Markdown",
        reply_markup=get_after_prediction_keyboard(index)
    )

# Кнопка "ещё"
def get_after_prediction_keyboard(index):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔁 Другое предсказание", callback_data=f"again:{index}")],
        [InlineKeyboardButton(text="📚 Выбрать другой рассказ", callback_data="back")]
    ])

@dp.callback_query(F.data.startswith("again:"))
async def handle_again(callback: CallbackQuery):
    index = int(callback.data.split(":")[1])
    title = list(FANFICS.keys())[index]
    phrase = random.choice(FANFICS[title])
    await callback.message.answer(
        f"🔮 *{title}*\n\n_{phrase}_",
        parse_mode="Markdown",
        reply_markup=get_after_prediction_keyboard(index)
    )

@dp.callback_query(F.data == "back")
async def handle_back(callback: CallbackQuery):
    await callback.message.answer("📚 Выбери рассказ:", reply_markup=get_fanfic_keyboard())

# Команда /addfanfic
@dp.message(Command("addfanfic"))
async def cmd_addfanfic(message: Message, state: FSMContext):
    if message.from_user.id != ADMIN_ID:
        return await message.answer("⛔ Только для администратора.")
    
    await state.set_state(AddFanfic.waiting_for_title)
    await message.answer("✍️ Введи название новой работы:")

@dp.message(AddFanfic.waiting_for_title)
async def get_title(message: Message, state: FSMContext):
    title = message.text.strip()
    if title in FANFICS:
        await message.answer("❗ Такая работа уже есть. Введи другое название.")
        return
    await state.update_data(title=title)
    await state.set_state(AddFanfic.waiting_for_text)
    await message.answer("📜 Теперь пришли текст — всё одним сообщением.\nБот сам разобьёт его на предложения.")

@dp.message(AddFanfic.waiting_for_text)
async def get_text(message: Message, state: FSMContext):
    data = await state.get_data()
    title = data["title"]
    text = message.text.strip()
    sentences = re.split(r'(?<=[.!?])\s+', text)
    sentences = [s.strip() for s in sentences if s.strip()]
    FANFICS[title] = sentences
    save_fanfics()
    await message.answer(f"✅ Работа *{title}* сохранена! Добавлено {len(sentences)} предложений.", parse_mode="Markdown")
    await state.clear()

# Запуск
async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
