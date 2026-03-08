from __future__ import annotations

from io import BytesIO
from pathlib import Path
import zipfile

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile, status
from fastapi.security import OAuth2PasswordBearer
from fastapi.responses import StreamingResponse
from jwt import PyJWTError
from PIL import Image, ImageOps
from sqlalchemy.orm import Session

from app import crud, models, schemas
from app.db import get_db
from app.security import create_access_token, decode_access_token

router = APIRouter()

_oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")
_MAX_UPLOAD_BYTES = 5 * 1024 * 1024
_AVATAR_SIZES = (200, 400, 800)
_MEDIA_DIR = Path(__file__).resolve().parents[2] / "media"
_AVATAR_DIR = _MEDIA_DIR / "avatars"


@router.post("/auth/login", response_model=schemas.Token)
def login(user_in: schemas.UserLogin, db: Session = Depends(get_db)):
    user = crud.authenticate_user(db, user_in.email, user_in.password)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    access_token = create_access_token(subject=str(user.id))
    return schemas.Token(access_token=access_token)


def get_current_user(
    token: str = Depends(_oauth2_scheme),
    db: Session = Depends(get_db),
):
    try:
        payload = decode_access_token(token)
        user_id = int(payload.get("sub"))
    except (PyJWTError, TypeError, ValueError):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Inactive user")
    return user


@router.get("/auth/me", response_model=schemas.UserOut)
def read_current_user(current_user: models.User = Depends(get_current_user)):
    return current_user


@router.post("/users", response_model=schemas.UserOut, status_code=status.HTTP_201_CREATED)
def create_user(user_in: schemas.UserCreate, db: Session = Depends(get_db)):
    existing = crud.get_user_by_email(db, user_in.email)
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")
    return crud.create_user(db, user_in)


@router.patch("/users/me", response_model=schemas.UserOut)
def update_self(
    updates: schemas.UserUpdateSelf,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    return crud.update_user_self(db, current_user, updates)


@router.patch("/users/{user_id}", response_model=schemas.UserOut)
def update_user_admin(
    user_id: int,
    updates: schemas.UserUpdateAdmin,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    if not current_user.is_superuser:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Superuser required")
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return crud.update_user_admin(db, user, updates)


@router.post("/users/me/avatar", response_model=schemas.UserOut)
async def upload_avatar(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    if not file.content_type or not file.content_type.startswith("image/"):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid file type")

    data = await file.read()
    if len(data) > _MAX_UPLOAD_BYTES:
        raise HTTPException(status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, detail="Image too large")

    try:
        image = Image.open(BytesIO(data))
        image = ImageOps.exif_transpose(image)
    except Exception:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid image file")

    user_dir = _AVATAR_DIR / str(current_user.id)
    user_dir.mkdir(parents=True, exist_ok=True)

    db.query(models.AvatarImage).filter(models.AvatarImage.user_id == current_user.id).delete()

    avatar_path = None
    avatar_records = []
    for size in _AVATAR_SIZES:
        resized = ImageOps.fit(image, (size, size), method=Image.Resampling.LANCZOS)
        if resized.mode not in ("RGB", "RGBA"):
            resized = resized.convert("RGBA")
        output_path = user_dir / f"avatar_{size}.webp"
        resized.save(output_path, format="WEBP", quality=82, method=6)
        path = f"/media/avatars/{current_user.id}/avatar_{size}.webp"
        avatar_records.append(
            models.AvatarImage(user_id=current_user.id, size=size, path=path)
        )
        if size == 200:
            avatar_path = path

    current_user.avatar_200_path = avatar_path
    db.add(current_user)
    db.add_all(avatar_records)
    db.commit()
    db.refresh(current_user)
    return current_user


@router.get("/users/me/avatar/download")
def download_avatar_images(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    user_dir = _AVATAR_DIR / str(current_user.id)
    files = []
    for size in _AVATAR_SIZES:
        path = user_dir / f"avatar_{size}.webp"
        if path.exists():
            files.append(path)

    if not files:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No avatars found")

    buffer = BytesIO()
    with zipfile.ZipFile(buffer, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for path in files:
            archive.write(path, arcname=path.name)
    buffer.seek(0)

    headers = {"Content-Disposition": "attachment; filename=avatars.zip"}
    return StreamingResponse(buffer, media_type="application/zip", headers=headers)


@router.get("/admin/users", response_model=list[schemas.UserOut])
def list_users_admin(
    limit: int = Query(default=50, ge=1, le=50),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    if not current_user.is_superuser:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Superuser required")
    return (
        db.query(models.User)
        .order_by(models.User.id.asc())
        .offset(offset)
        .limit(limit)
        .all()
    )


@router.get("/admin/users/{user_id}", response_model=schemas.UserOut)
def get_user_admin(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    if not current_user.is_superuser:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Superuser required")
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return user
