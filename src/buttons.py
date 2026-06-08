from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder


def create_button(text: str, callback_data):
    builder = InlineKeyboardBuilder()
    builder.button(text=text, callback_data=callback_data)
    return builder.as_markup()


def payment_buttons():
    buttons = []
    builder = InlineKeyboardBuilder()
    # builder.button(text="💳 Pay Now", callback_data="pay")
    builder.add(
        InlineKeyboardButton(text="💳 Pay Now", callback_data="pay"),
        InlineKeyboardButton(text="🔙 Back to Payment Plans", callback_data="back"),
    )
    return builder.as_markup()


login_button = create_button(text="LogIn 🔐", callback_data="login")

try_again_button = create_button(text="🔃 Try Again", callback_data="try_again")

do_tasks_button = create_button(text="🤖 Do Tasks", callback_data="tasks")

pay_now_button = create_button(text="💳 Pay Now", callback_data="pay")

back_to_plans_button = create_button(
    text="🔙 Back to Payment Plans", callback_data="back"
)

renew_button = create_button(text="💳 Renew Plan", callback_data="back")

view_plans_button = create_button(text="💰 View Plans", callback_data="back")

update_password_button = create_button(text="Change Password", callback_data="change")
