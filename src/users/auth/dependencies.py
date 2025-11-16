from fastapi import Depends

from src.users.auth.services.login_service import LoginService
from src.users.auth.services.registration_service import RegistrationService
from src.users.auth.services.refresh_service import RefreshService
from src.users.auth.services.token_service import TokenService
from src.users.dependencies import get_user_repository
from src.users.repository import UserRepository


async def get_registration_service(
    user_repository: UserRepository = Depends(get_user_repository),
) -> RegistrationService:
    return RegistrationService(user_repository)


async def get_login_service(
    user_repository: UserRepository = Depends(get_user_repository),
) -> LoginService:
    return LoginService(user_repository, TokenService())


async def get_refresh_service(
    user_repository: UserRepository = Depends(get_user_repository),
) -> RefreshService:
    return RefreshService(user_repository, TokenService())
