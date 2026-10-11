import io
import os
import subprocess
import tempfile
import uuid
from datetime import datetime

from fastapi import APIRouter, BackgroundTasks, Depends, File, Form, HTTPException, UploadFile, status
from fastapi.responses import RedirectResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.auth import get_current_user
from app.core.config import settings
from app.core.database import SessionLocal, get_db
from app.core.storage import (
    abort_multipart_upload,
    complete_multipart_upload,
    create_multipart_upload,
    delete_file,
    download_to_file,
    generate_presigned_download_url,
    generate_presigned_url,
    upload_file,
    upload_part as storage_upload_part,
)
from app.models.models import Permission, Photo, User
from app.api.albums import _get_user_role

router = APIRouter(tags=["photos"])

ALLOWED_IMAGE_TYPES = {
    "image/jpeg", "image/jpg", "image/png", "image/gif",
    "image/webp", "image/heic", "image/heif",
}

ALLOWED_VIDEO_TYPES = {
    "video/mp4", "video/quicktime", "video/webm",
    "video/x-msvideo", "video/avi",
}

ALLOWED_TYPES = ALLOWED_IMAGE_TYPES | ALLOWED_VIDEO_TYPES


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


def _extract_video_thumbnail(raw_bytes: bytes, ext: str) -> bytes | None:
    """Extract first frame of a video as JPEG bytes using ffmpeg. Returns None on failure."""
    in_path = os.path.join(tempfile.gettempdir(), f"{uuid.uuid4().hex}.{ext}")
    out_path = os.path.join(tempfile.gettempdir(), f"{uuid.uuid4().hex}.jpg")
    try:
        with open(in_path, "wb") as f:
            f.write(raw_bytes)
        result = subprocess.run(
            ["ffmpeg", "-y", "-i", in_path, "-frames:v", "1", "-f", "image2", out_path],
            capture_output=True,
            timeout=60,
        )
        if result.returncode != 0 or not os.path.exists(out_path):
            return None
        with open(out_path, "rb") as f:
            return f.read()
    except Exception:
        return None
    finally:
        for p in (in_path, out_path):
            try:
                os.remove(p)
            except OSError:
                pass


def _process_video_background(photo_id: int, tmp_path: str, orig_key: str, prefix: str, orig_ext: str, mime: str):
    """Upload video + generate thumbnails in background. Runs after HTTP response is sent."""
    db = SessionLocal()
    try:
        with open(tmp_path, "rb") as f:
            raw = f.read()

        upload_file(orig_key, io.BytesIO(raw), mime)

        frame_bytes = _extract_video_thumbnail(raw, orig_ext)
        thumb_300_key = None
        thumb_800_key = None
        if frame_bytes:
            try:
                from PIL import Image
                frame_img = Image.open(io.BytesIO(frame_bytes))
                if frame_img.mode not in ("RGB", "RGBA", "L"):
                    frame_img = frame_img.convert("RGB")
                thumb_300_key = f"{prefix}/thumb_300.jpg"
                thumb_800_key = f"{prefix}/thumb_800.jpg"
                upload_file(thumb_300_key, io.BytesIO(_make_thumbnail(frame_img, 300)), "image/jpeg")
                upload_file(thumb_800_key, io.BytesIO(_make_thumbnail(frame_img, 800)), "image/jpeg")
            except Exception:
                pass

        photo = db.query(Photo).filter(Photo.id == photo_id).first()
        if photo:
            photo.thumb_300_key = thumb_300_key
            photo.thumb_800_key = thumb_800_key
            db.commit()
    except Exception:
        pass
    finally:
        db.close()
        try:
            os.remove(tmp_path)
        except OSError:
            pass


def _extract_video_thumbnail_from_path(in_path: str) -> bytes | None:
    """Extract first frame of a video file as JPEG bytes using ffmpeg. Returns None on failure."""
    out_path = os.path.join(tempfile.gettempdir(), f"{uuid.uuid4().hex}.jpg")
    try:
        result = subprocess.run(
            ["ffmpeg", "-y", "-i", in_path, "-frames:v", "1", "-f", "image2", out_path],
            capture_output=True,
            timeout=120,
        )
        if result.returncode != 0 or not os.path.exists(out_path):
            return None
        with open(out_path, "rb") as f:
            return f.read()
    except Exception:
        return None
    finally:
        try:
            os.remove(out_path)
        except OSError:
            pass


def _thumbs_from_frame(frame_bytes: bytes, prefix: str) -> tuple[str, str]:
    """Build and upload 300/800 thumbnails from a JPEG frame. Returns (thumb_300_key, thumb_800_key)."""
    from PIL import Image
    frame_img = Image.open(io.BytesIO(frame_bytes))
    if frame_img.mode not in ("RGB", "RGBA", "L"):
        frame_img = frame_img.convert("RGB")
    thumb_300_key = f"{prefix}/thumb_300.jpg"
    thumb_800_key = f"{prefix}/thumb_800.jpg"
    upload_file(thumb_300_key, io.BytesIO(_make_thumbnail(frame_img, 300)), "image/jpeg")
    upload_file(thumb_800_key, io.BytesIO(_make_thumbnail(frame_img, 800)), "image/jpeg")
    return thumb_300_key, thumb_800_key


def _process_media_from_storage(photo_id: int, storage_key: str, prefix: str, orig_ext: str, mime: str):
    """Background: download the direct-uploaded original from storage, generate thumbnails
    (+ EXIF/dimensions for images), and update the Photo row. Used by the presigned-upload flow."""
    db = SessionLocal()
    tmp_path = os.path.join(tempfile.gettempdir(), f"{uuid.uuid4().hex}.{orig_ext}")
    try:
        download_to_file(storage_key, tmp_path)
        is_video = mime in ALLOWED_VIDEO_TYPES
        thumb_300_key = None
        thumb_800_key = None
        updates = {}

        if is_video:
            frame_bytes = _extract_video_thumbnail_from_path(tmp_path)
            if frame_bytes:
                try:
                    thumb_300_key, thumb_800_key = _thumbs_from_frame(frame_bytes, prefix)
                except Exception:
                    pass
        else:
            try:
                from PIL import Image, ImageOps
                img = Image.open(tmp_path)
                img.load()
            except Exception:
                import pillow_heif
                pillow_heif.register_heif_opener()
                from PIL import Image, ImageOps
                img = Image.open(tmp_path)
                img.load()
            updates.update(_extract_exif(img))
            img = ImageOps.exif_transpose(img)
            updates["width"], updates["height"] = img.size
            if img.mode not in ("RGB", "RGBA", "L"):
                img = img.convert("RGB")
            thumb_300_key = f"{prefix}/thumb_300.jpg"
            thumb_800_key = f"{prefix}/thumb_800.jpg"
            upload_file(thumb_300_key, io.BytesIO(_make_thumbnail(img, 300)), "image/jpeg")
            upload_file(thumb_800_key, io.BytesIO(_make_thumbnail(img, 800)), "image/jpeg")

        photo = db.query(Photo).filter(Photo.id == photo_id).first()
        if photo:
            photo.thumb_300_key = thumb_300_key
            photo.thumb_800_key = thumb_800_key
            for k, v in updates.items():
                setattr(photo, k, v)
            db.commit()
    except Exception:
        pass
    finally:
        db.close()
        try:
            os.remove(tmp_path)
        except OSError:
            pass


# --- Chunked (multipart) upload -------------------------------------------------
# Large files (esp. video) are split client-side into parts < 100 MB so each request
# clears the Cloudflare 100 MB body limit. Parts stream straight to object storage via
# an S3 multipart upload; `complete` finalises it and kicks off thumbnail processing.

class StartRequest(BaseModel):
    filename: str
    mime_type: str
    file_size: int


class CompletePart(BaseModel):
    part_number: int
    etag: str


class CompleteRequest(BaseModel):
    storage_key: str
    prefix: str
    upload_id: str
    filename: str
    mime_type: str
    file_size: int
    caption: str = ""
    parts: list[CompletePart]


def _require_upload_role(db: Session, current_user: User, album_id: int):
    from app.models.models import Album
    album = db.query(Album).filter(Album.id == album_id, Album.is_deleted == False).first()
    if not album:
        raise HTTPException(status_code=404, detail="Album not found")
    role = _get_user_role(db, current_user, album_id)
    if role not in ("admin", "uploader"):
        raise HTTPException(status_code=403, detail="Upload permission required")
    return role


@router.post("/albums/{album_id}/photos/upload/start")
def start_upload(
    album_id: int,
    body: StartRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Begin a chunked upload: validate, allocate the storage key, open an S3 multipart upload."""
    _require_upload_role(db, current_user, album_id)

    mime = body.mime_type or ""
    if mime not in ALLOWED_TYPES:
        raise HTTPException(status_code=400, detail=f"Unsupported file type: {mime}")

    is_video = mime in ALLOWED_VIDEO_TYPES
    max_mb = settings.max_video_mb if is_video else settings.max_upload_mb
    if body.file_size > max_mb * 1024 * 1024:
        raise HTTPException(status_code=413, detail=f"File exceeds {max_mb} MB limit")

    prefix = f"albums/{album_id}/{uuid.uuid4().hex}"
    orig_ext = (body.filename or "file").rsplit(".", 1)[-1].lower()
    orig_key = f"{prefix}/original.{orig_ext}"
    upload_id = create_multipart_upload(orig_key, mime)

    return {
        "storage_key": orig_key,
        "prefix": prefix,
        "upload_id": upload_id,
    }


@router.post("/albums/{album_id}/photos/upload/part")
async def upload_part_endpoint(
    album_id: int,
    storage_key: str = Form(...),
    upload_id: str = Form(...),
    part_number: int = Form(...),
    chunk: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Upload a single part; returns its ETag for the client to collect."""
    _require_upload_role(db, current_user, album_id)
    if not storage_key.startswith(f"albums/{album_id}/"):
        raise HTTPException(status_code=400, detail="Invalid storage key")

    data = await chunk.read()
    etag = storage_upload_part(storage_key, upload_id, part_number, data)
    return {"part_number": part_number, "etag": etag}


@router.post("/albums/{album_id}/photos/upload/complete", status_code=status.HTTP_201_CREATED)
def complete_upload(
    album_id: int,
    body: CompleteRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Finalise the multipart upload, create the Photo row, and process thumbnails in the background."""
    _require_upload_role(db, current_user, album_id)

    mime = body.mime_type or ""
    if mime not in ALLOWED_TYPES:
        raise HTTPException(status_code=400, detail=f"Unsupported file type: {mime}")
    if not body.storage_key.startswith(f"albums/{album_id}/"):
        raise HTTPException(status_code=400, detail="Invalid storage key")

    parts = [
        {"PartNumber": p.part_number, "ETag": p.etag}
        for p in sorted(body.parts, key=lambda p: p.part_number)
    ]
    try:
        complete_multipart_upload(body.storage_key, body.upload_id, parts)
    except Exception:
        abort_multipart_upload(body.storage_key, body.upload_id)
        raise HTTPException(status_code=400, detail="Failed to assemble upload")

    orig_ext = body.storage_key.rsplit(".", 1)[-1].lower()

    photo = Photo(
        album_id=album_id,
        uploaded_by=current_user.id,
        storage_key=body.storage_key,
        thumb_300_key=None,
        thumb_800_key=None,
        mime_type=mime,
        filename=body.filename or f"file.{orig_ext}",
        file_size_bytes=body.file_size,
        caption=body.caption.strip() or None,
    )
    db.add(photo)

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

    background_tasks.add_task(
        _process_media_from_storage,
        photo.id, body.storage_key, body.prefix, orig_ext, mime,
    )

    return {
        "id": photo.id,
        "thumb_300_url": None,
        "thumb_800_url": None,
        "mime_type": photo.mime_type,
        "filename": photo.filename,
        "caption": photo.caption,
        "width": None,
        "height": None,
        "exif_date_taken": None,
        "uploaded_at": photo.uploaded_at.isoformat(),
    }


@router.post("/albums/{album_id}/photos", status_code=status.HTTP_201_CREATED)
async def upload_photo(
    album_id: int,
    file: UploadFile = File(...),
    caption: str = Form(default=""),
    background_tasks: BackgroundTasks = ...,
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

    mime = file.content_type or ""
    if mime not in ALLOWED_TYPES:
        raise HTTPException(status_code=400, detail=f"Unsupported file type: {mime}")

    raw = await file.read()
    is_video = mime in ALLOWED_VIDEO_TYPES

    if is_video:
        max_bytes = settings.max_video_mb * 1024 * 1024
        if len(raw) > max_bytes:
            raise HTTPException(status_code=413, detail=f"File exceeds {settings.max_video_mb} MB limit")
    else:
        max_bytes = settings.max_upload_mb * 1024 * 1024
        if len(raw) > max_bytes:
            raise HTTPException(status_code=413, detail=f"File exceeds {settings.max_upload_mb} MB limit")

    prefix = f"albums/{album_id}/{uuid.uuid4().hex}"
    orig_ext = (file.filename or "file").rsplit(".", 1)[-1].lower()
    orig_key = f"{prefix}/original.{orig_ext}"

    if is_video:
        # Save to temp file and process in background — responds immediately, bypassing proxy timeouts
        tmp_path = os.path.join(tempfile.gettempdir(), f"{uuid.uuid4().hex}.{orig_ext}")
        with open(tmp_path, "wb") as f:
            f.write(raw)

        photo = Photo(
            album_id=album_id,
            uploaded_by=current_user.id,
            storage_key=orig_key,
            thumb_300_key=None,
            thumb_800_key=None,
            mime_type=mime,
            filename=file.filename or f"video.{orig_ext}",
            file_size_bytes=len(raw),
            caption=caption.strip() or None,
        )
        db.add(photo)

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

        background_tasks.add_task(
            _process_video_background,
            photo.id, tmp_path, orig_key, prefix, orig_ext, mime,
        )

        return {
            "id": photo.id,
            "thumb_300_url": None,
            "thumb_800_url": None,
            "mime_type": photo.mime_type,
            "filename": photo.filename,
            "caption": photo.caption,
            "width": None,
            "height": None,
            "exif_date_taken": None,
            "uploaded_at": photo.uploaded_at.isoformat(),
        }
    else:
        # Image path — existing Pillow processing
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
        img = ImageOps.exif_transpose(img)
        width, height = img.size

        if img.mode not in ("RGB", "RGBA", "L"):
            img = img.convert("RGB")

        thumb_300_bytes = _make_thumbnail(img, 300)
        thumb_800_bytes = _make_thumbnail(img, 800)

        thumb_300_key = f"{prefix}/thumb_300.jpg"
        thumb_800_key = f"{prefix}/thumb_800.jpg"
        upload_file(orig_key, io.BytesIO(raw), mime)
        upload_file(thumb_300_key, io.BytesIO(thumb_300_bytes), "image/jpeg")
        upload_file(thumb_800_key, io.BytesIO(thumb_800_bytes), "image/jpeg")

        photo = Photo(
            album_id=album_id,
            uploaded_by=current_user.id,
            storage_key=orig_key,
            thumb_300_key=thumb_300_key,
            thumb_800_key=thumb_800_key,
            mime_type=mime,
            filename=file.filename or "photo.jpg",
            file_size_bytes=len(raw),
            width=width,
            height=height,
            caption=caption.strip() or None,
            **exif,
        )

        db.add(photo)

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
            "mime_type": photo.mime_type,
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
        "mime_type": photo.mime_type,
        "caption": photo.caption,
        "original_url": generate_presigned_url(photo.storage_key),
        "thumb_300_url": generate_presigned_url(photo.thumb_300_key) if photo.thumb_300_key else None,
        "thumb_800_url": generate_presigned_url(photo.thumb_800_key) if photo.thumb_800_key else None,
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
