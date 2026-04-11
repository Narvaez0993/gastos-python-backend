from fastapi import HTTPException
from sqlite3 import IntegrityError

from app.dao.person_dao import PersonDAO


class PersonService:

    @staticmethod
    def list_persons():
        return PersonDAO.get_all()

    @staticmethod
    def get_person(person_id):
        person = PersonDAO.get_by_id(person_id)
        if not person:
            raise HTTPException(status_code=404, detail="Persona no encontrada")
        return person

    @staticmethod
    def create_person(data):
        name = data.name.strip()
        if not name:
            raise HTTPException(status_code=400, detail="El nombre es requerido")

        existing = PersonDAO.get_by_name(name)
        if existing:
            raise HTTPException(status_code=409, detail="La persona ya existe")

        return PersonDAO.create(name)

    @staticmethod
    def update_person(person_id, data):
        person = PersonDAO.get_by_id(person_id)
        if not person:
            raise HTTPException(status_code=404, detail="Persona no encontrada")

        name = data.name.strip()
        if not name:
            raise HTTPException(status_code=400, detail="El nombre es requerido")

        existing = PersonDAO.get_by_name(name)
        if existing and existing["id"] != person_id:
            raise HTTPException(status_code=409, detail="Ya existe una persona con ese nombre")

        return PersonDAO.update(person_id, name)

    @staticmethod
    def delete_person(person_id):
        person = PersonDAO.get_by_id(person_id)
        if not person:
            raise HTTPException(status_code=404, detail="Persona no encontrada")

        deleted = PersonDAO.delete(person_id)
        if not deleted:
            raise HTTPException(
                status_code=400,
                detail="No se puede eliminar la persona porque tiene gastos, presupuestos o fuentes de dinero asociadas",
            )
        return {"message": "Persona eliminada"}
