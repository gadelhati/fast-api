from enum import Enum

class EnumPermissionAction(str, Enum):
    """Enum for permission actions"""
    CREATE = "create"
    READ = "read"
    UPDATE = "update"
    DELETE = "delete"
    EXECUTE = "execute"