from fastapi import APIRouter, HTTPException, Depends, status

from src.users.auth.dependencies import get_refresh_service, get_registration_service, get_login_service
from src.users.auth.schemas import TokenResponseSchema, LoginSchema, RegistrationSchema, RefreshTokenRequestSchema
from src.users.auth.services.login_service import LoginService
from src.users.auth.services.refresh_service import RefreshService
from src.users.auth.services.registration_service import RegistrationService

auth_router = APIRouter(prefix="/auth", tags=["Authentication"])


@auth_router.post("/login", response_model=TokenResponseSchema)
async def login(
    login_data: LoginSchema,
    login_service: LoginService = Depends(get_login_service),
):
    return await login_service.login(login_data)


@auth_router.post("/register")
async def register(
    registration_data: RegistrationSchema,
    registration_service: RegistrationService = Depends(get_registration_service),
):
    await registration_service.register_user(registration_data)
    raise HTTPException(
        status_code=status.HTTP_200_OK,
        detail="Registration successful. Please check your email to verify your account.",
    )


@auth_router.post("/refresh", response_model=TokenResponseSchema)
async def refresh_tokens(
    refresh_data: RefreshTokenRequestSchema,
    refresh_service: RefreshService = Depends(get_refresh_service),
):
    return await refresh_service.refresh(refresh_data.refresh_token)
