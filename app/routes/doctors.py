from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.doctor import Doctor
from app.schemas.doctor_schema import DoctorOut, DoctorCreate, DoctorUpdate, DoctorCreateForm
from app.routes.users import get_current_user
from app.models.user import User
import os
import uuid
from pathlib import Path

router = APIRouter(prefix="/doctors", tags=["Doctors"])


# Public routes (no auth required)
@router.get("/", response_model=list[DoctorOut])
def list_doctors(db: Session = Depends(get_db)):
    return db.query(Doctor).all()


@router.get("/{doctor_id}", response_model=DoctorOut)
def get_doctor(doctor_id: int, db: Session = Depends(get_db)):
    doctor = db.query(Doctor).filter(Doctor.id == doctor_id).first()
    if not doctor:
        raise HTTPException(status_code=404, detail="Doctor not found")
    return doctor


# Admin-only routes
@router.post("/", response_model=DoctorOut)
def create_doctor(
    form_data: DoctorCreateForm = Depends(),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Check if user is admin
    if current_user.is_adman != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    
    # Handle image upload
    image_url = None
    if form_data.image:
        # Create uploads directory if it doesn't exist
        upload_dir = Path("uploads/doctor_images")
        upload_dir.mkdir(parents=True, exist_ok=True)
        
        # Generate unique filename
        file_extension = form_data.image.filename.split(".")[-1] if "." in form_data.image.filename else "jpg"
        unique_filename = f"{uuid.uuid4()}.{file_extension}"
        file_path = upload_dir / unique_filename
        
        # Save the file
        with open(file_path, "wb") as buffer:
            content = form_data.image.file.read()
            buffer.write(content)
        
        # Store relative URL
        image_url = f"/uploads/doctor_images/{unique_filename}"
    
    # Create doctor with validated data
    doctor_data = {
        "name": form_data.name,
        "specialty": form_data.specialty,
        "fee": form_data.fee,
        "bio": form_data.bio,
        "image_url": image_url
    }
    
    new_doc = Doctor(**doctor_data)
    db.add(new_doc)
    db.commit()
    db.refresh(new_doc)
    return new_doc


@router.put("/{doctor_id}", response_model=DoctorOut)
def update_doctor(
    doctor_id: int,
    doctor_update: DoctorUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Check if user is admin
    if current_user.is_adman != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    
    doctor = db.query(Doctor).filter(Doctor.id == doctor_id).first()
    if not doctor:
        raise HTTPException(status_code=404, detail="Doctor not found")
    
    # Update only provided fields
    update_data = doctor_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(doctor, field, value)
    
    db.commit()
    db.refresh(doctor)
    return doctor


@router.delete("/{doctor_id}")
def delete_doctor(
    doctor_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Check if user is admin
    if current_user.is_adman != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    
    doctor = db.query(Doctor).filter(Doctor.id == doctor_id).first()
    if not doctor:
        raise HTTPException(status_code=404, detail="Doctor not found")
    
    db.delete(doctor)
    db.commit()
    return {"message": f"Doctor {doctor.name} deleted successfully"}
