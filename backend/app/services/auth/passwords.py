import re

from passlib.context import CryptContext

WEAK_PASSWORDS = {
    "password",
    "password123",
    "password1234",
    "123456",
    "1234567",
    "12345678",
    "123456789",
    "1234567890",
    "qwerty",
    "qwerty123",
    "abc123",
    "abcd1234",
    "admin",
    "admin123",
    "letmein",
    "welcome",
    "monkey",
    "dragon",
    "master",
    "login",
}

SPECIAL_CHARS = "!@#$%^&*()_+-=[]{}|;':\",./<>?`~"


class PasswordValidationError(Exception):
    def __init__(self, errors: list[str]) -> None:
        self.errors = errors
        super().__init__("; ".join(errors))


class PasswordService:
    def __init__(self) -> None:
        self._context = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")

    def validate_password(self, password: str) -> None:
        errors: list[str] = []

        if len(password) < 8:
            errors.append("Password must be at least 8 characters long")

        if not re.search(r"[A-Z]", password):
            errors.append("Password must contain at least one uppercase letter")

        if not re.search(r"[a-z]", password):
            errors.append("Password must contain at least one lowercase letter")

        if not re.search(r"[0-9]", password):
            errors.append("Password must contain at least one digit")

        has_special = any(c in SPECIAL_CHARS for c in password)
        if not has_special:
            errors.append(
                "Password must contain at least one special character (!@#$%^&*()_+-=[]{}|;':\",./<>?`~)"
            )

        if password.lower() in WEAK_PASSWORDS:
            errors.append("This password is too common. Please choose a stronger password")

        if errors:
            raise PasswordValidationError(errors)

    def hash_password(self, password: str) -> str:
        return self._context.hash(password)

    def verify_password(self, *, plain_password: str, hashed_password: str) -> bool:
        return self._context.verify(plain_password, hashed_password)
