import asyncio
import logging
from aiogram import Bot, Dispatcher, F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, Message, InlineKeyboardMarkup, InlineKeyboardButton

# Ваши данные
TOKEN = "8732154314:AAHo2Pal20i_g_AO3t2_qFoNTo8wViU-FtU"
MANAGER_CHAT_ID = "1484269068" # Ваш личный Telegram ID для получения заявок

router = Router()

class EstimateState(StatesGroup):
    waiting_for_model = State()
    waiting_for_memory = State()
    waiting_for_repair = State()
    waiting_for_description = State()
    waiting_for_battery = State()

# База цен из вашего прайса
PRICELIST = {
    "11": {64: 4000, 128: 5000},
    "11 Pro": {64: 7000, 256: 9000},
    "12": {64: 6000, 128: 8000},
    "12 Pro": {128: 13000, 256: 15000},
    "13": {128: 15000, 256: 19000},
    "13 Pro": {128: 20000, 256: 24000},
    "14": {128: 19000, 256: 22000},
    "14 Pro": {128: 26000, 256: 32000},
    "15": {128: 28000, 256: 32000},
    "15 Pro": {128: 40000, 256: 46000},
    "16": {128: 40000, 256: 46000},
    "16 Pro": {128: 50000, 256: 57000, 512: 62000, 1024: 65000},
}

def get_models_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📱 iPhone 16 Pro", callback_data="model_16 Pro"),
         InlineKeyboardButton(text="📱 iPhone 16", callback_data="model_16")],
        [InlineKeyboardButton(text="📱 iPhone 15 Pro", callback_data="model_15 Pro"),
         InlineKeyboardButton(text="📱 iPhone 15", callback_data="model_15")],
        [InlineKeyboardButton(text="📱 iPhone 14 Pro", callback_data="model_14 Pro"),
         InlineKeyboardButton(text="📱 iPhone 14", callback_data="model_14")],
        [InlineKeyboardButton(text="📱 iPhone 13 Pro", callback_data="model_13 Pro"),
         InlineKeyboardButton(text="📱 iPhone 13", callback_data="model_13")],
        [InlineKeyboardButton(text="📱 iPhone 12 Pro / 11 Pro", callback_data="model_12 Pro"),
         InlineKeyboardButton(text="📱 iPhone 12 / 11", callback_data="model_12")],
    ])

def get_memory_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="64 GB", callback_data="mem_64"),
         InlineKeyboardButton(text="128 GB", callback_data="mem_128")],
        [InlineKeyboardButton(text="256 GB", callback_data="mem_256"),
         InlineKeyboardButton(text="512 GB / 1TB", callback_data="mem_512")],
    ])

def get_repair_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Нет, не вскрывался", callback_data="repair_no")],
        [InlineKeyboardButton(text="🛠 Да, был ремонт", callback_data="repair_yes")],
    ])

@router.message(Command("start"))
async def cmd_start(message: Message, state: FSMContext):
    await state.clear()
    welcome_text = (
        "⚡ <b>CODE COMMUNITY | Trade-In Bot</b>\n\n"
        "Приветствуем! Рассчитаем стоимость вашего iPhone по актуальному прайсу.\n\n"
        "👇 <i>Выберите модель устройства:</i>"
    )
    await message.answer(welcome_text, parse_mode="HTML", reply_markup=get_models_keyboard())
    await state.set_state(EstimateState.waiting_for_model)

@router.callback_query(F.data.startswith("model_"), EstimateState.waiting_for_model)
async def process_model(callback: CallbackQuery, state: FSMContext):
    model_name = callback.data.replace("model_", "")
    await state.update_data(model=model_name)
    
    text = f"📱 Выбрана модель: <b>{model_name}</b>\n\n💾 <i>Выберите объем памяти:</i>"
    await callback.message.edit_text(text, parse_mode="HTML", reply_markup=get_memory_keyboard())
    await state.set_state(EstimateState.waiting_for_memory)
    await callback.answer()

@router.callback_query(F.data.startswith("mem_"), EstimateState.waiting_for_memory)
async def process_memory(callback: CallbackQuery, state: FSMContext):
    memory_map = {"mem_64": 64, "mem_128": 128, "mem_256": 256, "mem_512": 512}
    memory = memory_map.get(callback.data, 128)
    await state.update_data(memory=memory)
    
    text = (
        "🛠 <b>История устройства</b>\n\n"
        "Производился ли ранее ремонт телефона (замена экрана, аккумулятора и т.д.)?"
    )
    await callback.message.edit_text(text, parse_mode="HTML", reply_markup=get_repair_keyboard())
    await state.set_state(EstimateState.waiting_for_repair)
    await callback.answer()

@router.callback_query(F.data.startswith("repair_"), EstimateState.waiting_for_repair)
async def process_repair(callback: CallbackQuery, state: FSMContext):
    repair_status = "Был ремонт" if callback.data == "repair_yes" else "Не ремонтировался"
    await state.update_data(repair=repair_status)
    
    text = (
        "💬 <b>Состояние и дефекты</b>\n\n"
        "Опишите своими словами текущее состояние:\n"
        "• Есть ли царапины, сколы, трещины?\n"
        "• Работает ли Face ID, камеры, динамики?\n\n"
        "<i>Просто отправьте текст ответным сообщением 👇</i>"
    )
    await callback.message.edit_text(text, parse_mode="HTML")
    await state.set_state(EstimateState.waiting_for_description)
    await callback.answer()

@router.message(EstimateState.waiting_for_description, F.text)
async def process_description(message: Message, state: FSMContext):
    await state.update_data(description=message.text)
    
    text = (
        "🔋 <b>Состояние аккумулятора</b>\n\n"
        "Укажите процент износа или емкости АКБ (например: <i>88%</i> или <i>как новый</i>)."
    )
    await message.answer(text, parse_mode="HTML")
    await state.set_state(EstimateState.waiting_for_battery)

@router.message(EstimateState.waiting_for_battery, F.text)
async def process_battery(message: Message, state: FSMContext, bot: Bot):
    await state.update_data(battery=message.text)
    data = await state.get_data()
    
    model = data.get('model')
    memory = data.get('memory')
    
    base_price = PRICELIST.get(model, {}).get(memory, None)
    
    if base_price:
        price_text = f"<b>до {base_price:,} ₽</b> (по базовому прайсу)".replace(",", ".")
    else:
        price_text = "<b>Рассчитывается индивидуально экспертом</b>"

    user_response = (
        "✨ <b>Предварительная оценка готова!</b>\n\n"
        f"📱 Модель: <code>{model} ({memory} GB)</code>\n"
        f"🛠 Ремонт: <code>{data.get('repair')}</code>\n"
        f"🔋 Аккумулятор: <code>{data.get('battery')}</code>\n\n"
        f"💰 Ориентировочная сумма скупки: {price_text}\n\n"
        "🎯 <i>Заявка передана оценщику. Скоро мы свяжемся с вами для подтверждения!</i>"
    )
    await message.answer(user_response, parse_mode="HTML")
    
    manager_notification = (
        "🔥 <b>Новая заявка на скупку (Community)</b>\n\n"
        f"👤 Клиент: @{message.from_user.username or 'нет юзернейма'} (ID: <code>{message.from_user.id}</code>)\n"
        f"📱 Устройство: iPhone {model} — {memory} GB\n"
        f"🛠 Ремонт: {data.get('repair')}\n"
        f"🔋 АКБ: {data.get('battery')}\n"
        f"💰 Цена по прайсу: {base_price if base_price else 'Под заказ'} ₽\n"
        f"📝 Описание:\n<i>{data.get('description')}</i>"
    )
    await bot.send_message(MANAGER_CHAT_ID, manager_notification, parse_mode="HTML")
    await state.clear()

async def main():
    bot = Bot(token=TOKEN)
    dp = Dispatcher()
    dp.include_router(router)
    
    print("🤖 Бот CODE COMMUNITY (Оценка iPhone) успешно запущен!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())