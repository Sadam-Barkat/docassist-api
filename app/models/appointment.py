# backend/app/models/appointment.py
from sqlalchemy import Column, Integer, String, ForeignKey, Date, Time, Boolean
from sqlalchemy.orm import relationship
from app.database import Base


class Appointment(Base):
    __tablename__ = "appointments"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    doctor_id = Column(Integer, ForeignKey("doctors.id"), nullable=False)
    date = Column(Date, nullable=False)
    time = Column(Time, nullable=False)
    reason = Column(String, nullable=True)
    status = Column(String, default="booked")  # booked, cancelled, completed
    paid = Column(Boolean, default=False)
    stripe_payment_id = Column(String, nullable=True)

    # relationships
    user = relationship("User", back_populates="appointments")
    doctor = relationship("Doctor", back_populates="appointments")
