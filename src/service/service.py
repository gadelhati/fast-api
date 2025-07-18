from typing import Type, TypeVar, Generic, Optional, List, Any
from uuid import UUID
from datetime import datetime
from sqlalchemy.orm import Session, Query
from sqlalchemy.exc import IntegrityError as IE
from pydantic import BaseModel
import logging
from contextlib import contextmanager
from werkzeug.security import generate_password_hash

from model import Base, User, Role, Permission
from schema import (
    DTOUserCreate, DTOUserUpdate, DTOUserResponse,
    DTORoleCreate, DTORoleUpdate, DTORoleResponse,
    DTOPermissionCreate, DTOPermissionUpdate, DTOPermissionResponse,
    EnumPermissionAction, Validation
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
    """Classe base genérica para operações CRUD.

    Suporta auditoria, soft delete e paginação para qualquer modelo SQLAlchemy
    com DTOs Pydantic correspondentes.

    Attributes:
        model: Classe do modelo SQLAlchemy.
        db: Sessão do banco de dados SQLAlchemy.
    """

    def __init__(self, model: Type[TModel], db: Session):
        self.model = model
        self.db = db

    @contextmanager
    def transaction(self):
        """Gerenciador de contexto para transações de banco de dados."""
        try:
            yield self.db
            self.db.commit()
        except Exception as e:
            self.db.rollback()
            raise

    def _apply_audit_fields(self, instance: TModel, current_user_id: Optional[UUID] = None) -> TModel:
        """
        Aplica campos de auditoria ao modelo.

        Args:
            instance: Instância do modelo.
            current_user_id: UUID do usuário que realiza a operação (para auditoria).

        Returns:
            Instância do modelo com campos de auditoria atualizados.
        """
        if hasattr(instance, 'created_by') and not instance.created_by:
            instance.created_by = current_user_id
        if hasattr(instance, 'updated_by'):
            instance.updated_by = current_user_id
        return instance

    def _to_response_dto(self, instance: TModel) -> TResponseSchema:
        """
        Converte uma instância do modelo em um DTO de resposta.

        Args:
            instance: Instância do modelo.

        Returns:
            DTO de resposta correspondente.
        """
        try:
            return TResponseSchema.model_validate(instance, from_attributes=True)
        except ServiceValidationError as e:
            raise RuntimeError(f"Erro ao converter para DTO: {e}")

    def get(self, id: UUID, include_deleted: bool = False) -> TResponseSchema:
        """
        Recupera um recurso pelo ID.

        Args:
            id: UUID do recurso.
            include_deleted: Se True, inclui recursos deletados logicamente.

        Returns:
            DTO de resposta correspondente ao recurso.

        Raises:
            NotFoundError: Se o recurso não for encontrado.
        """
        query = self.db.query(self.model).filter(self.model.id == id)
        if not include_deleted and hasattr(self.model, 'deleted_at'):
            query = query.filter(self.model.deleted_at.is_(None))
        instance = query.first()
        if not instance:
            raise NotFoundError(resource_name=self.model.__name__, resource_id=id)
        return self._to_response_dto(instance)

    def list(self, last_id: Optional[UUID] = None, limit: int = 100, include_deleted: bool = False) -> List[TResponseSchema]:
        """
        Lista recursos com paginação baseada em cursor.

        Args:
            last_id: UUID do último recurso para paginação (opcional).
            limit: Número máximo de registros a retornar.
            include_deleted: Se True, inclui recursos deletados logicamente.

        Returns:
            Lista de DTOs de resposta.

        Note:
            Recomenda-se criar um índice em `id` para otimizar a paginação.
        """
        query = self.db.query(self.model)
        if last_id:
            query = query.filter(self.model.id > last_id)
        if not include_deleted and hasattr(self.model, 'deleted_at'):
            query = query.filter(self.model.deleted_at.is_(None))
        instances = query.order_by(self.model.id).limit(limit).all()
        return [self._to_response_dto(instance) for instance in instances]

    def create(self, create_dto: TCreateSchema, current_user_id: Optional[UUID] = None) -> TResponseSchema:
        """
        Cria um novo recurso.

        Args:
            create_dto: DTO com dados para criação.
            current_user_id: UUID do usuário que realiza a operação (para auditoria).

        Returns:
            DTO de resposta do recurso criado.

        Raises:
            IntegrityError: Se houver violação de integridade no banco.
            ServiceException: Se ocorrer um erro inesperado.
        """
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
        except ServiceIntegrityError as e:
            logger.error(f"Erro de integridade ao criar {self.model.__name__}: {str(e)}")
            raise ServiceIntegrityError(f"Erro ao criar {self.model.__name__}: {str(e)}")
        except Exception as e:
            logger.error(f"Erro inesperado ao criar {self.model.__name__}: {str(e)}")
            raise ServiceException(f"Erro inesperado ao criar {self.model.__name__}")

    def update(self, id: UUID, update_dto: TUpdateSchema, current_user_id: Optional[UUID] = None) -> TResponseSchema:
        """
        Atualiza um recurso existente.

        Args:
            id: UUID do recurso.
            update_dto: DTO com dados para atualização.
            current_user_id: UUID do usuário que realiza a operação (para auditoria).

        Returns:
            DTO de resposta do recurso atualizado.

        Raises:
            NotFoundError: Se o recurso não for encontrado.
            IntegrityError: Se houver violação de integridade no banco.
            ServiceException: Se ocorrer um erro inesperado.
        """
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
        """
        Recupera um usuário pelo email.

        Args:
            email: Email do usuário.
            include_deleted: Se True, inclui usuários deletados logicamente.

        Returns:
            DTOUserResponse com os dados do usuário.

        Raises:
            NotFoundError: Se o usuário não for encontrado.
        """
        query = self.db.query(self.model).filter(self.model.email == email)
        if not include_deleted:
            query = query.filter(self.model.deleted_at.is_(None))
        instance = query.first()
        if not instance:
            raise NotFoundError(resource_name="User", resource_id=email)
        return self._to_response_dto(instance)

    def get_by_username(self, username: str, include_deleted: bool = False) -> DTOUserResponse:
        """
        Recupera um usuário pelo nome de usuário.

        Args:
            username: Nome de usuário.
            include_deleted: Se True, inclui usuários deletados logicamente.

        Returns:
            DTOUserResponse com os dados do usuário.

        Raises:
            NotFoundError: Se o usuário não for encontrado.
        """
        query = self.db.query(self.model).filter(self.model.username == username)
        if not include_deleted:
            query = query.filter(self.model.deleted_at.is_(None))
        instance = query.first()
        if not instance:
            raise NotFoundError(resource_name="User", resource_id=username)
        return self._to_response_dto(instance)

    def update_roles(self, user_id: UUID, role_ids: List[UUID], current_user_id: Optional[UUID] = None) -> DTOUserResponse:
        """
        Atualiza os papéis associados a um usuário.

        Args:
            user_id: UUID do usuário.
            role_ids: Lista de UUIDs dos papéis a serem associados.
            current_user_id: UUID do usuário que realiza a operação (para auditoria).

        Returns:
            DTOUserResponse com os dados atualizados do usuário.

        Raises:
            ValidationError: Se o número de papéis exceder o limite ou houver duplicatas.
            NotFoundError: Se o usuário ou algum papel não for encontrado.
            ServiceException: Se ocorrer um erro ao atualizar os papéis.
        """
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
        """
        Define a senha de um usuário (hash da senha).

        Args:
            user_id: UUID do usuário.
            password: Senha em texto plano a ser hasheada.
            current_user_id: UUID do usuário que realiza a operação (para auditoria).

        Returns:
            True se a senha for definida com sucesso.

        Raises:
            NotFoundError: Se o usuário não for encontrado.
            ServiceException: Se ocorrer um erro ao definir a senha.
        """
        if len(password) < 8:
            raise ServiceValidationError("A senha deve ter pelo menos 8 caracteres")
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
        """
        Recupera todos os papéis padrão.

        Args:
            include_deleted: Se True, inclui papéis deletados logicamente.

        Returns:
            Lista de DTOs de resposta com os papéis padrão.

        Note:
            Recomenda-se criar um índice em `is_default` para otimizar esta query.
        """
        query = self.db.query(self.model).filter(self.model.is_default == True)
        if not include_deleted:
            query = query.filter(self.model.deleted_at.is_(None))
        instances = query.all()
        return [self._to_response_dto(instance) for instance in instances]

    def update_permissions(self, role_id: UUID, permission_ids: List[UUID], current_user_id: Optional[UUID] = None) -> DTORoleResponse:
        """
        Atualiza as permissões associadas a um papel.

        Args:
            role_id: UUID do papel.
            permission_ids: Lista de UUIDs das permissões a serem associadas.
            current_user_id: UUID do usuário que realiza a operação (para auditoria).

        Returns:
            DTORoleResponse com os dados atualizados do papel.

        Raises:
            ValidationError: Se o número de permissões exceder o limite ou houver duplicatas.
            NotFoundError: Se o papel ou alguma permissão não for encontrada.
            ServiceException: Se ocorrer um erro ao atualizar as permissões.
        """
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

    def get_by_action(self, action: str, include_deleted: bool = False) -> List[DTOPermissionResponse]:
        """
        Recupera permissões pelo tipo de ação.

        Args:
            action: Tipo de ação (e.g., 'create', 'read').
            include_deleted: Se True, inclui permissões deletadas logicamente.

        Returns:
            Lista de DTOs de resposta com as permissões encontradas.

        Raises:
            ValidationError: Se a ação fornecida for inválida.
            NotFoundError: Se nenhuma permissão for encontrada.

        Note:
            Recomenda-se criar um índice em `action` para otimizar esta query.
        """
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