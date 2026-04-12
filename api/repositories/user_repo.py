from typing import Optional
from sqlalchemy.orm import Session
from api.models import User
from api.repositories.base import BaseRepository


class UserRepository(BaseRepository[User]):
    def __init__(self, db: Session):
        super().__init__(User, db)

    def get_by_email(self, email: str) -> Optional[User]:
        return self.db.query(User).filter(User.email == email).first()

    def email_exists(self, email: str) -> bool:
        return self.db.query(User.id).filter(User.email == email).scalar() is not None

    def set_totp_secret(self, user: User, secret: str) -> User:
        user.totp_secret = secret
        self.db.commit()
        self.db.refresh(user)
        return user

    def enable_2fa(self, user: User) -> User:
        user.two_fa_enabled = True
        self.db.commit()
        self.db.refresh(user)
        return user