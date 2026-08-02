from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware
from app.core.config import settings

from app.api import admin, auth, albums, photos, users, share, search, storage_info
from app.middleware import RequestLoggingMiddleware

app = FastAPI(
    title="Photo Gallery API",
    docs_url="/api/photo-gallery/docs",
    openapi_url="/api/photo-gallery/openapi.json",
)

app.add_middleware(SessionMiddleware, secret_key=settings.secret_key)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://cloud.hansu.tw", "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(RequestLoggingMiddleware)

app.include_router(admin.router, prefix="/api/photo-gallery")
app.include_router(auth.router, prefix="/api/photo-gallery")
app.include_router(albums.router, prefix="/api/photo-gallery")
app.include_router(photos.router, prefix="/api/photo-gallery")
app.include_router(users.router, prefix="/api/photo-gallery")
app.include_router(share.router, prefix="/api/photo-gallery")
app.include_router(search.router, prefix="/api/photo-gallery")
app.include_router(storage_info.router, prefix="/api/photo-gallery")
