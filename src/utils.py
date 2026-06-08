import httpx
from config import settings
from aiogram.types import Message
from buttons import do_tasks_button, update_password_button


async def update_user_info(message: Message, telegram_id: str, info: dict):
    timeout = httpx.Timeout(connect=6.0, read=12.0, write=6.0, pool=5.0)
    data = {"telegram_id": telegram_id, "info": info}
    async with httpx.AsyncClient(verify=False, timeout=timeout) as client:
        response = await client.post(
            f"{settings.DOMAIN_URL}/update_info",
            json=data,
        )
        updated = response.json()["Updated"]
        if updated:
            return True
        else:
            return False
