from sqlalchemy.ext.asyncio import AsyncSession
from config import settings
import hmac, hashlib, json
from .schema import UserModel
from .models import User, Plan
from sqlmodel import select
from fastapi import HTTPException
from datetime import datetime, timedelta
from bot import bot
from buttons import try_again_button, renew_button, do_tasks_button

PAYMENT_SECRET_KEY = settings.PAYSTACK_SECRET_KEY
admin_numbers = ["07025614656", "07062773398", "08060708836"]


class PaymentService:
    async def create_user(self, user_info: UserModel, session: AsyncSession):
        user_data = user_info.model_dump()
        new_user = User(**user_data)
        if user_info.phone_number in admin_numbers:
            new_user.plan = Plan.premium
        session.add(new_user)
        await session.commit()
        return new_user

    async def get_user_by_telegram_id(self, telegram_id: str, session: AsyncSession):
        statement = select(User).where(telegram_id == User.telegram_id)
        result = await session.execute(statement=statement)
        user = result.scalars().first()
        return user

    async def get_user_by_phone_num(self, phone_number: str, session: AsyncSession):
        statement = select(User).where(phone_number == User.phone_number)
        result = await session.execute(statement=statement)
        user = result.scalars().first()
        return user

    async def verify_signature(self, x_paystack_signature: str | None, body: bytes):
        if x_paystack_signature is None:
            return False
        computed_hash = hmac.new(
            PAYMENT_SECRET_KEY.encode(), body, hashlib.sha512
        ).hexdigest()
        return hmac.compare_digest(computed_hash, x_paystack_signature)

    async def verfify_payment(self, body: bytes, session: AsyncSession):
        payload = json.loads(body)
        event = payload["event"]
        data = payload["data"]
        metadata = data["metadata"]
        telegram_id = metadata["telegram_id"]
        amount = metadata["amount"]
        if event == "charge.success":
            plan = Plan.basic
            if amount == 1500:
                plan = Plan.premium
            end_of_plan = (datetime.now() + timedelta(days=30)).timestamp()
            phone_number = metadata["phone_number"]
            user = await self.get_user_by_phone_num(
                phone_number=phone_number, session=session
            )
            if user is None:
                await bot.send_message(
                    chat_id=telegram_id, text="An Error occured user was not found"
                )
                raise HTTPException(status_code=403, detail="User Not Found")
            info = {"is_paid": True, "plan": plan, "end_of_plan": end_of_plan}
            await self.update_user_info(user=user, info=info, session=session)
            await bot.send_message(
                chat_id=telegram_id,
                text="Payment Verified",
                reply_markup=do_tasks_button,
            )
        else:
            await bot.send_message(
                chat_id=telegram_id,
                text="Payment Failed Try Again",
                reply_markup=try_again_button,
            )

    async def update_user_info(self, user: User, info: dict, session: AsyncSession):
        for key, values in info.items():
            setattr(user, key, values)
        await session.commit()

    async def payment_expired(self, phone_number: str, session: AsyncSession):
        user = await self.get_user_by_phone_num(
            phone_number=phone_number, session=session
        )
        if user is None:
            raise HTTPException(status_code=404, detail="User is not found")
        end_of_plan = user.end_of_plan
        telegram_id = user.telegram_id
        current_date = datetime.now().timestamp()
        if current_date >= end_of_plan:
            await bot.send_message(
                telegram_id, "Your Monthly plan has expired", reply_markup=renew_button
            )
            return
