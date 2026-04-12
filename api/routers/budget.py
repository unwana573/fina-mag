from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from api.core.database import get_db
from api.core.dependencies import get_current_user
from api.models import User
from api.schemas.budget import BudgetCreate, BudgetUpdate, BudgetResponse
from api.services.budget_service import BudgetService

router = APIRouter(prefix="/budget", tags=["Budget"])


@router.get("", response_model=BudgetResponse)
def get_budget(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return BudgetService(db).get_current(current_user.id)


@router.post("", response_model=BudgetResponse, status_code=201)
def create_budget(
    body: BudgetCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return BudgetService(db).create(current_user.id, body)


@router.put("/{budget_id}", response_model=BudgetResponse)
def update_budget(
    budget_id: int,
    body: BudgetUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return BudgetService(db).update(current_user.id, budget_id, body)


@router.patch("/categories/{budget_id}/{category_id}")
def update_category_limit(
    budget_id: int,
    category_id: int,
    limit: float,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return BudgetService(db).update_category(current_user.id, budget_id, category_id, limit)