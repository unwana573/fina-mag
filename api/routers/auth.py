from fastapi import APIRouter, Depends
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from api.core.database import get_db
from api.core.dependencies import get_current_user
from api.models import User
from api.schemas.auth import (
    RegisterRequest, RefreshRequest,
    TokenResponse, Enable2FAResponse, Verify2FARequest,
)
from api.services.auth_service import AuthService

router = APIRouter(prefix="/auth", tags=["Auth"])


@router.post("/register", response_model=TokenResponse, status_code=201)
def register(body: RegisterRequest, db: Session = Depends(get_db)):
    return AuthService(db).register(body)


@router.post("/login", response_model=TokenResponse)
def login(
    form: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
):
    from api.schemas.auth import LoginRequest
    return AuthService(db).login(LoginRequest(email=form.username, password=form.password))


@router.post("/refresh", response_model=TokenResponse)
def refresh(body: RefreshRequest, db: Session = Depends(get_db)):
    return AuthService(db).refresh(body.refresh_token)


@router.post("/logout", status_code=204)
def logout(body: RefreshRequest, db: Session = Depends(get_db)):
    AuthService(db).logout(body.refresh_token)


@router.post("/2fa/enable", response_model=Enable2FAResponse)
def enable_2fa(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return AuthService(db).enable_2fa(current_user)


@router.post("/2fa/verify", status_code=200)
def verify_2fa(
    body: Verify2FARequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    AuthService(db).verify_2fa(current_user, body.code)
    return {"detail": "2FA enabled successfully"}