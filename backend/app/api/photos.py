import io
import uuid
from datetime import datetime

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from app.core.auth import get_current_user
from app.core.config import settings
from app.core.database import get_db
from app.core.storage import delete_file, generate_presigned_download_url, generate_presigned_url, upload_file
from app.models.models import Permission, Photo, User
from app.api.albums import _get_user_role

router = APIRouter(tags=["photos"])

ALLOWED_TYPES = {
    "image/jpeg", "image/jpg", "image/png", "image/gif",
    "image/webp", "image/heic", "image/heif",
}


def _check_photo_access(photo: Photo, current_user: User, db: Session):
    if not photo or photo.is_deleted:
        raise HTTPException(status_code=404, detail="Photo not found")
    role = _get_user_role(db, current_user, photo.album_id)
    if not role:
        raise HTTPException(status_code=403, detail="Access denied")
    return role


def _extract_exif(img):
    """Return dict with exif fields; tolerant of missing data."""
    result = {}
    try:
        exif_data = img._getexif()
        if not exif_data:
            return result
        from PIL.ExifTags import TAGS, GPSTAGS
        for tag_id, value in exif_data.items():
            tag = TAGS.get(tag_id, tag_id)
            if tag == "DateTimeOriginal":
                try:
                    result["exif_date_taken"] = datetime.strptime(value, "%Y:%m:%d %H:%M:%S")
                except Exception:
                    pass
            elif tag == "Model":
                result["exif_camera"] = str(value)[:100]
            elif tag == "GPSInfo":
                gps = {}
                for k, v in value.items():
                    gps[GPSTAGS.get(k, k)] = v
                try:
                    def dms(d): return d[0] + d[1] / 60 + d[2] / 3600
                    lat = dms(gps["GPSLatitude"])
                    if gps.get("GPSLatitudeRef") == "S":
                        lat = -lat
                    lon = dms(gps["GPSLongitude"])
                    if gps.get("GPSLongitudeRef") == "W":
                        lon = -lon
                    result["exif_gps_lat"] = round(float(lat), 7)
                    result["exif_gps_lon"] = round(float(lon), 7)
                except Exception:
                    pass
    except Exception:
        pass
    return result


def _make_thumbnail(img, max_px: int) -> bytes:
    thumb = img.copy()
    thumb.thumbnail((max_px, max_px))
    buf = io.BytesIO()
    fmt = "JPEG" if thumb.mode in ("RGB", "RGBA") else "PNG"
    if thumb.mode == "RGBA" and fmt == "JPEG":
        thumb = thumb.convert("RGB")
    thumb.save(buf, format=fmt, quality=85, optimize=True)
    return buf.getvalue()


@router.post("/albums/{album_id}/photos", status_code=status.HTTP_201_CREATED)
async def upload_photo(
    album_id: int,
    file: UploadFile = File(...),
    caption: str = Form(default=""),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    from app.models.models import Album
    album = db.query(Album).filter(Album.id == album_id, Album.is_deleted == False).first()
    if not album:
        raise HTTPException(status_code=404, detail="Album not found")

    role = _get_user_role(db, current_user, album_id)
    if role not in ("admin", "uploader"):
        raise HTTPException(status_code=403, detail="Upload permission required")

    if file.content_type not in ALLOWED_TYPES:
        raise HTTPException(status_code=400, detail=f"Unsupported file type: {file.content_type}")

    raw = await file.read()
    max_bytes = settings.max_upload_mb * 1024 * 1024
    if len(raw) > max_bytes:
        raise HTTPException(status_code=413, detail=f"File exceeds {settings.max_upload_mb} MB limit")

    # Open with Pillow
    try:
        from PIL import Image, ImageOps
        img = Image.open(io.BytesIO(raw))
        img.load()
    except Exception:
        try:
            import pillow_heif
            pillow_heif.register_heif_opener()
            from PIL import Image, ImageOps
            img = Image.open(io.BytesIO(raw))
            img.load()
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Cannot open image: {e}")

    exif = _extract_exif(img)

    # Apply EXIF orientation (fixes iPhone portrait photos rotated 90°)
    img = ImageOps.exif_transpose(img)

    width, height = img.size

    # Convert to RGB for thumbnails if needed
    if img.mode not in ("RGB", "RGBA", "L"):
        img = img.convert("RGB")

    thumb_300_bytes = _make_thumbnail(img, 300)
    thumb_800_bytes = _make_thumbnail(img, 800)

    # Storage keys
    prefix = f"albums/{album_id}/{uuid.uuid4().hex}"
    orig_ext = (file.filename or "photo.jpg").rsplit(".", 1)[-1].lower()
    orig_key = f"{prefix}/original.{orig_ext}"
    thumb_300_key = f"{prefix}/thumb_300.jpg"
    thumb_800_key = f"{prefix}/thumb_800.jpg"

    content_type = file.content_type or "image/jpeg"
    upload_file(orig_key, io.BytesIO(raw), content_type)
    upload_file(thumb_300_key, io.BytesIO(thumb_300_bytes), "image/jpeg")
    upload_file(thumb_800_key, io.BytesIO(thumb_800_bytes), "image/jpeg")

    photo = Photo(
        album_id=album_id,
        uploaded_by=current_user.id,
        storage_key=orig_key,
        thumb_300_key=thumb_300_key,
        thumb_800_key=thumb_800_key,
        filename=file.filename or "photo.jpg",
        file_size_bytes=len(raw),
        width=width,
        height=height,
        caption=caption.strip() or None,
        **exif,
    )
    db.add(photo)

    # Grant uploader permission if not already present
    existing_perm = db.query(Permission).filter(
        Permission.user_id == current_user.id,
        Permission.album_id == album_id,
    ).first()
    if not existing_perm:
        db.add(Permission(
            user_id=current_user.id,
            album_id=album_id,
            role="uploader",
            granted_by=current_user.id,
        ))

    db.commit()
    db.refresh(photo)

    return {
        "id": photo.id,
        "thumb_300_url": generate_presigned_url(photo.thumb_300_key),
        "thumb_800_url": generate_presigned_url(photo.thumb_800_key),
        "filename": photo.filename,
        "caption": photo.caption,
        "width": photo.width,
        "height": photo.height,
        "exif_date_taken": photo.exif_date_taken.isoformat() if photo.exif_date_taken else None,
        "uploaded_at": photo.uploaded_at.isoformat(),
    }


@router.get("/photos/{photo_id}")
def get_photo(
    photo_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    photo = db.query(Photo).filter(Photo.id == photo_id).first()
    role = _check_photo_access(photo, current_user, db)

    return {
        "id": photo.id,
        "album_id": photo.album_id,
        "filename": photo.filename,
        "caption": photo.caption,
        "original_url": generate_presigned_url(photo.storage_key),
        "thumb_300_url": generate_presigned_url(photo.thumb_300_key),
        "thumb_800_url": generate_presigned_url(photo.thumb_800_key),
        "file_size_bytes": photo.file_size_bytes,
        "width": photo.width,
        "height": photo.height,
        "exif_date_taken": photo.exif_date_taken.isoformat() if photo.exif_date_taken else None,
        "exif_camera": photo.exif_camera,
        "exif_gps_lat": float(photo.exif_gps_lat) if photo.exif_gps_lat else None,
        "exif_gps_lon": float(photo.exif_gps_lon) if photo.exif_gps_lon else None,
        "uploaded_at": photo.uploaded_at.isoformat(),
        "uploaded_by": {"id": photo.uploader.id, "name": photo.uploader.name},
        "my_role": role,
    }


@router.patch("/photos/{photo_id}")
def update_photo(
    photo_id: int,
    body: dict,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    photo = db.query(Photo).filter(Photo.id == photo_id).first()
    role = _check_photo_access(photo, current_user, db)

    if role not in ("uploader", "admin"):
        raise HTTPException(status_code=403, detail="Uploader or admin role required")

    if "caption" in body:
        photo.caption = body["caption"]
    db.commit()
    db.refresh(photo)
    return {"id": photo.id, "caption": photo.caption}


@router.delete("/photos/{photo_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_photo(
    photo_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    photo = db.query(Photo).filter(Photo.id == photo_id).first()
    role = _check_photo_access(photo, current_user, db)

    if role != "admin":
        raise HTTPException(status_code=403, detail="Admin role required")

    photo.is_deleted = True
    db.commit()


@router.get("/photos/{photo_id}/download")
def download_photo(
    photo_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    photo = db.query(Photo).filter(Photo.id == photo_id).first()
    _check_photo_access(photo, current_user, db)

    url = generate_presigned_download_url(photo.storage_key, photo.filename)
    return RedirectResponse(url=url)
