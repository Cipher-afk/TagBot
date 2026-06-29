from fastapi import FastAPI, Depends, HTTPException, Header
from fastapi.requests import Request
from backend.db_config import get_session, init_db
from contextlib import asynccontextmanager
from backend.services import PaymentService
from backend.schema import UserModel, UpdateModel
from sqlalchemy.ext.asyncio import AsyncSession
import httpx
from config import settings
from backend.models import Plan
from functools import lru_cache

service = PaymentService()


@lru_cache(maxsize=287)
async def cached_check_expired(phone_number: str, session: AsyncSession):
    expired = await service.payment_expired(phone_number=phone_number, session=session)
    return expired


@asynccontextmanager
async def lifespan(app: FastAPI):
    print("Server Starting...")
    await init_db()
    yield
    print("Server ending...")


app = FastAPI(title="tag_backend", lifespan=lifespan)


@app.get("/")
async def check_health():
    return "server_running"


@app.post("/create_user")
async def create_user(
    user_model: UserModel, session: AsyncSession = Depends(get_session)
):
    new_user = await service.create_user(user_info=user_model, session=session)
    return new_user


@app.post("/init_payment")
async def initialize_payment(
    phone_number: str, plan: str, session: AsyncSession = Depends(get_session)
):
    user = await service.get_user_by_phone_num(
        phone_number=phone_number, session=session
    )
    if user is None:
        raise HTTPException(status_code=404, detail="User Not Found")
    amount = 1000 if plan == Plan.basic else 1500
    if not user.is_paid:
        headers = {
            "Authorization": f"Bearer {settings.PAYSTACK_SECRET_KEY}",
            "Content-Type": "application/json",
        }

        data = {
            "email": settings.EMAIL,
            "amount": amount * 100,
            "metadata": {
                "telegram_id": user.telegram_id,
                "phone_number": user.phone_number,
                "amount": amount,
            },
        }
        async with httpx.AsyncClient(verify=False) as client:
            response = await client.post(
                url="https://api.paystack.co/transaction/initialize",
                headers=headers,
                json=data,
                timeout=100,
            )
            data = response.json()
            if not data["status"]:
                raise HTTPException(status_code=403, detail=data["message"])
            payment_link = data["data"]["authorization_url"]
        return {"payment_link": payment_link}
    # return {'payment_link':None}


@app.post("/webhook")
async def verify_payment(
    request: Request,
    x_paystack_signature: str = Header(None),
    session: AsyncSession = Depends(get_session),
):
    body = await request.body()
    if not await service.verify_signature(
        x_paystack_signature=x_paystack_signature, body=body
    ):
        raise HTTPException(status_code=403, detail="Bad Signature")
    await service.verfify_payment(body=body, session=session)
    cached_check_expired.cache_clear()


@app.get("/me")
async def get_user(telegram_id: str, session: AsyncSession = Depends(get_session)):
    user = await service.get_user_by_telegram_id(
        telegram_id=telegram_id, session=session
    )
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return user


@app.post("/update_info")
async def update_info(
    telegram_id: str,
    update_model: UpdateModel,
    session: AsyncSession = Depends(get_session),
):
    main_user = await service.get_user_by_telegram_id(
        telegram_id=telegram_id, session=session
    )
    user = await service.get_user_by_phone_num(
        phone_number=update_model.phone_number, session=session
    )
    info = update_model.info
    if user is None:
        info["plan"] = Plan.free
    else:
        info["plan"] = user.plan
        info["end_of_plan"] = user.end_of_plan
    await service.update_user_info(user=main_user, info=info, session=session)
    return {"Updated": True}


@app.get("/check_expired")
async def check_expired(
    phone_number: str, session: AsyncSession = Depends(get_session)
):
    expired = await cached_check_expired(phone_number, session)
    return expired


# @app.post("/update_password")
# async def update_password(telegram_id:str,password:str,session:AsyncSession = Depends(get_session)):
#     user = await service.get_user_by_telegram_id(
#         telegram_id=telegram_id, session=session
#     )
#     if user is None:
#         raise HTTPException(status_code=404, detail="User Not Found")
#     info = {'password':password}
#     await service.update_user_info(user=user, info=info, session=session)
#     return {"Updated": True}
