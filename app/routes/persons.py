from fastapi import APIRouter, Depends

from app.dependencies.containers import get_person_service
from app.schemas.person import PersonCreate, PersonUpdate
from app.services.person_service import PersonService

router = APIRouter(prefix="/api/persons", tags=["Personas"])


@router.get("", summary="Listar todas las personas")
def list_persons(service: PersonService = Depends(get_person_service)):
    """Retorna todas las personas registradas ordenadas alfabéticamente."""
    return service.list_persons()


@router.get("/{person_id}", summary="Obtener persona por ID")
def get_person(person_id: int, service: PersonService = Depends(get_person_service)):
    """Retorna una persona específica por su ID."""
    return service.get_person(person_id)


@router.post("", status_code=201, summary="Crear persona")
def create_person(data: PersonCreate, service: PersonService = Depends(get_person_service)):
    """Crea una nueva persona. El nombre debe ser único."""
    return service.create_person(data)


@router.put("/{person_id}", summary="Actualizar persona")
def update_person(
    person_id: int,
    data: PersonUpdate,
    service: PersonService = Depends(get_person_service),
):
    """Actualiza el nombre de una persona existente."""
    return service.update_person(person_id, data)


@router.delete("/{person_id}", summary="Eliminar persona")
def delete_person(person_id: int, service: PersonService = Depends(get_person_service)):
    """Elimina una persona del sistema."""
    return service.delete_person(person_id)
