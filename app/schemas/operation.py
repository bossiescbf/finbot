from datetime import datetime
from decimal import Decimal
from enum import Enum
from pydantic import BaseModel, ConfigDict, Field


class OperationKind(str, Enum):
    income = "income"
    expense = "expense"


class OperationBase(BaseModel):
    amount: Decimal = Field(..., gt=0, description="Сумма операции")
    kind: OperationKind = Field(..., description="Тип операции: income или expense")
    category_id: int = Field(..., description="ID категории")
    description: str | None = Field(None, description="Описание операции")


class OperationCreate(OperationBase):
    pass


class OperationUpdate(BaseModel):
    amount: Decimal | None = Field(None, gt=0)
    kind: OperationKind | None = None
    category_id: int | None = None
    description: str | None = None


class OperationInDB(OperationBase):
    model_config = ConfigDict(from_attributes=True)  # ← НОВЫЙ синтаксис V2
    
    id: int = Field(..., description="PK операции")
    user_id: int = Field(..., description="ID пользователя")
    ts: datetime = Field(..., description="Время создания операции")


class OperationOut(OperationInDB):
    pass