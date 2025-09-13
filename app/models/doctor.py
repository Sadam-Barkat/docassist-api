# backend/app/models/doctor.py
from sqlalchemy import Column, Integer, String, Text
from sqlalchemy.orm import relationship
from app.database import Base


class Doctor(Base):
    __tablename__ = "doctors"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    specialty = Column(String, nullable=False)
    bio = Column(Text, nullable=True)
    image_url = Column(String, nullable=True)
    fee = Column(String, nullable=False)

    # relationships - using string reference to avoid circular imports
    appointments = relationship("Appointment", back_populates="doctor", lazy="dynamic")
