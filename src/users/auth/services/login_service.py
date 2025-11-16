from fastapi import HTTPException, status

from src.users.auth.models import LoginModel, TokenPairModel
from src.users.auth.services.password_service import PasswordService
from src.users.auth.services.token_service import TokenService
from src.users.repository import AbstractUserRepository


class LoginService:
    def __init__(
            self,
            user_repository: AbstractUserRepository,
            token_service: TokenService | None = None,
    ) -> None:
        self._user_repository = user_repository
        self._token_service = token_service or TokenService()

    async def login(self, email: str, password: str) -> TokenPairModel:
        user = await self._user_repository.get_user_by_email(email)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email",
            )

        if not PasswordService.password_matches_hash(password, user.password_hash):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid password",
            )


        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Inactive user",
            )

        return self._token_service.generate_token(user)
