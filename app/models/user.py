# backend/app/models/user.py
from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship
from app.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    is_adman = Column(String, default="user")  # "user" or "admin"
    phone_number = Column(String, nullable=True)
    DOB = Column(String, nullable=True)
    image_url = Column(String, nullable=True)

    # relationships - using string reference to avoid circular imports
    appointments = relationship("Appointment", back_populates="user", lazy="dynamic")
