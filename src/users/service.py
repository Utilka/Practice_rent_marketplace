from abc import ABC, abstractmethod

import jwt
from fastapi import HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials
from typing_extensions import override

from src.users.auth.models import RegistrationModel, TokenPairModel
from src.users.auth.services.password_service import PasswordService
from src.users.auth.services.token_service import TokenService
from src.config import get_settings
from src.users.models import User
from src.users.repository import AbstractUserRepository


class AbstractUserService(ABC):
    @abstractmethod
    def __init__(self, user_repository: AbstractUserRepository): ...

    @abstractmethod
    async def register_user(self, user_data) -> dict: ...

    @abstractmethod
    async def login_user(self, email: str, password: str) -> TokenPairModel: ...

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
    async def authenticate(self, credentials: HTTPAuthorizationCredentials) -> User:
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
    async def register_user(self, user_data: RegistrationModel) -> dict:
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

        return user.serialise()

    @override
    async def login_user(self, email: str, password: str) -> TokenPairModel:
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

        return user.serialise()


