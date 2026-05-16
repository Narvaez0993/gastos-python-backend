
from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer

from app.dependencies.containers import get_auth_service
from app.services.auth_service import AuthService

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login", auto_error=True)

def get_current_user(
    token: str = Depends(oauth2_scheme),
    auth_service: AuthService = Depends(get_auth_service),
) -> dict:
    return auth_service.get_user_from_token(token)
