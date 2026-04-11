from fastapi import APIRouter

from app.schemas.person import PersonCreate, PersonUpdate
from app.services.person_service import PersonService

router = APIRouter(prefix="/api/persons", tags=["Personas"])


@router.get("", summary="Listar todas las personas")
def list_persons():
    """Retorna todas las personas registradas ordenadas alfabéticamente."""
    return PersonService.list_persons()


@router.get("/{person_id}", summary="Obtener persona por ID")
def get_person(person_id: int):
    """Retorna una persona específica por su ID."""
    return PersonService.get_person(person_id)


@router.post("", status_code=201, summary="Crear persona")
def create_person(data: PersonCreate):
    """Crea una nueva persona. El nombre debe ser único."""
    return PersonService.create_person(data)


@router.put("/{person_id}", summary="Actualizar persona")
def update_person(person_id: int, data: PersonUpdate):
    """Actualiza el nombre de una persona existente."""
    return PersonService.update_person(person_id, data)


@router.delete("/{person_id}", summary="Eliminar persona")
def delete_person(person_id: int):
    """Elimina una persona del sistema."""
    return PersonService.delete_person(person_id)
