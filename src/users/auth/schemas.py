from pydantic import BaseModel, EmailStr


class RegistrationSchema(BaseModel):
    email: EmailStr
    password: str
    full_name: str


class LoginSchema(BaseModel):
    email: EmailStr
    password: str


class AccessTokenSchema(BaseModel):
    sub: str
    iat: int
    exp: int
    iss: str
    jti: str


class RefreshTokenSchema(BaseModel):
    sub: str
    iat: int
    exp: int
    iss: str
    type: str


class TokenResponseSchema(BaseModel):
    access_token: str
    refresh_token: str


class RefreshTokenRequestSchema(BaseModel):
    refresh_token: str
