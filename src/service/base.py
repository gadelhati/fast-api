# services/base_service.py
from typing import Type, TypeVar, Generic, Optional, List, Any
from uuid import UUID
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from pydantic import BaseModel
import logging
from src.database import Base

# Type variables for generic service
TModel = TypeVar('TModel', bound=Base)
TCreateSchema = TypeVar('TCreateSchema', bound=BaseModel)
TUpdateSchema = TypeVar('TUpdateSchema', bound=BaseModel)
TResponseSchema = TypeVar('TResponseSchema', bound=BaseModel)

logger = logging.getLogger(__name__)

class ServiceException(Exception):
    """Base exception for service layer errors"""
    def __init__(self, message: str, code: str = None):
        self.message = message
        self.code = code
        super().__init__(message)

class NotFoundError(ServiceException):
    """Raised when a resource is not found"""
    def __init__(self, resource_name: str, resource_id: Any):
        super().__init__(
            message=f"{resource_name} with id {resource_id} not found",
            code="not_found"
        )

class IntegrityError(ServiceException):
    """Raised when a database integrity error occurs"""
    def __init__(self, message: str):
        super().__init__(
            message=message,
            code="integrity_error"
        )

class ValidationError(ServiceException):
    """Raised when validation fails"""
    def __init__(self, message: str, errors: dict = None):
        super().__init__(
            message=message,
            code="validation_error"
        )
        self.errors = errors or {}

class BaseService(Generic[TModel, TCreateSchema, TUpdateSchema, TResponseSchema]):
    """Generic service class for CRUD operations"""
    
    def __init__(self, model: Type[TModel], db: Session):
        self.model = model
        self.db = db
    
    def _apply_audit_fields(self, instance: TModel, current_user_id: Optional[UUID] = None) -> TModel:
        """Apply audit fields to model instance"""
        if hasattr(instance, 'created_by') and not instance.created_by:
            instance.created_by = current_user_id
        if hasattr(instance, 'updated_by'):
            instance.updated_by = current_user_id
        return instance
    
    def _to_response_dto(self, instance: TModel) -> TResponseSchema:
        """Convert model instance to response DTO"""
        return TResponseSchema.model_validate(instance, from_attributes=True)
    
    def get(self, id: UUID, include_deleted: bool = False) -> TResponseSchema:
        """Get a single resource by ID"""
        query = self.db.query(self.model).filter(self.model.id == id)
        
        if not include_deleted and hasattr(self.model, 'deleted_at'):
            query = query.filter(self.model.deleted_at.is_(None))
            
        instance = query.first()
        
        if not instance:
            raise NotFoundError(resource_name=self.model.__name__, resource_id=id)
            
        return self._to_response_dto(instance)
    
    def list(self, skip: int = 0, limit: int = 100, include_deleted: bool = False) -> List[TResponseSchema]:
        """List resources with pagination"""
        query = self.db.query(self.model)
        
        if not include_deleted and hasattr(self.model, 'deleted_at'):
            query = query.filter(self.model.deleted_at.is_(None))
            
        instances = query.offset(skip).limit(limit).all()
        return [self._to_response_dto(instance) for instance in instances]
    
    def create(self, create_dto: TCreateSchema, current_user_id: Optional[UUID] = None) -> TResponseSchema:
        """Create a new resource"""
        try:
            instance = self.model(**create_dto.model_dump(exclude_unset=True))
            self._apply_audit_fields(instance, current_user_id)
            
            self.db.add(instance)
            self.db.commit()
            self.db.refresh(instance)
            
            return self._to_response_dto(instance)
            
        except IntegrityError as e:
            self.db.rollback()
            logger.error(f"Integrity error creating {self.model.__name__}: {str(e)}")
            raise IntegrityError(f"Error creating {self.model.__name__}: {str(e)}")
        except Exception as e:
            self.db.rollback()
            logger.error(f"Unexpected error creating {self.model.__name__}: {str(e)}")
            raise ServiceException(f"Unexpected error creating {self.model.__name__}")
    
    def update(
        self, 
        id: UUID, 
        update_dto: TUpdateSchema, 
        current_user_id: Optional[UUID] = None
    ) -> TResponseSchema:
        """Update an existing resource"""
        instance = self.db.query(self.model).filter(self.model.id == id).first()
        if not instance:
            raise NotFoundError(resource_name=self.model.__name__, resource_id=id)
            
        try:
            update_data = update_dto.model_dump(exclude_unset=True)
            
            for field, value in update_data.items():
                setattr(instance, field, value)
                
            if hasattr(instance, 'updated_by'):
                instance.updated_by = current_user_id
                
            self.db.commit()
            self.db.refresh(instance)
            
            return self._to_response_dto(instance)
            
        except IntegrityError as e:
            self.db.rollback()
            logger.error(f"Integrity error updating {self.model.__name__}: {str(e)}")
            raise IntegrityError(f"Error updating {self.model.__name__}: {str(e)}")
        except Exception as e:
            self.db.rollback()
            logger.error(f"Unexpected error updating {self.model.__name__}: {str(e)}")
            raise ServiceException(f"Unexpected error updating {self.model.__name__}")
    
    def delete(self, id: UUID, current_user_id: Optional[UUID] = None, hard_delete: bool = False) -> bool:
        """Delete a resource (soft delete by default)"""
        instance = self.db.query(self.model).filter(self.model.id == id).first()
        if not instance:
            raise NotFoundError(resource_name=self.model.__name__, resource_id=id)
            
        try:
            if hard_delete or not hasattr(self.model, 'deleted_at'):
                # Hard delete
                self.db.delete(instance)
            else:
                # Soft delete
                instance.deleted_at = datetime.now()
                if hasattr(instance, 'deleted_by'):
                    instance.deleted_by = current_user_id
                    
            self.db.commit()
            return True
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error deleting {self.model.__name__}: {str(e)}")
            raise ServiceException(f"Error deleting {self.model.__name__}")
    
    def restore(self, id: UUID, current_user_id: Optional[UUID] = None) -> TResponseSchema:
        """Restore a soft-deleted resource"""
        if not hasattr(self.model, 'deleted_at'):
            raise ServiceException(f"{self.model.__name__} does not support soft delete")
            
        instance = self.db.query(self.model).filter(self.model.id == id).first()
        if not instance:
            raise NotFoundError(resource_name=self.model.__name__, resource_id=id)
            
        if not instance.deleted_at:
            raise ServiceException(f"{self.model.__name__} with id {id} is not deleted")
            
        try:
            instance.deleted_at = None
            instance.deleted_by = None
            
            if hasattr(instance, 'updated_by'):
                instance.updated_by = current_user_id
                
            self.db.commit()
            self.db.refresh(instance)
            
            return self._to_response_dto(instance)
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error restoring {self.model.__name__}: {str(e)}")
            raise ServiceException(f"Error restoring {self.model.__name__}")