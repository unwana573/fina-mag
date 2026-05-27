import os
import uuid
from fastapi import APIRouter, Depends, File, UploadFile, HTTPException
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session
from api.core.database import get_db
from api.core.dependencies import get_current_user
from api.core.config import settings
from api.models import User

router = APIRouter(prefix="/users", tags=["Profile Picture"])

ALLOWED_TYPES = {"image/jpeg", "image/png", "image/webp"}
MAX_BYTES = settings.MAX_AVATAR_SIZE_MB * 1024 * 1024


@router.post("/me/avatar")
async def upload_avatar(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    # Validate file type
    if file.content_type not in ALLOWED_TYPES:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid file type '{file.content_type}'. Only JPEG, PNG, and WebP are allowed."
        )

    # Read and validate file size
    contents = await file.read()
    if len(contents) > MAX_BYTES:
        raise HTTPException(
            status_code=400,
            detail=f"File too large. Maximum size is {settings.MAX_AVATAR_SIZE_MB}MB."
        )

    # Create upload directory if it doesn't exist
    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)

    # Delete old avatar file if exists
    if current_user.avatar_url:
        old_filename = current_user.avatar_url.split("/")[-1]
        old_path = os.path.join(settings.UPLOAD_DIR, old_filename)
        if os.path.exists(old_path):
            os.remove(old_path)

    # Generate unique filename
    ext = file.filename.split(".")[-1].lower()
    filename = f"{uuid.uuid4().hex}.{ext}"
    filepath = os.path.join(settings.UPLOAD_DIR, filename)

    # Save file to disk
    with open(filepath, "wb") as f:
        f.write(contents)

    # Build public URL
    avatar_url = f"{settings.BASE_URL}/static/avatars/{filename}"

    # Update user record
    current_user.avatar_url = avatar_url
    db.commit()
    db.refresh(current_user)

    return {
        "avatar_url": avatar_url,
        "message": "Profile picture updated successfully"
    }


@router.delete("/me/avatar")
def delete_avatar(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if not current_user.avatar_url:
        raise HTTPException(status_code=404, detail="No profile picture to delete")

    # Delete file from disk
    filename = current_user.avatar_url.split("/")[-1]
    filepath = os.path.join(settings.UPLOAD_DIR, filename)
    if os.path.exists(filepath):
        os.remove(filepath)

    # Clear avatar_url from user record
    current_user.avatar_url = None
    db.commit()

    return {"message": "Profile picture removed successfully"}