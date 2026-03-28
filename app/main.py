import os

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.database import Base, engine
from app.routes import budgets, expenses, money_sources, persons

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Gastos App API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

uploads_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "uploads")
os.makedirs(uploads_dir, exist_ok=True)
app.mount("/uploads", StaticFiles(directory=uploads_dir), name="uploads")

app.include_router(persons.router)
app.include_router(expenses.router)
app.include_router(money_sources.router)
app.include_router(budgets.router)


@app.get("/")
def root():
    return {"message": "Gastos App API running"}


if __name__ == "__main__":
    uvicorn.run("app.main:app", host="0.0.0.0", port=3002, reload=True)
