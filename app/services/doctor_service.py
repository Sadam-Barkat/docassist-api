# backend/app/services/doctor_service.py
from typing import List, Optional
from app.models.doctor import Doctor
from app.schemas.doctor_schema import DoctorCreate, DoctorUpdate


async def create_doctor(db, doctor_in: DoctorCreate) -> Doctor:
    doctor = Doctor(**doctor_in.dict())
    db.add(doctor)
    db.commit()
    db.refresh(doctor)
    return doctor


async def get_doctor_by_id(db, doctor_id: int) -> Optional[Doctor]:
    return db.query(Doctor).filter(Doctor.id == doctor_id).first()


async def list_doctors_by_specialty(db, specialty: Optional[str] = None) -> List[Doctor]:
    query = db.query(Doctor)
    if specialty:
        query = query.filter(Doctor.specialty.ilike(f"%{specialty}%"))
    return query.all()


async def find_doctors_by_query(db, query: str) -> List[Doctor]:
    return (
        db.query(Doctor)
        .filter(
            (Doctor.name.ilike(f"%{query}%")) | (Doctor.specialty.ilike(f"%{query}%"))
        )
        .all()
    )


async def update_doctor(db, doctor_id: int, update_data: DoctorUpdate) -> Optional[Doctor]:
    doctor = await get_doctor_by_id(db, doctor_id)
    if not doctor:
        return None
    for field, value in update_data.dict(exclude_unset=True).items():
        setattr(doctor, field, value)
    db.commit()
    db.refresh(doctor)
    return doctor


async def delete_doctor(db, doctor_id: int) -> bool:
    doctor = await get_doctor_by_id(db, doctor_id)
    if not doctor:
        return False
    db.delete(doctor)
    db.commit()
    return True
