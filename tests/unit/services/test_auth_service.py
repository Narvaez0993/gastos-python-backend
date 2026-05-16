import time
from datetime import datetime, timedelta, timezone

import pytest
from fastapi import HTTPException
from jose import jwt

from app.config.settings import get_settings
from app.schemas.auth import LoginRequest, RegisterRequest


def test_hash_password_es_no_reversible_pero_verificable(auth_service):
    hashed = auth_service.hash_password("secret123")
    assert hashed != "secret123"
    assert auth_service.verify_password("secret123", hashed) is True
    assert auth_service.verify_password("wrong", hashed) is False


def test_create_access_token_es_decodificable(auth_service):
    token, expires_in = auth_service.create_access_token(user_id=42)
    payload = auth_service.decode_token(token)
    assert payload["sub"] == "42"
    assert payload["type"] == "access"
    assert expires_in > 0


def test_decode_token_invalido_devuelve_401(auth_service):
    with pytest.raises(HTTPException) as exc:
        auth_service.decode_token("not-a-jwt")
    assert exc.value.status_code == 401


def test_decode_token_expirado_devuelve_401(auth_service):
    settings = get_settings()
    expired = jwt.encode(
        {
            "sub": "1",
            "iat": int((datetime.now(timezone.utc) - timedelta(hours=2)).timestamp()),
            "exp": int((datetime.now(timezone.utc) - timedelta(hours=1)).timestamp()),
            "type": "access",
        },
        settings.JWT_SECRET,
        algorithm=settings.JWT_ALGORITHM,
    )
    with pytest.raises(HTTPException) as exc:
        auth_service.decode_token(expired)
    assert exc.value.status_code == 401


def test_register_user_crea_y_devuelve_token(auth_service_sql):
    user, token, expires = auth_service_sql.register_user(
        RegisterRequest(email="a@b.com", password="secret123", name="A")
    )
    assert user["email"] == "a@b.com"
    assert "password_hash" not in user
    assert token
    assert expires > 0


def test_register_email_duplicado_lanza_409(auth_service_sql):
    auth_service_sql.register_user(
        RegisterRequest(email="dup@b.com", password="secret123", name="A")
    )
    with pytest.raises(HTTPException) as exc:
        auth_service_sql.register_user(
            RegisterRequest(email="dup@b.com", password="secret123", name="B")
        )
    assert exc.value.status_code == 409


def test_authenticate_user_ok_devuelve_token(auth_service_sql):
    auth_service_sql.register_user(
        RegisterRequest(email="login@b.com", password="secret123", name="X")
    )
    user, token, _ = auth_service_sql.authenticate_user(
        LoginRequest(email="login@b.com", password="secret123")
    )
    assert user["email"] == "login@b.com"
    assert "password_hash" not in user
    assert token


def test_authenticate_user_password_incorrecta_lanza_401(auth_service_sql):
    auth_service_sql.register_user(
        RegisterRequest(email="bad@b.com", password="secret123", name="X")
    )
    with pytest.raises(HTTPException) as exc:
        auth_service_sql.authenticate_user(
            LoginRequest(email="bad@b.com", password="WRONG")
        )
    assert exc.value.status_code == 401


def test_authenticate_user_email_inexistente_lanza_401(auth_service_sql):
    with pytest.raises(HTTPException) as exc:
        auth_service_sql.authenticate_user(
            LoginRequest(email="nope@b.com", password="anything")
        )
    assert exc.value.status_code == 401


def test_get_user_from_token_devuelve_user_sin_password_hash(auth_service_sql):
    user, token, _ = auth_service_sql.register_user(
        RegisterRequest(email="me@b.com", password="secret123", name="Me")
    )
    fetched = auth_service_sql.get_user_from_token(token)
    assert fetched["id"] == user["id"]
    assert "password_hash" not in fetched


def test_get_user_from_token_con_sub_inexistente_lanza_401(auth_service_sql):
    settings = get_settings()
    token = jwt.encode(
        {
            "sub": "99999",
            "iat": int(time.time()),
            "exp": int(time.time()) + 3600,
            "type": "access",
        },
        settings.JWT_SECRET,
        algorithm=settings.JWT_ALGORITHM,
    )
    with pytest.raises(HTTPException) as exc:
        auth_service_sql.get_user_from_token(token)
    assert exc.value.status_code == 401
