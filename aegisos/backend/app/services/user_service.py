import re
import secrets
from uuid import UUID
from sqlalchemy.orm import Session

from app.models.user import User
from app.schemas.user import UserCreate, UserUpdate
from app.core.security import password_hash, verify_password


class UserService:
    def _derive_username(self, db: Session, user_create: UserCreate) -> str:
        """Derive a unique username from full_name or email when not explicitly provided."""
        base = user_create.full_name or user_create.email.split("@")[0]
        slug = re.sub(r"[^a-zA-Z0-9_]+", "", base.replace(" ", "_")).lower() or "user"
        slug = slug[:140]
        candidate = slug
        attempt = 0
        while self.get_by_username(db, candidate):
            attempt += 1
            suffix = secrets.token_hex(3) if attempt > 5 else str(attempt)
            candidate = f"{slug}_{suffix}"[:150]
        return candidate

    def create(self, db: Session, user_create: UserCreate) -> User:
        if self.get_by_email(db, user_create.email):
            raise ValueError("Email already registered")

        username = user_create.username or self._derive_username(db, user_create)
        if user_create.username and self.get_by_username(db, user_create.username):
            raise ValueError("Username already taken")

        user = User(
            username=username,
            email=user_create.email,
            hashed_password=password_hash(user_create.password),
            role="viewer",
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        return user

    def get_by_email(self, db: Session, email: str) -> User | None:
        return db.query(User).filter(User.email == email).first()

    def get_by_username(self, db: Session, username: str) -> User | None:
        return db.query(User).filter(User.username == username).first()

    def get_by_id(self, db: Session, user_id: str | UUID) -> User | None:
        return db.query(User).filter(User.id == user_id).first()

    def get_all(self, db: Session, skip: int = 0, limit: int = 100) -> list[User]:
        return db.query(User).offset(skip).limit(limit).all()

    def update(self, db: Session, user_id: str | UUID, user_update: UserUpdate) -> User | None:
        user = self.get_by_id(db, user_id)
        if not user:
            return None
        update_data = user_update.model_dump(exclude_unset=True)
        if "password" in update_data:
            user.hashed_password = password_hash(update_data.pop("password"))
        for field, value in update_data.items():
            setattr(user, field, value)
        db.commit()
        db.refresh(user)
        return user


    def update_password(self, db: Session, user: User, new_password: str) -> User:
        user.hashed_password = password_hash(new_password)
        db.commit()
        db.refresh(user)
        return user

    def authenticate(self, db: Session, email: str, password: str) -> User | None:
        user = self.get_by_email(db, email)
        if not user:
            return None
        if not verify_password(password, user.hashed_password):
            return None
        return user


user_service = UserService()
