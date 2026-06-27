from aiogram import Dispatcher, Bot, Router, F
from aiogram.types import (
    Message,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    CallbackQuery,
)
from aiogram.utils.keyboard import InlineKeyboardBuilder
from backend.models import Plan
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from config import settings
from redis_config import save_userinfo, get_userinfo, get_plan, save_plan
import asyncio
from aiogram.exceptions import TelegramNetworkError
from bot_scraper import BotScraper
import httpx
from buttons import (
    login_button,
    try_again_button,
    do_tasks_button,
    pay_now_button,
    back_to_plans_button,
    renew_button,
    view_plans_button,
    payment_buttons,
    update_password_button,
)
from scheduler import scheduler
from utils import update_user_info, queue_worker
import asyncio

scrape_queue = asyncio.Queue()

tag_scraper = BotScraper()

bot = Bot(token=settings.BOT_TOKEN)
dp = Dispatcher()
router = Router()


class LoginState(StatesGroup):
    phone_number = State()
    password = State()


class UpdatePasswordState(StatesGroup):
    new_password = State()


async def get_payment_buttons():
    builder = InlineKeyboardBuilder()
    free_button = InlineKeyboardButton(text=" 🆓 Free", callback_data=Plan.free)
    basic_button = InlineKeyboardButton(text=" ⚡ Basic", callback_data=Plan.basic)
    premium_button = InlineKeyboardButton(
        text=" 💎 Premium", callback_data=Plan.premium
    )
    builder.add(free_button, basic_button, premium_button)
    return builder.as_markup()


async def get_user(message: Message):
    """This function gets the user from the backend and return the users info as a dictionary"""
    timeout = httpx.Timeout(connect=6.0, read=12.0, write=6.0, pool=5.0)
    async with httpx.AsyncClient(verify=False, timeout=timeout) as client:
        response = await client.get(
            f"{settings.DOMAIN_URL}/me", params={"telegram_id": str(message.chat.id)}
        )
        if response.is_error:
            print(response.json())
            await message.answer("An error occured while getting user try again...")
            return
        user = response.json()
        return user


async def get_payment_link(message: Message):
    data = await get_userinfo(telegram_id=message.chat.id)
    plan = await get_plan(telegram_id=message.chat.id)
    if data is not None:
        phone_number, password = data["phone_number"], data["password"]
    else:
        user = await get_user(message=message)
        phone_number, password = user["phone_number"], user["password"]
    timeout = httpx.Timeout(connect=6.0, read=12.0, write=6.0, pool=5.0)
    async with httpx.AsyncClient(verify=False, timeout=timeout) as client:
        response = await client.post(
            f"{settings.DOMAIN_URL}/init_payment",
            params={"phone_number": phone_number, "plan": plan},
        )
        data = response.json()
        return data["payment_link"]


async def do_tasks(message: Message):
    telegram_id = message.chat.id
    data = await get_userinfo(telegram_id=telegram_id)
    if data is not None:
        phone_number = data["phone_number"]
        password = data["password"]
        plan = await get_plan(telegram_id=telegram_id)
    else:
        user = await get_user(message=message)
        phone_number = user["phone_number"]
        password = user["password"]
        plan = user["plan"]
        await save_userinfo(
            telegram_id=telegram_id, phone_number=phone_number, password=password
        )
        await save_plan(telegram_id=telegram_id, plan=plan)
    await scrape_queue.put(
        {
            "phone_number": phone_number,
            "password": password,
            "message": message,
            "bot": bot,
            "plan": plan,
        }
    )
    await message.answer("Your Tasks are loading..... ⏳")
    # await tag_scraper.main(
    #     phone_number=phone_number,
    #     password=password,
    #     message=message,
    #     bot=bot,
    #     plan=plan,
    # )
    if plan == Plan.premium:
        scheduler.add_job(
            do_tasks, trigger="cron", day_of_week="mon-sat", hour=2, args=[message]
        )


@router.message(Command("start"))
async def start(message: Message):
    await message.answer("Welcome to Tag Scraper", reply_markup=login_button)


@router.callback_query(F.data == "try_again")
async def try_again(callback: CallbackQuery):
    await callback.answer()
    current_plan = await get_plan(telegram_id=callback.message.chat.id)
    await callback.message.edit_text("Payment Link Loading....")
    payment_link = await get_payment_link(plan=current_plan, message=callback.message)
    await callback.message.answer(
        f"Click On the link below to try again \n {payment_link}",
        reply_markup=try_again_button,
    )


@router.callback_query(F.data == Plan.free)
async def handle_free_user(callback: CallbackQuery):
    await callback.answer()
    await callback.message.edit_text(
        "🆓 Free \n Run Up to 3 tasks a day manually".title(),
        reply_markup=do_tasks_button,
    )


@router.callback_query(F.data == Plan.basic)
async def handle_basic_user(callback: CallbackQuery):
    await callback.answer()
    p_buttons = payment_buttons()
    await save_plan(telegram_id=callback.message.chat.id, plan=Plan.basic)
    await callback.message.edit_text(
        "⚡ Basic \n Run all your tasks at once, just show up once a day".title(),
        reply_markup=p_buttons,
    )


@router.callback_query(F.data == Plan.premium)
async def handle_premium_user(callback: CallbackQuery):
    await callback.answer()
    p_buttons = payment_buttons()
    await save_plan(telegram_id=callback.message.chat.id, plan=Plan.premium)
    await callback.message.edit_text(
        "👑 Premium \n The bot runs everything for you,every single day automatically".title(),
        reply_markup=p_buttons,
    )


@router.callback_query(F.data == "tasks")
async def handle_tasks(callback: CallbackQuery):
    await callback.answer()
    await do_tasks(message=callback.message)


@router.callback_query(F.data == "pay")
async def handle_pay(callback: CallbackQuery):
    await callback.answer()
    await callback.message.edit_text("Payment link loading....")
    payment_link = await get_payment_link(message=callback.message)
    await callback.message.edit_text(
        f"Click on the link below to make your payment 👇 \n {payment_link}",
        reply_markup=back_to_plans_button,
    )


@router.callback_query(F.data == "back")
async def go_to_plans(callback: CallbackQuery):
    await callback.answer()
    payment_buttons = await get_payment_buttons()
    await callback.message.edit_text(
        "Meet Tag Scraper 🤖 \n A bot that does all your tag tasks for you no stress just pure comfort \n Whether you want full control or you want the bot to handle everything while you just relax we have a plan for you\n Pick a plan now and get started in seconds",
        reply_markup=payment_buttons,
    )


@router.callback_query(F.data == "change")
async def update_password(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    await callback.message.answer("Enter Correct Password")
    await state.set_state(UpdatePasswordState.new_password)


@router.message(UpdatePasswordState.new_password)
async def handle_new_password(message: Message):
    new_password = message.text
    telegram_id = message.chat.id
    info = {"password": new_password}
    updated = await update_user_info(
        message=message, telegram_id=telegram_id, info=info
    )
    if updated:
        await message.answer(
            "Password Updated Successfully", reply_markup=do_tasks_button
        )
    else:
        await message.answer(
            "An Error Ocuured Try Again", reply_markup=update_password_button
        )


@router.callback_query(F.data == "login")
async def handle_login(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    await callback.message.answer("Enter Your Phone Number ☎")
    await state.set_state(LoginState.phone_number)


@router.message(LoginState.phone_number)
async def handle_username(
    message: Message,
    state: FSMContext,
):
    await state.update_data(phone_number=message.text)
    await message.answer("Enter your password 🔒".title())
    await state.set_state(LoginState.password)


@router.message(LoginState.password)
async def handle_password(message: Message, state: FSMContext):
    try:
        data = await state.get_data()
        phone_number = data["phone_number"]
        edited_phone_number = phone_number.lstrip("0")
        password = message.text
        telegram_id = str(message.chat.id)
        await state.clear()
        data = {
            "telegram_id": telegram_id,
            "phone_number": edited_phone_number,
            "password": password,
        }
        info = {
            "phone_number": edited_phone_number,
            "password": password,
        }
        user = await get_user(message=message)
        if user is not None:
            updated = await update_user_info(
                message=message, telegram_id=telegram_id, info=info
            )
            if updated:
                await message.answer(
                    "User Information Updated Successfully",
                    reply_markup=do_tasks_button,
                )
            else:
                await message.answer(
                    "Error occured while updating", reply_markup=login_button
                )
            return
        timeout = httpx.Timeout(connect=6.0, read=12.0, write=6.0, pool=5.0)
        async with httpx.AsyncClient(verify=False, timeout=timeout) as client:
            response = await client.post(
                f"{settings.DOMAIN_URL}/create_user", json=data
            )
            user = response.json()
            if user is not None:
                await save_userinfo(
                    telegram_id=telegram_id,
                    phone_number=edited_phone_number,
                    password=password,
                )
        await message.answer("Credentials Saving.....")
        await message.answer(
            "Credentials saved you can continue".title(), reply_markup=view_plans_button
        )
    except TelegramNetworkError:
        await message.answer("Check Your Network and try again".title())


@router.message(Command("do_tasks"))
async def complete_task(message: Message):
    await message.answer("Scraping Started 🚀")
    await do_tasks(message=message)


@router.message(Command("view_plans"))
async def view_plans(message: Message):
    payment_buttons = await get_payment_buttons()
    await message.answer(
        "Meet Tag Scraper 🤖 \n A bot that does all your tag tasks for you no stress just pure comfort \n Whether you want full control or you want the bot to handle everything while you just relax we have a plan for you\n Pick a plan now and get started in seconds",
        reply_markup=payment_buttons,
    )


async def main():
    dp.include_router(router=router)
    await asyncio.create_task(queue_worker())
    await dp.start_polling(bot)


if __name__ == "__main__":
    print("started....")
    asyncio.run(main())
