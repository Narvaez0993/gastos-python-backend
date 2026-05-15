# API de Gestión de Gastos

API REST para el registro y seguimiento de gastos personales. Permite a un usuario autenticado gestionar sus gastos, presupuestos y fuentes de dinero.

Implementada con arquitectura por capas con **inyección de dependencias** y patrón **Repository**, donde la capa de persistencia ofrece dos implementaciones intercambiables:

- **SQL crudo** (sqlite3 nativo) — utilizado para gastos, presupuestos y movimientos.
- **JPA / SQLAlchemy ORM** — utilizado para usuarios y fuentes de dinero.

```
Routes (endpoints REST, JWT Bearer)
        ↓ Depends(get_current_user) + Depends(service)
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
- **Pydantic** + **pydantic-settings** + `email-validator` — Validación y configuración
- **python-jose** + **passlib[bcrypt]** — JWT y hashing de contraseñas
- **pytest** + **pytest-cov** — Pruebas unitarias y cobertura

## Estructura del proyecto

```
app/
├── main.py                           # Punto de entrada, Swagger, CORS, routers
├── database.py                       # Conexión sqlite3 y DDL (constante SCHEMA_SQL)
├── config/
│   └── settings.py                   # Settings(BaseSettings) cargado desde .env por perfil
├── db/                               # Infraestructura SQLAlchemy (engine, sesión, modelos)
│   ├── base.py
│   ├── session.py
│   └── models/
│       ├── user_model.py             # ORM User
│       └── money_source_model.py     # ORM MoneySource
├── repositories/
│   ├── interfaces/                   # 5 ABCs — contrato del puerto (SOLID/DIP)
│   ├── sql/                          # implementación SQL crudo de los 5 dominios
│   └── jpa/                          # implementación SQLAlchemy de Users y MoneySources
├── services/                         # auth, expenses, budgets, money_sources
├── routes/                           # endpoints REST (Depends para current_user + service)
├── dependencies/
│   ├── containers.py                 # wiring de DI: get_*_repo y get_*_service
│   └── security.py                   # oauth2_scheme + get_current_user
├── schemas/                          # Pydantic models (request/response), incluye auth.py
└── utils/
    ├── dates.py                      # funciones puras de timezones
    └── budget_check.py               # check_budgets recibe repos por parámetro

tests/
├── conftest.py                       # fixtures: SQLite, sesión SA, mocks, auth_*
└── unit/
    ├── repositories/                 # tests de los 5 SqlRepository + 2 JpaRepository
    └── services/                     # tests de los 4 services + auth_service
```

## Configuración por perfiles

La aplicación selecciona el archivo `.env` según `APP_ENV`:

- `APP_ENV=dev` (default) → `.env.dev`
- `APP_ENV=prod` → `.env.prod`
- `APP_ENV=test` → variables de entorno explícitas (tests fuerzan defaults)

Variables disponibles (ver `.env.example`):

| Variable | Descripción |
|---|---|
| `APP_ENV` | Perfil activo (dev / prod / test) |
| `DATABASE_PATH` | Ruta del archivo SQLite |
| `HOST`, `PORT` | Servidor uvicorn |
| `RELOAD` | Recarga automática |
| `LOG_LEVEL` | Nivel de logs |
| `SQL_ECHO` | Si es `true`, SQLAlchemy imprime queries |
| `CORS_ORIGINS` | Orígenes permitidos, CSV |
| `USER_REPO_BACKEND` | `sql` o `jpa` |
| `MONEY_SOURCE_REPO_BACKEND` | `sql` o `jpa` |
| `DEFAULT_TIMEZONE` | Zona horaria por defecto |
| `JWT_SECRET` | Secret para HS256. **Obligatorio en prod**, ≥32 chars |
| `JWT_ALGORITHM` | `HS256` |
| `JWT_EXPIRES_MINUTES` | TTL del access token (default 1440 = 24 h) |
| `BCRYPT_ROUNDS` | Costo de bcrypt (default 12; tests usan 4) |

## Instalación y ejecución

```bash
# 1. Clonar y entrar al proyecto
cd gastos-python-backend

# 2. Crear y activar venv
python3 -m venv venv
source venv/bin/activate

# 3. Instalar dependencias
pip install -r requirements.txt

# 4. (Solo si vienes de la versión 1.x) Borrar la BD anterior — schema incompatible
rm -f gastos.db

# 5. Ejecutar en modo desarrollo
APP_ENV=dev python -m app.main

# Para prod: generar secret y exportarlo
# openssl rand -hex 32
APP_ENV=prod JWT_SECRET=<tu-secret> python -m app.main
```

El servidor escucha en `http://localhost:3002`. Documentación Swagger en `/docs`.

## Autenticación

Toda la API está protegida con JWT Bearer salvo `/`, `/api/auth/register` y `/api/auth/login`.

```bash
# Registrarse (devuelve user + access_token)
curl -X POST http://localhost:3002/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"seba@example.com","password":"secret123","name":"Sebastian"}'

# Iniciar sesión
curl -X POST http://localhost:3002/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"seba@example.com","password":"secret123"}'

# Usar el token en endpoints protegidos
TOKEN=<access_token>
curl http://localhost:3002/api/auth/me -H "Authorization: Bearer $TOKEN"
curl http://localhost:3002/api/expenses -H "Authorization: Bearer $TOKEN"

# Crear gasto (el user_id se infiere del token; no se envía en el body)
curl -X POST http://localhost:3002/api/expenses \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"amount":25000,"description":"Almuerzo","date":"2026-05-14","category":"Comida"}'
```

> **Nota**: El endpoint `/login` acepta JSON, no `OAuth2PasswordRequestForm`. El botón "Authorize" de Swagger UI no funciona por defecto: usar el header `Authorization: Bearer <token>` manualmente.

## Pruebas unitarias

```bash
pytest
pytest --cov=app --cov-report=term-missing
pytest tests/unit/repositories/
pytest tests/unit/services/
pytest -k "auth"
```

Los tests fuerzan `JWT_SECRET` y `BCRYPT_ROUNDS=4` automáticamente vía `conftest.py`.

## Endpoints

### Autenticación (`/api/auth`)
| Método | Endpoint | Descripción |
|---|---|---|
| POST | `/api/auth/register` | Registrar nueva cuenta. Devuelve `{user, access_token}` |
| POST | `/api/auth/login` | Iniciar sesión. Devuelve `{user, access_token}` |
| GET | `/api/auth/me` | Datos del usuario autenticado |
| PUT | `/api/auth/me` | Actualizar nombre o email |

### Gastos (`/api/expenses`) — backend: SQL crudo
| Método | Endpoint | Descripción |
|---|---|---|
| GET | `/api/expenses` | Listar (filtros: `period`, `startDate`, `endDate`, `tz`) |
| GET | `/api/expenses/summary` | Total y desglose por categoría |
| GET | `/api/expenses/{id}` | Obtener por ID |
| POST | `/api/expenses` | Crear |
| PUT | `/api/expenses/{id}` | Actualizar |
| DELETE | `/api/expenses/{id}` | Eliminar |

### Presupuestos (`/api/budgets`) — backend: SQL crudo
| Método | Endpoint | Descripción |
|---|---|---|
| GET | `/api/budgets` | Listar (del usuario actual) |
| GET | `/api/budgets/{id}` | Obtener por ID |
| POST | `/api/budgets` | Crear o actualizar (upsert por tipo) |
| PUT | `/api/budgets/{id}` | Actualizar |
| DELETE | `/api/budgets/{id}` | Eliminar |

### Fuentes de dinero (`/api/money-sources`) — backend: JPA por defecto
| Método | Endpoint | Descripción |
|---|---|---|
| GET | `/api/money-sources` | Listar (del usuario actual) |
| GET | `/api/money-sources/{id}` | Obtener por ID |
| POST | `/api/money-sources` | Crear |
| PUT | `/api/money-sources/{id}` | Actualizar |
| DELETE | `/api/money-sources/{id}` | Eliminar (solo si no tiene movimientos) |
| POST | `/api/money-sources/{id}/deposit` | Registrar depósito |
| GET | `/api/money-sources/{id}/movements` | Historial paginado |

## Breaking changes 2.0.0

> Migración necesaria si vienes de la versión 1.x. Borrar `gastos.db` para regenerar el schema.

| Cambio | Antes (1.x) | Ahora (2.0.0) |
|---|---|---|
| Tabla `persons` | `persons (id, name UNIQUE, created_at)` | renombrada a `users` con campos `email UNIQUE`, `password_hash` |
| Endpoints `/api/persons/*` | CRUD público | **eliminados** → reemplazados por `/api/auth/*` y `/api/auth/me` |
| FKs `person_id` | `expenses.person_id`, `budgets.person_id`, `money_sources.person_id` | renombradas a `user_id` |
| Query `?personId=` | obligatorio en GET de expenses/budgets/money-sources | **eliminado** — se deriva del JWT |
| Body `person_id` | obligatorio al crear expense/budget/money-source | **eliminado** — se deriva del JWT |
| Campo de respuesta | `person: {id, name}` en expenses/budgets | renombrado a `user: {id, name}` |
| Autenticación | ninguna | JWT Bearer obligatorio en todos los endpoints salvo `/`, `/api/auth/register`, `/api/auth/login` |

## Patrón Repository y SOLID

- **DIP**: los services dependen de las interfaces `IUserRepository`, `IExpenseRepository`, etc.
- **ISP**: cada dominio tiene su propia interfaz.
- **OCP**: agregar un backend (PostgreSQL) requiere solo crear un nuevo `*PgRepository`.

## Notas de diseño

- `init_db()` mantiene el schema. La constante `SCHEMA_SQL` se comparte entre runtime y `tests/conftest.py` para evitar drift.
- Sin Alembic: para un proyecto en desarrollo activo sin datos productivos, el costo de migración manual al cambiar schema es bajo. Cuando haya datos prod, introducir Alembic.
- Los services lanzan `HTTPException` (acoplo conocido a FastAPI) — refactor a excepciones de dominio queda como deuda técnica.
- `password_hash` solo se lee/escribe en el repositorio y `AuthService`. Los endpoints usan `response_model=UserOut` (que no incluye el hash).

## Zona horaria

Se puede especificar por request con el query param `?tz=America/Bogota` o el header `X-Timezone`. Default: `DEFAULT_TIMEZONE` (America/Bogota).
