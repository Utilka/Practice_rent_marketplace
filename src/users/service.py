from abc import ABC, abstractmethod

import jwt
from fastapi import HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials
from typing_extensions import override

from src.users.auth.schemas import RegistrationSchema, TokenResponseSchema
from src.users.auth.services.password_service import PasswordService
from src.users.auth.services.token_service import TokenService
from src.config import get_settings
from src.users.models import User
from src.users.repository import AbstractUserRepository


class AbstractUserService(ABC):
    @abstractmethod
    def __init__(self, user_repository: AbstractUserRepository): ...

    @abstractmethod
    async def get_current_user(
        self, credentials: HTTPAuthorizationCredentials
    ) -> User: ...

    @abstractmethod
    async def register_user(self, user_data) -> dict: ...

    @abstractmethod
    async def login_user(self, email: str, password: str) -> dict: ...

    @abstractmethod
    async def authenticate(
        self, credentials: HTTPAuthorizationCredentials
    ) -> User: ...

    @abstractmethod
    async def get_user_profile(self, user_id: int) -> dict: ...


class UserService(AbstractUserService):
    def __init__(self, user_repository: AbstractUserRepository):
        self.user_repository = user_repository
        self._token_service = TokenService()

    @override
    async def get_current_user(self, credentials: HTTPAuthorizationCredentials) -> User:
        try:
            payload = jwt.decode(
                credentials.credentials,
                get_settings().security.jwt_secret_key.get_secret_value(),
                algorithms=["HS256"],
                issuer=get_settings().security.jwt_issuer,
            )
        except jwt.InvalidTokenError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token"
            )
        user_id = payload.get("sub")
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token payload"
            )
        try:
            user_id_int = int(user_id)
        except (TypeError, ValueError):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token payload"
            )

        if payload.get("type") == "refresh":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Refresh tokens cannot access this resource",
            )

        user = await self.user_repository.get_user_by_id(user_id_int)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
            )

        return user

    @override
    async def register_user(self, user_data: RegistrationSchema) -> dict:
        existing_user = await self.user_repository.get_user_by_email(user_data.email)
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Email already registered",
            )

        user = await self.user_repository.create_user(
            dict(
                email=user_data.email,
                password_hash=PasswordService.get_password_hash(user_data.password),
                full_name=user_data.full_name,
            )
        )

        return self._serialize_user(user)

    @override
    async def login_user(self, email: str, password: str) -> TokenResponseSchema:
        user = await self.user_repository.get_user_by_email(email)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password",
            )

        if not PasswordService.password_matches_hash(password, user.password_hash):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password",
            )

        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Inactive user",
            )

        return self._token_service.generate_token(user)

    @override
    async def get_user_profile(self, user_id: int) -> dict:
        user = await self.user_repository.get_user_by_id(user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found",
            )

        return self._serialize_user(user)

    def _serialize_user(self, user: User) -> dict:
        return {
            "id": user.id,
            "email": user.email,
            "full_name": user.full_name,
            "is_active": user.is_active,
            "is_superuser": user.is_superuser,
            "created_at": user.created_at,
            "updated_at": user.updated_at,
        }
