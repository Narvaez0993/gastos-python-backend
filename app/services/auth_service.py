"""Servicio de autenticación: hashing, JWT, registro y login."""

from datetime import datetime, timedelta, timezone
from typing import Optional

import bcrypt
from fastapi import HTTPException, status
from jose import JWTError, jwt

from app.config.settings import get_settings
from app.repositories.interfaces.user_repository import IUserRepository
from app.schemas.auth import LoginRequest, RegisterRequest


# bcrypt acepta máximo 72 bytes en la entrada. Truncamos silenciosamente
# para mantener compatibilidad con el comportamiento clásico (pre bcrypt 4.1).
_BCRYPT_MAX_BYTES = 72


def _encode_for_bcrypt(password: str) -> bytes:
    encoded = password.encode("utf-8")
    return encoded[:_BCRYPT_MAX_BYTES]


class AuthService:
    """Encapsula registro, login y emisión/validación de JWT.

    Decisión: `password_hash` SOLO se lee/escribe acá y en el repositorio.
    Nunca debe salir hacia capas superiores (services, routes, schemas de respuesta).
    """

    def __init__(self, user_repo: IUserRepository):
        self.user_repo = user_repo
        self.rounds = get_settings().BCRYPT_ROUNDS

    def hash_password(self, password: str) -> str:
        salt = bcrypt.gensalt(rounds=self.rounds)
        hashed = bcrypt.hashpw(_encode_for_bcrypt(password), salt)
        return hashed.decode("utf-8")

    def verify_password(self, plain: str, hashed: str) -> bool:
        try:
            return bcrypt.checkpw(
                _encode_for_bcrypt(plain), hashed.encode("utf-8")
            )
        except (ValueError, TypeError):
            return False

    def create_access_token(self, user_id: int) -> tuple[str, int]:
        """Devuelve (token, expires_in_seconds)."""
        settings = get_settings()
        now = datetime.now(timezone.utc)
        expire = now + timedelta(minutes=settings.JWT_EXPIRES_MINUTES)
        payload = {
            "sub": str(user_id),
            "iat": int(now.timestamp()),
            "exp": int(expire.timestamp()),
            "type": "access",
        }
        token = jwt.encode(payload, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)
        return token, settings.JWT_EXPIRES_MINUTES * 60

    def decode_token(self, token: str) -> dict:
        settings = get_settings()
        try:
            return jwt.decode(
                token,
                settings.JWT_SECRET,
                algorithms=[settings.JWT_ALGORITHM],
            )
        except JWTError as e:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token inválido o expirado",
                headers={"WWW-Authenticate": "Bearer"},
            ) from e

    def register_user(self, data: RegisterRequest) -> tuple[dict, str, int]:
        """Crea un usuario y devuelve (user_public_dict, access_token, expires_in)."""
        existing = self.user_repo.get_by_email(data.email)
        if existing is not None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Ya existe una cuenta con ese email",
            )

        password_hash = self.hash_password(data.password)
        user = self.user_repo.create(
            name=data.name.strip(),
            email=data.email,
            password_hash=password_hash,
        )
        token, expires_in = self.create_access_token(user["id"])
        return user, token, expires_in

    def authenticate_user(self, data: LoginRequest) -> tuple[dict, str, int]:
        record = self.user_repo.get_by_email_with_credentials(data.email)
        if record is None or not self.verify_password(data.password, record["password_hash"]):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Email o contraseña incorrectos",
                headers={"WWW-Authenticate": "Bearer"},
            )

        public = {k: v for k, v in record.items() if k != "password_hash"}
        token, expires_in = self.create_access_token(public["id"])
        return public, token, expires_in

    def get_user_from_token(self, token: str) -> Optional[dict]:
        """Decodifica el JWT y carga el user (sin password_hash). Lanza 401 si inválido."""
        payload = self.decode_token(token)
        sub = payload.get("sub")
        if not sub:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token sin sujeto válido",
                headers={"WWW-Authenticate": "Bearer"},
            )
        try:
            user_id = int(sub)
        except (TypeError, ValueError) as e:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token con sub no entero",
                headers={"WWW-Authenticate": "Bearer"},
            ) from e

        user = self.user_repo.get_by_id(user_id)
        if user is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Usuario del token ya no existe",
                headers={"WWW-Authenticate": "Bearer"},
            )
        return user
