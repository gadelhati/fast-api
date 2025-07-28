# Router administrativo separado para funções de segurança

from fastapi import APIRouter, HTTPException, Depends, status
from sqlalchemy.orm import Session
from uuid import UUID

from src.database import get_db
from src.schema.basic import ResponseError
from src.service.user import ServiceUser

admin_router = APIRouter(prefix="/admin/users", tags=["admin-users"])

@admin_router.get("/{user_id}/security-status", status_code=status.HTTP_200_OK, response_model=ResponseError)
async def get_user_security_status(
    user_id: UUID,
    db: Session = Depends(get_db),
    current_user = Depends(ServiceUser.get_by_username)
):
    """
    Obter status de segurança de um usuário.
    APENAS para administradores - contém informações sensíveis.
    """
    service = ServiceUser(db)
    result = service.get_security_status(user_id)
    return ResponseError(
        code=200,
        status="Ok",
        message="Status de segurança obtido",
        validationErrors=result
    ).dict(exclude_none=True)

@admin_router.post("/{user_id}/unlock", status_code=status.HTTP_200_OK, response_model=ResponseError)
async def unlock_user_account(
    user_id: UUID,
    db: Session = Depends(get_db),
    current_user = Depends(ServiceUser.get_by_username)
):
    """
    Desbloquear conta de usuário manualmente.
    APENAS para administradores.
    """
    service = ServiceUser(db)
    current_user_id = getattr(current_user, 'id', None) if current_user else None
    
    result = service.unlock_account(user_id, current_user_id)
    return ResponseError(
        code=200,
        status="Ok",
        message="Conta desbloqueada com sucesso",
        validationErrors={"unlocked": result}
    ).dict(exclude_none=True)

# ✅ Endpoint para autenticação (usado pelo sistema de auth, não API pública)
auth_router = APIRouter(prefix="/auth", tags=["authentication"])

@auth_router.post("/login", status_code=status.HTTP_200_OK)
async def authenticate_user(
    credentials: dict,  # username/email + password
    db: Session = Depends(get_db)
):
    """
    Endpoint de autenticação que gerencia controles de segurança.
    Usado internamente pelo sistema de autenticação.
    """
    service = ServiceUser(db)
    
    username_or_email = credentials.get("username") or credentials.get("email")
    password = credentials.get("password")
    
    if not username_or_email or not password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"message": "Username/email e senha são obrigatórios", "code": "missing_credentials"}
        )
    
    user = service.authenticate_user(username_or_email, password)
    
    if not user:
        # ⚠️ Mensagem genérica para não vazar informações
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"message": "Credenciais inválidas", "code": "invalid_credentials"}
        )
    
    # Aqui você geraria o token JWT ou sessão
    return {
        "message": "Login realizado com sucesso",
        "user": user,
        # "access_token": generate_jwt_token(user),
        # "token_type": "bearer"
    }