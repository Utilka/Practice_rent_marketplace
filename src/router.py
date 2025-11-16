from fastapi import APIRouter

router = APIRouter(prefix="/api/v1")

from src.auth.router import router as auth_router
from src.users.router import router as users_router

router.include_router(auth_router)
router.include_router(users_router)