from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel
from api.core.database import get_db
from api.core.dependencies import get_current_user
from api.models import User, Category

router = APIRouter(prefix="/categories", tags=["Categories"])


class CategoryResponse(BaseModel):
    id: int
    name: str

    class Config:
        from_attributes = True


class CategoryCreate(BaseModel):
    name: str


@router.get("", response_model=list[CategoryResponse])
def list_categories(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return db.query(Category).order_by(Category.name).all()


@router.post("", response_model=CategoryResponse, status_code=201)
def create_category(
    body: CategoryCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    category = Category(name=body.name)
    db.add(category)
    db.commit()
    db.refresh(category)
    return category