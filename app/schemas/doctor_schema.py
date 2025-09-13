# backend/app/schemas/doctor_schema.py
from pydantic import BaseModel
from typing import Optional
from fastapi import Form, UploadFile, File


class DoctorBase(BaseModel):
    name: str
    specialty: str
    bio: Optional[str] = None
    image_url: Optional[str] = None
    fee: str


class DoctorCreate(DoctorBase):
    pass


class DoctorCreateForm:
    def __init__(
        self,
        name: str = Form(...),
        specialty: str = Form(...),
        fee: str = Form(...),
        bio: Optional[str] = Form(None),
        image: Optional[UploadFile] = File(None)
    ):
        self.name = name
        self.specialty = specialty
        self.fee = fee
        self.bio = bio
        self.image = image


class DoctorUpdate(BaseModel):
    name: Optional[str] = None
    specialty: Optional[str] = None
    bio: Optional[str] = None
    image_url: Optional[str] = None
    fee: Optional[str] = None


class DoctorOut(DoctorBase):
    id: int

    class Config:
        from_attributes = True

