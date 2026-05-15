"""Dependency de FastAPI para extraer el usuario actual a partir del JWT."""

from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer

from app.dependencies.containers import get_auth_service
from app.services.auth_service import AuthService


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login", auto_error=True)


def get_current_user(
    token: str = Depends(oauth2_scheme),
    auth_service: AuthService = Depends(get_auth_service),
) -> dict:
    """Devuelve el dict público del user actual o lanza 401."""
    return auth_service.get_user_from_token(token)
