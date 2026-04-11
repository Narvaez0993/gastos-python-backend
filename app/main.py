import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.database import init_db
from app.routes import budgets, expenses, money_sources, persons

app = FastAPI(
    title="API de Gestión de Gastos",
    description=(
        "API REST para el registro y seguimiento de gastos personales. "
        "Permite gestionar personas, gastos, presupuestos y fuentes de dinero. "
        "Implementada con arquitectura por capas (Routes → Services → DAO) "
        "y conexión manual a SQLite con SQL crudo."
    ),
    version="1.0.0",
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
    allow_origins=["*"],
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
    return {"message": "API de Gestión de Gastos funcionando"}


if __name__ == "__main__":
    uvicorn.run("app.main:app", host="0.0.0.0", port=3002, reload=True)
