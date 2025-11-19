from datetime import datetime
from pydantic import BaseModel, EmailStr

from src.users.models import UserRole


class UserCreate(BaseModel):
    email: EmailStr
    full_name: str | None = None
    password: str  # plain text from client
    roles: list[UserRole] = UserRole.CUSTOMER

class UserSelfUpdate(BaseModel):
    full_name: str | None = None

    class Config:
        extra = "forbid"  # reject unknown fields like roles, is_active, etc.

class UserAdminUpdate(BaseModel):
    full_name: str | None = None
    is_active: bool | None = None
    roles: list[UserRole] | None = None

    class Config:
        extra = "forbid"

class UserChangePassword(BaseModel):
    current_password: str
    new_password: str

    class Config:
        extra = "forbid"

class UserPublic(BaseModel):
    id: int
    email: EmailStr
    full_name: str | None = None
    is_active: bool
    roles: list[UserRole] | None = None

    created_at: datetime | None = None
    updated_at: datetime | None = None

    class Config:
        from_attributes = True  # was orm_mode = True in Pydantic v1