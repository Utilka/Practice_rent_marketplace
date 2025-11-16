from fastapi import APIRouter, Depends

from src.users.dependencies import get_current_user, get_user_service
from src.users.models import User

from src.users.auth.router import auth_router
from src.users.service import UserService

users_router = APIRouter(prefix="/users", tags=["User","Authentication"])

users_router.include_router(auth_router)

@users_router.get("/me")
async def read_current_user(
    user: User = Depends(get_current_user),
    user_service: UserService = Depends(get_user_service),
):
    return await user_service.get_user_profile(user.id)
