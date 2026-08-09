import uuid
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, Query, status
from typing import Optional
from sqlalchemy.orm import Session

from app.core.auth import require_admin
from app.core.database import get_db
from app.core.security import create_share_unlock_token, decode_share_unlock_token, verify_password
from app.core.storage import generate_presigned_url
from app.models.models import Album, Photo, ShareLink, User

router = APIRouter(tags=["share"])


def _link_response(link: ShareLink) -> dict:
    now = datetime.utcnow()
    return {
        "token": link.token,
        "album_id": link.album_id,
        "expires_at": link.expires_at.isoformat(),
        "is_revoked": link.is_revoked,
        "is_expired": link.expires_at < now,
        "created_at": link.created_at.isoformat(),
    }


@router.post("/albums/{album_id}/share", status_code=status.HTTP_201_CREATED)
def create_share_link(
    album_id: int,
    body: dict,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    album = db.query(Album).filter(Album.id == album_id, Album.is_deleted == False).first()
    if not album:
        raise HTTPException(status_code=404, detail="Album not found")

    expires_days = int(body.get("expires_days", 7))
    if expires_days < 1 or expires_days > 365:
        raise HTTPException(status_code=400, detail="expires_days 必須在 1~365 之間")

    link = ShareLink(
        token=str(uuid.uuid4()),
        album_id=album_id,
        created_by=current_user.id,
        expires_at=datetime.utcnow() + timedelta(days=expires_days),
    )
    db.add(link)
    db.commit()
    db.refresh(link)
    return _link_response(link)


@router.get("/albums/{album_id}/share")
def list_share_links(
    album_id: int,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    album = db.query(Album).filter(Album.id == album_id, Album.is_deleted == False).first()
    if not album:
        raise HTTPException(status_code=404, detail="Album not found")

    links = (
        db.query(ShareLink)
        .filter(ShareLink.album_id == album_id)
        .order_by(ShareLink.created_at.desc())
        .all()
    )
    return [_link_response(l) for l in links]


@router.delete("/share/{token}", status_code=status.HTTP_204_NO_CONTENT)
def revoke_share_link(
    token: str,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    link = db.query(ShareLink).filter(ShareLink.token == token).first()
    if not link:
        raise HTTPException(status_code=404, detail="Share link not found")
    link.is_revoked = True
    db.commit()


@router.get("/share/{token}")
def get_shared_album(
    token: str,
    page: int = 1,
    per_page: int = 100,
    unlock_token: Optional[str] = Query(default=None),
    db: Session = Depends(get_db),
):
    link = db.query(ShareLink).filter(ShareLink.token == token).first()
    if not link:
        raise HTTPException(status_code=404, detail="找不到此分享連結")
    if link.is_revoked:
        raise HTTPException(status_code=410, detail="此分享連結已被撤銷")
    if link.expires_at < datetime.utcnow():
        raise HTTPException(status_code=410, detail="此分享連結已過期")

    album = db.query(Album).filter(Album.id == link.album_id, Album.is_deleted == False).first()
    if not album:
        raise HTTPException(status_code=404, detail="相簿不存在或已刪除")

    album_info = {"id": album.id, "name": album.name, "description": album.description}

    if album.is_locked:
        if not unlock_token:
            return {"album": album_info, "locked": True, "photos": [], "total": 0, "page": page, "per_page": per_page, "expires_at": link.expires_at.isoformat()}
        payload = decode_share_unlock_token(unlock_token)
        if not payload or payload.get("album_id") != album.id or payload.get("share_token") != token:
            return {"album": album_info, "locked": True, "photos": [], "total": 0, "page": page, "per_page": per_page, "expires_at": link.expires_at.isoformat()}

    query = db.query(Photo).filter(Photo.album_id == album.id, Photo.is_deleted == False)
    query = query.order_by(Photo.uploaded_at.desc())
    total = query.count()
    photos = query.offset((page - 1) * per_page).limit(per_page).all()

    photo_list = []
    for p in photos:
        photo_list.append({
            "id": p.id,
            "thumb_300_url": generate_presigned_url(p.thumb_300_key) if p.thumb_300_key else None,
            "thumb_800_url": generate_presigned_url(p.thumb_800_key) if p.thumb_800_key else None,
            "original_url": generate_presigned_url(p.storage_key),
            "mime_type": p.mime_type,
            "caption": p.caption,
            "exif_date_taken": p.exif_date_taken.isoformat() if p.exif_date_taken else None,
            "width": p.width,
            "height": p.height,
            "filename": p.filename,
        })

    return {
        "album": album_info,
        "expires_at": link.expires_at.isoformat(),
        "photos": photo_list,
        "total": total,
        "page": page,
        "per_page": per_page,
    }


@router.post("/share/{token}/unlock")
def unlock_shared_album(
    token: str,
    body: dict,
    db: Session = Depends(get_db),
):
    link = db.query(ShareLink).filter(ShareLink.token == token).first()
    if not link:
        raise HTTPException(status_code=404, detail="找不到此分享連結")
    if link.is_revoked:
        raise HTTPException(status_code=410, detail="此分享連結已被撤銷")
    if link.expires_at < datetime.utcnow():
        raise HTTPException(status_code=410, detail="此分享連結已過期")

    album = db.query(Album).filter(Album.id == link.album_id, Album.is_deleted == False).first()
    if not album or not album.is_locked:
        raise HTTPException(status_code=400, detail="此相簿未設定密碼")

    if not verify_password(body.get("password", ""), album.password_hash or ""):
        raise HTTPException(status_code=401, detail="密碼錯誤")

    return {"unlock_token": create_share_unlock_token(album.id, token)}
