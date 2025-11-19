from pydantic import BaseModel, EmailStr


class RegistrationModel(BaseModel):
    email: EmailStr
    password: str
    full_name: str | None = None


class LoginModel(BaseModel):
    email: EmailStr
    password: str


class AccessTokenModel(BaseModel):
    sub: str
    iat: int
    exp: int
    iss: str
    jti: str


class RefreshTokenModel(BaseModel):
    sub: str
    iat: int
    exp: int
    iss: str
    type: str


class TokenPairModel(BaseModel):
    access_token: str
    refresh_token: str


class TokenRefreshRequestModel(BaseModel):
    refresh_token: str
