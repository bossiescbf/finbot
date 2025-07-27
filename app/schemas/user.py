from datetime import datetime
from pydantic import BaseModel, Field


class UserBase(BaseModel):
    telegram_id: int = Field(..., description="ID пользователя в Telegram")
    username: str | None = Field(None, description="Логин пользователя в Telegram")
    first_name: str | None = Field(None, description="Имя пользователя")
    last_name: str | None = Field(None, description="Фамилия пользователя")


class UserCreate(UserBase):
    pass  # все поля UserBase обязательны при создании


class UserUpdate(BaseModel):
    """Поля, которые можно обновить"""
    username: str | None = None
    first_name: str | None = None
    last_name: str | None = None


class UserInDB(UserBase):
    id: int = Field(..., description="PK в БД")
    created_at: datetime = Field(..., description="Время создания записи")

    class Config:
        orm_mode = True


class UserOut(UserInDB):
    """То, что возвращаем клиенту"""
    pass