from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.appointment import Appointment
from app.models.doctor import Doctor
from .users import get_current_user
import stripe
import os
from dotenv import load_dotenv

load_dotenv()
# Set Stripe API key
stripe.api_key = os.getenv("STRIPE_API_KEY")

# Webhook secret for verifying Stripe webhooks
STRIPE_WEBHOOK_SECRET = os.getenv("STRIPE_WEBHOOK_SECRET", "")

router = APIRouter(prefix="/payments", tags=["Payments"])

@router.post("/webhook")
def stripe_webhook(request: Request, db: Session = Depends(get_db)):
    """Handle Stripe webhook events"""
    payload = request.body()
    sig_header = request.headers.get('stripe-signature')
    
    # For development, skip webhook signature verification
    if STRIPE_WEBHOOK_SECRET and STRIPE_WEBHOOK_SECRET != "whsec_test_webhook_secret_here":
        try:
            event = stripe.Webhook.construct_event(
                payload, sig_header, STRIPE_WEBHOOK_SECRET
            )
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid payload")
        except stripe.error.SignatureVerificationError:
            raise HTTPException(status_code=400, detail="Invalid signature")
    else:
        # For development without webhook endpoint, parse payload directly
        import json
        try:
            event = json.loads(payload)
        except json.JSONDecodeError:
            raise HTTPException(status_code=400, detail="Invalid JSON payload")
    
    print(f"Webhook received event: {event.get('type', 'unknown')}")
    
    # Handle successful payment - CREATE appointment only after payment
    if event['type'] == 'checkout.session.completed':
        session = event['data']['object']
        metadata = session.get('metadata', {})
        
        print(f"Processing payment completion for session: {session.get('id')}")
        print(f"Metadata: {metadata}")
        
        # Create appointment from metadata
        if metadata:
            from app.models.appointment import Appointment
            from app.utils.email_service import send_email, create_appointment_email
            
            try:
                appointment = Appointment(
                    user_id=int(metadata['user_id']),
                    doctor_id=int(metadata['doctor_id']),
                    date=metadata['date'],
                    time=metadata['time'],
                    reason=metadata['reason'],
                    status="confirmed",
                    paid=True,
                    stripe_payment_id=session['id']
                )
                
                db.add(appointment)
                db.commit()
                db.refresh(appointment)
                
                print(f"Appointment created successfully: ID {appointment.id}")
                
                # Send confirmation email
                email_body = create_appointment_email(
                    user_name=metadata['user_name'],
                    doctor_name=metadata['doctor_name'],
                    specialty=metadata['doctor_specialty'],
                    date=metadata['date'],
                    time=metadata['time'],
                    reason=metadata['reason']
                )
                
                send_email(
                    to_email=metadata['user_email'],
                    subject="Appointment Confirmed - HealthCare+",
                    body=email_body
                )
                
                print(f"Confirmation email sent to: {metadata['user_email']}")
                
            except Exception as e:
                print(f"Error creating appointment: {str(e)}")
                db.rollback()
                raise HTTPException(status_code=500, detail=f"Failed to create appointment: {str(e)}")
        else:
            print("No metadata found in session")
    
    return {"status": "success"}

@router.get("/verify/{session_id}")
def verify_payment(
    session_id: str,
    db: Session = Depends(get_db)
):
    """Verify payment status from Stripe - No auth required for post-payment verification"""
    try:
        session = stripe.checkout.Session.retrieve(session_id)
        
        # Find appointment by session ID
        appointment = db.query(Appointment).filter(
            Appointment.stripe_payment_id == session_id
        ).first()
        
        if not appointment and session.payment_status == "paid":
            # Payment successful but no appointment - create it now (webhook simulation)
            metadata = session.metadata
            
            if metadata:
                from app.utils.email_service import send_email, create_appointment_email
                
                try:
                    appointment = Appointment(
                        user_id=int(metadata['user_id']),
                        doctor_id=int(metadata['doctor_id']),
                        date=metadata['date'],
                        time=metadata['time'],
                        reason=metadata['reason'],
                        status="confirmed",
                        paid=True,
                        stripe_payment_id=session_id
                    )
                    
                    db.add(appointment)
                    db.commit()
                    db.refresh(appointment)
                    
                    # Send confirmation email
                    email_body = create_appointment_email(
                        user_name=metadata['user_name'],
                        doctor_name=metadata['doctor_name'],
                        specialty=metadata['doctor_specialty'],
                        date=metadata['date'],
                        time=metadata['time'],
                        reason=metadata['reason']
                    )
                    
                    send_email(
                        to_email=metadata['user_email'],
                        subject="Appointment Confirmed - HealthCare+",
                        body=email_body
                    )
                    
                except Exception as e:
                    print(f"Error creating appointment: {str(e)}")
                    db.rollback()
        
        if not appointment:
            return {
                "payment_status": session.payment_status,
                "appointment_paid": False,
                "appointment_status": "not_found",
                "message": "Payment successful but appointment creation failed."
            }
        
        # Update appointment if payment successful
        if session.payment_status == "paid" and not appointment.paid:
            appointment.paid = True
            appointment.status = "confirmed"
            db.commit()
            db.refresh(appointment)
        
        return {
            "payment_status": session.payment_status,
            "appointment_paid": appointment.paid,
            "appointment_status": appointment.status
        }
    except stripe.error.StripeError as e:
        raise HTTPException(status_code=400, detail=f"Stripe error: {str(e)}")
