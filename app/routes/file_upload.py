from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.user import User
from app.utils.jwt_handler import decode_access_token
import os
import uuid
from pathlib import Path

router = APIRouter(prefix="/upload", tags=["File Upload"])

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")

# Allowed image extensions
ALLOWED_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp'}
MAX_FILE_SIZE = 5 * 1024 * 1024  # 5MB

def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    try:
        print(f"DEBUG: Received token: {token[:20]}..." if token else "No token")
        payload = decode_access_token(token)
        print(f"DEBUG: Token payload: {payload}")
    except Exception as e:
        print(f"DEBUG: Token decode error: {e}")
        raise HTTPException(status_code=401, detail="Invalid token")

    user_id = payload.get("sub")
    print(f"DEBUG: User ID from token: {user_id}")
    try:
        user_id = int(user_id)
    except Exception as e:
        print(f"DEBUG: User ID conversion error: {e}")
        raise HTTPException(status_code=401, detail="Invalid token payload")

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        print(f"DEBUG: User not found for ID: {user_id}")
        raise HTTPException(status_code=404, detail="User not found")
    print(f"DEBUG: User found: {user.name}")
    return user

def validate_image_file(file: UploadFile) -> bool:
    """Validate uploaded image file"""
    if not file.filename:
        return False
    
    # Check file extension
    file_ext = Path(file.filename).suffix.lower()
    if file_ext not in ALLOWED_EXTENSIONS:
        return False
    
    # Check file size
    if hasattr(file, 'size') and file.size > MAX_FILE_SIZE:
        return False
    
    return True

@router.post("/profile-image")
async def upload_profile_image(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Upload profile image for current user"""
    
    # Validate file
    if not validate_image_file(file):
        raise HTTPException(
            status_code=400, 
            detail="Invalid file. Please upload a valid image file (JPG, PNG, GIF, BMP, WebP) under 5MB."
        )
    
    try:
        # Create uploads directory if it doesn't exist
        upload_dir = Path("uploads/patient_profile_image")
        upload_dir.mkdir(parents=True, exist_ok=True)
        
        # Generate unique filename
        file_ext = Path(file.filename).suffix.lower()
        unique_filename = f"{uuid.uuid4()}{file_ext}"
        file_path = upload_dir / unique_filename
        
        # Save file
        with open(file_path, "wb") as buffer:
            content = await file.read()
            buffer.write(content)
        
        # Update user's image_url in database
        image_url = f"/uploads/patient_profile_image/{unique_filename}"
        current_user.image_url = image_url
        db.commit()
        db.refresh(current_user)
        
        return {
            "success": True,
            "message": "Profile image uploaded successfully",
            "image_url": image_url
        }
        
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Failed to upload image: {str(e)}"
        )

@router.delete("/profile-image")
async def delete_profile_image(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete current user's profile image"""
    
    if not current_user.image_url:
        raise HTTPException(status_code=404, detail="No profile image found")
    
    try:
        # Remove file from filesystem
        if current_user.image_url.startswith("/uploads/"):
            file_path = Path(current_user.image_url.lstrip("/"))
            if file_path.exists():
                file_path.unlink()
        
        # Update database
        current_user.image_url = None
        db.commit()
        db.refresh(current_user)
        
        return {
            "success": True,
            "message": "Profile image deleted successfully"
        }
        
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Failed to delete image: {str(e)}"
        )
