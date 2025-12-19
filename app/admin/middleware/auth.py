from fastapi import HTTPException, Depends, status, Request
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
import secrets

from ...database.database import get_db_context
from ...database.models import AdminUser
from ...config.settings import settings
from ...services.auth_service import AuthService

security = HTTPBasic()

def require_admin_auth(credentials: HTTPBasicCredentials = Depends(security)) -> dict:
    """Требует аутентификации администратора"""
    # Проверяем основного владельца
    correct_username = secrets.compare_digest(credentials.username, settings.ADMIN_USERNAME)
    correct_password = secrets.compare_digest(credentials.password, settings.ADMIN_PASSWORD)

    if correct_username and correct_password:
        # Возвращаем владельца из настроек
        return {
            "id": 1,
            "username": settings.ADMIN_USERNAME,
            "password": credentials.password,  # Добавляем пароль для JavaScript
            "email": "admin@example.com",
            "first_name": "Администратор",
            "last_name": "",
            "role": "owner",
            "is_active": True
        }

    # Проверяем пользователей из БД с использованием context manager
    with get_db_context() as db:
        from sqlalchemy import select
        stmt = select(AdminUser).where(
            AdminUser.username == credentials.username,
            AdminUser.is_active == True
        )
        user = db.execute(stmt).scalar_one_or_none()

        if user and AuthService.verify_password(credentials.password, user.password_hash):
            # Извлекаем все атрибуты пока сессия активна
            user_data = {
                "id": user.id,
                "username": user.username,
                "password": credentials.password,
                "email": user.email,
                "first_name": user.first_name,
                "last_name": user.last_name,
                "role": user.role,
                "is_active": user.is_active
            }
            return user_data

    # Если ни один способ не сработал
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Неверные учетные данные",
        headers={"WWW-Authenticate": "Basic"},
    )

def get_current_admin_user(credentials: HTTPBasicCredentials = Depends(security)) -> dict:
    """Получить текущего администратора (алиас для require_admin_auth)"""
    return require_admin_auth(credentials)

def authenticate(credentials: HTTPBasicCredentials = Depends(security)) -> str:
    """Аутентификация пользователя, возвращает имя пользователя"""
    user_data = require_admin_auth(credentials)
    return user_data["username"]
