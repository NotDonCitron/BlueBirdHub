from typing import List, Optional
from sqlalchemy.orm import Session
from .base import CRUDBase
from models.user import User, UserPreference
from schemas.user import UserCreate, UserUpdate, UserPreferenceCreate, UserPreferenceUpdate

class CRUDUser(CRUDBase[User, UserCreate, UserUpdate]):
    def get_by_username(self, db: Session, *, username: str) -> Optional[User]:
        """Get user by username"""
        return db.query(User).filter(User.username == username).first()

    def get_by_email(self, db: Session, *, email: str) -> Optional[User]:
        """Get user by email"""
        return db.query(User).filter(User.email == email).first()

    def create_user(self, db: Session, *, obj_in: UserCreate) -> User:
        """Create a new user"""
        db_obj = User(
            username=obj_in.username,
            email=obj_in.email,
            is_active=obj_in.is_active if obj_in.is_active is not None else True
        )
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def get_active_users(self, db: Session, *, skip: int = 0, limit: int = 100) -> List[User]:
        """Get active users only"""
        return db.query(User).filter(User.is_active == True).offset(skip).limit(limit).all()

class CRUDUserPreference(CRUDBase[UserPreference, UserPreferenceCreate, UserPreferenceUpdate]):
    def get_by_user_and_key(
        self, db: Session, *, user_id: int, preference_key: str
    ) -> Optional[UserPreference]:
        """Get user preference by user ID and key"""
        return db.query(UserPreference).filter(
            UserPreference.user_id == user_id,
            UserPreference.preference_key == preference_key
        ).first()

    def get_user_preferences(
        self, db: Session, *, user_id: int
    ) -> List[UserPreference]:
        """Get all preferences for a user"""
        return db.query(UserPreference).filter(
            UserPreference.user_id == user_id
        ).all()

    def set_preference(
        self, db: Session, *, user_id: int, key: str, value: any
    ) -> UserPreference:
        """Set or update a user preference"""
        preference = self.get_by_user_and_key(db, user_id=user_id, preference_key=key)
        if preference:
            preference.preference_value = value
            db.commit()
            db.refresh(preference)
            return preference
        else:
            new_preference = UserPreference(
                user_id=user_id,
                preference_key=key,
                preference_value=value
            )
            db.add(new_preference)
            db.commit()
            db.refresh(new_preference)
            return new_preference

user = CRUDUser(User)
user_preference = CRUDUserPreference(UserPreference)