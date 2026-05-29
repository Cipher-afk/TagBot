from aiogram import Dispatcher, Bot, Router, F
from aiogram.types import (
    Message,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    CallbackQuery,
)
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from config import settings
import asyncio

bot = Bot(token=settings.BOT_TOKEN)
dp = Dispatcher()
router = Router()


class LoginState(StatesGroup):
    phone_number = State()
    password = State()


login_button = InlineKeyboardMarkup(
    [InlineKeyboardButton(text="LogIn 🔐", callback_data="login")]
)


@router.message(Command("start"))
async def start(message: Message):
    await message.answer("Welcome to Tag Scraper", reply_markup=login_button)


@router.callback_query(F.data == "login")
async def handle_login(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    await state.set_state(LoginState.phone_number)
    await callback.message.edit_text("Enter Your Phone Number ☎")


async def main():
    dp.include_router(router=router)
    await dp.start_polling(bot)


if __name__ == "__main__":
    print("started....")
    asyncio.run(main())
