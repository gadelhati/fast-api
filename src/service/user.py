from uuid import UUID
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from typing import Optional, List
from passlib.context import CryptContext
from src.model.user import User
from src.model.role import Role
from src.schema.user import DTOUserCreate, DTOUserUpdate, DTOUserRetrieve
from src.schema import (DTOUserCreate, DTOUserUpdate, DTOUserRetrieve)
from pydantic import ValidationError
from src.service.basic import ServiceBase, ServiceException
from src.validation.validations import Validation
from src.config import SECRET_KEY, ALGORITHM
from jose import jwt, JWTError, ExpiredSignatureError
import logging

logger = logging.getLogger(__name__)

class ServiceUser(ServiceBase[User, DTOUserCreate, DTOUserUpdate, DTOUserRetrieve]):
    """User service with additional user-specific methods."""
    pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
    
    def __init__(self, db: Session):
        super().__init__(User, db, DTOUserRetrieve)

    def _increment_failed_attempts(self, user: User) -> None:
        """Increments failed login attempts."""
        user.failed_login_attempts += 1
        if user.failed_login_attempts >= self.MAX_FAILED_ATTEMPTS:
            user.locked_until = datetime.now() + timedelta(minutes=self.LOCKOUT_DURATION_MINUTES)
            logger.warning(f"Account blocked for excessive attempts: {user.username}")

    def _reset_failed_attempts(self, user: User) -> None:
        """Resets failed attempts after successful login."""
        user.failed_login_attempts = 0
        user.locked_until = None
        user.last_login = datetime.now()
    
    def _is_account_locked(self, user: User) -> bool:
        """Checks if the account is blocked."""
        if user.locked_until is None:
            return False
        if datetime.now() >= user.locked_until:
            # Auto-unlock after period expires
            user.locked_until = None
            user.failed_login_attempts = 0
            return False
        return True
    
    def get_current_user(self, token: str) -> DTOUserRetrieve:
        """Resolves the authenticated user from the token"""
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            user_id: str = payload.get("sub")
            if user_id is None:
                raise ServiceException("Invalid token", code="invalid_token")
            user = self._get_instance(UUID(user_id))
            if not user or (hasattr(user, "deleted_at") or user.deleted_at is not None):
                raise ServiceException("User not found", code="not_found")
            return self._to_response_dto(user)
        except ExpiredSignatureError:
            raise ServiceException("Expired token", code="token_expired")
        except JWTError:
            raise ServiceException("Invalid token", code="invalid_token")

    def authenticate_user(self, username_or_email: str, password: str) -> Optional[DTOUserRetrieve]:
        """
        Authenticates user and manages security controls.
        Method for using the authentication system - DO NOT expose in the API.
        """
        try:
            user = self.db.query(User).filter(
                User.username == username_or_email,
                User.deleted_at.is_(None)
            ).first()
            # Login attempt with non-existent user
            if not user:
                logger.warning(f"Incorrect username or password: {username_or_email}")
                return None
            
            if self._is_account_locked(user):
                logger.warning(f"Login attempt to blocked account: {user.username}")
                return None
            if not user.is_active:
                logger.warning(f"Attempted login to inactive account: {user.username}")
                return None
            # Incorrect password for user
            if not self.pwd_context.verify(password, user.password):
                self._increment_failed_attempts(user)
                self.db.commit()
                logger.warning(f"Incorrect username or password")
                return None
            self._reset_failed_attempts(user)
            self.db.commit()
            logger.info(f"Successful login: {user.username}")
            return self._to_response_dto(user)
            
        except Exception as e:
            logger.error(f"Error during authentication: {str(e)}")
            self.db.rollback()
            return None
    
    def unlock_account(self, user_id: UUID, current_user_id: Optional[UUID] = None) -> bool:
        """
        Unlock an account manually (admins only).
        Can be exposed on administrative endpoint with specific permissions.
        """
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            raise ServiceException(resource_name="User", resource_id=user_id)
        try:
            with self.transaction():
                user.failed_login_attempts = 0
                user.locked_until = None
                if hasattr(user, 'updated_by'):
                    user.updated_by = current_user_id
                logger.info(f"Account unlocked manually: {user.username} por usuário {current_user_id}")
                return True
        except Exception as e:
            logger.error(f"Error unlocking account: {str(e)}")
            raise ServiceException(f"Error unlocking account: {str(e)}")
    
    def get_security_status(self, user_id: UUID) -> dict:
        """
        Returns security status (administrators only).
        Can be used internally or on an administrative endpoint.
        """
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            raise ServiceException(resource_name="User", resource_id=user_id)
        return {
            "is_locked": self._is_account_locked(user),
            "failed_attempts": user.failed_login_attempts,
            "locked_until": user.locked_until,
            "last_login": user.last_login,
            "is_active": user.is_active,
            "is_verified": user.is_verified
        }
    
    def get_by_email(self, email: str, include_deleted: bool = False) -> Optional[DTOUserRetrieve]:
        """Get user by email"""
        query = self.db.query(self.model).filter(self.model.email == email)
        if not include_deleted and hasattr(self.model, 'deleted_at'):
            query = query.filter(self.model.deleted_at.is_(None))
        instance = query.first()
        return self._to_response_dto(instance) if instance else None
    
    def get_by_username(self, username: str, include_deleted: bool = False) -> Optional[DTOUserRetrieve]:
        """Get user by username"""
        query = self.db.query(self.model).filter(self.model.username == username)
        if not include_deleted and hasattr(self.model, 'deleted_at'):
            query = query.filter(self.model.deleted_at.is_(None))
        instance = query.first()
        return self._to_response_dto(instance) if instance else None
    
    def update_roles(self, user_id: UUID, role_ids: List[UUID], current_user_id: Optional[UUID] = None) -> DTOUserRetrieve:
        """Update user roles"""
        if len(role_ids) > Validation.MAX_ROLES_PER_USER:
            raise ValidationError(
                message=f"A user cannot have more than {Validation.MAX_ROLES_PER_USER} roles",
                errors={"role_ids": "Too many roles"}
            )
        if len(role_ids) != len(set(role_ids)):
            raise ServiceException(
                message="Papéis duplicados não são permitidos",
                errors={"role_ids": "Duplicatas detectadas"}
            )
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            raise ServiceException(resource_name="User", resource_id=user_id)
        roles = self.db.query(Role).filter(Role.id.in_(role_ids)).all()
        if len(roles) != len(role_ids):
            found_ids = {str(role.id) for role in roles}
            missing_ids = [str(rid) for rid in role_ids if rid not in found_ids]
            raise ServiceException(
                message=f"Some roles not found: {', '.join(missing_ids)}",
                code="roles_not_found"
            )
        try:
            user.roles = roles
            if hasattr(user, 'updated_by'):
                user.updated_by = current_user_id
            self.db.commit()
            self.db.refresh(user)
            return self._to_response_dto(user)
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error updating user roles: {str(e)}")
            raise ServiceException(f"Error updating user roles: {str(e)}")
    
    def set_password(self, user_id: UUID, password: str, current_user_id: Optional[UUID] = None) -> bool:
        """Set user password hash"""
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            raise ServiceException(f"User with id {user_id} not found")
        try:
            user.password = self.pwd_context.hash(password)
            if hasattr(user, 'updated_by'):
                user.updated_by = current_user_id
            self.db.commit()
            return True
        except Exception as e:
            self.db.rollback()
            raise ServiceException(f"Error setting password: {str(e)}")