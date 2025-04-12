import asyncio
from aiogram import Bot, Dispatcher, F, types
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
from aiogram.filters import CommandStart, Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from config import BOT_TOKEN, ADMIN_ID
from database import init_db, add_full_request, delete_request_by_id, get_admin_message_id

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# Кнопки управления
def get_nav_keyboard():
    return ReplyKeyboardMarkup(keyboard=[
        [KeyboardButton(text="⬅ Назад")],
        [KeyboardButton(text="🔄 Начать сначала")]
    ], resize_keyboard=True)

def get_final_keyboard():
    return ReplyKeyboardMarkup(keyboard=[
        [KeyboardButton(text="🆕 Новый заказ")],
        [KeyboardButton(text="❌ Отменить заявку")]
    ], resize_keyboard=True)

# Состояния анкеты
class RequestForm(StatesGroup):
    name = State()
    contact = State()
    bot_name = State()
    purpose = State()
    functions = State()
    admin_panel = State()
    buttons = State()
    data_storage = State()
    notifications = State()
    payment = State()
    business_info = State()
    urgency = State()
    other = State()

questions = [
    ("name", "Как вас зовут?"),
    ("contact", "Удобный контакт для связи (телефон, почта или @ник в Telegram):"),
    ("bot_name", "Какое название вы хотите для бота?"),
    ("purpose", "Для чего вам нужен бот? Опишите цель."),
    ("functions", "Что должен уметь делать бот?"),
    ("admin_panel", "Нужна ли админ-панель? Что в ней должно быть?"),
    ("buttons", "Какие кнопки и разделы должны быть у бота?"),
    ("data_storage", "Должны ли данные сохраняться (например, заявки, список клиентов)?"),
    ("notifications", "Какие уведомления должен отправлять бот и кому?"),
    ("payment", "Нужна ли оплата в Telegram? В какой валюте?"),
    ("business_info", "Если бот связан с бизнесом, укажите: название, нишу, ссылки."),
    ("urgency", "Насколько срочно нужно сделать бота?"),
    ("other", "Есть ли ещё пожелания?")
]

state_order = [RequestForm.name, RequestForm.contact, RequestForm.bot_name, RequestForm.purpose,
               RequestForm.functions, RequestForm.admin_panel, RequestForm.buttons,
               RequestForm.data_storage, RequestForm.notifications, RequestForm.payment,
               RequestForm.business_info, RequestForm.urgency, RequestForm.other]

@dp.message(CommandStart())
@dp.message(F.text == "🆕 Новый заказ")
async def start(message: Message, state: FSMContext):
    await state.clear()
    await message.answer("Привет! Я помогу собрать ТЗ на Telegram-бота.\n\n" + questions[0][1],
                         reply_markup=get_nav_keyboard())
    await state.set_state(state_order[0])

@dp.message(F.text == "🔄 Начать сначала")
async def restart(message: Message, state: FSMContext):
    await state.clear()
    await message.answer("Начинаем заново.\n\n" + questions[0][1],
                         reply_markup=get_nav_keyboard())
    await state.set_state(state_order[0])

@dp.message(F.text == "⬅ Назад")
async def go_back(message: Message, state: FSMContext):
    current = await state.get_state()
    if current in [s.state for s in state_order]:
        idx = [s.state for s in state_order].index(current)
        if idx > 0:
            await state.set_state(state_order[idx - 1])
            await message.answer(questions[idx - 1][1], reply_markup=get_nav_keyboard())
        else:
            await message.answer("Вы уже на первом шаге.", reply_markup=get_nav_keyboard())
    else:
        await message.answer("Невозможно вернуться назад.")

@dp.message(F.text == "❌ Отменить заявку")
async def cancel_order(message: Message, state: FSMContext):
    await message.answer("Введите ID заявки, которую хотите отменить:")
    await state.clear()
    await state.set_state("awaiting_cancel_id")

@dp.message(F.text)
async def handle_question(message: Message, state: FSMContext):
    current = await state.get_state()

    # Обработка удаления по ID
    if current == "awaiting_cancel_id":
        try:
            request_id = int(message.text.strip())
            admin_msg_id = get_admin_message_id(request_id)
            deleted = delete_request_by_id(request_id)
            if deleted:
                if admin_msg_id:
                    try:
                        await bot.delete_message(chat_id=ADMIN_ID, message_id=admin_msg_id)
                    except Exception:
                        pass
                await bot.send_message(ADMIN_ID, f"❌ Клиент отменил заявку #{request_id}.")
                await message.answer(f"✅ Заявка #{request_id} отменена.", reply_markup=get_final_keyboard())
            else:
                await message.answer(
                    f"❌ Заявка с ID {request_id} не найдена или уже была удалена.\nПроверьте правильность номера.",
                    reply_markup=get_final_keyboard()
                )
        except ValueError:
            await message.answer("Введите корректный ID (числом).", reply_markup=get_final_keyboard())
        await state.clear()
        return

    if current not in [s.state for s in state_order]:
        await message.answer("Пожалуйста, начните с команды /start")
        return

    idx = [s.state for s in state_order].index(current)
    key = questions[idx][0]
    await state.update_data({key: message.text})

    if idx + 1 < len(state_order):
        await state.set_state(state_order[idx + 1])
        await message.answer(questions[idx + 1][1], reply_markup=get_nav_keyboard())
    else:
        data = await state.get_data()

        user = message.from_user
        user_info = f"👤 Отправитель: {user.full_name}"
        if user.username:
            user_info += f" (@{user.username})"
        user_info += f"\n🆔 ID: {user.id}"

        text = (
            f"📩 Новая заявка на бота:\n\n"
            f"{user_info}\n\n"
            f"Имя: {data['name']}\n"
            f"Контакт: {data['contact']}\n"
            f"🤖 Название: {data['bot_name']}\n"
            f"🎯 Цель: {data['purpose']}\n"
            f"⚙️ Функции: {data['functions']}\n"
            f"🛠 Админ-панель: {data['admin_panel']}\n"
            f"📋 Кнопки: {data['buttons']}\n"
            f"💾 Данные: {data['data_storage']}\n"
            f"🔔 Уведомления: {data['notifications']}\n"
            f"💳 Оплата: {data['payment']}\n"
            f"🏢 Бизнес: {data['business_info']}\n"
            f"⏱ Срочность: {data['urgency']}\n"
            f"📝 Другое: {data['other']}"
        )

        admin_message = await bot.send_message(ADMIN_ID, text)
        request_id = add_full_request(**data, admin_message_id=admin_message.message_id)

        await message.answer(
            f"Спасибо! Ваша заявка принята ✅ Администратор с Вами свяжется!\n\n📌 ID заявки: {request_id}",
            reply_markup=get_final_keyboard()
        )
        await state.clear()

async def main():
    init_db()
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())

