from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.user import User
from app.schemas.user_schema import UserOut, UserUpdate
from app.utils.jwt_handler import decode_access_token
from fastapi.security import OAuth2PasswordBearer
from fastapi import HTTPException

router = APIRouter(prefix="/users", tags=["Users"])

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")


def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    try:
        payload = decode_access_token(token)
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid token")

    user_id = payload.get("sub")
    try:
        user_id = int(user_id)
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid token payload")

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


@router.get("/", response_model=list[UserOut])
def get_all_users(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    # Only allow admins to view all users
    if current_user.is_adman != "admin":
        raise HTTPException(status_code=403, detail="Access forbidden: Admin privileges required")
    
    return db.query(User).all()


@router.get("/me", response_model=UserOut)
def get_profile(current_user: User = Depends(get_current_user)):
    return current_user


@router.put("/me", response_model=UserOut)
def update_profile(user_update: UserUpdate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    # Update only the fields that are provided
    if user_update.name is not None:
        current_user.name = user_update.name
    if user_update.email is not None:
        current_user.email = user_update.email
    if user_update.phone_number is not None:
        current_user.phone_number = user_update.phone_number
    if user_update.DOB is not None:
        current_user.DOB = user_update.DOB
    if user_update.image_url is not None:
        current_user.image_url = user_update.image_url
    
    db.commit()
    db.refresh(current_user)
    return current_user


# Admin-only user management routes
@router.put("/{user_id}", response_model=UserOut)
def update_user(
    user_id: int,
    user_update: UserUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Check if user is admin
    if current_user.is_adman != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Update only provided fields
    if user_update.name is not None:
        user.name = user_update.name
    if user_update.email is not None:
        # Check if email already exists for another user
        existing_user = db.query(User).filter(User.email == user_update.email, User.id != user_id).first()
        if existing_user:
            raise HTTPException(status_code=400, detail="Email already registered")
        user.email = user_update.email
    if user_update.phone_number is not None:
        user.phone_number = user_update.phone_number
    if user_update.DOB is not None:
        user.DOB = user_update.DOB
    if user_update.image_url is not None:
        user.image_url = user_update.image_url
    
    db.commit()
    db.refresh(user)
    return user


@router.delete("/{user_id}")
def delete_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Check if user is admin
    if current_user.is_adman != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    
    # Prevent admin from deleting themselves
    if current_user.id == user_id:
        raise HTTPException(status_code=400, detail="Cannot delete your own account")
    
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    try:
        # Check if user has appointments
        from app.models.appointment import Appointment
        appointments = db.query(Appointment).filter(Appointment.user_id == user_id).all()
        
        if appointments:
            appointment_count = len(appointments)
            raise HTTPException(
                status_code=400, 
                detail=f"Cannot delete user {user.name}. They have {appointment_count} appointment(s). Please cancel or reassign their appointments first."
            )
        
        db.delete(user)
        db.commit()
        return {"message": f"User {user.name} deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500, 
            detail=f"Failed to delete user {user.name}. Please try again or contact support."
        )
