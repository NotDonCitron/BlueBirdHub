from typing import Optional, Any
from pydantic import BaseModel
from datetime import datetime

# User Schemas
class UserBase(BaseModel):
    username: str
    email: Optional[str] = None  # Temporarily using str instead of EmailStr
    is_active: Optional[bool] = True

class UserCreate(UserBase):
    password: str

class UserUpdate(UserBase):
    username: Optional[str] = None
    is_active: Optional[bool] = None

class UserInDBBase(UserBase):
    id: Optional[int] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class User(UserInDBBase):
    pass

class UserInDB(UserInDBBase):
    pass

# User Preference Schemas
class UserPreferenceBase(BaseModel):
    preference_key: str
    preference_value: Any

class UserPreferenceCreate(UserPreferenceBase):
    user_id: int

class UserPreferenceUpdate(BaseModel):
    preference_value: Optional[Any] = None

class UserPreferenceInDBBase(UserPreferenceBase):
    id: Optional[int] = None
    user_id: int
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class UserPreference(UserPreferenceInDBBase):
    pass