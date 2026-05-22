from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import or_
from pydantic import BaseModel
from api.core.database import get_db
from api.core.dependencies import get_current_user
from api.core.audit import log
from api.models import User, Category

router = APIRouter(prefix="/categories", tags=["Categories"])


class CategoryResponse(BaseModel):
    id: int
    name: str
    is_custom: bool = False

    class Config:
        from_attributes = True


class CategoryCreate(BaseModel):
    name: str


@router.get("", response_model=list[CategoryResponse])
def list_categories(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Returns global categories + user's own custom categories.
    user_id = NULL means global, user_id = current user means custom.
    """
    categories = (
        db.query(Category)
        .filter(
            or_(Category.user_id == None, Category.user_id == current_user.id)
        )
        .order_by(Category.name)
        .all()
    )
    return [
        CategoryResponse(
            id=c.id,
            name=c.name,
            is_custom=c.user_id is not None,
        )
        for c in categories
    ]


@router.post("", response_model=CategoryResponse, status_code=201)
def create_category(
    body: CategoryCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Creates a custom category visible only to the current user."""
    existing = (
        db.query(Category)
        .filter(
            Category.name == body.name,
            or_(Category.user_id == None, Category.user_id == current_user.id)
        )
        .first()
    )
    if existing:
        raise HTTPException(status_code=409, detail="Category already exists")

    category = Category(name=body.name, user_id=current_user.id)
    db.add(category)
    db.commit()
    db.refresh(category)
    log(db, action="category.created", user_id=current_user.id,
        entity="category", entity_id=category.id, detail=f"name={body.name}")
    return CategoryResponse(id=category.id, name=category.name, is_custom=True)


@router.delete("/{category_id}", status_code=204)
def delete_category(
    category_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Only custom categories created by the user can be deleted."""
    category = db.query(Category).filter(
        Category.id == category_id,
        Category.user_id == current_user.id,
    ).first()

    if not category:
        raise HTTPException(
            status_code=404,
            detail="Category not found or you can't delete a global category"
        )

    log(db, action="category.deleted", user_id=current_user.id,
        entity="category", entity_id=category_id)
    db.delete(category)
    db.commit()