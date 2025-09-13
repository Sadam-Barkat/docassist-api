# backend/app/schemas/appointment_schema.py
from pydantic import BaseModel
from typing import Optional
from datetime import date, time


class AppointmentBase(BaseModel):
    doctor_id: int
    date: date
    time: time
    reason: Optional[str] = None


class AppointmentCreate(AppointmentBase):
    pass


class AppointmentOut(AppointmentBase):
    id: int
    user_id: int
    status: str
    paid: bool
    stripe_payment_id: Optional[str] = None

    class Config:
        from_attributes = True

