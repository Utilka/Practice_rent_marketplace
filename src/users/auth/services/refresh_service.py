from fastapi import HTTPException, status

from src.users.auth.schemas import TokenResponseSchema
from src.users.auth.services.token_service import TokenService, TokenValidationError
from src.users.repository import AbstractUserRepository


class RefreshService:
    def __init__(
        self,
        user_repository: AbstractUserRepository,
        token_service: TokenService | None = None,
    ) -> None:
        self._user_repository = user_repository
        self._token_service = token_service or TokenService()

    async def refresh(self, refresh_token: str) -> TokenResponseSchema:
        try:
            payload = self._token_service.decode(refresh_token)
        except TokenValidationError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid refresh token",
            ) from None

        subject = payload.get("sub")
        if subject is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid refresh token",
            )

        try:
            user_id = int(subject)
        except (TypeError, ValueError) as err:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid refresh token",
            ) from err

        user = await self._user_repository.get_user_by_id(user_id)
        if not user or not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid refresh token",
            )

        return self._token_service.generate_token(user)
