from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import or_, case
from typing import Optional
from datetime import date, datetime, timedelta

from app.core.auth import get_current_user
from app.core.database import get_db
from app.core.storage import generate_presigned_url
from app.models.models import Photo, Album, Permission, User

router = APIRouter(tags=["search"])


@router.get("/search")
def search_photos(
    q: Optional[str] = Query(None),
    album_id: Optional[int] = Query(None),
    date_from: Optional[date] = Query(None),
    date_to: Optional[date] = Query(None),
    page: int = Query(1, ge=1),
    per_page: int = Query(50, ge=1, le=200),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if not any([q, album_id, date_from, date_to]):
        raise HTTPException(status_code=400, detail="至少需提供一個搜尋條件")

    # Build permitted album IDs
    if current_user.is_admin:
        permitted_ids = [
            row.id for row in db.query(Album.id).filter(Album.is_deleted == False).all()
        ]
    else:
        permitted_ids = [
            row.album_id for row in db.query(Permission.album_id)
            .filter(Permission.user_id == current_user.id).all()
        ]

    if album_id is not None and album_id not in permitted_ids:
        raise HTTPException(status_code=403, detail="Access denied")

    if not permitted_ids:
        return {"photos": [], "total": 0, "page": page, "per_page": per_page}

    query = (
        db.query(Photo, Album)
        .join(Album, Album.id == Photo.album_id)
        .filter(
            Photo.is_deleted == False,
            Album.is_deleted == False,
            Photo.album_id.in_(permitted_ids),
        )
    )

    if album_id is not None:
        query = query.filter(Photo.album_id == album_id)

    if q:
        pattern = f"%{q}%"
        query = query.filter(
            or_(Photo.filename.ilike(pattern), Photo.caption.ilike(pattern))
        )

    if date_from:
        query = query.filter(
            Photo.exif_date_taken != None,
            Photo.exif_date_taken >= datetime(date_from.year, date_from.month, date_from.day),
        )

    if date_to:
        query = query.filter(
            Photo.exif_date_taken != None,
            Photo.exif_date_taken < datetime(date_to.year, date_to.month, date_to.day) + timedelta(days=1),
        )

    query = query.order_by(
        case((Photo.exif_date_taken.is_(None), 1), else_=0),
        Photo.exif_date_taken.desc(),
        Photo.uploaded_at.desc(),
    )

    total = query.count()
    rows = query.offset((page - 1) * per_page).limit(per_page).all()

    photos = []
    for photo, album in rows:
        photos.append({
            "id": photo.id,
            "filename": photo.filename,
            "mime_type": photo.mime_type,
            "caption": photo.caption,
            "thumb_300_url": generate_presigned_url(photo.thumb_300_key) if photo.thumb_300_key else None,
            "thumb_800_url": generate_presigned_url(photo.thumb_800_key) if photo.thumb_800_key else None,
            "exif_date_taken": photo.exif_date_taken.isoformat() if photo.exif_date_taken else None,
            "width": photo.width,
            "height": photo.height,
            "album_id": album.id,
            "album_name": album.name,
        })

    return {"photos": photos, "total": total, "page": page, "per_page": per_page}
