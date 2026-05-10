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
    get_person_repo,
)
from app.repositories.interfaces.budget_repository import IBudgetRepository
from app.repositories.interfaces.expense_repository import IExpenseRepository
from app.repositories.interfaces.money_source_movement_repository import (
    IMoneySourceMovementRepository,
)
from app.repositories.interfaces.money_source_repository import IMoneySourceRepository
from app.repositories.interfaces.person_repository import IPersonRepository
from app.routes import budgets, expenses, money_sources, persons

settings = get_settings()

app = FastAPI(
    title="API de Gestión de Gastos",
    description=(
        "API REST para el registro y seguimiento de gastos personales. "
        "Permite gestionar personas, gastos, presupuestos y fuentes de dinero. "
        "Implementada con arquitectura por capas (Routes → Services → DAO) "
        "y conexión manual a SQLite con SQL crudo."
    ),
    version="1.1.0",
    openapi_tags=[
        {
            "name": "Personas",
            "description": "Operaciones CRUD para la gestión de personas registradas en el sistema.",
        },
        {
            "name": "Gastos",
            "description": "Operaciones para crear, consultar, actualizar y eliminar gastos.",
        },
        {
            "name": "Presupuestos",
            "description": "Gestión de presupuestos diarios, semanales y mensuales por persona.",
        },
        {
            "name": "Fuentes de Dinero",
            "description": "Gestión de fuentes de dinero (cuentas, billeteras), depósitos y movimientos.",
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

app.include_router(persons.router)
app.include_router(expenses.router)
app.include_router(budgets.router)
app.include_router(money_sources.router)


@app.on_event("startup")
def on_startup():
    init_db()


@app.get("/", tags=["Root"], summary="Estado de la API")
def root():
    """Verifica que la API está funcionando correctamente."""
    return {
        "message": "API de Gestión de Gastos funcionando",
        "environment": settings.APP_ENV,
    }


@app.get(
    "/api/_debug/repos",
    tags=["Root"],
    summary="Debug: muestra qué implementación concreta usa cada repositorio (solo en dev)",
)
def debug_repos(
    person_repo: IPersonRepository = Depends(get_person_repo),
    money_source_repo: IMoneySourceRepository = Depends(get_money_source_repo),
    expense_repo: IExpenseRepository = Depends(get_expense_repo),
    budget_repo: IBudgetRepository = Depends(get_budget_repo),
    movement_repo: IMoneySourceMovementRepository = Depends(get_movement_repo),
):
    """Demuestra que SQL y JPA conviven en runtime.

    Útil para validar la inyección de dependencias y para mostrar al profesor
    que la selección de backend es polimórfica.
    """
    if settings.APP_ENV != "dev":
        raise HTTPException(status_code=404, detail="Not found")

    return {
        "person_repo": type(person_repo).__name__,
        "money_source_repo": type(money_source_repo).__name__,
        "expense_repo": type(expense_repo).__name__,
        "budget_repo": type(budget_repo).__name__,
        "movement_repo": type(movement_repo).__name__,
        "settings": {
            "PERSON_REPO_BACKEND": settings.PERSON_REPO_BACKEND,
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
