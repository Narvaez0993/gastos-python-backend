# Gastos Python Backend

REST API for expense tracking with budget alerts, money source management, and image uploads. Built with FastAPI + SQLAlchemy + SQLite.

## Requirements

- Python 3.11+

## Setup

```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run database migrations
alembic upgrade head

# Start server (port 3002)
python -m app.main
```

The server starts at `http://localhost:3002`.

## API Endpoints

### Persons
- `POST /api/persons` — Create a person
- `GET /api/persons` — List all persons

### Expenses
- `POST /api/expenses` — Create expense (multipart form, supports image uploads)
- `GET /api/expenses` — List expenses (filters: `personName`, `period`, `startDate`, `endDate`, `tz`)
- `GET /api/expenses/summary` — Expense summary by category
- `GET /api/expenses/{id}` — Get single expense
- `DELETE /api/expenses/{id}` — Delete expense (reverts money source balance)

### Budgets
- `POST /api/budgets` — Create or update budget (upsert by person + type)
- `GET /api/budgets?personName=...` — List budgets for a person
- `DELETE /api/budgets/{id}` — Delete budget

### Money Sources
- `POST /api/money-sources` — Create money source
- `GET /api/money-sources?personName=...` — List money sources
- `PATCH /api/money-sources/{id}` — Update money source
- `DELETE /api/money-sources/{id}` — Delete (only if no movements)
- `POST /api/money-sources/{id}/deposit` — Register deposit
- `GET /api/money-sources/{id}/movements` — Movement history (paginated)

## Configuration

| Variable | Default |
|---|---|
| Port | 3002 |
| Database | `./gastos.db` (SQLite) |
| Timezone | `America/Bogota` |
| CORS | Open (all origins) |
| Upload dir | `./uploads/` |

## Timezone Handling

Pass timezone via query param `?tz=America/Bogota` or header `X-Timezone`. Defaults to `America/Bogota`.
