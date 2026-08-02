from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import desc
from sqlalchemy.orm import Session

from app.core.auth import require_admin
from app.core.database import get_db
from app.models.models import Album, LoginLog, Permission, RequestLog, User

router = APIRouter(prefix="/admin", tags=["admin"])


class UserUpdate(BaseModel):
    is_admin: Optional[bool] = None


@router.get("/users")
def list_users(
    _: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    users = db.query(User).order_by(User.created_at).all()
    return [
        {
            "id": u.id,
            "email": u.email,
            "name": u.name,
            "avatar_url": u.avatar_url,
            "is_admin": u.is_admin,
            "created_at": u.created_at.isoformat(),
            "last_login_at": u.last_login_at.isoformat() if u.last_login_at else None,
        }
        for u in users
    ]


@router.patch("/users/{user_id}")
def update_user(
    user_id: int,
    body: UserUpdate,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if user.id == current_user.id:
        raise HTTPException(status_code=400, detail="Cannot modify your own admin status")
    if body.is_admin is not None:
        user.is_admin = body.is_admin
    db.commit()
    return {"id": user.id, "is_admin": user.is_admin}


@router.get("/users/{user_id}/permissions")
def get_user_permissions(
    user_id: int,
    _: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    albums = db.query(Album).filter(Album.is_deleted == False).order_by(Album.name).all()
    perms = {
        p.album_id: p.role
        for p in db.query(Permission).filter(Permission.user_id == user_id).all()
    }
    return [
        {"album_id": a.id, "album_name": a.name, "role": perms.get(a.id)}
        for a in albums
    ]


@router.get("/login-logs")
def list_login_logs(
    page: int = 1,
    per_page: int = 50,
    email: str = "",
    _: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    per_page = min(per_page, 100)
    q = db.query(LoginLog).order_by(desc(LoginLog.logged_in_at))
    if email:
        q = q.filter(LoginLog.email.contains(email))
    total = q.count()
    items = q.offset((page - 1) * per_page).limit(per_page).all()
    return {
        "total": total,
        "page": page,
        "per_page": per_page,
        "items": [
            {
                "id": l.id,
                "email": l.email,
                "ip_address": l.ip_address,
                "user_agent": l.user_agent,
                "logged_in_at": l.logged_in_at.isoformat(),
            }
            for l in items
        ],
    }


@router.get("/request-logs")
def list_request_logs(
    page: int = 1,
    per_page: int = 50,
    email: str = "",
    path: str = "",
    method: str = "",
    _: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    per_page = min(per_page, 100)
    q = db.query(RequestLog).order_by(desc(RequestLog.requested_at))
    if email:
        q = q.filter(RequestLog.email.contains(email))
    if path:
        q = q.filter(RequestLog.path.contains(path))
    if method:
        q = q.filter(RequestLog.method == method.upper())
    total = q.count()
    items = q.offset((page - 1) * per_page).limit(per_page).all()
    return {
        "total": total,
        "page": page,
        "per_page": per_page,
        "items": [
            {
                "id": r.id,
                "email": r.email,
                "method": r.method,
                "path": r.path,
                "status_code": r.status_code,
                "response_time_ms": r.response_time_ms,
                "ip_address": r.ip_address,
                "requested_at": r.requested_at.isoformat(),
            }
            for r in items
        ],
    }
