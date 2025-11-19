from fastapi import HTTPException, status

from src.users.auth.schemas import RegistrationModel
from src.users.auth.services.password_service import PasswordService
from src.users.repository import AbstractUserRepository


class RegistrationService:
    def __init__(self, user_repository: AbstractUserRepository) -> None:
        self._user_repository = user_repository

    async def register_user(self, user_data: RegistrationModel) -> None:
        existing_user = await self._user_repository.get_user_by_email(user_data.email)
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
