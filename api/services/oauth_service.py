from sqlalchemy.orm import Session
from api.models import User, OAuthAccount
from api.repositories.user_repo import UserRepository
from api.repositories.refresh_token_repo import RefreshTokenRepository
from api.core.security import create_access_token
from api.schemas.auth import TokenResponse
from fastapi import HTTPException

class OAuthService:
    def __init__(self, db: Session):
        self.db = db
        self.user_repo = UserRepository(db)
        self.token_repo = RefreshTokenRepository(db)

    def _get_oauth_account(self, provider: str, provider_id: str):
        return (
            self.db.query(OAuthAccount)
            .filter(
                OAuthAccount.provider == provider,
                OAuthAccount.provider_id == provider_id,
            )
            .first()
        )

    def _create_oauth_user(self, email: str, full_name: str, provider: str, provider_id: str, avatar_url: str = None) -> User:
        user = self.user_repo.get_by_email(email)

        if not user:
            user = self.user_repo.create({
                "email": email,
                "full_name": full_name or email.split("@")[0],
                "hashed_password": None,
                "currency": "NGN",
                "avatar_url": avatar_url,
            })

        existing_oauth = self._get_oauth_account(provider, provider_id)
        if not existing_oauth:
            oauth_account = OAuthAccount(
                user_id=user.id,
                provider=provider,
                provider_id=provider_id,
                avatar_url=avatar_url,
            )
            self.db.add(oauth_account)
            self.db.commit()

        return user

    def authenticate(self, provider_data: dict) -> TokenResponse:
        provider    = provider_data["provider"]
        provider_id = provider_data["provider_id"]
        email       = provider_data["email"]
        full_name   = provider_data.get("full_name", "")
        avatar_url  = provider_data.get("avatar_url")

        oauth_account = self._get_oauth_account(provider, provider_id)

        if oauth_account:
            user = oauth_account.user
        else:
            user = self._create_oauth_user(email, full_name, provider, provider_id, avatar_url)

        if not user.is_active:
            
            raise HTTPException(status_code=403, detail="Account disabled")

        token = self.token_repo.create_for_user(user.id)
        return TokenResponse(
            access_token=create_access_token(user.id),
            refresh_token=token.token,
        )