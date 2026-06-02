from sqlmodel import SQLModel, Field, Column
from datetime import datetime
import sqlalchemy.dialects.postgresql as pg
from enum import Enum


class Plan(str, Enum):
    free: str = "free"
    basic: str = "basic"
    premium: str = "premium"


class User(SQLModel, table=True):
    __tablename__ = "users"
    telegram_id: str = Field(
        sa_column=Column(pg.VARCHAR, unique=True, primary_key=True, nullable=False)
    )
    phone_number: str
    password: str
    plan: str = Field(sa_column=Column(pg.VARCHAR, default=Plan.free))
    is_paid: bool = Field(sa_column=Column(pg.BOOLEAN, default=False))
    end_of_plan: float = Field(sa_column=Column(pg.FLOAT, nullable=True, default=None))
