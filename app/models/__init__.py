# backend/app/models/__init__.py
# Import all models to ensure they are registered with SQLAlchemy
from .user import User
from .doctor import Doctor
from .appointment import Appointment

# Make models available at package level
__all__ = ["User", "Doctor", "Appointment"]
