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
from sqlalchemy.exc import IntegrityError as IE
import logging

logger = logging.getLogger(__name__)

class ServiceUser(ServiceBase[User, DTOUserCreate, DTOUserUpdate, DTOUserRetrieve]):
    pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
    """User service with additional user-specific methods"""
    
    def __init__(self, db: Session):
        super().__init__(User, db)
    
    def _increment_failed_attempts(self, user: User) -> None:
        """Incrementa tentativas de login falhadas (método interno)."""
        user.failed_login_attempts += 1
        if user.failed_login_attempts >= self.MAX_FAILED_ATTEMPTS:
            user.locked_until = datetime.now() + timedelta(minutes=self.LOCKOUT_DURATION_MINUTES)
            logger.warning(f"Conta bloqueada por tentativas excessivas: {user.username}")
    
    def _reset_failed_attempts(self, user: User) -> None:
        """Reseta tentativas falhadas após login bem-sucedido (método interno)."""
        user.failed_login_attempts = 0
        user.locked_until = None
        user.last_login = datetime.now()
    
    def _is_account_locked(self, user: User) -> bool:
        """Verifica se a conta está bloqueada (método interno)."""
        if user.locked_until is None:
            return False
        
        if datetime.now() >= user.locked_until:
            # Auto-desbloqueio após período expirar
            user.locked_until = None
            user.failed_login_attempts = 0
            return False
        
        return True
    
    def authenticate_user(self, username_or_email: str, password: str) -> Optional[DTOUserRetrieve]:
        """
        Autentica usuário e gerencia controles de segurança.
        Método para uso do sistema de autenticação - NÃO expor na API.
        """
        try:
            # Buscar usuário por username ou email
            user = None
            if "@" in username_or_email:
                user = self.db.query(User).filter(
                    User.email == username_or_email,
                    User.deleted_at.is_(None)
                ).first()
            else:
                user = self.db.query(User).filter(
                    User.username == username_or_email,
                    User.deleted_at.is_(None)
                ).first()
            
            if not user:
                logger.warning(f"Tentativa de login com usuário inexistente: {username_or_email}")
                return None
            
            # Verificar se conta está bloqueada
            if self._is_account_locked(user):
                logger.warning(f"Tentativa de login em conta bloqueada: {user.username}")
                return None
            
            # Verificar se conta está ativa
            if not user.is_active:
                logger.warning(f"Tentativa de login em conta inativa: {user.username}")
                return None
            
            # Verificar senha
            if not self.pwd_context.verify(password, user.password):
                self._increment_failed_attempts(user)
                self.db.commit()
                logger.warning(f"Senha incorreta para usuário: {user.username}")
                return None
            
            # Login bem-sucedido
            self._reset_failed_attempts(user)
            self.db.commit()
            logger.info(f"Login bem-sucedido: {user.username}")
            
            return self._to_response_dto(user)
            
        except Exception as e:
            logger.error(f"Erro durante autenticação: {str(e)}")
            self.db.rollback()
            return None
    
    def unlock_account(self, user_id: UUID, current_user_id: Optional[UUID] = None) -> bool:
        """
        Desbloqueia uma conta manualmente (apenas para administradores).
        Pode ser exposto em endpoint administrativo com permissões específicas.
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
                
                logger.info(f"Conta desbloqueada manualmente: {user.username} por usuário {current_user_id}")
                return True
        except Exception as e:
            logger.error(f"Erro ao desbloquear conta: {str(e)}")
            raise ServiceException(f"Erro ao desbloquear conta: {str(e)}")
    
    def get_security_status(self, user_id: UUID) -> dict:
        """
        Retorna status de segurança (apenas para administradores).
        Pode ser usado internamente ou em endpoint administrativo.
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
    
    def create(self, create_dto: DTOUserCreate, current_user_id: Optional[UUID] = None) -> DTOUserRetrieve:
        """Cria um novo usuário com senha hasheada."""
        try:
            with self.transaction():
                # Verificação de constraints únicos
                existing_email = self.db.query(self.model).filter(
                    self.model.email == create_dto.email,
                    self.model.deleted_at.is_(None)
                ).first()
                if existing_email:
                    raise ServiceException(f"Usuário com email {create_dto.email} já existe.")
                
                existing_username = self.db.query(self.model).filter(
                    self.model.username == create_dto.username,
                    self.model.deleted_at.is_(None)
                ).first()
                if existing_username:
                    raise ServiceException(f"Usuário com username {create_dto.username} já existe.")
                
                # Criar dados do usuário sem a senha
                user_data = create_dto.model_dump(exclude={'password'})
                instance = self.model(**user_data)
                
                # Hash da senha
                instance.password = self.pwd_context.hash(create_dto.password)
                
                # ✅ Inicializar campos de segurança com valores padrão seguros
                instance.failed_login_attempts = 0
                instance.locked_until = None
                instance.last_login = None
                
                self._apply_audit_fields(instance, current_user_id)
                self.db.add(instance)
                logger.info(f"Criando usuário: {create_dto.username}")
                self.db.refresh(instance)
                return self._to_response_dto(instance)
        except IE as e:
            logger.error(f"Erro de integridade ao criar usuário: {str(e)}")
            raise ServiceException(f"Erro ao criar usuário: {str(e)}")
        except ServiceException:
            raise
        except Exception as e:
            logger.error(f"Erro inesperado ao criar usuário: {str(e)}")
            raise ServiceException(f"Erro inesperado ao criar usuário")

    def update(self, id: UUID, update_dto: DTOUserUpdate, current_user_id: Optional[UUID] = None) -> DTOUserRetrieve:
        """Atualiza um recurso existente."""
        instance = self.db.query(self.model).filter(self.model.id == id).first()
        if not instance:
            raise ServiceException(resource_name=self.model.__name__, resource_id=id)
        try:
            with self.transaction():
                update_data = update_dto.model_dump(exclude_unset=True)
                if not update_data:
                    raise ServiceException("Pelo menos um campo deve ser fornecido para atualização")
                for field, value in update_data.items():
                    setattr(instance, field, value)
                if hasattr(instance, 'updated_by'):
                    instance.updated_by = current_user_id
                self.db.refresh(instance)
                return self._to_response_dto(instance)
        except ServiceException as e:
            logger.error(f"Erro de integridade ao atualizar {self.model.__name__}: {str(e)}")
            raise ServiceException(f"Erro ao atualizar {self.model.__name__}: {str(e)}")
        except Exception as e:
            logger.error(f"Erro inesperado ao atualizar {self.model.__name__}: {str(e)}")
            raise ServiceException(f"Erro inesperado ao atualizar {self.model.__name__}")

    def delete(self, id: UUID, current_user_id: Optional[UUID] = None, hard_delete: bool = False) -> bool:
        instance = self.db.query(self.model).filter(self.model.id == id).first()
        if not instance:
            raise ServiceException(resource_name=self.model.__name__, resource_id=id)
        try:
            with self.transaction():
                if hard_delete or not hasattr(self.model, 'deleted_at'):
                    self.db.delete(instance)
                else:
                    instance.deleted_at = datetime.now()
                    if hasattr(instance, 'deleted_by'):
                        instance.deleted_by = current_user_id
                return True
        except Exception as e:
            logger.error(f"Erro ao deletar {self.model.__name__}: {str(e)}")
            raise ServiceException(f"Erro ao deletar {self.model.__name__}")
        
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
    
    def set_password(self, user_id: UUID, password_hash: str, current_user_id: Optional[UUID] = None) -> bool:
        """Set user password hash"""
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            raise ServiceException(resource_name="User", resource_id=user_id)
            
        try:
            user._password_hash = password_hash
            if hasattr(user, 'updated_by'):
                user.updated_by = current_user_id
                
            self.db.commit()
            return True
            
        except Exception as e:
            self.db.rollback()
            raise ServiceException(f"Error setting password: {str(e)}")