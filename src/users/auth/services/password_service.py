import bcrypt

from src.config import get_settings


class PasswordService:
    @staticmethod
    def password_matches_hash(plain_password: str, hashed_password: str) -> bool:
        try:
            return bcrypt.checkpw(
                plain_password.encode("utf-8"), hashed_password.encode("utf-8")
            )
        except ValueError:
            return False

    @staticmethod
    def get_password_hash(password: str) -> str:
        return bcrypt.hashpw(
            password.encode(),
            bcrypt.gensalt(get_settings().security.password_bcrypt_rounds),
        ).decode()
