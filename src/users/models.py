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

class UserBase(Base):
    full_name: Mapped[str | None]
    email: Mapped[str]
    is_active: Mapped[bool] = mapped_column(default=True)
    is_superuser: Mapped[bool] = mapped_column(default=False)

    roles: Mapped[list[UserRole]] = mapped_column(ARRAY(SAEnum(UserRole, name="user_role")), nullable=False, default=[UserRole.CUSTOMER])

    def __repr__(self) -> str:
        return f"User(id={self.id}, email={self.email})"


class UserCreate(UserBase):
    password: str  # plain text, straight from client


class UserInDB(UserBase):
    __tablename__ = "users"
    password_hash: str


class UserPublic(UserBase):
    pass
