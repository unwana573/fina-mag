from fastapi import HTTPException
from sqlalchemy.orm import Session
from api.core.security import hash_password, verify_password, create_access_token
from api.core.audit import log
from api.repositories.user_repo import UserRepository
from api.repositories.refresh_token_repo import RefreshTokenRepository
from api.schemas.auth import RegisterRequest, LoginRequest, TokenResponse


class AuthService:
    def __init__(self, db: Session):
        self.user_repo = UserRepository(db)
        self.token_repo = RefreshTokenRepository(db)
        self.db = db

    def register(self, body: RegisterRequest) -> TokenResponse:
        if self.user_repo.email_exists(body.email):
            raise HTTPException(status_code=409, detail="Email already registered")

        user = self.user_repo.create({
            "email": body.email,
            "full_name": body.full_name,
            "hashed_password": hash_password(body.password),
            "currency": "NGN",
        })
        token = self.token_repo.create_for_user(user.id)
        log(self.db, action="user.registered", user_id=user.id, entity="user", entity_id=user.id)
        return TokenResponse(
            access_token=create_access_token(user.id),
            refresh_token=token.token,
        )

    def login(self, body: LoginRequest) -> TokenResponse:
        user = self.user_repo.get_by_email(body.email)

        if not user:
            raise HTTPException(status_code=401, detail="Invalid email or password")

        if not user.hashed_password:
            raise HTTPException(
                status_code=401,
                detail="This account uses Google or Apple sign-in. Please use that instead."
            )

        if not verify_password(body.password, user.hashed_password):
            log(self.db, action="user.login_failed", user_id=user.id, detail=f"email={body.email}")
            raise HTTPException(status_code=401, detail="Invalid email or password")

        if not user.is_active:
            raise HTTPException(status_code=403, detail="Account disabled")

        token = self.token_repo.create_for_user(user.id)
        log(self.db, action="user.login", user_id=user.id)
        return TokenResponse(
            access_token=create_access_token(user.id),
            refresh_token=token.token,
        )

    def refresh(self, refresh_token: str) -> TokenResponse:
        stored = self.token_repo.get_by_token(refresh_token)
        if not stored:
            raise HTTPException(status_code=401, detail="Invalid refresh token")
        if self.token_repo.is_expired(stored):
            self.token_repo.delete(stored)
            raise HTTPException(status_code=401, detail="Refresh token expired")

        new_token = self.token_repo.rotate(stored)
        return TokenResponse(
            access_token=create_access_token(new_token.user_id),
            refresh_token=new_token.token,
        )

    def logout(self, refresh_token: str) -> None:
        stored = self.token_repo.get_by_token(refresh_token)
        if stored:
            log(self.db, action="user.logout", user_id=stored.user_id)
            self.token_repo.revoke(refresh_token)

    def enable_2fa(self, user) -> dict:
        try:
            import pyotp
        except ImportError:
            raise HTTPException(status_code=501, detail="Install pyotp: pip install pyotp")

        if not user.hashed_password:
            raise HTTPException(
                status_code=400,
                detail="Set a password on your account before enabling 2FA."
            )

        from api.core.config import settings
        secret = pyotp.random_base32()
        totp = pyotp.TOTP(secret)
        uri = totp.provisioning_uri(name=user.email, issuer_name=settings.TOTP_ISSUER)
        self.user_repo.set_totp_secret(user, secret)
        log(self.db, action="user.2fa_enabled", user_id=user.id)
        return {"otp_uri": uri, "secret": secret}

    def verify_2fa(self, user, code: str) -> None:
        try:
            import pyotp
        except ImportError:
            raise HTTPException(status_code=501, detail="Install pyotp: pip install pyotp")

        if not user.totp_secret:
            raise HTTPException(status_code=400, detail="2FA not set up — call /2fa/enable first")

        totp = pyotp.TOTP(user.totp_secret)
        if not totp.verify(code, valid_window=1):
            log(self.db, action="user.2fa_failed", user_id=user.id)
            raise HTTPException(status_code=400, detail="Invalid or expired OTP code")

        self.user_repo.enable_2fa(user)
        log(self.db, action="user.2fa_verified", user_id=user.id)