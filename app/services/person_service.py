from fastapi import HTTPException

from app.repositories.interfaces.person_repository import IPersonRepository


class PersonService:
    """Lógica de negocio para personas. Depende de IPersonRepository (no de implementación)."""

    def __init__(self, person_repo: IPersonRepository):
        self.person_repo = person_repo

    def list_persons(self):
        return self.person_repo.get_all()

    def get_person(self, person_id):
        person = self.person_repo.get_by_id(person_id)
        if not person:
            raise HTTPException(status_code=404, detail="Persona no encontrada")
        return person

    def create_person(self, data):
        name = data.name.strip()
        if not name:
            raise HTTPException(status_code=400, detail="El nombre es requerido")

        existing = self.person_repo.get_by_name(name)
        if existing:
            raise HTTPException(status_code=409, detail="La persona ya existe")

        return self.person_repo.create(name)

    def update_person(self, person_id, data):
        person = self.person_repo.get_by_id(person_id)
        if not person:
            raise HTTPException(status_code=404, detail="Persona no encontrada")

        name = data.name.strip()
        if not name:
            raise HTTPException(status_code=400, detail="El nombre es requerido")

        existing = self.person_repo.get_by_name(name)
        if existing and existing["id"] != person_id:
            raise HTTPException(status_code=409, detail="Ya existe una persona con ese nombre")

        return self.person_repo.update(person_id, name)

    def delete_person(self, person_id):
        person = self.person_repo.get_by_id(person_id)
        if not person:
            raise HTTPException(status_code=404, detail="Persona no encontrada")

        deleted = self.person_repo.delete(person_id)
        if not deleted:
            raise HTTPException(
                status_code=400,
                detail="No se puede eliminar la persona porque tiene gastos, presupuestos o fuentes de dinero asociadas",
            )
        return {"message": "Persona eliminada"}
