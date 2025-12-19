from fastapi import FastAPI, HTTPException, Depends, Request, Form, APIRouter, File, UploadFile
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from datetime import datetime, timedelta
from sqlalchemy import func
import secrets
from typing import Optional, Dict, Any, List
import json
import os
import calendar

from ..config.settings import settings
from ..config.logging import get_logger
from ..database.database import get_db_context
from ..database.models import User, Project, ConsultantSession, Portfolio, Settings as DBSettings, AdminUser, ProjectFile, FinanceTransaction
from ..services.analytics_service import analytics_service, get_dashboard_data
from ..services.auth_service import AuthService
from .middleware.roles import RoleMiddleware
from .navigation import get_navigation_items

def get_image_url(image_path: str, request: Request = None) -> str:
    """Формирует правильный URL для изображения"""
    if not image_path:
        return None
    
    # Убираем префикс uploads/portfolio/ если он есть
    clean_path = image_path.replace("uploads/portfolio/", "").replace("uploads/", "")
    
    # Формируем полный URL
    if request:
        # Используем хост из запроса
        base_url = f"{request.url.scheme}://{request.url.netloc}"
    else:
        # Fallback для случаев без request (например API для бота)
        base_url = f"http://localhost:{settings.ADMIN_PORT}"
    
    return f"{base_url}/uploads/portfolio/{clean_path}"

# Импорт роутера портфолио
try:
    from .routers.portfolio import router as portfolio_router
    print("Роутер портфолио подключен")
except ImportError as e:
    print(f"Ошибка импорта роутера портфолио: {e}")
    portfolio_router = None

# Импорт роутера проектов
try:
    from .routers.projects import router as projects_router
    print("Используется основной роутер проектов")
except ImportError as e:
    print(f"Ошибка импорта роутера проектов: {e}")
    projects_router = None

# Импорт роутера пользователей
try:
    from .routers.users import router as users_router
    print("Роутер пользователей подключен")
except ImportError as e:
    print(f"Ошибка импорта роутера пользователей: {e}")
    users_router = None

# Импорт роутера файлов
try:
    from .routers.files import router as files_router
    print("Роутер файлов подключен")
except ImportError as e:
    print(f"Ошибка импорта роутера файлов: {e}")
    files_router = None

# Импорт роутера задач
try:
    from .routers.tasks import router as tasks_router
    print("Роутер задач подключен")
except ImportError as e:
    print(f"Ошибка импорта роутера задач: {e}")
    tasks_router = None

# Импорт роутера статусов проектов
try:
    from .routers.project_statuses import router as project_statuses_router
    print("Роутер статусов проектов подключен")
except ImportError as e:
    print(f"Ошибка импорта роутера статусов проектов: {e}")
    project_statuses_router = None

# Импорт роутера финансов
try:
    from .routers.finance import router as finance_router
    print("Роутер финансов подключен")
except ImportError as e:
    print(f"Ошибка импорта роутера финансов: {e}")
    finance_router = None

# Импорт роутера настроек
try:
    from .routers.settings import router as settings_router
    print("Роутер настроек подключен")
except ImportError as e:
    print(f"Ошибка импорта роутера настроек: {e}")
    settings_router = None

# Импорт роутера исполнителей
try:
    from .routers.contractors import router as contractors_router
    print("Роутер исполнителей подключен")
except ImportError as e:
    print(f"Ошибка импорта роутера исполнителей: {e}")
    contractors_router = None

# Импорт роутера сервисов
try:
    from .routers.services import router as services_router
    print("Роутер сервисов подключен")
except ImportError as e:
    print(f"Ошибка импорта роутера сервисов: {e}")
    services_router = None

# Импорт роутера правок
try:
    from .routers.revisions import router as revisions_router
    print("Роутер правок подключен")
except ImportError as e:
    print(f"Ошибка импорта роутера правок: {e}")
    revisions_router = None

# Импорт роутера транзакций
try:
    from .routers.transactions import router as transactions_router
    print("Роутер транзакций подключен")
except ImportError as e:
    print(f"Ошибка импорта роутера транзакций: {e}")
    transactions_router = None

# Импорт роутера автоматизации
try:
    from .routers.automation import router as automation_router
    print("Роутер автоматизации подключен")
except ImportError as e:
    print(f"Ошибка импорта роутера автоматизации: {e}")
    automation_router = None

# Импорт роутера отчетов
try:
    from .routers.reports import router as reports_router
    print("Роутер отчетов подключен")
except ImportError as e:
    print(f"Ошибка импорта роутера отчетов: {e}")
    reports_router = None

# Импорт роутера хостинга
try:
    from .routers.hosting import router as hosting_router
    print("Роутер хостинга подключен")
except ImportError as e:
    print(f"Ошибка импорта роутера хостинга: {e}")
    hosting_router = None

# Импорт роутера аутентификации
try:
    from .routers.auth import router as auth_router
    print("Роутер аутентификации подключен")
except ImportError as e:
    print(f"Ошибка импорта роутера аутентификации: {e}")
    auth_router = None

# Импорт роутера чатов проектов
try:
    from .routers.project_chats import router as project_chats_router
    print("Роутер чатов проектов подключен")
except ImportError as e:
    print(f"Ошибка импорта роутера чатов проектов: {e}")
    project_chats_router = None

# Импорт роутера ресурсов проектов (документы, платежи)
try:
    from .routers.project_resources import router as project_resources_router
    print("Роутер ресурсов проектов подключен")
except ImportError as e:
    print(f"Ошибка импорта роутера ресурсов проектов: {e}")
    project_resources_router = None

# Импорт роутера регламентов тимлида
try:
    from .routers.timlead_regulations import router as timlead_regulations_router
    print("Роутер регламентов тимлида подключен")
except ImportError as e:
    print(f"Ошибка импорта роутера регламентов тимлида: {e}")
    timlead_regulations_router = None

logger = get_logger(__name__)

# Создаем роутер для админки
admin_router = APIRouter()

# Подключаем роутер аутентификации (должен быть первым, без префикса для /login)
if auth_router:
    admin_router.include_router(auth_router, prefix="/api/auth", tags=["auth"])

# Подключаем роутер портфолио
if portfolio_router:
    admin_router.include_router(portfolio_router)

# Подключаем роутер проектов
if projects_router:
    admin_router.include_router(projects_router, prefix="/api/projects")
    # Backwards compatibility для React
    admin_router.include_router(projects_router, prefix="/projects")

# Подключаем роутер чатов проектов
if project_chats_router:
    admin_router.include_router(project_chats_router, prefix="/api/projects")

# Подключаем роутер ресурсов проектов
if project_resources_router:
    admin_router.include_router(project_resources_router, prefix="/api/projects")

# Подключаем роутер пользователей
if users_router:
    admin_router.include_router(users_router, prefix="/api/users")

# Подключаем роутер файлов
if files_router:
    admin_router.include_router(files_router, prefix="/api/files")
    # Backwards compatibility для React
    admin_router.include_router(files_router, prefix="/files")

# Подключаем роутер задач
# ВАЖНО: Подключаем только для API, HTML отдает React
if tasks_router:
    admin_router.include_router(tasks_router, prefix="/api/tasks")

# Подключаем роутер статусов проектов
if project_statuses_router:
    admin_router.include_router(project_statuses_router, prefix="/api/project-statuses")

# Подключаем роутер финансов
if finance_router:
    # Исправлено: был /finance, теперь /api/finance для React
    admin_router.include_router(finance_router, prefix="/api/finance")
    # Backwards compatibility для Dashboard component
    admin_router.include_router(finance_router, prefix="/finance")

# Подключаем роутер настроек
if settings_router:
    admin_router.include_router(settings_router)

# Подключаем роутер исполнителей
if contractors_router:
    admin_router.include_router(contractors_router, prefix="/api/contractors")

# Подключаем роутер сервисов
if services_router:
    admin_router.include_router(services_router)

# Подключаем роутер правок
if revisions_router:
    admin_router.include_router(revisions_router, prefix="")

# Подключаем роутер транзакций
if transactions_router:
    admin_router.include_router(transactions_router, prefix="/api/transactions")

if automation_router:
    # Подключаем роутер для страниц автоматизации
    admin_router.include_router(automation_router)

if reports_router:
    # Подключаем роутер для страниц отчетов
    admin_router.include_router(reports_router)

if hosting_router:
    # Подключаем роутер для управления хостингом
    admin_router.include_router(hosting_router)

if timlead_regulations_router:
    # Подключаем роутер регламентов тимлида
    admin_router.include_router(timlead_regulations_router, prefix="/api")

# Импорт роутера аналитики
try:
    from .routers.analytics import router as analytics_router
    print("Роутер аналитики подключен")
except ImportError as e:
    print(f"Ошибка импорта роутера аналитики: {e}")
    analytics_router = None

# Подключаем роутер аналитики (только API, страница уже есть в основном роутере)
if analytics_router:
    admin_router.include_router(analytics_router)

# Импорт роутера клиентов CRM
try:
    from .routers.clients import router as clients_router
    print("Роутер клиентов подключен")
except ImportError as e:
    print(f"Ошибка импорта роутера клиентов: {e}")
    clients_router = None

# Подключаем роутер клиентов
if clients_router:
    admin_router.include_router(clients_router, prefix="/api/clients")  # API endpoints
    admin_router.include_router(clients_router, prefix="/clients")      # HTML pages

# Импорт роутера лидов
try:
    from .routers.leads import router as leads_router
    print("Роутер лидов подключен")
except ImportError as e:
    print(f"Ошибка импорта роутера лидов: {e}")
    # Fallback на простую версию
    try:
        from .routers.leads_simple import router as leads_router
        print("Роутер лидов (простая версия) подключен")
    except ImportError as e2:
        print(f"Ошибка импорта простого роутера лидов: {e2}")
        leads_router = None

# Подключаем роутер лидов
if leads_router:
    admin_router.include_router(leads_router)

# Импорт роутера сделок
try:
    from .routers.deals import router as deals_router
    print("Роутер сделок подключен")
except ImportError as e:
    print(f"Ошибка импорта роутера сделок: {e}")
    deals_router = None

# Подключаем роутер сделок
if deals_router:
    admin_router.include_router(deals_router)

# Импорт роутера документов (используем упрощенную версию без pdfkit)
try:
    from .routers.documents_new import router as documents_router
    print("Роутер документов подключен (упрощенная версия)")
except ImportError as e:
    print(f"Ошибка импорта роутера документов: {e}")
    documents_router = None

# Подключаем роутер документов
if documents_router:
    admin_router.include_router(documents_router)

# Импорт роутера транскрибаций
try:
    from .routers.transcriptions import router as transcriptions_router
    print("Роутер транскрибаций подключен")
except ImportError as e:
    print(f"Ошибка импорта роутера транскрибаций: {e}")
    transcriptions_router = None

# Подключаем роутер транскрибаций
if transcriptions_router:
    admin_router.include_router(transcriptions_router)

# Импорт роутера AI-звонков
try:
    from .routers.ai_calls import router as ai_calls_router
    print("Роутер AI-звонков подключен")
except ImportError as e:
    print(f"Ошибка импорта роутера AI-звонков: {e}")
    ai_calls_router = None

# Подключаем роутер AI-звонков
if ai_calls_router:
    admin_router.include_router(ai_calls_router)

# Импорт роутера Авито
try:
    from .routers.avito import router as avito_router
    print("Роутер Авито подключен")
except ImportError as e:
    print(f"Ошибка импорта роутера Авито: {e}")
    avito_router = None

# Импорт OAuth роутера Авито
try:
    from .routers.avito_oauth import router as avito_oauth_router
    print("OAuth роутер Авито подключен")
except ImportError as e:
    print(f"Ошибка импорта OAuth роутера Авито: {e}")
    avito_oauth_router = None

# Подключаем роутер Авито
if avito_router:
    admin_router.include_router(avito_router, prefix="/avito")

# Подключаем OAuth роутер Авито
if avito_oauth_router:
    admin_router.include_router(avito_oauth_router)

# Подключаем роутер управления правами
try:
    from .routers.permissions_management import router as permissions_router
    admin_router.include_router(permissions_router, prefix="/permissions")
    print("Роутер управления правами подключен")
except ImportError as e:
    print(f"⚠️ Не удалось подключить роутер управления правами: {e}")
    permissions_router = None

# Подключаем роутер детальных UI прав
# (будет подключен к app напрямую позже, после создания объекта app)
try:
    from .routers.ui_permissions import router as ui_permissions_router
    # Не подключаем к admin_router, так как этот роутер должен быть доступен без префикса /admin
    print("Роутер детальных UI прав импортирован")
except ImportError as e:
    print(f"⚠️ Не удалось подключить роутер детальных UI прав: {e}")
    ui_permissions_router = None

# Подключаем роутер уведомлений
try:
    from .routers.notifications import router as notifications_router
    admin_router.include_router(notifications_router)
    print("Роутер уведомлений подключен")
except ImportError as e:
    print(f"⚠️ Не удалось подключить роутер уведомлений: {e}")
    notifications_router = None

# Подключаем роутер отслеживания (Wialon)
try:
    from .routers.tracking import router as tracking_router
    admin_router.include_router(tracking_router)
    print("Роутер отслеживания транспорта подключен")
except ImportError as e:
    print(f"⚠️ Не удалось подключить роутер отслеживания: {e}")
    tracking_router = None

# Подключаем роутер чатов
try:
    from .routers.chats import router as chats_router
    admin_router.include_router(chats_router)
    print("Роутер чатов подключен")
except ImportError as e:
    print(f"⚠️ Не удалось подключить роутер чатов: {e}")
    chats_router = None

# Базовая аутентификация
security = HTTPBasic()

def get_user_role(username: str) -> str:
    """Определение роли пользователя"""
    if username == settings.ADMIN_USERNAME:
        return "owner"
    else:
        # Проверяем в базе данных
        with get_db_context() as db:
            admin_user = db.query(AdminUser).filter(AdminUser.username == username).first()
            if admin_user:
                return admin_user.role
        return "executor"

def get_current_user(username: str):
    """Получение текущего пользователя"""
    if username == settings.ADMIN_USERNAME:
        return {"username": username, "role": "owner", "id": 1}
    else:
        with get_db_context() as db:
            admin_user = db.query(AdminUser).filter(AdminUser.username == username).first()
            if admin_user:
                return {
                    "username": admin_user.username,
                    "role": admin_user.role,
                    "id": admin_user.id,
                    "first_name": admin_user.first_name,
                    "last_name": admin_user.last_name,
                    "email": admin_user.email
                }
        return None

def authenticate(credentials: HTTPBasicCredentials = Depends(security)):
    """Проверка аутентификации с поддержкой обеих систем"""
    logger.info(f"Попытка входа пользователя: {credentials.username}")
    logger.info(f"Ожидаемый admin username: {settings.ADMIN_USERNAME}")
    
    # Дополнительная проверка с дефолтными значениями
    if credentials.username == "admin" and credentials.password == "qwerty123":
        logger.info(f"Вход по дефолтным учетным данным")
        return credentials.username
    
    # Проверяем основного владельца
    correct_username = secrets.compare_digest(credentials.username, settings.ADMIN_USERNAME)
    correct_password = secrets.compare_digest(credentials.password, settings.ADMIN_PASSWORD)
    
    logger.info(f"Username совпадает: {correct_username}, Password совпадает: {correct_password}")
    
    if correct_username and correct_password:
        logger.info(f"Успешный вход владельца: {credentials.username}")
        return credentials.username
    
    # Проверяем исполнителей в базе данных
    try:
        admin_user = AuthService.authenticate_user(credentials.username, credentials.password)
        if admin_user:
            logger.info(f"Успешный вход исполнителя: {credentials.username}")
            return credentials.username
    except Exception as e:
        logger.error(f"Ошибка при проверке исполнителя: {e}")
    
    logger.warning(f"Неудачная попытка входа: {credentials.username}")
    # Если ни один способ не сработал
    raise HTTPException(
        status_code=401,
        detail="Неверные учетные данные",
        headers={"WWW-Authenticate": "Basic"},
    )

@admin_router.post("/api/portfolio")
async def create_portfolio_item(
    title: str = Form(...),
    description: str = Form(...),
    category: str = Form(...),
    complexity: str = Form("medium"),
    technologies: str = Form(""),
    cost: int = Form(0),
    duration: int = Form(0),
    featured: bool = Form(False),
    active: bool = Form(True),
    show_cost: bool = Form(False),
    order: int = Form(0),
    main_image: UploadFile = File(None),
    username: str = Depends(authenticate)
):
    """API для создания элемента портфолио"""
    try:
        with get_db_context() as db:
            # Создаем новый элемент портфолио
            new_portfolio = Portfolio(
                title=title,
                description=description,
                category=category,
                complexity_level=1,  # Базовая сложность
                development_time=duration if duration > 0 else None,
                cost_range=f"{cost}-{cost}" if cost > 0 else None,
                is_featured=featured,
                sort_order=order,
                views_count=0,
                created_at=datetime.utcnow()
            )
            
            # Обрабатываем технологии
            if technologies:
                tech_list = [tech.strip() for tech in technologies.split(',')]
                new_portfolio.technologies = tech_list
            
            # Сохраняем изображение если есть
            image_paths = []
            if main_image and main_image.filename:
                # Создаем директорию если не существует
                upload_dir = "uploads/portfolio"
                os.makedirs(upload_dir, exist_ok=True)
                
                # Сохраняем файл
                file_path = f"{upload_dir}/{datetime.now().strftime('%Y%m%d_%H%M%S')}_{main_image.filename}"
                with open(file_path, "wb") as buffer:
                    content = await main_image.read()
                    buffer.write(content)
                
                image_paths.append(file_path)
            
            new_portfolio.image_paths = image_paths
            
            db.add(new_portfolio)
            db.commit()
            
            logger.info(f"Создан новый элемент портфолио: {title}")
            
            return {"success": True, "message": "Проект добавлен в портфолио", "id": new_portfolio.id}
        
    except Exception as e:
        logger.error(f"Ошибка в create_portfolio_item: {e}")
        return {"success": False, "error": str(e)}

@admin_router.delete("/api/portfolio/{item_id}")
async def delete_portfolio_item(item_id: int, username: str = Depends(authenticate)):
    """API для удаления элемента портфолио"""
    try:
        with get_db_context() as db:
            portfolio_item = db.query(Portfolio).filter(Portfolio.id == item_id).first()
            
            if not portfolio_item:
                return {"success": False, "error": "Элемент портфолио не найден"}
            
            # Удаляем файлы изображений
            if portfolio_item.image_paths:
                for image_path in portfolio_item.image_paths:
                    try:
                        if os.path.exists(image_path):
                            os.remove(image_path)
                    except Exception as e:
                        logger.warning(f"Не удалось удалить файл {image_path}: {e}")
            
            # Удаляем элемент из базы
            db.delete(portfolio_item)
            db.commit()
            
            logger.info(f"Удален элемент портфолио: {portfolio_item.title}")
            
            return {"success": True, "message": "Элемент портфолио удален"}
        
    except Exception as e:
        logger.error(f"Ошибка в delete_portfolio_item: {e}")
        return {"success": False, "error": str(e)}

@admin_router.get("/api/portfolio/{item_id}")
async def get_portfolio_item(item_id: int, username: str = Depends(authenticate)):
    """API для получения элемента портфолио для редактирования"""
    try:
        with get_db_context() as db:
            portfolio_item = db.query(Portfolio).filter(Portfolio.id == item_id).first()
            
            if not portfolio_item:
                return {"success": False, "error": "Элемент портфолио не найден"}
            
            project_dict = portfolio_item.to_dict()
            
            # Формируем правильные URL для изображений
            if portfolio_item.main_image:
                project_dict['main_image'] = f"/uploads/portfolio/{portfolio_item.main_image}"
            
            if project_dict.get('image_paths'):
                project_dict['image_paths'] = [f"/uploads/portfolio/{img}" for img in project_dict['image_paths']]
            
            return {
                "success": True,
                "project": project_dict
            }
        
    except Exception as e:
        logger.error(f"Ошибка в get_portfolio_item: {e}")
        return {"success": False, "error": str(e)}

@admin_router.put("/api/portfolio/{item_id}")
async def update_portfolio_item(
    item_id: int,
    title: str = Form(...),
    description: str = Form(...),
    category: str = Form(...),
    complexity: str = Form("medium"),
    technologies: str = Form(""),
    cost: int = Form(0),
    duration: int = Form(0),
    featured: bool = Form(False),
    active: bool = Form(True),
    show_cost: bool = Form(False),
    order: int = Form(0),
    main_image: UploadFile = File(None),
    username: str = Depends(authenticate)
):
    """API для обновления элемента портфолио"""
    try:
        with get_db_context() as db:
            portfolio_item = db.query(Portfolio).filter(Portfolio.id == item_id).first()
            
            if not portfolio_item:
                return {"success": False, "error": "Элемент портфолио не найден"}
            
            # Обновляем поля
            portfolio_item.title = title
            portfolio_item.description = description
            portfolio_item.category = category
            portfolio_item.development_time = duration if duration > 0 else None
            portfolio_item.cost_range = f"{cost}-{cost}" if cost > 0 else None
            portfolio_item.is_featured = featured
            portfolio_item.sort_order = order
            
            # Обрабатываем технологии
            if technologies:
                tech_list = [tech.strip() for tech in technologies.split(',')]
                portfolio_item.technologies = tech_list
            
            # Обрабатываем новое изображение
            if main_image and main_image.filename:
                # Удаляем старые изображения
                if portfolio_item.image_paths:
                    for old_path in portfolio_item.image_paths:
                        try:
                            if os.path.exists(old_path):
                                os.remove(old_path)
                        except Exception as e:
                            logger.warning(f"Не удалось удалить старый файл {old_path}: {e}")
                
                # Сохраняем новое изображение
                upload_dir = "uploads/portfolio"
                os.makedirs(upload_dir, exist_ok=True)
                
                file_path = f"{upload_dir}/{datetime.now().strftime('%Y%m%d_%H%M%S')}_{main_image.filename}"
                with open(file_path, "wb") as buffer:
                    content = await main_image.read()
                    buffer.write(content)
                
                portfolio_item.image_paths = [file_path]
            
            db.commit()
            
            logger.info(f"Обновлен элемент портфолио: {title}")
            
            return {"success": True, "message": "Элемент портфолио обновлен"}
        
    except Exception as e:
        logger.error(f"Ошибка в update_portfolio_item: {e}")
        return {"success": False, "error": str(e)}

# API endpoints для управления проектами
@admin_router.get("/api/stats")
async def api_stats(username: str = Depends(authenticate)):
    """API для получения статистики"""
    try:
        stats = get_dashboard_data(7)
        return {"success": True, "data": stats}
    except Exception as e:
        logger.error(f"Ошибка в api_stats: {e}")
        return {"success": False, "error": str(e)}

@admin_router.get("/api/dashboard/stats")
async def api_dashboard_stats(username: str = Depends(authenticate)):
    """API для получения статистики дашборда - новый формат для React"""
    try:
        from ..database.models import Project, Task, User, Transaction, AdminUser
        from datetime import datetime, timedelta

        with get_db_context() as db:
            now = datetime.utcnow()
            month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

            # Получаем информацию о пользователе из admin_users таблицы
            user = db.query(AdminUser).filter(AdminUser.username == username).first()
            user_role = user.role if user and hasattr(user, 'role') else 'owner'

            # Проекты - получаем все для финансовых расчетов
            all_projects = db.query(Project).all()
            recent_projects = db.query(Project).order_by(Project.created_at.desc()).limit(10).all()
            projects_list = []
            for proj in recent_projects:
                projects_list.append({
                    "id": proj.id,
                    "title": proj.title or "Без названия",
                    "client_name": proj.client_name if hasattr(proj, 'client_name') else None,
                    "status": proj.status or "new",
                    "deadline": proj.deadline.isoformat() if proj.deadline else None,
                    "progress": int(proj.progress) if hasattr(proj, 'progress') and proj.progress else 0,
                })

            # Финансовые метрики из проектов
            active_statuses = ['new', 'in_progress', 'review', 'accepted', 'testing']
            active_projects = [p for p in all_projects if p.status in active_statuses]

            # Общая сумма активных проектов
            total_active_projects_sum = sum(p.estimated_cost or 0 for p in active_projects)

            # Сумма полученных от клиентов (по всем проектам)
            total_received_from_clients = sum(p.client_paid_total or 0 for p in all_projects)

            # Сумма ожидаемых платежей (разница между оценкой и полученным по активным проектам)
            total_pending_payments = sum(
                (p.estimated_cost or 0) - (p.client_paid_total or 0)
                for p in active_projects
                if (p.estimated_cost or 0) > (p.client_paid_total or 0)
            )

            # Сумма выплат исполнителям
            total_paid_to_executors = sum(p.executor_paid_total or 0 for p in all_projects)

            # Чистая прибыль (полученное от клиентов минус выплаченное исполнителям)
            net_profit = total_received_from_clients - total_paid_to_executors

            # Финансы за месяц из Transaction
            try:
                month_income = db.query(func.sum(Transaction.amount)).filter(
                    Transaction.transaction_type == 'income',
                    Transaction.status == 'completed',
                    Transaction.transaction_date >= month_start
                ).scalar() or 0

                month_expenses = db.query(func.sum(Transaction.amount)).filter(
                    Transaction.transaction_type == 'expense',
                    Transaction.status == 'completed',
                    Transaction.transaction_date >= month_start
                ).scalar() or 0

                month_revenue = month_income - month_expenses
            except Exception as e:
                logger.warning(f"Ошибка подсчета транзакций за месяц: {e}")
                month_revenue = 0

            # Задачи - разбиваем на категории
            # Для исполнителей показываем только их задачи
            if user_role == 'executor':
                all_tasks = db.query(Task).filter(Task.assigned_to_id == user.id).all()
            else:
                all_tasks = db.query(Task).all()

            overdue_tasks = []
            upcoming_tasks = []
            new_tasks = []

            for task in all_tasks:
                task_data = {
                    "id": task.id,
                    "title": task.title or "Без названия",
                    "deadline": task.deadline.isoformat() if task.deadline else None,
                    "priority": task.priority or "medium",
                    "status": task.status or "pending",
                    "executor_name": task.executor_name if hasattr(task, 'executor_name') else None,
                }

                # Просроченные
                if task.deadline and task.deadline < now and task.status != "completed":
                    overdue_tasks.append(task_data)
                # Предстоящие (в течение недели)
                elif task.deadline and task.deadline > now and task.deadline < now + timedelta(days=7):
                    upcoming_tasks.append(task_data)
                # Новые (созданы за последние 3 дня)
                elif task.created_at and task.created_at > now - timedelta(days=3):
                    task_data["created_at"] = task.created_at.isoformat()
                    new_tasks.append(task_data)

            # Клиенты - подсчитываем уникальных из проектов
            unique_users = set(p.user_id for p in all_projects if p.user_id)
            active_clients = len(unique_users)
            new_leads_week = 0

            # Формируем ответ в новом формате
            response_data = {
                "user": {
                    "id": user.id if user else 1,
                    "username": username,
                    "role": user_role,
                    "full_name": user.full_name if user and hasattr(user, 'full_name') else username,
                },
                "greeting": {
                    "title": f"Привет, {username}!",
                    "subtitle": f"У вас {len(overdue_tasks)} просроченных задач"
                },
                "summary": {
                    "active_projects": len(active_projects),
                    "active_clients": active_clients,
                    "month_revenue": round(month_revenue, 2),
                    "overdue_tasks": len(overdue_tasks),
                    "tasks_today": len([t for t in upcoming_tasks if t.get('deadline') and datetime.fromisoformat(t['deadline']).date() == now.date()]),
                    "total_active_projects_sum": round(total_active_projects_sum, 2),
                    "net_profit": round(net_profit, 2),
                    "total_projects": len(all_projects),
                    "total_tasks": len(all_tasks),
                },
                "projects": projects_list,
                "tasks": {
                    "overdue": overdue_tasks[:10],
                    "upcoming": upcoming_tasks[:10],
                    "new": new_tasks[:10],
                },
                "clients": {
                    "active_count": active_clients,
                    "new_leads_week": new_leads_week,
                    "recent": []
                },
                "finance": {
                    "month_revenue": round(month_revenue, 2),
                    "paid": round(total_received_from_clients, 2),
                    "pending": round(total_pending_payments, 2),
                    "overdue": 0,
                    "total_active_projects_sum": round(total_active_projects_sum, 2),
                    "net_profit": round(net_profit, 2),
                    "total_paid_to_executors": round(total_paid_to_executors, 2),
                },
                "alerts": [],
                "documents": [],
                "activity": [],
                "quick_actions": [
                    {"id": "new_task", "label": "Создать задачу", "link": "/tasks", "icon": "tasks"},
                    {"id": "new_project", "label": "Новый проект", "link": "/projects", "icon": "projects"},
                ],
                "charts": {
                    "tasks_by_status": {
                        "pending": len([t for t in all_tasks if t.status == 'pending']),
                        "in_progress": len([t for t in all_tasks if t.status == 'in_progress']),
                        "completed": len([t for t in all_tasks if t.status == 'completed']),
                    },
                    "projects_distribution": {
                        "new": len([p for p in all_projects if p.status == 'new']),
                        "in_progress": len([p for p in all_projects if p.status == 'in_progress']),
                        "completed": len([p for p in all_projects if p.status == 'completed']),
                    }
                }
            }

            return {"success": True, "data": response_data}
    except Exception as e:
        logger.error(f"Ошибка в api_dashboard_stats: {e}", exc_info=True)
        return {"success": False, "error": str(e)}

@admin_router.get("/api/dashboard/charts/daily")
async def api_dashboard_daily_charts(
    days: int = 30,
    username: str = Depends(authenticate)
):
    """API для получения данных графиков по дням"""
    try:
        from ..database.models import Project, Transaction
        from datetime import datetime, timedelta
        from collections import defaultdict

        with get_db_context() as db:
            now = datetime.utcnow()
            start_date = now - timedelta(days=days)

            # График проектов по дням
            projects = db.query(Project).filter(
                Project.created_at >= start_date
            ).all()

            # Группируем проекты по дням
            projects_by_day = defaultdict(lambda: {"count": 0, "sum": 0})
            for project in projects:
                day_key = project.created_at.date().isoformat() if project.created_at else None
                if day_key:
                    projects_by_day[day_key]["count"] += 1
                    projects_by_day[day_key]["sum"] += project.estimated_cost or 0

            # График платежей по дням (из Transaction)
            try:
                income_transactions = db.query(Transaction).filter(
                    Transaction.transaction_type == 'income',
                    Transaction.status == 'completed',
                    Transaction.transaction_date >= start_date
                ).all()

                payments_by_day = defaultdict(float)
                for trans in income_transactions:
                    day_key = trans.transaction_date.date().isoformat() if trans.transaction_date else None
                    if day_key:
                        payments_by_day[day_key] += trans.amount or 0
            except Exception as e:
                logger.warning(f"Ошибка получения транзакций для графика: {e}")
                payments_by_day = {}

            # Формируем массив дат для последних N дней
            daily_data = []
            for i in range(days):
                current_date = (now - timedelta(days=days - 1 - i)).date()
                day_key = current_date.isoformat()

                daily_data.append({
                    "date": day_key,
                    "projects_count": projects_by_day[day_key]["count"],
                    "projects_sum": round(projects_by_day[day_key]["sum"], 2),
                    "payments_sum": round(payments_by_day.get(day_key, 0), 2),
                })

            return {
                "success": True,
                "data": {
                    "daily": daily_data,
                    "period": {
                        "days": days,
                        "start_date": start_date.date().isoformat(),
                        "end_date": now.date().isoformat()
                    }
                }
            }
    except Exception as e:
        logger.error(f"Ошибка в api_dashboard_daily_charts: {e}", exc_info=True)
        return {"success": False, "error": str(e)}

@admin_router.get("/api/dashboard/crm")
async def api_dashboard_crm(username: str = Depends(authenticate)):
    """API для получения данных CRM дашборда"""
    try:
        with get_db_context() as db:
            from ..services.reports_service import ReportsService
            from ..database.crm_models import Client, Lead, Deal, DealStatus, LeadStatus
            
            reports_service = ReportsService(db)
            
            # Получаем основные метрики
            now = datetime.utcnow()
            month_start = now.replace(day=1, hour=0, minute=0, second=0)
            last_month_start = (month_start - timedelta(days=1)).replace(day=1)
            
            # Клиенты
            total_clients = db.query(func.count(Client.id)).scalar()
            new_clients_month = db.query(func.count(Client.id)).filter(
                Client.created_at >= month_start
            ).scalar()
            
            # Сделки
            active_deals = db.query(func.count(Deal.id)).filter(
                Deal.status.notin_([DealStatus.COMPLETED, DealStatus.CANCELLED])
            ).scalar()
            
            deals_amount = db.query(func.sum(Deal.amount)).filter(
                Deal.status.notin_([DealStatus.COMPLETED, DealStatus.CANCELLED])
            ).scalar() or 0
            
            # Выручка
            month_revenue = db.query(func.sum(Deal.amount)).filter(
                Deal.status == DealStatus.COMPLETED,
                Deal.closed_at >= month_start
            ).scalar() or 0
            
            last_month_revenue = db.query(func.sum(Deal.amount)).filter(
                Deal.status == DealStatus.COMPLETED,
                Deal.closed_at >= last_month_start,
                Deal.closed_at < month_start
            ).scalar() or 0
            
            revenue_change = 0
            if last_month_revenue > 0:
                revenue_change = ((month_revenue - last_month_revenue) / last_month_revenue) * 100
            
            # Проекты
            active_projects = db.query(func.count(Project.id)).filter(
                Project.status == 'in_progress'
            ).scalar()
            
            completed_projects = db.query(func.count(Project.id)).filter(
                Project.status == 'completed',
                Project.actual_end_date >= month_start
            ).scalar()
            
            total_projects = db.query(func.count(Project.id)).filter(
                Project.status.in_(['in_progress', 'completed'])
            ).scalar()
            
            projects_completion = (completed_projects / total_projects * 100) if total_projects > 0 else 0
            
            # Воронка продаж
            leads_total = db.query(func.count(Lead.id)).filter(
                Lead.created_at >= month_start
            ).scalar()
            
            leads_qualified = db.query(func.count(Lead.id)).filter(
                Lead.created_at >= month_start,
                Lead.status.in_([LeadStatus.QUALIFICATION, LeadStatus.PROPOSAL_SENT, LeadStatus.NEGOTIATION, LeadStatus.WON])
            ).scalar()
            
            leads_proposals = db.query(func.count(Lead.id)).filter(
                Lead.created_at >= month_start,
                Lead.status.in_([LeadStatus.PROPOSAL_SENT, LeadStatus.NEGOTIATION, LeadStatus.WON])
            ).scalar()
            
            leads_won = db.query(func.count(Lead.id)).filter(
                Lead.created_at >= month_start,
                Lead.status == LeadStatus.WON
            ).scalar()
            
            conversion_rate = (leads_won / leads_total * 100) if leads_total > 0 else 0
            
            # График доходов
            revenue_chart = []
            for i in range(5, -1, -1):
                month_date = now - timedelta(days=30 * i)
                m_start = month_date.replace(day=1)
                m_end = (m_start + timedelta(days=32)).replace(day=1)
                
                m_revenue = db.query(func.sum(Deal.amount)).filter(
                    Deal.status == DealStatus.COMPLETED,
                    Deal.closed_at >= m_start,
                    Deal.closed_at < m_end
                ).scalar() or 0
                
                revenue_chart.append({
                    "month": calendar.month_name[m_start.month][:3],
                    "revenue": float(m_revenue)
                })
            
            # Топ клиенты
            top_clients = db.query(
                Client.name,
                func.count(Deal.id).label('deals_count'),
                func.sum(Deal.amount).label('total_revenue')
            ).join(
                Deal, Deal.client_id == Client.id
            ).filter(
                Deal.status == DealStatus.COMPLETED
            ).group_by(Client.id, Client.name).order_by(
                func.sum(Deal.amount).desc()
            ).limit(5).all()
            
            # Активные сделки
            active_deals_list = db.query(Deal).filter(
                Deal.status.notin_([DealStatus.COMPLETED, DealStatus.CANCELLED])
            ).order_by(Deal.amount.desc()).limit(5).all()
            
            # Последняя активность
            recent_activities = []
            
            # Последние сделки
            recent_deals = db.query(Deal).order_by(Deal.created_at.desc()).limit(3).all()
            for deal in recent_deals:
                recent_activities.append({
                    "type": "deal",
                    "title": f"Новая сделка: {deal.title}",
                    "amount": float(deal.amount or 0),
                    "date": deal.created_at.isoformat()
                })
            
            # Последние проекты
            recent_projects = db.query(Project).order_by(Project.created_at.desc()).limit(3).all()
            for project in recent_projects:
                recent_activities.append({
                    "type": "project",
                    "title": f"Проект: {project.title}",
                    "status": project.status,
                    "date": project.created_at.isoformat()
                })
            
            recent_activities.sort(key=lambda x: x['date'], reverse=True)
            
            # KPI менеджеров (упрощенная версия)
            managers_kpi = db.query(
                AdminUser.username.label('name'),
                func.count(func.distinct(Lead.id)).label('leads_count'),
                func.count(func.distinct(Deal.id)).label('deals_count'),
                func.sum(Deal.amount).label('revenue')
            ).outerjoin(
                Lead, Lead.responsible_manager_id == AdminUser.id
            ).outerjoin(
                Deal, Deal.responsible_manager_id == AdminUser.id
            ).filter(
                AdminUser.role.in_(['owner', 'manager'])
            ).group_by(AdminUser.id, AdminUser.username).all()
            
            return {
                "success": True,
                "metrics": {
                    "total_clients": total_clients,
                    "new_clients_month": new_clients_month,
                    "active_deals": active_deals,
                    "deals_amount": float(deals_amount),
                    "month_revenue": float(month_revenue),
                    "revenue_change": round(revenue_change, 1),
                    "active_projects": active_projects,
                    "projects_completion": round(projects_completion, 1)
                },
                "funnel": {
                    "leads": leads_total,
                    "qualified": leads_qualified,
                    "proposals": leads_proposals,
                    "won": leads_won,
                    "conversion_rate": round(conversion_rate, 1)
                },
                "revenue_chart": revenue_chart,
                "top_clients": [
                    {
                        "name": client.name,
                        "deals_count": client.deals_count,
                        "total_revenue": float(client.total_revenue or 0)
                    }
                    for client in top_clients
                ],
                "active_deals_list": [
                    {
                        "title": deal.title,
                        "status": deal.status.value,
                        "status_label": deal.status.value,
                        "amount": float(deal.amount or 0)
                    }
                    for deal in active_deals_list
                ],
                "recent_activities": recent_activities[:6],
                "managers_kpi": [
                    {
                        "name": row.name,
                        "leads_count": row.leads_count or 0,
                        "deals_count": row.deals_count or 0,
                        "conversion_rate": round((row.deals_count / row.leads_count * 100) if row.leads_count > 0 else 0, 1),
                        "revenue": float(row.revenue or 0),
                        "avg_deal_size": float(row.revenue / row.deals_count) if row.deals_count > 0 else 0,
                        "efficiency": min(100, round((row.deals_count / max(row.leads_count, 1)) * 100, 1))
                    }
                    for row in managers_kpi
                ]
            }
            
    except Exception as e:
        logger.error(f"Ошибка в api_dashboard_crm: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return {"success": False, "error": str(e)}

@admin_router.post("/api/project/{project_id}/status")
async def update_project_status(
    project_id: int,
    status: str = Form(...),
    comment: str = Form(""),
    username: str = Depends(authenticate)
):
    """API для обновления статуса проекта с уведомлением клиента"""
    try:
        with get_db_context() as db:
            project = db.query(Project).filter(Project.id == project_id).first()
            if not project:
                raise HTTPException(status_code=404, detail="Проект не найден")
            
            old_status = project.status
            project.status = status
            project.updated_at = datetime.utcnow()
            db.commit()
            
            # Получаем пользователя для отправки уведомления
            user = db.query(User).filter(User.id == project.user_id).first()
            
            if user and user.telegram_id:
                try:
                    # Отправляем уведомление через notification_service
                    from ..services.notification_service import notification_service
                    
                    # Устанавливаем бот для notification_service если не установлен
                    if not notification_service.bot:
                        from telegram import Bot
                        notification_service.set_bot(Bot(settings.BOT_TOKEN))
                    
                    # Формируем сообщение об изменении статуса
                    status_names = {
                        'new': '🆕 Новый',
                        'review': '👀 На рассмотрении', 
                        'accepted': '✅ Принят в работу',
                        'in_progress': '🔄 В работе',
                        'testing': '🧪 Тестирование',
                        'completed': '🎉 Завершен',
                        'cancelled': '❌ Отменен'
                    }
                    
                    new_status_name = status_names.get(status, status)
                    
                    notification_text = f"""
{new_status_name} <b>Обновление по вашему проекту</b>

📋 <b>Проект:</b> {project.title}

🔄 <b>Статус изменен:</b> {status_names.get(old_status, old_status)} → {new_status_name}

{comment if comment else _get_status_description(status)}

<i>Дата обновления: {datetime.now().strftime('%d.%m.%Y %H:%M')}</i>
                    """
                    
                    await notification_service.send_user_notification(
                        user.telegram_id, 
                        notification_text
                    )
                    
                    logger.info(f"Уведомление о смене статуса отправлено пользователю {user.telegram_id}")
                    
                except Exception as notify_error:
                    logger.error(f"Ошибка отправки уведомления: {notify_error}")
                    # Не прерываем выполнение если уведомление не отправилось
            
            return {
                "success": True, 
                "message": f"Статус проекта изменен на '{new_status_name}'" + 
                          (" и клиент уведомлен" if user and user.telegram_id else "")
            }
        
    except Exception as e:
        logger.error(f"Ошибка в update_project_status: {e}")
        return {"success": False, "error": str(e)}

def _get_status_description(status: str) -> str:
    """Получение описания статуса для клиента"""
    descriptions = {
        'new': 'Ваш проект зарегистрирован в системе. Мы скоро свяжемся с вами для уточнения деталей.',
        'review': 'Мы изучаем ваш проект и готовим предложение. Ожидайте звонка в ближайшее время.',
        'accepted': 'Отлично! Ваш проект принят в работу. Мы свяжемся с вами для подписания договора.',
        'in_progress': 'Разработка началась! Мы будем регулярно информировать вас о прогрессе.',
        'testing': 'Проект находится на стадии тестирования. Скоро пришлем вам демо для ознакомления.',
        'completed': '🎉 Поздравляем! Ваш проект готов. Спасибо за доверие!',
        'cancelled': 'К сожалению, проект был отменен. Если у вас есть вопросы, свяжитесь с нами.'
    }
    
    return descriptions.get(status, 'Статус проекта обновлен.')

@admin_router.post("/api/settings/update")
async def update_settings(
    key: str = Form(...),
    value: str = Form(...),
    username: str = Depends(authenticate)
):
    """API для обновления настроек"""
    try:
        with get_db_context() as db:
            setting = db.query(DBSettings).filter(DBSettings.key == key).first()
            if setting:
                setting.value = value
                setting.updated_at = datetime.utcnow()
            else:
                setting = DBSettings(
                    key=key, 
                    value=value,
                    created_at=datetime.utcnow(),
                    updated_at=datetime.utcnow()
                )
                db.add(setting)
            
            db.commit()
        
        return {"success": True, "message": "Настройка обновлена"}
        
    except Exception as e:
        logger.error(f"Ошибка в update_settings: {e}")
        return {"success": False, "error": str(e)}

@admin_router.get("/api/export/projects")
async def export_projects(username: str = Depends(authenticate)):
    """Экспорт проектов в JSON"""
    try:
        with get_db_context() as db:
            projects_raw = db.query(Project).all()
            
            # Конвертируем в словари В РАМКАХ СЕССИИ
            projects_data = []
            for p in projects_raw:
                projects_data.append(p.to_dict())
        
        return {"success": True, "data": projects_data}
        
    except Exception as e:
        logger.error(f"Ошибка в export_projects: {e}")
        return {"success": False, "error": str(e)}

@admin_router.get("/health")
async def health_check():
    """Проверка здоровья сервиса"""
    try:
        # Проверяем подключение к базе данных
        with get_db_context() as db:
            db.query(User).count()
        
        return {
            "status": "healthy",
            "timestamp": datetime.utcnow().isoformat(),
            "version": "1.0.0"
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }

# TODO: Добавить миграцию для таблицы admin_activity_logs
# @admin_router.get("/api/activity")
# async def get_activity_logs(username: str = Depends(authenticate)):
#     """Получить логи активности"""
#     try:
#         user_role = get_user_role(username)
#         current_user = get_current_user(username)
#         
#         with get_db_context() as db:
#             from app.database.models import AdminActivityLog
#             
#             # Если не владелец, показываем только его активность
#             if user_role == 'owner':
#                 logs = db.query(AdminActivityLog).order_by(
#                     AdminActivityLog.created_at.desc()
#                 ).limit(100).all()
#             else:
#                 logs = db.query(AdminActivityLog).filter(
#                     AdminActivityLog.user_id == current_user['id']
#                 ).order_by(
#                     AdminActivityLog.created_at.desc()
#                 ).limit(50).all()
#             
#             # Добавляем имена пользователей
#             activities = []
#             for log in logs:
#                 log_dict = log.to_dict()
#                 user = db.query(AdminUser).filter(AdminUser.id == log.user_id).first()
#                 if user:
#                     log_dict['user_name'] = f"{user.first_name or ''} {user.last_name or ''} (@{user.username})".strip()
#                 activities.append(log_dict)
#             
#             return {
#                 "success": True,
#                 "activities": activities
#             }
#     except Exception as e:
#         logger.error(f"Ошибка получения логов активности: {e}")
#         return {"success": False, "error": str(e)}

@admin_router.get("/api/notifications/bot-status")
async def check_bot_status(request: Request):
    """Проверка статуса бота"""
    try:
        from telegram import Bot
        
        bot = Bot(settings.BOT_TOKEN)
        bot_info = await bot.get_me()
        
        return JSONResponse({
            "success": True,
            "bot_info": {
                "username": bot_info.username,
                "first_name": bot_info.first_name,
                "id": bot_info.id
            }
        })
        
    except Exception as e:
        logger.error(f"Ошибка проверки статуса бота: {e}")
        return JSONResponse({
            "success": False,
            "message": str(e)
        }, status_code=500)


@admin_router.post("/api/notifications/test-admin")
async def test_admin_notification(request: Request):
    """Тестовое уведомление администратору"""
    try:
        data = await request.json()
        message = data.get("message", "🧪 Тестовое уведомление из админ-панели")
        
        # Отправляем уведомление в admin chat
        from telegram import Bot
        bot = Bot(settings.BOT_TOKEN)
        
        # Получаем admin chat ID из настроек
        admin_chat_id = settings.ADMIN_CHAT_ID or settings.ADMIN_USERNAME
        
        if admin_chat_id:
            await bot.send_message(chat_id=admin_chat_id, text=message)
            logger.info(f"Тестовое уведомление отправлено администратору: {message}")
            
            return JSONResponse({
                "success": True,
                "message": "Тестовое уведомление отправлено администратору"
            })
        else:
            return JSONResponse({
                "success": False,
                "message": "Не настроен admin chat ID"
            }, status_code=400)
        
    except Exception as e:
        logger.error(f"Ошибка отправки тестового уведомления: {e}")
        return JSONResponse({
            "success": False,
            "message": f"Ошибка отправки уведомления: {str(e)}"
        }, status_code=500)


@admin_router.post("/api/notifications/test-error")
async def test_error_notification(request: Request):
    """Тестовое уведомление об ошибке"""
    try:
        data = await request.json()
        error = data.get("error", "Тестовая ошибка из админ-панели")
        context = data.get("context", {})
        
        # Формируем сообщение об ошибке
        message = f"🚨 Ошибка в системе:\n\n{error}\n\nКонтекст: {json.dumps(context, ensure_ascii=False, indent=2)}"
        
        # Отправляем уведомление в admin chat
        from telegram import Bot
        bot = Bot(settings.BOT_TOKEN)
        
        admin_chat_id = settings.ADMIN_CHAT_ID or settings.ADMIN_USERNAME
        
        if admin_chat_id:
            await bot.send_message(chat_id=admin_chat_id, text=message)
            logger.info(f"Тестовое уведомление об ошибке отправлено: {error}")
            
            return JSONResponse({
                "success": True,
                "message": "Уведомление об ошибке отправлено"
            })
        else:
            return JSONResponse({
                "success": False,
                "message": "Не настроен admin chat ID"
            }, status_code=400)
        
    except Exception as e:
        logger.error(f"Ошибка отправки уведомления об ошибке: {e}")
        return JSONResponse({
            "success": False,
            "message": f"Ошибка отправки уведомления: {str(e)}"
        }, status_code=500)


@admin_router.post("/api/notifications/daily-report")
async def test_daily_report(request: Request):
    """Тестовый ежедневный отчет"""
    try:
        # Генерируем тестовый ежедневный отчет
        with get_db_context() as db:
            # Статистика проектов
            total_projects = db.query(Project).count()
            new_projects = db.query(Project).filter(Project.status == 'new').count()
            in_progress_projects = db.query(Project).filter(Project.status == 'in_progress').count()
            completed_projects = db.query(Project).filter(Project.status == 'completed').count()
            
            # Статистика пользователей
            total_users = db.query(User).count()
            
            report = f"""📊 Ежедневный отчет системы

🗂 Проекты:
• Всего проектов: {total_projects}
• Новые: {new_projects}
• В работе: {in_progress_projects}
• Завершенные: {completed_projects}

👥 Пользователи:
• Всего пользователей: {total_users}

📅 Дата отчета: {datetime.now().strftime('%d.%m.%Y %H:%M')}
🤖 Сгенерировано автоматически"""
        
        # Отправляем отчет в admin chat
        from telegram import Bot
        bot = Bot(settings.BOT_TOKEN)
        
        admin_chat_id = settings.ADMIN_CHAT_ID or settings.ADMIN_USERNAME
        
        if admin_chat_id:
            await bot.send_message(chat_id=admin_chat_id, text=report)
            logger.info("Ежедневный отчет отправлен администратору")
            
            return JSONResponse({
                "success": True,
                "message": "Ежедневный отчет отправлен"
            })
        else:
            return JSONResponse({
                "success": False,
                "message": "Не настроен admin chat ID"
            }, status_code=400)
        
    except Exception as e:
        logger.error(f"Ошибка отправки ежедневного отчета: {e}")
        return JSONResponse({
            "success": False,
            "message": f"Ошибка отправки отчета: {str(e)}"
        }, status_code=500)


@admin_router.post("/api/notifications/avito-webhook")
async def avito_notification_webhook(request: Request):
    """Webhook для получения уведомлений от Avito"""
    try:
        data = await request.json()
        
        # Логируем все входящие данные от Авито
        logger.info(f"Получено уведомление от Авито: {data}")
        
        # Парсим данные от Авито
        message_type = data.get('type', 'message')  # новое сообщение, изменение статуса и т.д.
        chat_id = data.get('chat_id')
        message = data.get('message', {})
        
        if message_type == 'message' and chat_id and message:
            # Находим всех продажников, которые должны получить уведомления
            with get_db_context() as db:
                salespeople = db.query(AdminUser).filter(
                    AdminUser.role.in_(['salesperson', 'sales']),
                    AdminUser.is_active == True
                ).all()
                
                # Отправляем уведомления всем продажникам
                from telegram import Bot
                bot = Bot(settings.BOT_TOKEN)
                
                for salesperson in salespeople:
                    if salesperson.telegram_id:
                        try:
                            notification_text = f"""📩 Новое сообщение в Авито!
                            
🔗 Чат ID: {chat_id}
👤 От: {message.get('author_name', 'Неизвестно')}
📝 Сообщение: {message.get('content', message.get('text', 'Без текста'))}
⏰ Время: {datetime.now().strftime('%H:%M:%S')}

👈 Перейти в админ-панель для ответа"""

                            await bot.send_message(
                                chat_id=salesperson.telegram_id,
                                text=notification_text
                            )
                            
                            logger.info(f"Уведомление отправлено продажнику {salesperson.username}")
                            
                        except Exception as e:
                            logger.error(f"Не удалось отправить уведомление продажнику {salesperson.username}: {e}")
                
                return JSONResponse({
                    "success": True,
                    "message": "Уведомления отправлены продажникам"
                })
        
        return JSONResponse({
            "success": True,
            "message": "Webhook обработан"
        })
        
    except Exception as e:
        logger.error(f"Ошибка обработки Авито webhook: {e}")
        return JSONResponse({
            "success": False,
            "message": f"Ошибка: {str(e)}"
        }, status_code=500)


@admin_router.post("/api/notifications/test-avito")
async def test_avito_notification(request: Request):
    """Тестовое уведомление для Авито"""
    try:
        # Симулируем получение сообщения с Авито
        test_data = {
            "type": "message",
            "chat_id": "test_chat_123",
            "message": {
                "author_name": "Тестовый клиент",
                "content": "Здравствуйте! Интересует ваша услуга. Можете рассказать подробнее?",
                "created_at": datetime.now().isoformat()
            }
        }
        
        # Прямо отправляем уведомление всем продавцам
        from app.services.notification_service import notification_service
        
        message = f"""🔔 <b>Новое сообщение с Авито</b>
        
👤 <b>От:</b> {test_data['message']['author_name']}
💬 <b>Сообщение:</b> {test_data['message']['content']}
🕐 <b>Время:</b> {test_data['message']['created_at']}
        
<i>Это тестовое уведомление от админ-панели</i>"""
        
        # Отправляем всем продавцам
        with get_db_context() as db:
            salespersons = db.query(AdminUser).filter(
                AdminUser.role == 'salesperson',
                AdminUser.telegram_id.isnot(None),
                AdminUser.is_active == True
            ).all()
            
            sent_count = 0
            for person in salespersons:
                try:
                    await notification_service.send_notification(
                        chat_id=person.telegram_id,
                        message=message
                    )
                    sent_count += 1
                except Exception as e:
                    logger.error(f"Ошибка отправки уведомления {person.username}: {e}")
        
        return JSONResponse({
            "success": True,
            "message": f"Тестовое уведомление отправлено {sent_count} продавцам"
        })
        
    except Exception as e:
        logger.error(f"Ошибка тестирования Авито уведомлений: {e}")
        return JSONResponse({
            "success": False,
            "message": f"Ошибка: {str(e)}"
        }, status_code=500)


@admin_router.put("/api/projects/{project_id}/status")
async def update_project_status_direct(
    project_id: int,
    request: Request,
    username: str = Depends(authenticate)
):
    """Прямое обновление статуса проекта с уведомлением"""
    try:
        data = await request.json()
        new_status = data.get("status")
        comment = data.get("comment", "")
        
        logger.info(f"[DIRECT] Смена статуса проекта {project_id} на '{new_status}'")
        
        # Статусы проектов
        PROJECT_STATUSES = {
            "new": "Новый",
            "review": "На рассмотрении", 
            "accepted": "Принят",
            "in_progress": "В работе",
            "testing": "Тестирование",
            "completed": "Завершен",
            "cancelled": "Отменен",
            "on_hold": "Приостановлен"
        }
        
        if not new_status or new_status not in PROJECT_STATUSES:
            raise HTTPException(status_code=400, detail="Неверный статус")
        
        with get_db_context() as db:
            project = db.query(Project).filter(Project.id == project_id).first()
            if not project:
                raise HTTPException(status_code=404, detail="Проект не найден")
            
            old_status = project.status
            project.status = new_status
            project.updated_at = datetime.utcnow()
            
            # Обновляем историю
            if not project.project_metadata:
                project.project_metadata = {}
            
            if "status_history" not in project.project_metadata:
                project.project_metadata["status_history"] = []
            
            project.project_metadata["status_history"].append({
                "from_status": old_status,
                "to_status": new_status,
                "changed_at": datetime.utcnow().isoformat(),
                "comment": comment
            })
            
            db.commit()
            db.refresh(project)
            
            # Отправляем уведомление
            user = db.query(User).filter(User.id == project.user_id).first()
            notification_sent = False
            
            if user and user.telegram_id:
                try:
                    from ..services.notification_service import NotificationService
                    from telegram import Bot
                    
                    notification_service = NotificationService()
                    notification_service.set_bot(Bot(settings.BOT_TOKEN))
                    
                    notification_sent = await notification_service.notify_project_status_changed(
                        project, old_status, user
                    )
                    
                    logger.info(f"[DIRECT] Уведомление клиенту {user.telegram_id}: {'отправлено' if notification_sent else 'ошибка'}")
                    
                except Exception as e:
                    logger.error(f"[DIRECT] Ошибка уведомления: {e}")
            
            logger.info(f"[DIRECT] Статус проекта {project_id} изменен: {old_status} -> {new_status}")
            
            return {
                "success": True,
                "message": f"Статус изменен на '{PROJECT_STATUSES[new_status]}'" + 
                          (" (уведомление отправлено)" if notification_sent else " (уведомление не отправлено)"),
                "project": {
                    "id": project.id,
                    "status": project.status,
                    "status_name": PROJECT_STATUSES[project.status],
                    "updated_at": project.updated_at.isoformat()
                }
            }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[DIRECT] Ошибка смены статуса проекта {project_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@admin_router.post("/api/projects/{project_id}/assign-executor")
async def assign_executor_to_project(
    project_id: int,
    executor_id: int = Form(...),
    username: str = Depends(authenticate)
):
    """Назначить исполнителя на проект (только владелец)"""
    try:
        user_role = get_user_role(username)
        if user_role != "owner":
            raise HTTPException(status_code=403, detail="Доступ запрещен")
        
        with get_db_context() as db:
            # Проверяем существование проекта
            project = db.query(Project).filter(Project.id == project_id).first()
            if not project:
                raise HTTPException(status_code=404, detail="Проект не найден")
            
            # Проверяем существование исполнителя
            executor = db.query(AdminUser).filter(
                AdminUser.id == executor_id,
                AdminUser.role == "executor"
            ).first()
            if not executor:
                raise HTTPException(status_code=404, detail="Исполнитель не найден")
            
            # Назначаем исполнителя
            project.assigned_executor_id = executor_id
            project.updated_at = datetime.utcnow()
            db.commit()
            
            return {
                "success": True,
                "message": f"Исполнитель {executor.username} назначен на проект {project.title}"
            }
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Ошибка назначения исполнителя: {str(e)}")
        return {"success": False, "error": str(e)}

def _get_full_analytics_data() -> Dict[str, Any]:
    """Получение полных данных аналитики из базы данных"""
    try:
        with get_db_context() as db:
            # Общая статистика проектов
            total_projects = db.query(Project).count()
            active_projects = db.query(Project).filter(
                Project.status.in_(['new', 'review', 'accepted', 'in_progress', 'testing'])
            ).count()
            completed_projects = db.query(Project).filter(Project.status == 'completed').count()
            cancelled_projects = db.query(Project).filter(Project.status == 'cancelled').count()
            
            # Финансовая статистика
            total_estimated_cost = db.query(func.sum(Project.estimated_cost)).scalar() or 0
            total_completed_cost = db.query(func.sum(Project.final_cost)).filter(
                Project.status == 'completed'
            ).scalar() or 0
            
            # Открытые заказы (не завершенные)
            open_orders_sum = db.query(func.sum(Project.estimated_cost)).filter(
                Project.status.in_(['new', 'review', 'accepted', 'in_progress', 'testing'])
            ).scalar() or 0
            
            # Платежи клиентов
            total_client_payments = db.query(func.sum(Project.client_paid_total)).scalar() or 0
            
            # Выплаты исполнителям
            total_executor_payments = db.query(func.sum(Project.executor_paid_total)).scalar() or 0
            
            # Средние показатели
            avg_project_cost = db.query(func.avg(Project.estimated_cost)).scalar() or 0
            avg_completion_time = db.query(func.avg(Project.estimated_hours)).scalar() or 0
            
            # Статистика по статусам
            status_stats = {}
            status_names = {
                'new': 'Новые',
                'review': 'На рассмотрении', 
                'accepted': 'Приняты',
                'in_progress': 'В работе',
                'testing': 'Тестирование',
                'completed': 'Завершены',
                'cancelled': 'Отменены'
            }
            
            for status_key, status_name in status_names.items():
                count = db.query(Project).filter(Project.status == status_key).count()
                sum_cost = db.query(func.sum(Project.estimated_cost)).filter(
                    Project.status == status_key
                ).scalar() or 0
                status_stats[status_key] = {
                    'name': status_name,
                    'count': count,
                    'sum': float(sum_cost)
                }
            
            # Статистика по типам проектов
            type_stats = {}
            project_types = db.query(Project.project_type, func.count(Project.id)).group_by(
                Project.project_type
            ).all()
            
            for project_type, count in project_types:
                if project_type:
                    type_stats[project_type] = count
            
            # Статистика пользователей
            total_users = db.query(User).count()
            active_users = db.query(User).filter(User.projects.any()).count()
            
            # Прибыль (разница между платежами клиентов и выплатами исполнителям)
            profit = total_client_payments - total_executor_payments
            
            # Конверсия завершенных проектов
            completion_rate = (completed_projects / total_projects * 100) if total_projects > 0 else 0
            
            # Средняя стоимость завершенного проекта
            avg_completed_cost = db.query(func.avg(Project.final_cost)).filter(
                Project.status == 'completed'
            ).scalar() or 0
            
            return {
                'total_projects': total_projects,
                'active_projects': active_projects,
                'completed_projects': completed_projects,
                'cancelled_projects': cancelled_projects,
                'total_estimated_cost': float(total_estimated_cost),
                'total_completed_cost': float(total_completed_cost),
                'open_orders_sum': float(open_orders_sum),
                'total_client_payments': float(total_client_payments),
                'total_executor_payments': float(total_executor_payments),
                'profit': float(profit),
                'avg_project_cost': float(avg_project_cost),
                'avg_completed_cost': float(avg_completed_cost),
                'avg_completion_time': float(avg_completion_time),
                'completion_rate': float(completion_rate),
                'status_stats': status_stats,
                'type_stats': type_stats,
                'total_users': total_users,
                'active_users': active_users
            }
            
    except Exception as e:
        logger.error(f"Ошибка получения данных аналитики: {e}")
        return {}


# =============================================================================
# ПУБЛИЧНЫЕ API ENDPOINTS ДЛЯ ПОРТФОЛИО (для бота)
# =============================================================================

@admin_router.get("/api/portfolio/public/categories")
async def get_public_portfolio_categories():
    """Получить список категорий портфолио для бота"""
    try:
        with get_db_context() as db:
            # Получаем уникальные категории из видимых проектов
            categories_raw = db.query(Portfolio.category).filter(
                Portfolio.is_visible == True
            ).distinct().all()
            
            # Преобразуем в список с названиями
            category_map = {
                "telegram_bots": "🤖 Telegram боты",
                "web_development": "🌐 Веб-разработка", 
                "mobile_apps": "📱 Мобильные приложения",
                "ai_integration": "🧠 AI интеграции",
                "automation": "⚙️ Автоматизация",
                "ecommerce": "🛒 E-commerce",
                "other": "🔧 Другое"
            }
            
            categories = []
            for (cat,) in categories_raw:
                if cat in category_map:
                    categories.append({
                        "key": cat,
                        "name": category_map[cat],
                        "emoji": category_map[cat].split()[0]
                    })
            
            return {
                "success": True,
                "categories": categories
            }
            
    except Exception as e:
        logger.error(f"Ошибка получения категорий портфолио: {e}")
        return {
            "success": False,
            "error": str(e),
            "categories": []
        }

@admin_router.get("/api/portfolio/public/featured")
async def get_public_featured_portfolio():
    """Получить рекомендуемые проекты портфолио для бота"""
    try:
        with get_db_context() as db:
            projects = db.query(Portfolio).filter(
                Portfolio.is_visible == True,
                Portfolio.is_featured == True
            ).order_by(Portfolio.sort_order.asc(), Portfolio.created_at.desc()).limit(10).all()
            
            projects_data = []
            for project in projects:
                project_dict = project.to_dict()
                
                # Добавляем полные URL для изображений
                if project_dict.get('main_image'):
                    project_dict['main_image'] = get_image_url(project_dict['main_image'])
                
                if project_dict.get('image_paths'):
                    project_dict['image_paths'] = [
                        get_image_url(img) for img in project_dict['image_paths']
                    ]
                
                projects_data.append(project_dict)
            
            return {
                "success": True,
                "projects": projects_data,
                "count": len(projects_data)
            }
            
    except Exception as e:
        logger.error(f"Ошибка получения рекомендуемых проектов: {e}")
        return {
            "success": False,
            "error": str(e),
            "projects": []
        }

@admin_router.get("/api/portfolio/public/category/{category}")
async def get_public_portfolio_by_category(category: str, page: int = 0, limit: int = 5):
    """Получить проекты портфолио по категории для бота"""
    try:
        with get_db_context() as db:
            offset = page * limit
            
            projects = db.query(Portfolio).filter(
                Portfolio.is_visible == True,
                Portfolio.category == category
            ).order_by(
                Portfolio.sort_order.asc(), 
                Portfolio.created_at.desc()
            ).offset(offset).limit(limit).all()
            
            total_count = db.query(Portfolio).filter(
                Portfolio.is_visible == True,
                Portfolio.category == category
            ).count()
            
            projects_data = []
            for project in projects:
                project_dict = project.to_dict()
                
                # Добавляем полные URL для изображений
                if project_dict.get('main_image'):
                    project_dict['main_image'] = get_image_url(project_dict['main_image'])
                
                if project_dict.get('image_paths'):
                    project_dict['image_paths'] = [
                        get_image_url(img) for img in project_dict['image_paths']
                    ]
                
                projects_data.append(project_dict)
            
            return {
                "success": True,
                "projects": projects_data,
                "pagination": {
                    "page": page,
                    "limit": limit,
                    "total": total_count,
                    "has_more": (offset + limit) < total_count
                }
            }
            
    except Exception as e:
        logger.error(f"Ошибка получения проектов категории {category}: {e}")
        return {
            "success": False,
            "error": str(e),
            "projects": []
        }

@admin_router.get("/api/portfolio/public/{project_id}")
async def get_public_portfolio_item(project_id: int):
    """Получить детальную информацию о проекте портфолио для бота"""
    try:
        with get_db_context() as db:
            project = db.query(Portfolio).filter(
                Portfolio.id == project_id,
                Portfolio.is_visible == True
            ).first()
            
            if not project:
                return {
                    "success": False,
                    "error": "Проект не найден или недоступен"
                }
            
            # Увеличиваем счетчик просмотров
            project.views_count = (project.views_count or 0) + 1
            db.commit()
            
            project_dict = project.to_dict()
            
            # Добавляем полные URL для изображений
            if project_dict.get('main_image'):
                project_dict['main_image'] = get_image_url(project_dict['main_image'])
            
            if project_dict.get('image_paths'):
                project_dict['image_paths'] = [
                    get_image_url(img) for img in project_dict['image_paths']
                ]
            
            return {
                "success": True,
                "project": project_dict
            }
            
    except Exception as e:
        logger.error(f"Ошибка получения проекта {project_id}: {e}")
        return {
            "success": False,
            "error": str(e)
        }

@admin_router.get("/api/portfolio/public/list")
async def get_public_portfolio_list(
    category: str = None, 
    featured: bool = None,
    page: int = 0, 
    limit: int = 5
):
    """Получить список проектов портфолио с фильтрами для бота"""
    try:
        with get_db_context() as db:
            query = db.query(Portfolio).filter(Portfolio.is_visible == True)
            
            if category:
                query = query.filter(Portfolio.category == category)
            
            if featured is not None:
                query = query.filter(Portfolio.is_featured == featured)
            
            total_count = query.count()
            offset = page * limit
            
            projects = query.order_by(
                Portfolio.sort_order.asc(), 
                Portfolio.created_at.desc()
            ).offset(offset).limit(limit).all()
            
            projects_data = []
            for project in projects:
                project_dict = project.to_dict()
                
                # Добавляем полные URL для изображений
                if project_dict.get('main_image'):
                    project_dict['main_image'] = get_image_url(project_dict['main_image'])
                
                if project_dict.get('image_paths'):
                    project_dict['image_paths'] = [
                        get_image_url(img) for img in project_dict['image_paths']
                    ]
                
                projects_data.append(project_dict)
            
            return {
                "success": True,
                "projects": projects_data,
                "pagination": {
                    "page": page,
                    "limit": limit,
                    "total": total_count,
                    "has_more": (offset + limit) < total_count
                }
            }
            
    except Exception as e:
        logger.error(f"Ошибка получения списка портфолио: {e}")
        return {
            "success": False,
            "error": str(e),
            "projects": []
        }

@admin_router.post("/api/portfolio/public/{project_id}/like")
async def like_portfolio_project(project_id: int):
    """Лайкнуть проект портфолио"""
    try:
        with get_db_context() as db:
            project = db.query(Portfolio).filter(
                Portfolio.id == project_id,
                Portfolio.is_visible == True
            ).first()
            
            if not project:
                return {
                    "success": False,
                    "error": "Проект не найден"
                }
            
            # Увеличиваем счетчик лайков
            project.likes_count = (project.likes_count or 0) + 1
            db.commit()
            
            return {
                "success": True,
                "likes": project.likes_count,
                "message": "Спасибо за лайк!"
            }
            
    except Exception as e:
        logger.error(f"Ошибка лайка проекта {project_id}: {e}")
        return {
            "success": False,
            "error": str(e)
        }

# API для публикации портфолио в Telegram
@admin_router.post("/api/portfolio/{portfolio_id}/publish")
async def publish_to_telegram(portfolio_id: int, username: str = Depends(authenticate)):
    """Опубликовать элемент портфолио в Telegram канал"""
    try:
        with get_db_context() as db:
            # Получаем элемент портфолио
            portfolio_item = db.query(Portfolio).filter(Portfolio.id == portfolio_id).first()
            if not portfolio_item:
                return JSONResponse(
                    status_code=404,
                    content={"success": False, "error": "Элемент портфолио не найден"}
                )
            
            # Проверяем, не опубликован ли уже
            if portfolio_item.is_published:
                return JSONResponse(
                    status_code=400,
                    content={"success": False, "error": "Элемент уже опубликован в канале"}
                )
            
            # Импортируем сервис публикации
            try:
                from ...services.portfolio_telegram_service import portfolio_telegram_service
                # Публикуем в Telegram канал
                result = await portfolio_telegram_service.publish_portfolio_item(portfolio_item, db)
                
                if result["success"]:
                    return JSONResponse(content={
                        "success": True,
                        "message": "Элемент портфолио опубликован в Telegram канал",
                        "message_id": result.get("message_id"),
                        "channel_id": result.get("channel_id")
                    })
                else:
                    return JSONResponse(
                        status_code=400,
                        content={"success": False, "error": result["error"]}
                    )
            except ImportError:
                return JSONResponse(
                    status_code=500,
                    content={"success": False, "error": "Telegram сервис недоступен"}
                )
        
    except Exception as e:
        logger.error(f"Ошибка публикации в Telegram: {e}")
        return JSONResponse(
            status_code=500,
            content={"success": False, "error": "Внутренняя ошибка сервера"}
        )

@admin_router.put("/api/portfolio/{portfolio_id}/update-published")
async def update_published_item(portfolio_id: int, username: str = Depends(authenticate)):
    """Обновить уже опубликованный элемент портфолио в Telegram канале"""
    try:
        with get_db_context() as db:
            # Получаем элемент портфолио
            portfolio_item = db.query(Portfolio).filter(Portfolio.id == portfolio_id).first()
            if not portfolio_item:
                return JSONResponse(
                    status_code=404,
                    content={"success": False, "error": "Элемент портфолио не найден"}
                )
            
            # Импортируем сервис публикации
            try:
                from ...services.portfolio_telegram_service import portfolio_telegram_service
                # Обновляем в Telegram канале
                result = await portfolio_telegram_service.update_published_item(portfolio_item, db)
                
                if result["success"]:
                    return JSONResponse(content={
                        "success": True,
                        "message": "Элемент портфолио обновлен в Telegram канале"
                    })
                else:
                    return JSONResponse(
                        status_code=400,
                        content={"success": False, "error": result["error"]}
                    )
            except ImportError:
                return JSONResponse(
                    status_code=500,
                    content={"success": False, "error": "Telegram сервис недоступен"}
                )
        
    except Exception as e:
        logger.error(f"Ошибка обновления в Telegram: {e}")
        return JSONResponse(
            status_code=500,
            content={"success": False, "error": "Внутренняя ошибка сервера"}
        )

@admin_router.delete("/api/portfolio/{portfolio_id}/unpublish")
async def unpublish_from_telegram(portfolio_id: int, username: str = Depends(authenticate)):
    """Удалить элемент портфолио из Telegram канала"""
    try:
        with get_db_context() as db:
            # Получаем элемент портфолио
            portfolio_item = db.query(Portfolio).filter(Portfolio.id == portfolio_id).first()
            if not portfolio_item:
                return JSONResponse(
                    status_code=404,
                    content={"success": False, "error": "Элемент портфолио не найден"}
                )
            
            # Импортируем сервис публикации
            try:
                from ...services.portfolio_telegram_service import portfolio_telegram_service
                # Удаляем из Telegram канала
                result = await portfolio_telegram_service.delete_published_item(portfolio_item, db)
                
                if result["success"]:
                    return JSONResponse(content={
                        "success": True,
                        "message": "Элемент портфолио удален из Telegram канала"
                    })
                else:
                    return JSONResponse(
                        status_code=400,
                        content={"success": False, "error": result["error"]}
                    )
            except ImportError:
                return JSONResponse(
                    status_code=500,
                    content={"success": False, "error": "Telegram сервис недоступен"}
                )
        
    except Exception as e:
        logger.error(f"Ошибка удаления из Telegram: {e}")
        return JSONResponse(
            status_code=500,
            content={"success": False, "error": "Внутренняя ошибка сервера"}
        )

# Роуты для аутентификации
@admin_router.post("/logout")
async def logout():
    """Выход из системы"""
    return RedirectResponse(url="/admin/login", status_code=302)

@admin_router.get("/logout-auth")
async def logout_auth(request: Request, switch: str = None):
    """Специальный роут для очистки HTTP Basic Auth"""
    from fastapi.responses import HTMLResponse
    
    # Определяем URL для перенаправления
    redirect_url = "/admin/login?switch=true" if switch else "/admin/login"
    
    # HTML страница которая очищает аутентификацию и перенаправляет
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Выход из системы</title>
        <meta charset="UTF-8">
        <style>
            body {{ 
                font-family: 'Arial', sans-serif; 
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                display: flex; 
                justify-content: center; 
                align-items: center; 
                height: 100vh; 
                margin: 0; 
            }}
            .logout-container {{ 
                background: white; 
                padding: 2rem; 
                border-radius: 10px; 
                text-align: center; 
                box-shadow: 0 4px 6px rgba(0,0,0,0.1);
            }}
            .spinner {{
                border: 4px solid #f3f3f3;
                border-top: 4px solid #667eea;
                border-radius: 50%;
                width: 40px;
                height: 40px;
                animation: spin 1s linear infinite;
                margin: 1rem auto;
            }}
            @keyframes spin {{
                0% {{ transform: rotate(0deg); }}
                100% {{ transform: rotate(360deg); }}
            }}
        </style>
    </head>
    <body>
        <div class="logout-container">
            <h3>🚪 Выход из системы</h3>
            <div class="spinner"></div>
            <p>Очистка данных аутентификации...</p>
            <p><small>Если перенаправление не произошло автоматически, <a href="{redirect_url}">нажмите здесь</a></small></p>
        </div>
        
        <script>
            // Попытка очистить HTTP Basic Auth через подмену заголовков
            function clearAuth() {{
                // Создаем XMLHttpRequest с неверными учетными данными для сброса кэша
                fetch('/admin/', {{
                    method: 'GET',
                    headers: {{
                        'Authorization': 'Basic ' + btoa('logout:logout')
                    }}
                }}).catch(() => {{
                    // Игнорируем ошибку - это ожидаемо
                }}).finally(() => {{
                    // Перенаправляем на страницу логина через 2 секунды
                    setTimeout(() => {{
                        window.location.href = '{redirect_url}';
                    }}, 2000);
                }});
            }}
            
            // Запускаем очистку при загрузке страницы
            document.addEventListener('DOMContentLoaded', clearAuth);
        </script>
    </body>
    </html>
    """
    
    return HTMLResponse(content=html_content, status_code=200)


# Основные HTML роуты
# Примечание: /permissions управляется через permissions_management роутер

# ===== CATCH-ALL ROUTE ДЛЯ REACT =====
# ВАЖНО: Этот роут вынесен в отдельный роутер, который регистрируется ПОСЛЕДНИМ в main.py
# чтобы не перехватывать API и WebSocket запросы

# Создаем отдельный роутер для catch-all
catch_all_router = APIRouter()

@catch_all_router.get("/{full_path:path}", response_class=HTMLResponse)
async def catch_all_react(full_path: str):
    """
    Catch-all роут для React приложения
    Отдает index.html для всех несовпавших маршрутов,
    позволяя React Router обрабатывать клиентскую маршрутизацию
    """
    from fastapi.responses import FileResponse
    import os

    # Игнорируем API запросы - они должны обрабатываться своими роутерами
    if full_path.startswith("api/"):
        raise HTTPException(status_code=404, detail="API endpoint not found")

    # Игнорируем WebSocket запросы - они должны обрабатываться WebSocket роутерами
    if full_path.startswith("ws/"):
        raise HTTPException(status_code=404, detail="WebSocket endpoint not found")

    # Игнорируем статические файлы (assets) - они должны обрабатываться StaticFiles
    # Проверяем расширение файла
    if "." in full_path.split("/")[-1]:
        asset_extensions = ['.js', '.css', '.svg', '.png', '.jpg', '.jpeg', '.gif', '.ico', '.woff', '.woff2', '.ttf', '.eot', '.map']
        if any(full_path.endswith(ext) for ext in asset_extensions):
            raise HTTPException(status_code=404, detail="Static file not found")

    # Путь к React приложению
    react_index = os.path.join("app", "admin", "static", "index.html")

    if os.path.exists(react_index):
        return FileResponse(react_index)
    else:
        # Если React приложение не найдено, показываем ошибку
        raise HTTPException(status_code=404, detail="React app not found")

# Создание FastAPI приложения
app = FastAPI(title="Admin Panel")

# Корневой редирект на админку
@app.get("/")
async def root():
    return RedirectResponse(url="/admin/", status_code=302)

# ВАЖНО: Монтируем статические файлы React ПЕРЕД роутерами
# чтобы они обрабатывались до catch-all роута
app.mount("/admin/assets", StaticFiles(directory="app/admin/static/assets"), name="react-assets")

# Подключение роутера к приложению с префиксом /admin
app.include_router(admin_router, prefix="/admin")

# Подключение роутера UI permissions напрямую к app (без префикса /admin)
if ui_permissions_router:
    app.include_router(ui_permissions_router)
    print("✅ Роутер детальных UI прав подключен к app")

# Подключение статических файлов
app.mount("/static", StaticFiles(directory="app/admin/static"), name="static")
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

# Добавление middleware
auth_service = AuthService()
security = HTTPBasic()

# Role middleware is applied via decorators in individual routes
role_middleware = RoleMiddleware()

# ВАЖНО: Подключаем catch-all роутер ПОСЛЕДНИМ, чтобы React SPA обрабатывал все несовпавшие маршруты
# Это должно быть после всех API роутеров, чтобы не перехватывать API запросы
app.include_router(catch_all_router, prefix="/admin")

