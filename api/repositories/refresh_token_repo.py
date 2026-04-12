from datetime import datetime, timedelta
from typing import Optional
from sqlalchemy.orm import Session
from api.models import RefreshToken
from api.repositories.base import BaseRepository
from api.core.config import settings
from api.core.security import generate_refresh_token


class RefreshTokenRepository(BaseRepository[RefreshToken]):
    def __init__(self, db: Session):
        super().__init__(RefreshToken, db)

    def get_by_token(self, token: str) -> Optional[RefreshToken]:
        return self.db.query(RefreshToken).filter(RefreshToken.token == token).first()

    def create_for_user(self, user_id: int) -> RefreshToken:
        raw = generate_refresh_token()
        return self.create({
            "user_id": user_id,
            "token": raw,
            "expires_at": datetime.utcnow() + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS),
        })

    def rotate(self, old_token: RefreshToken) -> RefreshToken:
        user_id = old_token.user_id
        self.delete(old_token)
        return self.create_for_user(user_id)

    def revoke(self, token: str) -> None:
        stored = self.get_by_token(token)
        if stored:
            self.delete(stored)

    def is_expired(self, token: RefreshToken) -> bool:
        return token.expires_at < datetime.utcnow()