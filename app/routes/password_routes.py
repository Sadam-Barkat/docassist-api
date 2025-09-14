from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.user import User
from app.schemas import PasswordResetRequest, PasswordResetConfirm
from app.utils.jwt_handler import create_reset_token, verify_token
from app.utils.security import hash_password
from app.utils.email_service import send_email
from config import RESET_TOKEN_EXPIRE_MINUTES
import urllib.parse

router = APIRouter(prefix="/password", tags=["password"])

@router.post("/forgot")
def forgot_password(data: PasswordResetRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == data.email).first()
    if not user:
        return {"msg": "If the email exists, a reset link was sent."}

    token = create_reset_token({"sub": str(user.id), "email": user.email})
    
    # Use frontend URL from environment variable
    frontend_url = os.getenv("NEXT_PUBLIC_API_URL", "https://docassist-web.vercel.app")
    reset_link = f"{frontend_url}/reset-password?token={urllib.parse.quote(token)}"

    body = f"Hello,\n\nClick the link to reset your password (valid {RESET_TOKEN_EXPIRE_MINUTES} minutes):\n{reset_link}"
    send_email(user.email, "Password Reset", body)

    return {"msg": "If the email exists, a reset link was sent."}


@router.post("/reset")
def reset_password(data: PasswordResetConfirm, db: Session = Depends(get_db)):
    try:
        payload = verify_token(data.token, expected_type="reset")
        user_id = int(payload["sub"])
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid or expired token")

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    user.hashed_password = hash_password(data.new_password)
    db.add(user)
    db.commit()
    return {"msg": "Password reset successful"}
    