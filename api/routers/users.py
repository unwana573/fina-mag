from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from api.core.database import get_db
from api.core.dependencies import get_current_user
from api.core.security import verify_password, hash_password
from api.models import User
from api.schemas.user import UserResponse, UpdateUserRequest, ChangePasswordRequest

router = APIRouter(prefix="/users", tags=["Users"])


@router.get("/me", response_model=UserResponse)
def get_me(current_user: User = Depends(get_current_user)):
    return current_user


@router.put("/me", response_model=UserResponse)
def update_me(
    body: UpdateUserRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if body.full_name:
        current_user.full_name = body.full_name
    if body.currency:
        current_user.currency = body.currency
    db.commit()
    db.refresh(current_user)
    return current_user


@router.put("/me/password", status_code=200)
def change_password(
    body: ChangePasswordRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if not current_user.hashed_password:
        raise HTTPException(
            status_code=400,
            detail="This account uses Google or Apple sign-in and has no password. "
                   "Use /users/me/set-password to add one."
        )
    if not verify_password(body.current_password, current_user.hashed_password):
        raise HTTPException(status_code=400, detail="Current password is incorrect")
    current_user.hashed_password = hash_password(body.new_password)
    db.commit()
    return {"detail": "Password updated successfully"}


@router.post("/me/set-password", status_code=200)
def set_password(
    body: ChangePasswordRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Allows OAuth users (Google/Apple) to add a password to their account
    so they can also log in with email + password.
    """
    if current_user.hashed_password:
        raise HTTPException(
            status_code=400,
            detail="Account already has a password. Use /users/me/password to change it."
        )
    current_user.hashed_password = hash_password(body.new_password)
    db.commit()
    return {"detail": "Password set successfully"}


@router.delete("/me", status_code=204)
def delete_me(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    db.delete(current_user)
    db.commit()