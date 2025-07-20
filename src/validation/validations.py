from typing import Optional
import re

class Validation:
    """Centralized validation rules"""
    USERNAME_MIN_LENGTH = 3
    USERNAME_MAX_LENGTH = 100
    PASSWORD_MIN_LENGTH = 8
    NAME_MAX_LENGTH = 100
    MAX_ROLES_PER_USER = 10
    MAX_PERMISSIONS_PER_ROLE = 50

    @staticmethod
    def validate_username(v: str) -> str:
        v = v.strip()
        if len(v) < Validation.USERNAME_MIN_LENGTH:
            raise ValueError(f"Username must be at least {Validation.USERNAME_MIN_LENGTH} characters long")
        if len(v) > Validation.USERNAME_MAX_LENGTH:
            raise ValueError(f"Username must be at most {Validation.USERNAME_MAX_LENGTH} characters long")
        if not re.match(r'^[a-zA-Z0-9_.-]+$', v):
            raise ValueError("Username must contain only letters, numbers, underscores, dots and hyphens")
        return v

    @staticmethod
    def validate_password(v: str) -> str:
        if len(v) < Validation.PASSWORD_MIN_LENGTH:
            raise ValueError(f"Password must be at least {Validation.PASSWORD_MIN_LENGTH} characters")
        if not any(c.isupper() for c in v):
            raise ValueError("Password must contain at least one uppercase letter")
        if not any(c.islower() for c in v):
            raise ValueError("Password must contain at least one lowercase letter")
        if not any(c.isdigit() for c in v):
            raise ValueError("Password must contain at least one number")
        if not any(c in "!@#$%^&*()_+-=[]{}|;:,.<>?" for c in v):
            raise ValueError("Password must contain at least one special character")
        return v

    @staticmethod
    def validate_name(v: Optional[str], field_name: str) -> Optional[str]:
        if v is None:
            return None
        v = v.strip()
        if len(v) < 1:
            raise ValueError(f"{field_name} cannot be empty")
        if len(v) > Validation.NAME_MAX_LENGTH:
            raise ValueError(f"{field_name} must be at most {Validation.NAME_MAX_LENGTH} characters long")
        return v