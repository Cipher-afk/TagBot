from pydantic import BaseModel


class UserModel(BaseModel):
    telegram_id: str
    phone_number: str
    password: str


class UpdateModel(BaseModel):
    telegram_id: str
    info: dict[str, str]
