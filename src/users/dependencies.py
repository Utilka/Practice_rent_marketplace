from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from src.users.repository import UserRepository
from src.users.service import UserService
from src.core.dependencies import SessionDep
from src.users.models import User


async def get_user_repository(
    session: SessionDep,
) -> UserRepository:
    return UserRepository(session)


async def get_user_service(
    user_repository: UserRepository = Depends(get_user_repository),
) -> UserService:
    return UserService(user_repository)


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(HTTPBearer()),
    user_service: UserService = Depends(get_user_service),
) -> User:
    return await user_service.authenticate(credentials)
