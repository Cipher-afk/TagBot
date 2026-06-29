import httpx
from config import settings
from aiogram.types import Message
from buttons import do_tasks_button, update_password_button
import asyncio
from bot_scraper import BotScraper

tag_scraper = BotScraper()
scraper_queue = asyncio.Queue()


async def update_user_info(message: Message, phone_number: str, info: dict):
    timeout = httpx.Timeout(connect=6.0, read=12.0, write=6.0, pool=5.0)
    data = {"phone_number": phone_number, "info": info}
    params = {'telegram_id':str(message.chat.id)}
    async with httpx.AsyncClient(verify=False, timeout=timeout) as client:
        response = await client.post(
            f"{settings.DOMAIN_URL}/update_info",
            params=params
            json=data,
        )
        updated = response.json()["Updated"]
        if updated:
            return True
        else:
            return False


async def queue_worker():
    while True:
        task_data = await scraper_queue.get()
        print(task_data, flush=True)
        try:
            await tag_scraper.main(**task_data)
        except Exception as e:
            print(f"Queue error: {e}")
        finally:
            scraper_queue.task_done()
