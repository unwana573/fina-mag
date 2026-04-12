from typing import List, Optional
from pydantic import BaseModel


class BudgetItemCreate(BaseModel):
    category_id: int
    limit: float


class BudgetItemResponse(BaseModel):
    id: int
    category_id: int
    limit: float
    spent: float = 0.0
    remaining: float = 0.0

    class Config:
        from_attributes = True


class BudgetCreate(BaseModel):
    month: int
    year: int
    items: List[BudgetItemCreate]


class BudgetUpdate(BaseModel):
    items: List[BudgetItemCreate]


class BudgetResponse(BaseModel):
    id: int
    month: int
    year: int
    total_budget: float
    total_spent: float
    remaining: float
    items: List[BudgetItemResponse]

    class Config:
        from_attributes = True