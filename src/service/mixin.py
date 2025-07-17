from typing import Any, Optional
from uuid import UUID as PyUUID
from datetime import datetime, timezone

class ServiceMixin:

    @staticmethod
    def soft_delete(entity: Any, deleted_by: Optional[PyUUID] = None) -> None:
        entity.deleted_at = datetime.now(timezone.utc)
        entity.deleted_by = deleted_by

    @staticmethod
    def restore(entity: Any) -> None:
        entity.deleted_at = None
        entity.deleted_by = None

    @staticmethod
    def is_deleted(entity: Any) -> bool:
        return entity.deleted_at is not None