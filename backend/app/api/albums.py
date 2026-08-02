from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import Optional
import re
from datetime import date

from app.core.auth import get_current_user, require_admin
from app.core.database import get_db
from app.core.storage import generate_presigned_url
from app.models.models import Album, Photo, Permission, User

_DATE_RE = re.compile(r'(\d{4})[.\-](\d{2})[.\-](\d{2})')

def _parse_date_from_title(name: str) -> Optional[date]:
    m = _DATE_RE.search(name)
    if not m:
        return None
    try:
        return date(int(m.group(1)), int(m.group(2)), int(m.group(3)))
    except ValueError:
        return None

router = APIRouter(tags=["albums"])


def _get_user_role(db: Session, user: User, album_id: int) -> Optional[str]:
    if user.is_admin:
        return "admin"
    perm = db.query(Permission).filter(
        Permission.user_id == user.id,
        Permission.album_id == album_id,
    ).first()
    return perm.role if perm else None


def _album_response(album: Album, role: str, db: Session) -> dict:
    photo_count = db.query(func.count(Photo.id)).filter(
        Photo.album_id == album.id, Photo.is_deleted == False
    ).scalar()

    cover_url = None
    cover_photo = None
    if album.cover_photo_id:
        cover_photo = db.query(Photo).filter(Photo.id == album.cover_photo_id).first()
    if not cover_photo:
        cover_photo = db.query(Photo).filter(
            Photo.album_id == album.id, Photo.is_deleted == False
        ).order_by(Photo.uploaded_at).first()
    if cover_photo:
        cover_url = generate_presigned_url(cover_photo.thumb_300_key)

    return {
        "id": album.id,
        "name": album.name,
        "description": album.description,
        "album_date": album.album_date.isoformat() if album.album_date else None,
        "cover_thumb_url": cover_url,
        "photo_count": photo_count,
        "my_role": role,
        "created_at": album.created_at.isoformat(),
    }


@router.get("/albums")
def list_albums(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    order = [func.isnull(Album.album_date), Album.album_date.desc(), Album.created_at.desc()]

    if current_user.is_admin:
        albums = db.query(Album).filter(Album.is_deleted == False).order_by(*order).all()
        return [_album_response(a, "admin", db) for a in albums]

    perms = db.query(Permission).filter(Permission.user_id == current_user.id).all()
    album_ids = [p.album_id for p in perms]
    albums = db.query(Album).filter(
        Album.id.in_(album_ids), Album.is_deleted == False
    ).order_by(*order).all()

    role_map = {p.album_id: p.role for p in perms}
    return [_album_response(a, role_map[a.id], db) for a in albums]


@router.post("/albums", status_code=status.HTTP_201_CREATED)
def create_album(
    body: dict,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    name = body["name"]
    album_date = None
    if "album_date" in body and body["album_date"]:
        try:
            album_date = date.fromisoformat(body["album_date"])
        except ValueError:
            pass
    if album_date is None:
        album_date = _parse_date_from_title(name)

    album = Album(
        name=name,
        description=body.get("description"),
        album_date=album_date,
        created_by=current_user.id,
    )
    db.add(album)
    db.commit()
    db.refresh(album)
    return _album_response(album, "admin", db)


@router.get("/albums/{album_id}")
def get_album(
    album_id: int,
    page: int = 1,
    per_page: int = 50,
    sort: str = "uploaded_at",
    order: str = "desc",
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    album = db.query(Album).filter(Album.id == album_id, Album.is_deleted == False).first()
    if not album:
        raise HTTPException(status_code=404, detail="Album not found")

    role = _get_user_role(db, current_user, album_id)
    if not role:
        raise HTTPException(status_code=403, detail="Access denied")

    sort_col = Photo.uploaded_at if sort == "uploaded_at" else Photo.exif_date_taken
    query = db.query(Photo).filter(Photo.album_id == album_id, Photo.is_deleted == False)
    query = query.order_by(sort_col.desc() if order == "desc" else sort_col.asc())

    total = query.count()
    photos = query.offset((page - 1) * per_page).limit(per_page).all()

    photo_list = []
    for p in photos:
        photo_list.append({
            "id": p.id,
            "thumb_300_url": generate_presigned_url(p.thumb_300_key),
            "thumb_800_url": generate_presigned_url(p.thumb_800_key),
            "caption": p.caption,
            "exif_date_taken": p.exif_date_taken.isoformat() if p.exif_date_taken else None,
            "width": p.width,
            "height": p.height,
            "filename": p.filename,
        })

    return {
        "album": _album_response(album, role, db),
        "photos": photo_list,
        "total": total,
        "page": page,
        "per_page": per_page,
    }


@router.patch("/albums/{album_id}")
def update_album(
    album_id: int,
    body: dict,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    album = db.query(Album).filter(Album.id == album_id, Album.is_deleted == False).first()
    if not album:
        raise HTTPException(status_code=404, detail="Album not found")

    role = _get_user_role(db, current_user, album_id)
    if role != "admin":
        raise HTTPException(status_code=403, detail="Admin role required")

    if "name" in body:
        album.name = body["name"]
    if "description" in body:
        album.description = body["description"]
    if "cover_photo_id" in body:
        album.cover_photo_id = body["cover_photo_id"]
    if "album_date" in body:
        try:
            album.album_date = date.fromisoformat(body["album_date"]) if body["album_date"] else None
        except ValueError:
            pass

    db.commit()
    db.refresh(album)
    return _album_response(album, "admin", db)


@router.delete("/albums/{album_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_album(
    album_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    album = db.query(Album).filter(Album.id == album_id, Album.is_deleted == False).first()
    if not album:
        raise HTTPException(status_code=404, detail="Album not found")

    role = _get_user_role(db, current_user, album_id)
    if role != "admin":
        raise HTTPException(status_code=403, detail="Admin role required")

    db.query(Photo).filter(Photo.album_id == album_id).update({"is_deleted": True})
    album.is_deleted = True
    db.commit()


@router.get("/albums/{album_id}/permissions")
def list_permissions(
    album_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    role = _get_user_role(db, current_user, album_id)
    if role != "admin":
        raise HTTPException(status_code=403, detail="Admin role required")

    perms = db.query(Permission).filter(Permission.album_id == album_id).all()
    result = []
    for p in perms:
        user = db.query(User).filter(User.id == p.user_id).first()
        result.append({
            "user_id": p.user_id,
            "email": user.email,
            "name": user.name,
            "role": p.role,
            "granted_at": p.granted_at.isoformat(),
        })
    return result


@router.put("/albums/{album_id}/permissions/{user_id}")
def set_permission(
    album_id: int,
    user_id: int,
    body: dict,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    role = _get_user_role(db, current_user, album_id)
    if role != "admin":
        raise HTTPException(status_code=403, detail="Admin role required")

    perm = db.query(Permission).filter(
        Permission.user_id == user_id, Permission.album_id == album_id
    ).first()

    if perm:
        perm.role = body["role"]
    else:
        perm = Permission(
            user_id=user_id,
            album_id=album_id,
            role=body["role"],
            granted_by=current_user.id,
        )
        db.add(perm)
    db.commit()
    return {"ok": True}


@router.delete("/albums/{album_id}/permissions/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def revoke_permission(
    album_id: int,
    user_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    role = _get_user_role(db, current_user, album_id)
    if role != "admin":
        raise HTTPException(status_code=403, detail="Admin role required")

    db.query(Permission).filter(
        Permission.user_id == user_id, Permission.album_id == album_id
    ).delete()
    db.commit()
