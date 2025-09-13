# backend/app/utils/email_service.py
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from config import SMTP_SERVER, SMTP_PORT, SMTP_USER, SMTP_PASSWORD


def send_email(to_email: str, subject: str, body: str) -> bool:
    """
    Send an email using SMTP.
    Returns True if sent successfully, else False.
    """
    try:
        msg = MIMEMultipart()
        msg["From"] = SMTP_USER
        msg["To"] = to_email
        msg["Subject"] = subject

        msg.attach(MIMEText(body, "plain"))

        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            server.login(SMTP_USER, SMTP_PASSWORD)
            server.send_message(msg)

        print(f"Email sent to {to_email}")
        return True
    except Exception as e:
        print("Email error:", e)
        return False


def create_appointment_email(
    user_name: str,
    doctor_name: str,
    specialty: str,
    date: str,
    time: str,
    reason: str
) -> str:
    """
    Creates the email body for appointment confirmation.
    """
    email_body = f"""
Dear {user_name},

Your appointment has been successfully booked!

Appointment Details:
- Doctor: Dr. {doctor_name}
- Specialty: {specialty}
- Date: {date}
- Time: {time}
- Reason: {reason}

Please arrive 15 minutes early for your appointment.

If you need to cancel or reschedule, please contact us at least 24 hours in advance.

Thank you for choosing HealthCare+!

Best regards,
HealthCare+ Team
    """
    return email_body
