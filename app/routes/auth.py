from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.schemas.user_schema import UserCreate, UserLogin, UserOut
from app.models.user import User
from app.database import get_db
from app.utils.security import hash_password, verify_password
from app.utils.jwt_handler import create_access_token

router = APIRouter(prefix="/auth", tags=["Auth"])


@router.post("/register")
def register(user: UserCreate, db: Session = Depends(get_db)):
    db_user = db.query(User).filter(User.email == user.email).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")

    new_user = User(
        email=user.email,
        name=user.name,
        hashed_password=hash_password(user.password),
        is_adman="user",
        phone_number=user.phone_number,
        DOB=user.DOB
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    # Create JWT token for automatic login
    token = create_access_token({"sub": str(new_user.id), "is_adman": new_user.is_adman})
    
    return {
        "user": new_user,
        "access_token": token, 
        "token_type": "bearer"
    }


@router.post("/login")
def login(user: UserLogin, db: Session = Depends(get_db)):
    db_user = db.query(User).filter(User.email == user.email).first()
    if not db_user or not verify_password(user.password, db_user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    # Convert user ID to string for JWT
    token = create_access_token({"sub": str(db_user.id), "is_adman": db_user.is_adman})
    return {"access_token": token, "token_type": "bearer"}
