# API de Gestión de Gastos

API REST para el registro y seguimiento de gastos personales. Permite gestionar personas, gastos, presupuestos y fuentes de dinero.

Implementada con arquitectura por capas (Routes → Services → DAO) y conexión manual a SQLite con SQL crudo.

## Tecnologías

- **Python 3.9+**
- **FastAPI** — Framework web
- **SQLite** — Base de datos relacional
- **sqlite3** — Driver de conexión manual (sin ORM)
- **Pydantic** — Validación de datos
- **Uvicorn** — Servidor ASGI

## Arquitectura

```
Routes (endpoints REST)  →  Services (lógica de negocio)  →  DAO (SQL crudo)  →  SQLite
```

```
app/
├── main.py          # Punto de entrada, configuración Swagger y CORS
├── database.py      # Conexión manual a SQLite con sqlite3
├── dao/             # Capa de persistencia - Patrón DAO con SQL crudo
├── services/        # Capa de lógica de negocio
├── schemas/         # Esquemas Pydantic (validación request/response)
├── routes/          # Endpoints REST (GET, POST, PUT, DELETE)
└── utils/           # Utilidades (zonas horarias, verificación de presupuestos)
```

## Requisitos previos

- **Python 3.9** o superior instalado en el sistema
- **pip** (gestor de paquetes de Python)
- **Git**

Para verificar que tienes Python instalado:

```bash
python3 --version
```

## Instalación y ejecución

### 1. Clonar el repositorio

```bash
git clone <URL_DEL_REPOSITORIO>
cd gastos-python-backend
```

### 2. Crear entorno virtual

```bash
python3 -m venv venv
```

### 3. Activar entorno virtual

En **macOS / Linux**:
```bash
source venv/bin/activate
```

En **Windows** (cmd):
```bash
venv\Scripts\activate
```

En **Windows** (PowerShell):
```bash
venv\Scripts\Activate.ps1
```

### 4. Instalar dependencias

```bash
pip install -r requirements.txt
```

### 5. Ejecutar el servidor

```bash
python -m app.main
```

El servidor se inicia en `http://localhost:3002`.

La base de datos SQLite (`gastos.db`) se crea automáticamente al iniciar el servidor por primera vez.

### 6. Abrir la documentación Swagger

Ir a `http://localhost:3002/docs` en el navegador para ver y probar todos los endpoints de la API.

## Endpoints de la API

### Personas (`/api/persons`)
| Método | Endpoint | Descripción |
|--------|----------|-------------|
| GET | `/api/persons` | Listar todas las personas |
| GET | `/api/persons/{id}` | Obtener persona por ID |
| POST | `/api/persons` | Crear persona |
| PUT | `/api/persons/{id}` | Actualizar persona |
| DELETE | `/api/persons/{id}` | Eliminar persona |

### Gastos (`/api/expenses`)
| Método | Endpoint | Descripción |
|--------|----------|-------------|
| GET | `/api/expenses` | Listar gastos (filtros: `personName`, `period`, `startDate`, `endDate`) |
| GET | `/api/expenses/summary` | Resumen por categoría |
| GET | `/api/expenses/{id}` | Obtener gasto por ID |
| POST | `/api/expenses` | Crear gasto |
| PUT | `/api/expenses/{id}` | Actualizar gasto |
| DELETE | `/api/expenses/{id}` | Eliminar gasto |

### Presupuestos (`/api/budgets`)
| Método | Endpoint | Descripción |
|--------|----------|-------------|
| GET | `/api/budgets?personName=...` | Listar presupuestos por persona |
| GET | `/api/budgets/{id}` | Obtener presupuesto por ID |
| POST | `/api/budgets` | Crear o actualizar presupuesto |
| PUT | `/api/budgets/{id}` | Actualizar presupuesto |
| DELETE | `/api/budgets/{id}` | Eliminar presupuesto |

### Fuentes de Dinero (`/api/money-sources`)
| Método | Endpoint | Descripción |
|--------|----------|-------------|
| GET | `/api/money-sources?personName=...` | Listar fuentes de dinero |
| GET | `/api/money-sources/{id}` | Obtener fuente por ID |
| POST | `/api/money-sources` | Crear fuente de dinero |
| PUT | `/api/money-sources/{id}` | Actualizar fuente de dinero |
| DELETE | `/api/money-sources/{id}` | Eliminar fuente de dinero |
| POST | `/api/money-sources/{id}/deposit` | Registrar depósito |
| GET | `/api/money-sources/{id}/movements` | Historial de movimientos |

## Configuración

| Parámetro | Valor por defecto |
|-----------|-------------------|
| Puerto | `3002` |
| Base de datos | `./gastos.db` (SQLite) |
| Zona horaria | `America/Bogota` |
| CORS | Todos los orígenes permitidos |

## Zona horaria

Se puede especificar la zona horaria por request con el query param `?tz=America/Bogota` o el header `X-Timezone`. Por defecto usa `America/Bogota`.
