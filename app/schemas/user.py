from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field


class UserBase(BaseModel):
    telegram_id: int = Field(..., description="ID пользователя в Telegram")
    username: str | None = Field(None, description="Логин пользователя в Telegram")
    first_name: str | None = Field(None, description="Имя пользователя")
    last_name: str | None = Field(None, description="Фамилия пользователя")


class UserCreate(UserBase):
    pass


class UserUpdate(BaseModel):
    username: str | None = None
    first_name: str | None = None
    last_name: str | None = None


class UserInDB(UserBase):
    model_config = ConfigDict(from_attributes=True)  # ← НОВЫЙ синтаксис V2
    
    id: int = Field(..., description="PK в БД")
    created_at: datetime = Field(..., description="Время создания записи")


class UserOut(UserInDB):
    pass