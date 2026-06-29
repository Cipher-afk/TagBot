from redis.asyncio import Redis
from config import settings

redis = Redis(
    host=settings.REDIS_HOST,
    port=settings.REDIS_PORT,
    password=settings.REDIS_PASSWORD,
    decode_responses=True,
)


async def save_userinfo(telegram_id: str, phone_number: str, password: str):
    await redis.hset(
        f"{telegram_id}_tag",
        mapping={"phone_number": phone_number, "password": password},
    )


async def get_userinfo(telegram_id: str):
    user_info = await redis.hgetall(f"{telegram_id}_tag")
    return user_info


async def save_plan(telegram_id: str, plan: str):
    await redis.set(f"{telegram_id}_plan", plan, ex=10800)


async def get_plan(telegram_id: str):
    current_plan = await redis.get(f"{telegram_id}_plan")
    return current_plan


async def set_task_done(telegram_id: str):
    await redis.set(f"{telegram_id}_task_done", True, ex=86400)


async def check_if_tasks_done(telegram_id: str):
    task_done = await redis.get(f"{telegram_id}_task_done")
    return True if task_done == "True" else False
