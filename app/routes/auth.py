
from fastapi import APIRouter, Depends, HTTPException, status

from app.dependencies.containers import get_auth_service, get_user_repo
from app.dependencies.security import get_current_user
from app.repositories.interfaces.user_repository import IUserRepository
from app.schemas.auth import (
    AuthResponse,
    LoginRequest,
    RegisterRequest,
    UpdateMeRequest,
    UserOut,
)
from app.services.auth_service import AuthService

router = APIRouter(prefix="/api/auth", tags=["Autenticación"])

def _to_auth_response(user: dict, token: str, expires_in: int) -> AuthResponse:
    return AuthResponse(
        user=UserOut(**user),
        access_token=token,
        token_type="bearer",
        expires_in=expires_in,
    )

@router.post(
    "/register",
    status_code=201,
    response_model=AuthResponse,
    summary="Registrar nueva cuenta",
)
def register(
    data: RegisterRequest,
    auth_service: AuthService = Depends(get_auth_service),
) -> AuthResponse:
    user, token, expires_in = auth_service.register_user(data)
    return _to_auth_response(user, token, expires_in)

@router.post(
    "/login",
    response_model=AuthResponse,
    summary="Iniciar sesión y obtener JWT",
)
def login(
    data: LoginRequest,
    auth_service: AuthService = Depends(get_auth_service),
) -> AuthResponse:
    user, token, expires_in = auth_service.authenticate_user(data)
    return _to_auth_response(user, token, expires_in)

@router.get(
    "/me",
    response_model=UserOut,
    summary="Datos del usuario autenticado",
)
def me(current_user: dict = Depends(get_current_user)) -> UserOut:
    return UserOut(**current_user)

@router.put(
    "/me",
    response_model=UserOut,
    summary="Actualizar nombre o email del usuario actual",
)
def update_me(
    data: UpdateMeRequest,
    current_user: dict = Depends(get_current_user),
    user_repo: IUserRepository = Depends(get_user_repo),
) -> UserOut:
    user_id = current_user["id"]
    updated = current_user

    if data.email is not None and data.email != current_user["email"]:
        existing = user_repo.get_by_email(data.email)
        if existing and existing["id"] != user_id:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Ya existe una cuenta con ese email",
            )
        updated = user_repo.update_email(user_id, data.email) or updated

    if data.name is not None and data.name.strip() != current_user["name"]:
        updated = user_repo.update_name(user_id, data.name.strip()) or updated

    return UserOut(**updated)
