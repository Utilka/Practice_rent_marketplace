import time
from typing import Any
from uuid import uuid4

import jwt

from src.users.auth.schemas import AccessTokenModel, RefreshTokenModel, TokenPairModel
from src.config import get_settings
from src.users.models import User


class TokenValidationError(Exception):
    """Raised when a token fails validation."""


class TokenService:
    def __init__(self) -> None:
        self._settings = get_settings()

    def generate_token(self, user: User) -> TokenPairModel:
        now = int(time.time())
        access_token = AccessTokenModel(
            sub=str(user.id),
            iat=now,
            exp=now + self._settings.security.jwt_access_token_expire_secs,
            iss=self._settings.security.jwt_issuer,
            jti=str(uuid4())[:8],
        )
        refresh_token = RefreshTokenModel(
            sub=str(user.id),
            iat=now,
            exp=now + self._settings.security.refresh_token_expire_secs,
            iss=self._settings.security.jwt_issuer,
            type="refresh",
        )
        encoded_access_token = jwt.encode(
            access_token.model_dump(mode="json"),
            self._settings.security.jwt_secret_key.get_secret_value(),
            algorithm="HS256",
        )
        encoded_refresh_token = jwt.encode(
            refresh_token.model_dump(mode="json"),
            self._settings.security.jwt_secret_key.get_secret_value(),
            algorithm="HS256",
        )
        return TokenPairModel(
            access_token=encoded_access_token,
            refresh_token=encoded_refresh_token,
        )

    def validate_token(self, token: str) -> bool:
        try:
            self.decode(token)
        except TokenValidationError:
            return False

        return True

    def decode(self, token: str) -> dict[str, Any]:
        try:
            return jwt.decode(
                token,
                self._settings.security.jwt_secret_key.get_secret_value(),
                algorithms=["HS256"],
                issuer=self._settings.security.jwt_issuer,
            )
        except jwt.ExpiredSignatureError as exc:  # pragma: no cover - library-specific error
            raise TokenValidationError("Token expired") from exc
        except jwt.InvalidTokenError as exc:
            raise TokenValidationError("Invalid token") from exc
