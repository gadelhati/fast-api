from typing import Type, TypeVar, Generic, Optional, List, Any
from uuid import UUID
from datetime import datetime
from sqlalchemy.orm import Session, Query
from sqlalchemy.exc import IntegrityError as IE
from pydantic import BaseModel, ValidationError
import logging
from contextlib import contextmanager
from werkzeug.security import generate_password_hash
from src.database import Base
from src.model.user import User
from src.model.role import Role
from src.model.permission import Permission
from src.enum.permissionAction import EnumPermissionAction
from src.schema import (
    DTOUserCreate, DTOUserUpdate, DTOUserResponse,
    DTORoleCreate, DTORoleUpdate, DTORoleResponse,
    DTOPermissionCreate, DTOPermissionUpdate, DTOPermissionResponse
)

# Type variables for generic service
TModel = TypeVar('TModel', bound=Base)
TCreateSchema = TypeVar('TCreateSchema', bound=BaseModel)
TUpdateSchema = TypeVar('TUpdateSchema', bound=BaseModel)
TResponseSchema = TypeVar('TResponseSchema', bound=BaseModel)

logger = logging.getLogger(__name__)

class ServiceException(Exception):
    """Exceção base para erros na camada de serviço."""
    def __init__(self, message: str, code: str = None):
        self.message = message
        self.code = code
        super().__init__(message)

class NotFoundError(ServiceException):
    """Exceção lançada quando um recurso não é encontrado."""
    def __init__(self, resource_name: str, resource_id: Any):
        super().__init__(
            message=f"{resource_name} com id {resource_id} não encontrado",
            code="not_found"
        )

class ServiceIntegrityError(ServiceException):
    """Exceção lançada quando ocorre um erro de integridade no banco de dados."""
    def __init__(self, message: str):
        super().__init__(
            message=message,
            code="integrity_error"
        )

class ServiceValidationError(ServiceException):
    """Exceção lançada quando a validação falha."""
    def __init__(self, message: str, errors: dict = None):
        super().__init__(
            message=message,
            code="validation_error"
        )
        self.errors = errors or {}

class BaseService(Generic[TModel, TCreateSchema, TUpdateSchema, TResponseSchema]):
    """Classe base genérica para operações CRUD."""

    def __init__(self, model: Type[TModel], db: Session):
        self.model = model
        self.db = db

    @contextmanager
    def transaction(self):
        """Gerenciador de contexto para transações de banco de dados."""
        try:
            yield self.db
        except Exception as e:
            self.db.rollback()
            raise
        else:
            self.db.commit()

    def _apply_audit_fields(self, instance: TModel, current_user_id: Optional[UUID] = None) -> TModel:
        """Aplica campos de auditoria ao modelo."""
        if hasattr(instance, 'created_by') and not instance.created_by:
            instance.created_by = current_user_id
        if hasattr(instance, 'updated_by'):
            instance.updated_by = current_user_id
        return instance

    def _to_response_dto(self, instance: TModel) -> TResponseSchema:
        """Converte uma instância do modelo em um DTO de resposta."""
        try:
            return TResponseSchema.model_validate(instance, from_attributes=True)
        except ValidationError as e:
            raise RuntimeError(f"Erro ao converter para DTO: {e}")

    def get(self, id: UUID, include_deleted: bool = False) -> TResponseSchema:
        """Recupera um recurso pelo ID."""
        query = self.db.query(self.model).filter(self.model.id == id)
        if not include_deleted and hasattr(self.model, 'deleted_at'):
            query = query.filter(self.model.deleted_at.is_(None))
        instance = query.first()
        if not instance:
            raise NotFoundError(resource_name=self.model.__name__, resource_id=id)
        return self._to_response_dto(instance)

    def list(self, last_id: Optional[UUID] = None, limit: int = 100, include_deleted: bool = False) -> List[TResponseSchema]:
        """Lista recursos com paginação baseada em cursor."""
        query = self.db.query(self.model)
        if last_id:
            query = query.filter(self.model.id > last_id)
        if not include_deleted and hasattr(self.model, 'deleted_at'):
            query = query.filter(self.model.deleted_at.is_(None))
        instances = query.order_by(self.model.id).limit(limit).all()
        return [self._to_response_dto(instance) for instance in instances]

    def create(self, create_dto: TCreateSchema, current_user_id: Optional[UUID] = None) -> TResponseSchema:
        """Cria um novo recurso."""
        try:
            create_dto.model_validate(create_dto, strict=True)
        except ServiceValidationError as e:
            raise ServiceValidationError("Dados de criação inválidos", errors=e.errors())
        try:
            with self.transaction():
                unique_constraints = [col.name for col in self.model.__table__.columns if col.unique]
                for field in unique_constraints:
                    if hasattr(create_dto, field):
                        existing = self.db.query(self.model).filter(
                            getattr(self.model, field) == getattr(create_dto, field),
                            getattr(self.model, 'deleted_at', None) == None
                        ).first()
                        if existing:
                            raise ServiceValidationError(f"{self.model.__name__} com {field} já existe.")
                instance = self.model(**create_dto.model_dump(exclude_unset=True))
                self._apply_audit_fields(instance, current_user_id)
                self.db.add(instance)
                logger.info(f"Criando {self.model.__name__} com dados: {create_dto}")
                self.db.refresh(instance)
                return self._to_response_dto(instance)
        except IE as e:
            logger.error(f"Erro de integridade ao criar {self.model.__name__}: {str(e)}")
            raise ServiceIntegrityError(f"Erro ao criar {self.model.__name__}: {str(e)}")
        except Exception as e:
            logger.error(f"Erro inesperado ao criar {self.model.__name__}: {str(e)}")
            raise ServiceException(f"Erro inesperado ao criar {self.model.__name__}")

    def update(self, id: UUID, update_dto: TUpdateSchema, current_user_id: Optional[UUID] = None) -> TResponseSchema:
        """Atualiza um recurso existente."""
        instance = self.db.query(self.model).filter(self.model.id == id).first()
        if not instance:
            raise NotFoundError(resource_name=self.model.__name__, resource_id=id)
        try:
            with self.transaction():
                update_data = update_dto.model_dump(exclude_unset=True)
                if not update_data:
                    raise ServiceValidationError("Pelo menos um campo deve ser fornecido para atualização")
                for field, value in update_data.items():
                    setattr(instance, field, value)
                if hasattr(instance, 'updated_by'):
                    instance.updated_by = current_user_id
                self.db.refresh(instance)
                return self._to_response_dto(instance)
        except ServiceIntegrityError as e:
            logger.error(f"Erro de integridade ao atualizar {self.model.__name__}: {str(e)}")
            raise ServiceIntegrityError(f"Erro ao atualizar {self.model.__name__}: {str(e)}")
        except Exception as e:
            logger.error(f"Erro inesperado ao atualizar {self.model.__name__}: {str(e)}")
            raise ServiceException(f"Erro inesperado ao atualizar {self.model.__name__}")

    def delete(self, id: UUID, current_user_id: Optional[UUID] = None, hard_delete: bool = False) -> bool:
        instance = self.db.query(self.model).filter(self.model.id == id).first()
        if not instance:
            raise NotFoundError(resource_name=self.model.__name__, resource_id=id)
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

    def restore(self, id: UUID, current_user_id: Optional[UUID] = None) -> TResponseSchema:
        if not hasattr(self.model, 'deleted_at'):
            raise ServiceException(f"{self.model.__name__} não suporta soft delete")
        instance = self.db.query(self.model).filter(self.model.id == id).first()
        if not instance:
            raise NotFoundError(resource_name=self.model.__name__, resource_id=id)
        if not instance.deleted_at:
            raise ServiceException(f"{self.model.__name__} com id {id} não está deletado")
        if instance.deleted_at is None:
            logger.info(f"{self.model.__name__} com id {id} já está restaurado")
            return self._to_response_dto(instance)
        try:
            with self.transaction():
                instance.deleted_at = None
                instance.deleted_by = None
                if hasattr(instance, 'updated_by'):
                    instance.updated_by = current_user_id
                self.db.refresh(instance)
                return self._to_response_dto(instance)
        except Exception as e:
            logger.error(f"Erro ao restaurar {self.model.__name__}: {str(e)}")
            raise ServiceException(f"Erro ao restaurar {self.model.__name__}")

class UserService(BaseService[User, DTOUserCreate, DTOUserUpdate, DTOUserResponse]):
    """Serviço para operações CRUD de usuários, com métodos específicos para email, username e papéis."""

    def __init__(self, db: Session):
        super().__init__(User, db)

    def get_by_email(self, email: str, include_deleted: bool = False) -> DTOUserResponse:
        """Recupera um usuário pelo email."""
        query = self.db.query(self.model).filter(self.model.email == email)
        if not include_deleted:
            query = query.filter(self.model.deleted_at.is_(None))
        instance = query.first()
        if not instance:
            raise NotFoundError(resource_name="User", resource_id=email)
        return self._to_response_dto(instance)

    def get_by_username(self, username: str, include_deleted: bool = False) -> DTOUserResponse:
        """Recupera um usuário pelo nome de usuário."""
        query = self.db.query(self.model).filter(self.model.username == username)
        if not include_deleted:
            query = query.filter(self.model.deleted_at.is_(None))
        instance = query.first()
        if not instance:
            raise NotFoundError(resource_name="User", resource_id=username)
        return self._to_response_dto(instance)

    def update_roles(self, user_id: UUID, role_ids: List[UUID], current_user_id: Optional[UUID] = None) -> DTOUserResponse:
        """Atualiza os papéis associados a um usuário."""
        if len(role_ids) > Validation.MAX_ROLES_PER_USER:
            raise ServiceValidationError(
                message=f"Um usuário não pode ter mais de {Validation.MAX_ROLES_PER_USER} papéis",
                errors={"role_ids": "Muitos papéis"}
            )
        if len(role_ids) != len(set(role_ids)):
            raise ServiceValidationError(
                message="Papéis duplicados não são permitidos",
                errors={"role_ids": "Duplicatas detectadas"}
            )
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            raise NotFoundError(resource_name="User", resource_id=user_id)
        roles = self.db.query(Role).filter(Role.id.in_(role_ids), Role.deleted_at.is_(None)).all()
        permissions = set()
        for role in roles:
            for perm in role.permissions:
                if perm.action in permissions:
                    raise ServiceValidationError(f"Conflito de permissões detectado: {perm.action}")
                permissions.add(perm.action)
        if len(roles) != len(role_ids):
            found_ids = {str(role.id) for role in roles}
            missing_ids = [str(rid) for rid in role_ids if rid not in found_ids]
            raise NotFoundError(
                message=f"Alguns papéis não encontrados: {', '.join(missing_ids)}",
                code="roles_not_found"
            )
        try:
            with self.transaction():
                user.roles = roles
                if hasattr(user, 'updated_by'):
                    user.updated_by = current_user_id
                self.db.refresh(user)
                return self._to_response_dto(user)
        except Exception as e:
            logger.error(f"Erro ao atualizar papéis do usuário: {str(e)}")
            raise ServiceException(f"Erro ao atualizar papéis do usuário: {str(e)}")

    def set_password(self, user_id: UUID, password: str, current_user_id: Optional[UUID] = None) -> bool:
        """Define a senha de um usuário (hash da senha)."""
        PASSWORD_MIN_LENGTH = 8
        if len(password) < PASSWORD_MIN_LENGTH:
            raise ServiceValidationError(f"A senha deve ter pelo menos {PASSWORD_MIN_LENGTH} caracteres")
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            raise NotFoundError(resource_name="User", resource_id=user_id)
        try:
            with self.transaction():
                user.set_password(generate_password_hash(password, method='pbkdf2:sha256'))
                if hasattr(user, 'updated_by'):
                    user.updated_by = current_user_id
                return True
        except Exception as e:
            logger.error(f"Erro ao definir senha: {str(e)}")
            raise ServiceException(f"Erro ao definir senha: {str(e)}")

class RoleService(BaseService[Role, DTORoleCreate, DTORoleUpdate, DTORoleResponse]):
    """Serviço para operações CRUD de papéis, com métodos para papéis padrão e permissões."""

    def __init__(self, db: Session):
        super().__init__(Role, db)

    def get_default_roles(self, include_deleted: bool = False) -> List[DTORoleResponse]:
        """Recupera todos os papéis padrão."""
        query = self.db.query(self.model).filter(self.model.is_default == True)
        if not include_deleted:
            query = query.filter(self.model.deleted_at.is_(None))
        instances = query.all()
        return [self._to_response_dto(instance) for instance in instances]

    def update_permissions(self, role_id: UUID, permission_ids: List[UUID], current_user_id: Optional[UUID] = None) -> DTORoleResponse:
        """Atualiza as permissões associadas a um papel."""
        if len(permission_ids) > Validation.MAX_PERMISSIONS_PER_ROLE:
            raise ServiceValidationError(
                message=f"Um papel não pode ter mais de {Validation.MAX_PERMISSIONS_PER_ROLE} permissões",
                errors={"permission_ids": "Muitas permissões"}
            )
        if len(permission_ids) != len(set(permission_ids)):
            raise ServiceValidationError(
                message="Permissões duplicadas não são permitidas",
                errors={"permission_ids": "Duplicatas detectadas"}
            )
        role = self.db.query(Role).filter(Role.id == role_id).first()
        if not role:
            raise NotFoundError(resource_name="Role", resource_id=role_id)
        permissions = self.db.query(Permission).filter(Permission.id.in_(permission_ids), Permission.deleted_at.is_(None)).all()
        if len(permissions) != len(permission_ids):
            found_ids = {str(perm.id) for perm in permissions}
            missing_ids = [str(pid) for pid in permission_ids if pid not in found_ids]
            raise NotFoundError(
                message=f"Algumas permissões não encontradas: {', '.join(missing_ids)}",
                code="permissions_not_found"
            )
        try:
            with self.transaction():
                role.permissions = permissions
                if hasattr(role, 'updated_by'):
                    role.updated_by = current_user_id
                self.db.refresh(role)
                return self._to_response_dto(role)
        except Exception as e:
            logger.error(f"Erro ao atualizar permissões do papel: {str(e)}")
            raise ServiceException(f"Erro ao atualizar permissões do papel: {str(e)}")

class PermissionService(BaseService[Permission, DTOPermissionCreate, DTOPermissionUpdate, DTOPermissionResponse]):
    """Serviço para operações CRUD de permissões, com método específico para busca por ação."""

    def __init__(self, db: Session):
        super().__init__(Permission, db)

    def get_by_actions(self, action: str, include_deleted: bool = False) -> List[DTOPermissionResponse]:
        """Recupera permissões pelo tipo de ação."""
        if action not in [e.value for e in EnumPermissionAction]:
            raise ServiceValidationError(f"Ação inválida: {action}", errors={"action": "Ação não existe"})
        query = self.db.query(self.model).filter(self.model.action == action)
        if not include_deleted:
            query = query.filter(self.model.deleted_at.is_(None))
        instances = query.all()
        if not instances:
            raise NotFoundError(resource_name="Permission", resource_id=f"action={action}")
        return [self._to_response_dto(instance) for instance in instances]

__all__ = [
    'BaseService',
    'ServiceException',
    'NotFoundError',
    'ServiceIntegrityError',
    'ServiceValidationError',
    'UserService',
    'RoleService',
    'PermissionService'
]