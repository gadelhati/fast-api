from fastapi import APIRouter, Depends, HTTPException, Query, Path
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional
from uuid import UUID

from src.service.permission import ServicePermission
from src.schema.permission import DTOPermissionRetrieve
from src.enum.permissionAction import EnumPermissionAction
from src.service.basic import ServiceException
from src.database import get_db

permission = APIRouter(
    prefix="/permissions",
    tags=["permissions"]
)

def get_permission_service(db: Session = Depends(get_db)) -> ServicePermission:
    """Dependency to get permission service instance"""
    return ServicePermission(db)

@permission.get("/", response_model=Dict[str, Any])
async def list_permissions(
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(20, ge=1, le=100, description="Items per page"),
    include_deleted: bool = Query(False, description="Include soft-deleted permissions"),
    action: Optional[str] = Query(None, description="Filter by action"),
    service: ServicePermission = Depends(get_permission_service)
):
    """
    List all permissions with pagination and optional filters
    """
    try:
        filters = {}
        if action:
            filters["action"] = action
        
        result = service.list(
            page=page,
            limit=limit,
            include_deleted=include_deleted,
            **filters
        )
        return result
    except ServiceException as e:
        raise HTTPException(status_code=400, detail=e.message)
    except Exception as e:
        raise HTTPException(status_code=500, detail="Internal server error")

@permission.get("/{permission_id}", response_model=DTOPermissionRetrieve)
async def get_permission(
    permission_id: UUID = Path(..., description="Permission ID"),
    include_deleted: bool = Query(False, description="Include soft-deleted permissions"),
    service: ServicePermission = Depends(get_permission_service)
):
    """
    Get a specific permission by ID
    """
    try:
        return service.get(permission_id, include_deleted=include_deleted)
    except ServiceException as e:
        if e.code == "not_found":
            raise HTTPException(status_code=404, detail=e.message)
        raise HTTPException(status_code=400, detail=e.message)
    except Exception as e:
        raise HTTPException(status_code=500, detail="Internal server error")

@permission.get("/by-action/{action}", response_model=List[DTOPermissionRetrieve])
async def get_permissions_by_action(
    action: EnumPermissionAction = Path(..., description="Permission action"),
    include_deleted: bool = Query(False, description="Include soft-deleted permissions"),
    service: ServicePermission = Depends(get_permission_service)
):
    """
    Get all permissions by action type
    """
    try:
        return service.get_by_action(action, include_deleted=include_deleted)
    except ServiceException as e:
        raise HTTPException(status_code=400, detail=e.message)
    except Exception as e:
        raise HTTPException(status_code=500, detail="Internal server error")

@permission.post("/sync")
async def sync_permissions_with_enum(
    service: ServicePermission = Depends(get_permission_service)
):
    """
    Synchronize permissions in database with enum values
    Creates missing permissions based on EnumPermissionAction
    """
    try:
        service.sync_with_enum()
        return {"message": "Permissions synchronized successfully"}
    except ServiceException as e:
        raise HTTPException(status_code=400, detail=e.message)
    except Exception as e:
        raise HTTPException(status_code=500, detail="Internal server error")

@permission.delete("/{permission_id}")
async def delete_permission(
    permission_id: UUID = Path(..., description="Permission ID"),
    service: ServicePermission = Depends(get_permission_service)
):
    """
    Hard delete a permission (permanently remove from database)
    """
    try:
        success = service.delete(permission_id)
        if success:
            return {"message": "Permission deleted successfully"}
        else:
            raise HTTPException(status_code=400, detail="Failed to delete permission")
    except ServiceException as e:
        if e.code == "not_found":
            raise HTTPException(status_code=404, detail=e.message)
        raise HTTPException(status_code=400, detail=e.message)
    except Exception as e:
        raise HTTPException(status_code=500, detail="Internal server error")

@permission.patch("/{permission_id}/soft-delete")
async def soft_delete_permission(
    permission_id: UUID = Path(..., description="Permission ID"),
    current_user_id: Optional[UUID] = Query(None, description="Current user ID for audit"),
    service: ServicePermission = Depends(get_permission_service)
):
    """
    Soft delete a permission (mark as deleted without removing from database)
    """
    try:
        success = service.soft_delete(permission_id, current_user_id=current_user_id)
        if success:
            return {"message": "Permission soft deleted successfully"}
        else:
            raise HTTPException(status_code=400, detail="Failed to soft delete permission")
    except ServiceException as e:
        if e.code == "not_found":
            raise HTTPException(status_code=404, detail=e.message)
        elif e.code == "not_supported":
            raise HTTPException(status_code=400, detail=e.message)
        raise HTTPException(status_code=400, detail=e.message)
    except Exception as e:
        raise HTTPException(status_code=500, detail="Internal server error")

@permission.patch("/{permission_id}/restore", response_model=DTOPermissionRetrieve)
async def restore_permission(
    permission_id: UUID = Path(..., description="Permission ID"),
    current_user_id: Optional[UUID] = Query(None, description="Current user ID for audit"),
    service: ServicePermission = Depends(get_permission_service)
):
    """
    Restore a soft-deleted permission
    """
    try:
        return service.restore(permission_id, current_user_id=current_user_id)
    except ServiceException as e:
        if e.code == "not_found":
            raise HTTPException(status_code=404, detail=e.message)
        elif e.code == "invalid_operation":
            raise HTTPException(status_code=400, detail=e.message)
        raise HTTPException(status_code=400, detail=e.message)
    except Exception as e:
        raise HTTPException(status_code=500, detail="Internal server error")

# Additional utility endpoints
@permission.get("/actions/available", response_model=List[str])
async def get_available_actions():
    """
    Get all available permission actions from enum
    """
    return [action.value for action in EnumPermissionAction]

@permission.get("/health/check")
async def health_check(
    service: ServicePermission = Depends(get_permission_service)
):
    """
    Health check endpoint to verify service connectivity
    """
    try:
        # Try to perform a simple query to check database connectivity
        service.list(page=1, limit=1)
        return {"status": "healthy", "service": "permission"}
    except Exception as e:
        raise HTTPException(status_code=503, detail="Service unavailable")