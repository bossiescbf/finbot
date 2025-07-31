from datetime import datetime
from decimal import Decimal
from enum import Enum
from pydantic import BaseModel, ConfigDict, Field
from typing import Literal

class OperationBase(BaseModel):
    amount: Decimal = Field(..., gt=0, description="Сумма операции")
    type: str = Field(..., description="Тип операции: income или expense") 
    category_id: int = Field(..., description="ID категории")
    description: str | None = Field(None, description="Описание операции")

class OperationCreate(BaseModel):
    amount: float
    category_id: int
    type: Literal['income', 'expense']
    occurred_at: datetime

class OperationUpdate(BaseModel):
    amount: Decimal | None = Field(None, gt=0)
    type: str | None = None
    category_id: int | None = None
    description: str | None = None

class OperationInDB(OperationBase):
    model_config = ConfigDict(from_attributes=True)
    
    id: int = Field(..., description="PK операции")
    user_id: int = Field(..., description="ID пользователя")
    occurred_at: datetime = Field(..., description="Время операции")
    created_at: datetime = Field(..., description="Время создания записи")

class OperationOut(OperationInDB):
    pass