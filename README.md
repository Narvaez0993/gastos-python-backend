# API de Gestión de Gastos

API REST para el registro y seguimiento de gastos personales. Permite gestionar personas, gastos, presupuestos y fuentes de dinero.

Implementada con arquitectura por capas con **inyección de dependencias** y patrón **Repository**, donde la capa de persistencia ofrece dos implementaciones intercambiables:

- **SQL crudo** (sqlite3 nativo) — utilizado para gastos, presupuestos y movimientos.
- **JPA / SQLAlchemy ORM** — utilizado para personas y fuentes de dinero.

```
Routes (endpoints REST)
        ↓ Depends()
Services (lógica de negocio, dependen de IRepository)
        ↓
IRepository (interfaces ABC, contrato del puerto)
        ↓
{ SqlRepository (SQL crudo) | JpaRepository (SQLAlchemy ORM) }
        ↓
SQLite
```

## Tecnologías

- **Python 3.9+**
- **FastAPI** + **Uvicorn** — Framework web y servidor ASGI
- **SQLite** — Base de datos relacional
- **sqlite3** — Driver nativo (capa SQL crudo)
- **SQLAlchemy 2.x** — ORM (capa JPA)
- **Pydantic** + **pydantic-settings** — Validación de datos y configuración por perfiles
- **pytest** + **pytest-cov** — Pruebas unitarias y cobertura

## Estructura del proyecto

```
app/
├── main.py                           # Punto de entrada, Swagger y CORS
├── database.py                       # Conexión sqlite3 y DDL inicial
├── config/
│   └── settings.py                   # Settings(BaseSettings) cargado desde .env por perfil
├── db/                               # Infraestructura SQLAlchemy (engine, sesión, modelos)
│   ├── base.py
│   ├── session.py                    # engine + listener PRAGMA foreign_keys + get_db
│   └── models/
│       ├── person_model.py           # ORM
│       └── money_source_model.py     # ORM
├── repositories/
│   ├── interfaces/                   # 5 ABCs — contrato del puerto (SOLID/DIP)
│   ├── sql/                          # implementación SQL crudo de los 5 dominios
│   └── jpa/                          # implementación SQLAlchemy de Persons y MoneySources
├── services/                         # lógica de negocio (clases instanciables)
├── routes/                           # endpoints REST (usan Depends para inyectar service)
├── dependencies/
│   └── containers.py                 # wiring de DI: get_*_repo y get_*_service
├── schemas/                          # Pydantic models (request/response)
└── utils/
    ├── dates.py                      # funciones puras de timezones
    └── budget_check.py               # check_budgets recibe repos por parámetro

tests/
├── conftest.py                       # fixtures: tmp SQLite, sesión SA en memoria, mocks
└── unit/
    ├── repositories/                 # tests de los 5 SqlRepository + 2 JpaRepository
    └── services/                     # tests de los 4 services con mocks
```

## Configuración por perfiles

La aplicación selecciona el archivo `.env` según la variable de entorno `APP_ENV`:

- `APP_ENV=dev` (por defecto) → `.env.dev`
- `APP_ENV=prod` → `.env.prod`

Variables disponibles (ver `.env.example`):

| Variable | Descripción |
|---|---|
| `APP_ENV` | Perfil activo (dev / prod) |
| `DATABASE_PATH` | Ruta del archivo SQLite (relativa o absoluta) |
| `HOST`, `PORT` | Servidor uvicorn |
| `RELOAD` | Recarga automática (true en dev, false en prod) |
| `LOG_LEVEL` | Nivel de logs |
| `SQL_ECHO` | Si es `true`, SQLAlchemy imprime cada query del ORM en consola |
| `CORS_ORIGINS` | Lista de orígenes permitidos, separados por coma |
| `PERSON_REPO_BACKEND` | `sql` o `jpa` (selecciona implementación de PersonRepository) |
| `MONEY_SOURCE_REPO_BACKEND` | `sql` o `jpa` |
| `DEFAULT_TIMEZONE` | Zona horaria por defecto |

Diferencias clave entre `.env.dev` y `.env.prod`: `RELOAD`, `LOG_LEVEL`, `CORS_ORIGINS` y `SQL_ECHO`.

## Instalación y ejecución

```bash
# 1. Clonar y entrar al proyecto
git clone <URL_DEL_REPOSITORIO>
cd gastos-python-backend

# 2. Crear y activar venv
python3 -m venv venv
source venv/bin/activate    # macOS/Linux
# venv\Scripts\activate     # Windows

# 3. Instalar dependencias
pip install -r requirements.txt

# 4. Ejecutar en modo desarrollo
APP_ENV=dev python -m app.main

# 5. Ejecutar en modo producción
APP_ENV=prod python -m app.main
```

El servidor escucha en `http://localhost:3002`. Documentación Swagger en `http://localhost:3002/docs`.

## Pruebas unitarias

```bash
pytest                                  # corre las 54 pruebas (~1s)
pytest --cov=app --cov-report=term-missing
pytest tests/unit/repositories/         # solo repositorios
pytest tests/unit/services/             # solo services
pytest -k "jpa"                         # solo JPA
```

Estructura: 22 pruebas de repositorios SQL, 10 de repositorios JPA, 22 de services con mocks. Cobertura ≥ 70 %.

## Demostrar la coexistencia SQL + JPA

En modo dev hay un endpoint de inspección que muestra qué clase concreta atiende cada repositorio:

```bash
curl http://localhost:3002/api/_debug/repos
```

Respuesta típica con `PERSON_REPO_BACKEND=jpa`:
```json
{
  "person_repo": "PersonJpaRepository",
  "money_source_repo": "MoneySourceJpaRepository",
  "expense_repo": "ExpenseSqlRepository",
  "budget_repo": "BudgetSqlRepository",
  "movement_repo": "MoneySourceMovementSqlRepository"
}
```

Además, con `SQL_ECHO=true` (activado en `.env.dev`), las queries que genera SQLAlchemy aparecen en consola al golpear `/api/persons` o `/api/money-sources`. Las queries de `/api/expenses` y `/api/budgets` no aparecen ahí porque son SQL crudo.

## Endpoints

### Personas (`/api/persons`) — backend: JPA por defecto
| Método | Endpoint | Descripción |
|--------|----------|-------------|
| GET | `/api/persons` | Listar todas |
| GET | `/api/persons/{id}` | Obtener por ID |
| POST | `/api/persons` | Crear |
| PUT | `/api/persons/{id}` | Actualizar |
| DELETE | `/api/persons/{id}` | Eliminar |

### Fuentes de dinero (`/api/money-sources`) — backend: JPA por defecto
| Método | Endpoint | Descripción |
|--------|----------|-------------|
| GET | `/api/money-sources?personId=...` | Listar por persona |
| GET | `/api/money-sources/{id}` | Obtener por ID |
| POST | `/api/money-sources` | Crear |
| PUT | `/api/money-sources/{id}` | Actualizar |
| DELETE | `/api/money-sources/{id}` | Eliminar |
| POST | `/api/money-sources/{id}/deposit` | Registrar depósito |
| GET | `/api/money-sources/{id}/movements` | Historial paginado |

### Gastos (`/api/expenses`) — backend: SQL crudo
| Método | Endpoint | Descripción |
|--------|----------|-------------|
| GET | `/api/expenses` | Listar (filtros: `personId`, `period`, `startDate`, `endDate`) |
| GET | `/api/expenses/summary` | Total y desglose por categoría |
| GET | `/api/expenses/{id}` | Obtener por ID |
| POST | `/api/expenses` | Crear |
| PUT | `/api/expenses/{id}` | Actualizar |
| DELETE | `/api/expenses/{id}` | Eliminar |

### Presupuestos (`/api/budgets`) — backend: SQL crudo
| Método | Endpoint | Descripción |
|--------|----------|-------------|
| GET | `/api/budgets?personId=...` | Listar por persona |
| GET | `/api/budgets/{id}` | Obtener por ID |
| POST | `/api/budgets` | Crear o actualizar |
| PUT | `/api/budgets/{id}` | Actualizar |
| DELETE | `/api/budgets/{id}` | Eliminar |

## Patrón Repository y SOLID

- **DIP (Dependency Inversion Principle)**: los services dependen de las interfaces `IPersonRepository`, `IExpenseRepository`, etc., no de las clases concretas. Se inyectan vía `Depends()` de FastAPI.
- **ISP (Interface Segregation Principle)**: cada dominio tiene su propia interfaz con los métodos que realmente necesita (no hay un `IRepository[T]` genérico forzado).
- **OCP (Open/Closed Principle)**: agregar un nuevo backend (por ejemplo PostgreSQL) requiere solo crear un nuevo `*PgRepository` que implemente la interfaz; ni los services ni las routes cambian.

## Notas de diseño

- `init_db()` (en `database.py`) sigue siendo el dueño del schema. SQLAlchemy mapea las tablas existentes pero **no** ejecuta `Base.metadata.create_all()` en runtime — la BD es una sola y vive en SQL crudo.
- Para mantener integridad referencial idéntica entre ambos backends, el engine de SQLAlchemy registra un listener que ejecuta `PRAGMA foreign_keys=ON` en cada conexión nueva.
- Los services siguen lanzando `HTTPException` (acoplo conocido a FastAPI). Refactorizar a excepciones de dominio queda como deuda técnica fuera del alcance de esta entrega.

## Zona horaria

Se puede especificar la zona horaria por request con el query param `?tz=America/Bogota` o el header `X-Timezone`. Por defecto usa la `DEFAULT_TIMEZONE` configurada (America/Bogota).
