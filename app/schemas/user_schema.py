# backend/app/schemas/user_schema.py
from pydantic import BaseModel, EmailStr
from typing import Optional


class UserBase(BaseModel):
    name: str
    email: EmailStr


class UserCreate(UserBase):
    password: str
    phone_number: Optional[str] = None
    DOB: Optional[str] = None


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[EmailStr] = None
    phone_number: Optional[str] = None
    DOB: Optional[str] = None
    image_url: Optional[str] = None


class UserOut(UserBase):
    id: int
    is_adman: str  # Changed from bool to str since it stores "admin" or "user"
    phone_number: Optional[str] = None
    DOB: Optional[str] = None
    image_url: Optional[str] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None

    class Config:
        from_attributes = True

