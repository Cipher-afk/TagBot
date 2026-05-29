from redis.asyncio import Redis
from config import settings

redis = Redis(host=settings.REDIS_HOST, port=settings.REDIS_PORT)


async def save_userinfo(telegram_id: str, phone_number: str, password: str):
    edited_phonenum = phone_number.lstrip("0")
    await redis.hset(
        telegram_id, mapping={"phone_number": edited_phonenum, "password": password}
    )


async def get_userinfo(telegram_id: str):
    user_info = await redis.hgetall(telegram_id)
    return userinfo
