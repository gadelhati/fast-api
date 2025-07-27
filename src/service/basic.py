from typing import TypeVar, Generic, Optional, Any
from uuid import UUID
from sqlalchemy.exc import IntegrityError as IE
from pydantic import BaseModel
import logging
from contextlib import contextmanager
from src.database import Base

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

    def create(self, create_dto: TCreateSchema, current_user_id: Optional[UUID] = None) -> TResponseSchema:
        """Cria um novo recurso."""
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
        except ServiceValidationError:
            raise
        except Exception as e:
            logger.error(f"Erro inesperado ao criar {self.model.__name__}: {str(e)}")
            raise ServiceException(f"Erro inesperado ao criar {self.model.__name__}")

__all__ = [
    'BaseService',
    'ServiceException',
    'NotFoundError',
    'ServiceIntegrityError',
    'ServiceValidationError'
]