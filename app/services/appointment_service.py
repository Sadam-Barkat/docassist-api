# backend/app/services/appointment_service.py
from typing import List, Optional
from app.models.appointment import Appointment
from app.schemas.appointment_schema import AppointmentCreate


async def create_appointment_for_user(
    db, user_id: int, doctor_id: int, date: str, time: str, reason: str
) -> Optional[Appointment]:
    appointment = Appointment(
        user_id=user_id,
        doctor_id=doctor_id,
        date=date,
        time=time,
        reason=reason,
        status="booked",
    )
    db.add(appointment)
    db.commit()
    db.refresh(appointment)
    return appointment


async def get_appointment_by_id(db, appointment_id: int) -> Optional[Appointment]:
    return db.query(Appointment).filter(Appointment.id == appointment_id).first()


async def list_user_appointments(db, user_id: int) -> List[Appointment]:
    return db.query(Appointment).filter(Appointment.user_id == user_id).all()


async def list_all_appointments(db) -> List[Appointment]:
    return db.query(Appointment).all()


async def cancel_appointment(db, appointment_id: int) -> bool:
    appointment = await get_appointment_by_id(db, appointment_id)
    if not appointment:
        return False
    appointment.status = "cancelled"
    db.commit()
    db.refresh(appointment)
    return True
