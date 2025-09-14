# backend/app/routes/appointments.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.appointment import Appointment
from app.models.doctor import Doctor
from app.schemas.appointment_schema import AppointmentCreate, AppointmentOut
from app.utils.email_service import send_email, create_appointment_email
import stripe
import os
from .users import get_current_user
from dotenv import load_dotenv

load_dotenv() 

# Set Stripe API key
stripe.api_key = os.getenv("STRIPE_API_KEY")
router = APIRouter(prefix="/appointments", tags=["Appointments"])

SUCCESS_URL = "https://docassist-web.vercel.app/appointments/success"
CANCEL_URL = "https://docassist-web.vercel.app/appointments/cancel"

@router.post("/")
def book_appointment(
    data: AppointmentCreate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    """Create Stripe checkout session for appointment booking - no appointment created until payment"""
    # Validate appointment date - must be today or future
    from datetime import date as date_type
    today = date_type.today()
    
    if data.date < today:
        raise HTTPException(
            status_code=400, 
            detail=f"Invalid date. Please select a date from today ({today.strftime('%Y-%m-%d')}) onwards. You cannot book appointments for past dates."
        )
    
    doctor = db.query(Doctor).filter(Doctor.id == data.doctor_id).first()
    if not doctor:
        raise HTTPException(status_code=404, detail="Doctor not found")
    
    # Check if user already has a pending/confirmed appointment with this doctor
    from app.models.appointment import Appointment
    existing_appointment = db.query(Appointment).filter(
        Appointment.user_id == current_user.id,
        Appointment.doctor_id == data.doctor_id,
        Appointment.status.in_(["scheduled", "confirmed"])
    ).first()
    
    if existing_appointment:
        raise HTTPException(
            status_code=400, 
            detail=f"You already have an appointment with Dr. {doctor.name}. Please cancel your existing appointment before booking a new one."
        )

    # Store appointment data in session metadata for later creation
    appointment_metadata = {
        "user_id": str(current_user.id),
        "user_name": current_user.name,
        "user_email": current_user.email,
        "doctor_id": str(doctor.id),
        "doctor_name": doctor.name,
        "doctor_specialty": doctor.specialty,
        "date": str(data.date),
        "time": str(data.time),
        "reason": data.reason,
    }

    # Create Stripe checkout session
    try:
        checkout_session = stripe.checkout.Session.create(
            payment_method_types=['card'],
            line_items=[{
                'price_data': {
                    'currency': 'usd',
                    'product_data': {
                        'name': f'Appointment with Dr. {doctor.name}',
                        'description': f'{doctor.specialty} consultation on {data.date} at {data.time}',
                    },
                    'unit_amount': int(float(doctor.fee.replace("$", "").replace(",", "")) * 100),
                },
                'quantity': 1,
            }],
            mode='payment',
            success_url=f"{os.getenv('FRONTEND_URL', 'https://docassist-web.vercel.app')}/appointments/success?session_id={{CHECKOUT_SESSION_ID}}",
            cancel_url=f"{os.getenv('FRONTEND_URL', 'https://docassist-web.vercel.app')}/appointments/cancel",
            metadata=appointment_metadata
        )

        
        return {"checkout_url": checkout_session.url}
    except Exception as e:
        print(f"Stripe error details: {str(e)}")
        print(f"Doctor fee value: {doctor.fee}")
        print(f"Appointment metadata: {appointment_metadata}")
        raise HTTPException(status_code=400, detail=f"Payment session creation failed: {str(e)}")


# Remove payment success/cancel routes - handled in payments.py



@router.get("/", response_model=list[AppointmentOut])
def list_my_appointments(db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    return db.query(Appointment).filter(Appointment.user_id == current_user.id).all()


@router.get("/all", response_model=list[AppointmentOut])
def list_all_appointments(db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    if not getattr(current_user, "is_adman", False) and current_user.is_adman != "admin":
        raise HTTPException(status_code=403, detail="Not authorized")
    return db.query(Appointment).all()


@router.post("/{appointment_id}/cancel", response_model=AppointmentOut)
def cancel_appointment(appointment_id: int, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    appointment = db.query(Appointment).filter(Appointment.id == appointment_id).first()
    if not appointment:
        raise HTTPException(status_code=404, detail="Appointment not found")

    if appointment.user_id != current_user.id and not (getattr(current_user, "is_adman", False) or current_user.is_adman == "admin"):
        raise HTTPException(status_code=403, detail="Not authorized to cancel this appointment")

    appointment.status = "cancelled"
    db.commit()
    db.refresh(appointment)
    return appointment
