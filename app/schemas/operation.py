from datetime import datetime
from decimal import Decimal
from enum import Enum

from pydantic import BaseModel, Field


class OperationKind(str, Enum):
    income = "income"
    expense = "expense"


class OperationBase(BaseModel):
    amount: Decimal = Field(..., gt=0, description="Сумма операции")
    kind: OperationKind = Field(..., description="Тип операции: income или expense")
    category_id: int = Field(..., description="ID категории")
    description: str | None = Field(None, description="Описание операции")


class OperationCreate(OperationBase):
    pass  # все поля обязательны


class OperationUpdate(BaseModel):
    amount: Decimal | None = Field(None, gt=0)
    kind: OperationKind | None = None
    category_id: int | None = None
    description: str | None = None


class OperationInDB(OperationBase):
    id: int = Field(..., description="PK операции")
    user_id: int = Field(..., description="ID пользователя")
    ts: datetime = Field(..., description="Время создания операции")

    class Config:
        orm_mode = True


class OperationOut(OperationInDB):
    """То, что возвращаем клиенту"""
    pass