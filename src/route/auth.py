from fastapi import APIRouter, HTTPException, Depends, status
from sqlalchemy.orm import Session
from uuid import uuid4
from src.database import get_db
from src.schema.auth import DTOLogin
from src.service.user import ServiceUser

auth = APIRouter(prefix="/auth", tags=["auth"])

@auth.post("/login", status_code=status.HTTP_200_OK)
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


@auth.post('/signup', summary="Create new user", response_model=DTOLogin)
async def create_user(data: DTOLogin):
    # querying database to check if user already exist
    user = db.get(data.email, None)
    if user is not None:
            raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User with this email already exist"
        )
    user = {
        'email': data.email,
        'password': get_hashed_password(data.password),
        'id': str(uuid4())
    }
    db[data.email] = user    # saving user to database
    return user