import json
from typing import Optional
from agents import function_tool, RunContextWrapper
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.user import User
from app.models.doctor import Doctor
from app.models.appointment import Appointment
from app.services.doctor_service import get_doctor_by_id, list_doctors_by_specialty
from app.services.appointment_service import create_appointment_for_user
from app.utils.email_service import create_appointment_email, send_email
from datetime import datetime, timedelta, date
import calendar


# ==================== DASHBOARD TOOLS ====================

@function_tool
async def show_dashboard(ctx: RunContextWrapper[dict]) -> str:
    """Redirect to dashboard page."""
    user_id = ctx.context.get("user_id")
    if not user_id:
        return json.dumps({
            "type": "navigation_response",
            "success": False,
            "message": "Please log in first.",
            "navigation": {"action": "navigate", "path": "/login", "delay_ms": 500}
        })

    db: Session = next(get_db())
    try:
        user = db.query(User).filter(User.id == user_id).first()
        dashboard_path = "/dashboard"
        
        return json.dumps({
            "type": "navigation_response",
            "success": True,
            "message": "Opening your dashboard...",
            "navigation": {"action": "navigate", "path": dashboard_path, "delay_ms": 200}
        })
    finally:
        db.close()


@function_tool
async def show_admin_dashboard(ctx: RunContextWrapper[dict]) -> str:
    """Redirect to admin dashboard page."""
    user_id = ctx.context.get("user_id")
    if not user_id:
        return json.dumps({
            "type": "navigation_response",
            "success": False,
            "message": "Please log in first.",
            "navigation": {"action": "navigate", "path": "/login", "delay_ms": 500}
        })

    db: Session = next(get_db())
    try:
        user = db.query(User).filter(User.id == user_id).first()
        if not user or user.is_adman != "admin":
            return json.dumps({
                "type": "message_response",
                "success": False,
                "message": "Admin access required."
            })
        
        return json.dumps({
            "type": "navigation_response",
            "success": True,
            "message": "Opening admin dashboard...",
            "navigation": {"action": "navigate", "path": "/admin", "delay_ms": 200}
        })
    finally:
        db.close()


# ==================== DOCTORS TOOLS ====================

@function_tool
async def show_doctors(ctx: RunContextWrapper[dict], specialty: Optional[str] = None) -> str:
    """Show doctors list in chatbot AND redirect to doctors page."""
    db: Session = next(get_db())
    try:
        # Get all doctors directly from database
        doctors = db.query(Doctor).all()
        
        if not doctors:
            return json.dumps({
                "type": "navigation_response",
                "success": True,
                "message": "No doctors found. Redirecting to doctors page...",
                "navigation": {"action": "navigate", "path": "/doctors", "delay_ms": 200}
            })
        
        message = "🩺 **Available Doctors:**\n\n"
        for doctor in doctors:
            message += f"• **Dr. {doctor.name}**\n"
            message += f"  Specialty: {doctor.specialty}\n"
            if doctor.fee:
                message += f"  Fee: ${doctor.fee}\n"
            message += "\n"
        
        message += "Opening doctors page for more details..."
        
        return json.dumps({
            "type": "navigation_response",
            "success": True,
            "message": message,
            "data": {"doctors": [{"id": d.id, "name": d.name, "specialty": d.specialty, "fee": d.fee} for d in doctors]},
            "navigation": {"action": "navigate", "path": "/doctors", "delay_ms": 300}
        })
    except Exception as e:
        print(f"Error in show_doctors: {e}")
        return json.dumps({
            "type": "message_response",
            "success": False,
            "message": f"Error fetching doctors: {str(e)}"
        })
    finally:
        db.close()


# ==================== APPOINTMENTS TOOLS ====================

@function_tool
async def show_appointments(ctx: RunContextWrapper[dict]) -> str:
    """Show appointments list in chatbot AND redirect to appointments page."""
    user_id = ctx.context.get("user_id")
    if not user_id:
        return json.dumps({
            "type": "navigation_response",
            "success": False,
            "message": "Please log in first.",
            "navigation": {"action": "navigate", "path": "/login", "delay_ms": 500}
        })

    db: Session = next(get_db())
    try:
        appointments = db.query(Appointment).filter(Appointment.user_id == user_id).all()
        
        if not appointments:
            return json.dumps({
                "type": "navigation_response",
                "success": True,
                "message": "You have no appointments. Opening appointments page...",
                "navigation": {"action": "navigate", "path": "/appointments", "delay_ms": 200}
            })
        
        message = "📅 **Your Appointments:**\n\n"
        for apt in appointments:
            doctor = db.query(Doctor).filter(Doctor.id == apt.doctor_id).first()
            doctor_name = doctor.name if doctor else "Unknown Doctor"
            message += f"• **{apt.date} at {apt.time}**\n"
            message += f"  Doctor: Dr. {doctor_name}\n"
            message += f"  Status: {apt.status.title()}\n\n"
        
        message += "Opening appointments page for more details..."
        
        return json.dumps({
            "type": "navigation_response",
            "success": True,
            "message": message,
            "navigation": {"action": "navigate", "path": "/appointments", "delay_ms": 300}
        })
    finally:
        db.close()


# ==================== PROFILE TOOLS ====================

@function_tool
async def show_profile(ctx: RunContextWrapper[dict]) -> str:
    """Redirect to profile page."""
    user_id = ctx.context.get("user_id")
    if not user_id:
        return json.dumps({
            "type": "navigation_response",
            "success": False,
            "message": "Please log in first.",
            "navigation": {"action": "navigate", "path": "/login", "delay_ms": 500}
        })
    
    return json.dumps({
        "type": "navigation_response",
        "success": True,
        "message": "Opening your profile...",
        "navigation": {"action": "navigate", "path": "/profile", "delay_ms": 200}
    })


# ==================== BOOKING TOOLS (CHATBOT ONLY) ====================

@function_tool
async def book_appointment(ctx: RunContextWrapper[dict], doctor_id: int, date: str, time: str, reason: Optional[str] = None) -> str:
    """Complete appointment booking with payment."""
    user_id = ctx.context.get("user_id")
    if not user_id:
        return json.dumps({
            "type": "message_response",
            "success": False,
            "message": "Please log in to book an appointment."
        })

    db: Session = next(get_db())
    try:
        # Debug logging
        print(f"DEBUG: Looking for doctor_id: {doctor_id}")
        print(f"DEBUG: User ID: {user_id}, Date: {date}, Time: {time}")
        
        # Find doctor by ID
        doctor = db.query(Doctor).filter(Doctor.id == doctor_id).first()
        print(f"DEBUG: Doctor found: {doctor}")
        if not doctor:
            return json.dumps({
                "type": "message_response",
                "success": False,
                "message": "❌ **Doctor Not Found** - Please select a doctor from the available list. Would you like me to show you the available doctors?"
            })
        
        # Check for duplicate appointment
        from app.models.appointment import Appointment
        existing_appointment = db.query(Appointment).filter(
            Appointment.user_id == user_id,
            Appointment.doctor_id == doctor_id,
            Appointment.status.in_(["scheduled", "confirmed"])
        ).first()
        
        if existing_appointment:
            return json.dumps({
                "type": "message_response",
                "success": False,
                "message": f"❌ **Duplicate Appointment** - You already have an appointment with Dr. {doctor.name}. Please cancel your existing appointment before booking a new one."
            })
        
        # Validate and parse appointment date
        from datetime import datetime, date as date_type, timedelta
        import re

        try:
            lower_date = date.lower().strip()
            print(f"DEBUG: Original date input: '{date}', lower_date: '{lower_date}'")
            
            # Handle natural language dates
            if lower_date == "today":
                appointment_date = date_type.today()
                print(f"DEBUG: Parsed as today: {appointment_date}")
            elif lower_date == "tomorrow":
                appointment_date = date_type.today() + timedelta(days=1)
                print(f"DEBUG: Parsed as tomorrow: {appointment_date}")
            elif lower_date == "yesterday":
                return json.dumps({
                    "type": "message_response",
                    "success": False,
                    "message": "❌ **Invalid Date** - You cannot book appointments for past dates like yesterday."
                })
            elif "next" in lower_date:
                # Handle "next monday", "next week", etc.
                days_ahead = 7  # Default to next week
                if "monday" in lower_date:
                    days_ahead = (0 - date_type.today().weekday() + 7) % 7
                    if days_ahead == 0:
                        days_ahead = 7
                elif "tuesday" in lower_date:
                    days_ahead = (1 - date_type.today().weekday() + 7) % 7
                    if days_ahead == 0:
                        days_ahead = 7
                elif "wednesday" in lower_date:
                    days_ahead = (2 - date_type.today().weekday() + 7) % 7
                    if days_ahead == 0:
                        days_ahead = 7
                elif "thursday" in lower_date:
                    days_ahead = (3 - date_type.today().weekday() + 7) % 7
                    if days_ahead == 0:
                        days_ahead = 7
                elif "friday" in lower_date:
                    days_ahead = (4 - date_type.today().weekday() + 7) % 7
                    if days_ahead == 0:
                        days_ahead = 7
                elif "saturday" in lower_date:
                    days_ahead = (5 - date_type.today().weekday() + 7) % 7
                    if days_ahead == 0:
                        days_ahead = 7
                elif "sunday" in lower_date:
                    days_ahead = (6 - date_type.today().weekday() + 7) % 7
                    if days_ahead == 0:
                        days_ahead = 7
                
                appointment_date = date_type.today() + timedelta(days=days_ahead)
            elif any(day in lower_date for day in ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]):
                # Handle "this monday", "monday", etc.
                days_ahead = 0
                if "monday" in lower_date:
                    days_ahead = (0 - date_type.today().weekday()) % 7
                elif "tuesday" in lower_date:
                    days_ahead = (1 - date_type.today().weekday()) % 7
                elif "wednesday" in lower_date:
                    days_ahead = (2 - date_type.today().weekday()) % 7
                elif "thursday" in lower_date:
                    days_ahead = (3 - date_type.today().weekday()) % 7
                elif "friday" in lower_date:
                    days_ahead = (4 - date_type.today().weekday()) % 7
                elif "saturday" in lower_date:
                    days_ahead = (5 - date_type.today().weekday()) % 7
                elif "sunday" in lower_date:
                    days_ahead = (6 - date_type.today().weekday()) % 7
                
                # If the day has already passed this week, move to next week
                if days_ahead == 0 and date_type.today().weekday() != 0:  # Not Monday
                    days_ahead = 7
                
                appointment_date = date_type.today() + timedelta(days=days_ahead)
            else:
                # Try to parse as YYYY-MM-DD format
                appointment_date = datetime.strptime(date, "%Y-%m-%d").date()

            today = date_type.today()
            print(f"DEBUG: Parsed appointment_date: {appointment_date}, today: {today}")
            print(f"DEBUG: appointment_date < today: {appointment_date < today}")
            
            if appointment_date < today:
                return json.dumps({
                    "type": "message_response",
                    "success": False,
                    "message": f"❌ **Invalid Date** - Please select a date from today ({today.strftime('%Y-%m-%d')}) onwards."
                })
            
            # Convert to string YYYY-MM-DD for Stripe metadata and response
            parsed_date_str = appointment_date.strftime("%Y-%m-%d")

        except ValueError as ve:
            print(f"DEBUG: Date parsing error: {str(ve)}")
            return json.dumps({
                "type": "message_response",
                "success": False,
                "message": "❌ **Invalid Date Format** - Please provide date as 'today', 'tomorrow', 'next Monday', or YYYY-MM-DD format (e.g., 2025-01-15)."
            })
        except Exception as e:
            print(f"DEBUG: Unexpected error in date parsing: {str(e)}")
            return json.dumps({
                "type": "message_response",
                "success": False,
                "message": f"❌ **Date Processing Error** - {str(e)}"
            })

        # Stripe payment setup
        import stripe
        from dotenv import load_dotenv
        import os
        load_dotenv() 

        stripe.api_key = os.getenv("STRIPE_API_KEY")
        
        try:
            checkout_session = stripe.checkout.Session.create(
                payment_method_types=['card'],
                line_items=[{
                    'price_data': {
                        'currency': 'usd',
                        'product_data': {
                            'name': f'Appointment with Dr. {doctor.name}',
                            'description': f'{doctor.specialty} - {parsed_date_str} at {time}',
                        },
                        'unit_amount': int(float(doctor.fee or "100") * 100),
                    },
                    'quantity': 1,
                }],
                mode='payment',
                success_url=f"{os.getenv('FRONTEND_URL', 'https://docassist-web.vercel.app')}/appointments/success?session_id={{CHECKOUT_SESSION_ID}}",
                cancel_url=f"{os.getenv('FRONTEND_URL', 'https://docassist-web.vercel.app')}/appointments/cancel",
                metadata={
                    'user_id': str(user_id),
                    'doctor_id': str(doctor_id),
                    'date': parsed_date_str,
                    'time': time,
                    'reason': reason or '',
                    'user_name': ctx.context.get("name", ""),
                    'user_email': ctx.context.get("email", ""),
                    'doctor_name': doctor.name,
                    'doctor_specialty': doctor.specialty
                }
            )
            
            return json.dumps({
                "type": "payment_redirect",
                "success": True,
                "message": "💳 **Pay Now** - Redirecting to secure payment...",
                "payment_url": checkout_session.url,
                "appointment_details": {
                    "doctor": doctor.name,
                    "specialty": doctor.specialty,
                    "date": parsed_date_str,
                    "time": time,
                    "fee": float(doctor.fee or "100")
                }
            })
            
        except stripe.error.StripeError as e:
            print(f"DEBUG: Stripe error: {str(e)}")
            return json.dumps({
                "type": "message_response",
                "success": False,
                "message": f"Payment setup failed: {str(e)}"
            })
        except Exception as e:
            print(f"DEBUG: General error in book_appointment: {str(e)}")
            import traceback
            print(f"DEBUG: Full traceback: {traceback.format_exc()}")
            return json.dumps({
                "type": "message_response",
                "success": False,
                "message": f"An error occurred while booking your appointment: {str(e)}"
            })
        
    except Exception as e:
        print(f"DEBUG: Outer exception in book_appointment: {str(e)}")
        import traceback
        print(f"DEBUG: Full outer traceback: {traceback.format_exc()}")
        return json.dumps({
            "type": "message_response",
            "success": False,
            "message": "An error occurred while booking your appointment. Please try again."
        })
    finally:
        db.close()


# ==================== ADMIN USER MANAGEMENT ====================

@function_tool
async def show_users(ctx: RunContextWrapper[dict]) -> str:
    """Redirect to users management page (admin only)."""
    user_id = ctx.context.get("user_id")
    if not user_id:
        return json.dumps({
            "type": "navigation_response",
            "success": False,
            "message": "Please log in first.",
            "navigation": {"action": "navigate", "path": "/login", "delay_ms": 500}
        })

    db: Session = next(get_db())
    try:
        user = db.query(User).filter(User.id == user_id).first()
        if not user or user.is_adman != "admin":
            return json.dumps({
                "type": "message_response",
                "success": False,
                "message": "Admin access required."
            })
        
        return json.dumps({
            "type": "navigation_response",
            "success": True,
            "message": "Opening users management...",
            "navigation": {"action": "navigate", "path": "/admin", "delay_ms": 500}
        })
    finally:
        db.close()


@function_tool
async def delete_user(ctx: RunContextWrapper[dict], user_name: str) -> str:
    """Delete a user by name (admin only)."""
    admin_id = ctx.context.get("user_id")
    if not admin_id:
        return json.dumps({
            "type": "message_response",
            "success": False,
            "message": "Please log in first."
        })

    db: Session = next(get_db())
    try:
        admin = db.query(User).filter(User.id == admin_id).first()
        if not admin or admin.is_adman != "admin":
            return json.dumps({
                "type": "message_response",
                "success": False,
                "message": "Admin access required."
            })
        
        target_user = db.query(User).filter(User.name.ilike(f"%{user_name}%")).first()
        if not target_user:
            return json.dumps({
                "type": "message_response",
                "success": False,
                "message": f"User '{user_name}' not found."
            })
        
        if target_user.id == admin_id:
            return json.dumps({
                "type": "message_response",
                "success": False,
                "message": "You cannot delete your own account."
            })
        
        db.delete(target_user)
        db.commit()
        
        return json.dumps({
            "type": "message_response",
            "success": True,
            "message": f"✅ User '{target_user.name}' deleted successfully."
        })
    finally:
        db.close()


@function_tool
async def edit_user(ctx: RunContextWrapper[dict], user_name: str) -> str:
    """Redirect to edit user page (admin only)."""
    admin_id = ctx.context.get("user_id")
    if not admin_id:
        return json.dumps({
            "type": "navigation_response",
            "success": False,
            "message": "Please log in first.",
            "navigation": {"action": "navigate", "path": "/login", "delay_ms": 500}
        })

    db: Session = next(get_db())
    try:
        admin = db.query(User).filter(User.id == admin_id).first()
        if not admin or admin.is_adman != "admin":
            return json.dumps({
                "type": "message_response",
                "success": False,
                "message": "Admin access required."
            })
        
        target_user = db.query(User).filter(User.name.ilike(f"%{user_name}%")).first()
        if not target_user:
            return json.dumps({
                "type": "message_response",
                "success": False,
                "message": f"User '{user_name}' not found."
            })
        
        return json.dumps({
            "type": "navigation_response",
            "success": True,
            "message": f"Opening edit page for {target_user.name}...",
            "navigation": {"action": "navigate", "path": "/admin/", "delay_ms": 200}
        })
    finally:
        db.close()


@function_tool
async def update_user_profile(ctx: RunContextWrapper[dict], name: Optional[str] = None, email: Optional[str] = None, phone: Optional[str] = None, dob: Optional[str] = None) -> str:
    """Update user profile information."""
    user_id = ctx.context.get("user_id")
    if not user_id:
        return json.dumps({
            "type": "message_response",
            "success": False,
            "message": "Please log in first."
        })

    db: Session = next(get_db())
    try:
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            return json.dumps({
                "type": "message_response",
                "success": False,
                "message": "User not found."
            })
        
        updates = []
        if name:
            user.name = name
            updates.append("name")
        if email:
            user.email = email
            updates.append("email")
        if phone:
            user.phone_number = phone
            updates.append("phone")
        if dob:
            user.DOB = dob
            updates.append("date of birth")
        
        if updates:
            db.commit()
            return json.dumps({
                "type": "message_response",
                "success": True,
                "message": f"✅ Successfully updated: {', '.join(updates)}"
            })
        else:
            return json.dumps({
                "type": "message_response",
                "success": False,
                "message": "No updates provided."
            })
    finally:
        db.close()


# ==================== ADMIN DOCTOR MANAGEMENT ====================

@function_tool
async def add_doctor(ctx: RunContextWrapper[dict]) -> str:
    """Redirect to add doctor page (admin only)."""
    admin_id = ctx.context.get("user_id")
    if not admin_id:
        return json.dumps({
            "type": "navigation_response",
            "success": False,
            "message": "Please log in first.",
            "navigation": {"action": "navigate", "path": "/login", "delay_ms": 500}
        })

    db: Session = next(get_db())
    try:
        admin = db.query(User).filter(User.id == admin_id).first()
        if not admin or admin.is_adman != "admin":
            return json.dumps({
                "type": "message_response",
                "success": False,
                "message": "Admin access required."
            })
        
        return json.dumps({
            "type": "navigation_response",
            "success": True,
            "message": "Opening add doctor page...",
            "navigation": {"action": "navigate", "path": "/admin", "delay_ms": 200}
        })
    finally:
        db.close()


@function_tool
async def delete_doctor(ctx: RunContextWrapper[dict], doctor_name: str) -> str:
    """Delete a doctor by name (admin only)."""
    admin_id = ctx.context.get("user_id")
    if not admin_id:
        return json.dumps({
            "type": "message_response",
            "success": False,
            "message": "Please log in first."
        })

    db: Session = next(get_db())
    try:
        admin = db.query(User).filter(User.id == admin_id).first()
        if not admin or admin.is_adman != "admin":
            return json.dumps({
                "type": "message_response",
                "success": False,
                "message": "Admin access required."
            })
        
        doctor = db.query(Doctor).filter(Doctor.name.ilike(f"%{doctor_name}%")).first()
        if not doctor:
            return json.dumps({
                "type": "message_response",
                "success": False,
                "message": f"Doctor '{doctor_name}' not found."
            })
        
        db.delete(doctor)
        db.commit()
        
        return json.dumps({
            "type": "message_response",
            "success": True,
            "message": f"✅ Doctor '{doctor.name}' deleted successfully."
        })
    finally:
        db.close()


@function_tool
async def edit_doctor(ctx: RunContextWrapper[dict], doctor_name: str) -> str:
    """Redirect to edit doctor page (admin only)."""
    admin_id = ctx.context.get("user_id")
    if not admin_id:
        return json.dumps({
            "type": "navigation_response",
            "success": False,
            "message": "Please log in first.",
            "navigation": {"action": "navigate", "path": "/login", "delay_ms": 500}
        })

    db: Session = next(get_db())
    try:
        admin = db.query(User).filter(User.id == admin_id).first()
        if not admin or admin.is_adman != "admin":
            return json.dumps({
                "type": "message_response",
                "success": False,
                "message": "Admin access required."
            })
        
        doctor = db.query(Doctor).filter(Doctor.name.ilike(f"%{doctor_name}%")).first()
        if not doctor:
            return json.dumps({
                "type": "message_response",
                "success": False,
                "message": f"Doctor '{doctor_name}' not found."
            })
        
        return json.dumps({
            "type": "navigation_response",
            "success": True,
            "message": f"Opening edit page for Dr. {doctor.name}...",
            "navigation": {"action": "navigate", "path": "/admin", "delay_ms": 200}
        })
    finally:
        db.close()

@function_tool
async def start_booking(ctx: RunContextWrapper[dict], doctor_name: Optional[str] = None) -> str:
    """Start appointment booking process in chatbot."""
    user_id = ctx.context.get("user_id")
    if not user_id:
        return json.dumps({
            "type": "message_response",
            "success": False,
            "message": "Please log in to book an appointment."
        })

    db: Session = next(get_db())
    try:
        if doctor_name:
            # Find specific doctor by name (case insensitive, partial match)
            doctor = db.query(Doctor).filter(Doctor.name.ilike(f"%{doctor_name}%")).first()
            if doctor:
                return json.dumps({
                    "type": "message_response",
                    "success": True,
                    "message": f"Perfect! I found {doctor.name} ({doctor.specialty}) - ID: {doctor.id}.\n\nTo complete your booking, please provide:\n\n📅 **Date**: When would you like your appointment? (e.g., 'today', 'tomorrow', 'next Monday')\n⏰ **Time**: What time works for you? (e.g., 'morning', '2 PM', '14:30')\n📝 **Reason**: What's the reason for your visit? (optional)\n\nYou can provide all details in one message like: 'Tomorrow at 2 PM for skin consultation'"
                })
            else:
                # Doctor not found, show available doctors
                doctors = db.query(Doctor).all()
                if not doctors:
                    return json.dumps({
                        "type": "message_response",
                        "success": False,
                        "message": "No doctors available at the moment."
                    })
                
                message = f"I couldn't find a doctor named '{doctor_name}'. Here are our available doctors:\n\n"
                for i, doc in enumerate(doctors[:5], 1):
                    message += f"{i}. **{doc.name}** - {doc.specialty} (ID: {doc.id})\n"
                
                message += "\nPlease tell me the exact doctor's name you'd like to book with."
                
                return json.dumps({
                    "type": "message_response",
                    "success": True,
                    "message": message
                })
        
        # Show available doctors when no specific doctor mentioned
        doctors = db.query(Doctor).all()
        if not doctors:
            return json.dumps({
                "type": "message_response",
                "success": False,
                "message": "No doctors available at the moment."
            })
        
        message = "Which doctor would you like to book with?\n\n"
        for i, doctor in enumerate(doctors[:5], 1):
            message += f"{i}. **{doctor.name}** - {doctor.specialty} (ID: {doctor.id})\n"
        
        message += "\nPlease tell me the doctor's name."
        
        return json.dumps({
            "type": "message_response",
            "success": True,
            "message": message
        })
    finally:
        db.close()
