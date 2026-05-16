import uvicorn
from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from app.config.settings import get_settings
from app.database import init_db
from app.dependencies.containers import (
    get_budget_repo,
    get_expense_repo,
    get_money_source_repo,
    get_movement_repo,
    get_user_repo,
)
from app.repositories.interfaces.budget_repository import IBudgetRepository
from app.repositories.interfaces.expense_repository import IExpenseRepository
from app.repositories.interfaces.money_source_movement_repository import (
    IMoneySourceMovementRepository,
)
from app.repositories.interfaces.money_source_repository import IMoneySourceRepository
from app.repositories.interfaces.user_repository import IUserRepository
from app.routes import (
    attachments,
    auth,
    budgets,
    capture,
    chat,
    expenses,
    money_sources,
)

settings = get_settings()

app = FastAPI(
    title="API de Gestión de Gastos",
    description=(
        "API REST para el registro y seguimiento de gastos personales. "
        "Permite gestionar usuarios autenticados, gastos, presupuestos y "
        "fuentes de dinero. Implementada con arquitectura por capas "
        "(Routes → Services → Repositories) con interfaces ABC y dos backends "
        "intercambiables (SQL crudo + SQLAlchemy/JPA). Autenticación JWT."
    ),
    version="2.0.0",
    openapi_tags=[
        {
            "name": "Autenticación",
            "description": "Registro, login y datos del usuario actual.",
        },
        {
            "name": "Gastos",
            "description": "Operaciones para crear, consultar, actualizar y eliminar gastos del usuario autenticado.",
        },
        {
            "name": "Presupuestos",
            "description": "Gestión de presupuestos diarios, semanales y mensuales del usuario autenticado.",
        },
        {
            "name": "Fuentes de Dinero",
            "description": "Gestión de fuentes de dinero (cuentas, billeteras), depósitos y movimientos.",
        },
        {
            "name": "Captura IA",
            "description": "Parsing de gastos en lenguaje natural usando Claude (texto, audio, recibos).",
        },
        {
            "name": "Chat IA",
            "description": "Asistente conversacional financiero con acceso a los datos del usuario vía tools.",
        },
        {
            "name": "Adjuntos",
            "description": "Subida y descarga de recibos/facturas vinculados a gastos.",
        },
    ],
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(expenses.router)
app.include_router(budgets.router)
app.include_router(money_sources.router)
app.include_router(capture.router)
app.include_router(chat.router)
app.include_router(attachments.router)

@app.on_event("startup")
def on_startup():
    init_db()

@app.get("/", tags=["Root"], summary="Estado de la API")
def root():
    return {
        "message": "API de Gestión de Gastos funcionando",
        "environment": settings.APP_ENV,
        "version": app.version,
    }

@app.get(
    "/api/_debug/repos",
    tags=["Root"],
    summary="Debug: muestra qué implementación concreta usa cada repositorio (solo en dev)",
)
def debug_repos(
    user_repo: IUserRepository = Depends(get_user_repo),
    money_source_repo: IMoneySourceRepository = Depends(get_money_source_repo),
    expense_repo: IExpenseRepository = Depends(get_expense_repo),
    budget_repo: IBudgetRepository = Depends(get_budget_repo),
    movement_repo: IMoneySourceMovementRepository = Depends(get_movement_repo),
):
    if settings.APP_ENV != "dev":
        raise HTTPException(status_code=404, detail="Not found")

    return {
        "user_repo": type(user_repo).__name__,
        "money_source_repo": type(money_source_repo).__name__,
        "expense_repo": type(expense_repo).__name__,
        "budget_repo": type(budget_repo).__name__,
        "movement_repo": type(movement_repo).__name__,
        "settings": {
            "USER_REPO_BACKEND": settings.USER_REPO_BACKEND,
            "MONEY_SOURCE_REPO_BACKEND": settings.MONEY_SOURCE_REPO_BACKEND,
            "SQL_ECHO": settings.SQL_ECHO,
        },
    }

if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.RELOAD,
        log_level=settings.LOG_LEVEL,
    )
