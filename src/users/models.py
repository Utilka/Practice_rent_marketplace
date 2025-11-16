import enum

from sqlalchemy.orm import Mapped
from sqlalchemy.testing.schema import mapped_column

from src.core.database import Base


from sqlalchemy import String, Boolean, Enum as SAEnum
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class UserRole(str, enum.Enum):
    CUSTOMER = "customer"
    SELLER = "seller"
    ADMIN = "admin"

class User(Base):
    full_name: Mapped[str | None]
    email: Mapped[str]
    is_active: Mapped[bool] = mapped_column(default=True)
    is_superuser: Mapped[bool] = mapped_column(default=False)

    roles: Mapped[list[UserRole]] = mapped_column(ARRAY(SAEnum(UserRole, name="user_role")), nullable=False, default=[UserRole.CUSTOMER])

    def __repr__(self) -> str:
        return f"User(id={self.id}, email={self.email})"

    def serialise(self) -> dict:
        return {
            "id": self.id,
            "email": self.email,
            "full_name": self.full_name,
            "is_active": self.is_active,
            "is_superuser": self.is_superuser,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }


class UserCreate(User):
    password: str  # plain text, straight from client


class UserInDB(User):
    __tablename__ = "users"
    password_hash: str


class UserPublic(User):
    pass
