from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel
from api.models import TransactionType


class TransactionCreate(BaseModel):
    description: str
    amount: float
    type: TransactionType
    category_id: Optional[int] = None
    date: Optional[datetime] = None


class TransactionUpdate(BaseModel):
    description: Optional[str] = None
    amount: Optional[float] = None
    category_id: Optional[int] = None
    date: Optional[datetime] = None


class TransactionResponse(BaseModel):
    id: int
    description: str
    amount: float
    type: TransactionType
    category_id: Optional[int]
    date: datetime
    created_at: datetime

    class Config:
        from_attributes = True


class PaginatedTransactions(BaseModel):
    items: List[TransactionResponse]
    total: int
    skip: int
    limit: int