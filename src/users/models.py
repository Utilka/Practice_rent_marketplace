import enum


from src.core.database import BaseModel


from sqlalchemy import String, Boolean, Enum as SAEnum
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.orm import Mapped, mapped_column


class UserRole(str, enum.Enum):
    CUSTOMER = "customer"
    SELLER = "seller"
    ADMIN = "admin"

class User(BaseModel):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    email: Mapped[str] = mapped_column(String, unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String, nullable=False)

    full_name: Mapped[str | None] = mapped_column(String, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    roles: Mapped[list[UserRole]] = mapped_column(
        ARRAY(SAEnum(UserRole, name="user_role")),
        nullable=False,
        default=lambda: [UserRole.CUSTOMER],
    )


    def __repr__(self) -> str:
        return f"User(id={self.id}, email={self.email})"

    def serialise(self) -> dict:
        return {
            "id": self.id,
            "email": self.email,
            "full_name": self.full_name,
            "is_active": self.is_active,
            "is_superuser": self.is_superuser,
            "roles": [r.value for r in self.roles] if self.roles is not None else None,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }
