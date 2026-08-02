from datetime import datetime

from authlib.integrations.starlette_client import OAuth
from fastapi import APIRouter, Depends, Response
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from starlette.requests import Request

from app.core.auth import create_access_token, get_current_user
from app.core.config import settings
from app.core.database import get_db
from app.models.models import User

router = APIRouter(tags=["auth"])

oauth = OAuth()
oauth.register(
    name="google",
    client_id=settings.google_client_id,
    client_secret=settings.google_client_secret,
    server_metadata_url="https://accounts.google.com/.well-known/openid-configuration",
    client_kwargs={"scope": "openid email profile"},
)


@router.get("/auth/login")
async def login(request: Request):
    return await oauth.google.authorize_redirect(request, settings.google_redirect_uri)


@router.get("/auth/callback")
async def callback(request: Request, db: Session = Depends(get_db)):
    token = await oauth.google.authorize_access_token(request)
    user_info = token.get("userinfo")

    user = db.query(User).filter(User.google_id == user_info["sub"]).first()
    if user:
        user.last_login_at = datetime.utcnow()
        user.name = user_info.get("name", user.name)
        user.avatar_url = user_info.get("picture", user.avatar_url)
    else:
        user = User(
            google_id=user_info["sub"],
            email=user_info["email"],
            name=user_info.get("name", ""),
            avatar_url=user_info.get("picture"),
            is_admin=user_info["email"] == settings.bootstrap_admin_email,
        )
        db.add(user)

    db.commit()
    db.refresh(user)

    access_token = create_access_token({"user_id": user.id, "email": user.email, "is_admin": user.is_admin})

    response = RedirectResponse(url="/sites/photo-gallery/")
    response.set_cookie(
        key="pg_session",
        value=access_token,
        httponly=True,
        secure=True,
        samesite="lax",
        max_age=86400,
    )
    return response


@router.post("/auth/logout")
async def logout(response: Response):
    response.delete_cookie("pg_session")
    return {"ok": True}


@router.get("/auth/me")
async def me(current_user: User = Depends(get_current_user)):
    return {
        "id": current_user.id,
        "email": current_user.email,
        "name": current_user.name,
        "avatar_url": current_user.avatar_url,
        "is_admin": current_user.is_admin,
    }
