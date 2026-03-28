from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.controllers import person_controller
from app.database import get_db
from app.schemas.person import PersonCreate, PersonOut

router = APIRouter(prefix="/api/persons", tags=["Persons"])


@router.post("/", response_model=PersonOut, status_code=201)
def create_person(data: PersonCreate, db: Session = Depends(get_db)):
    """Create a new person."""
    person = person_controller.create_person(db, data)
    return person


@router.get("/", response_model=list[PersonOut])
def list_persons(db: Session = Depends(get_db)):
    """List all persons sorted alphabetically."""
    return person_controller.list_persons(db)
