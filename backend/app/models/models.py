from datetime import datetime
from sqlalchemy import (
    Boolean, Column, Date, DateTime, Integer, BigInteger,
    String, Text, Enum, DECIMAL, ForeignKey, UniqueConstraint, Index
)
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, autoincrement=True)
    google_id = Column(String(128), unique=True, nullable=False)
    email = Column(String(255), unique=True, nullable=False)
    name = Column(String(255), nullable=False)
    avatar_url = Column(String(512), nullable=True)
    is_admin = Column(Boolean, nullable=False, default=False)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    last_login_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    permissions = relationship("Permission", foreign_keys="Permission.user_id", back_populates="user")
    albums_created = relationship("Album", back_populates="creator")

    __table_args__ = (
        Index("idx_users_google_id", "google_id"),
        Index("idx_users_email", "email"),
    )


class Album(Base):
    __tablename__ = "albums"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    cover_photo_id = Column(Integer, ForeignKey("photos.id", use_alter=True), nullable=True)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    album_date = Column(Date, nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_deleted = Column(Boolean, nullable=False, default=False)

    is_locked = Column(Boolean, nullable=False, default=False, server_default='0')
    password_hash = Column(String(255), nullable=True)

    creator = relationship("User", back_populates="albums_created")
    photos = relationship("Photo", foreign_keys="Photo.album_id", back_populates="album")
    permissions = relationship("Permission", back_populates="album")
    share_links = relationship("ShareLink", back_populates="album")


class Photo(Base):
    __tablename__ = "photos"

    id = Column(Integer, primary_key=True, autoincrement=True)
    album_id = Column(Integer, ForeignKey("albums.id"), nullable=False)
    uploaded_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    filename = Column(String(512), nullable=False)
    mime_type = Column(String(100), nullable=True)
    caption = Column(Text, nullable=True)
    storage_key = Column(String(1024), nullable=False)
    thumb_300_key = Column(String(1024), nullable=True)
    thumb_800_key = Column(String(1024), nullable=True)
    file_size_bytes = Column(BigInteger, nullable=False)
    width = Column(Integer, nullable=True)
    height = Column(Integer, nullable=True)
    exif_date_taken = Column(DateTime, nullable=True)
    exif_camera = Column(String(255), nullable=True)
    exif_gps_lat = Column(DECIMAL(10, 7), nullable=True)
    exif_gps_lon = Column(DECIMAL(10, 7), nullable=True)
    uploaded_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    is_deleted = Column(Boolean, nullable=False, default=False)

    album = relationship("Album", foreign_keys=[album_id], back_populates="photos")
    uploader = relationship("User")

    __table_args__ = (
        Index("idx_photos_album_id", "album_id"),
        Index("idx_photos_exif_date", "album_id", "exif_date_taken"),
    )


class Permission(Base):
    __tablename__ = "permissions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    album_id = Column(Integer, ForeignKey("albums.id"), nullable=False)
    role = Column(Enum("viewer", "uploader", "admin"), nullable=False)
    granted_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    granted_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    user = relationship("User", foreign_keys=[user_id], back_populates="permissions")
    album = relationship("Album", back_populates="permissions")
    granter = relationship("User", foreign_keys=[granted_by])

    __table_args__ = (
        UniqueConstraint("user_id", "album_id", name="uq_permission_user_album"),
        Index("idx_perm_user_album", "user_id", "album_id"),
        Index("idx_perm_album", "album_id"),
    )


class ShareLink(Base):
    __tablename__ = "share_links"

    id = Column(Integer, primary_key=True, autoincrement=True)
    token = Column(String(36), unique=True, nullable=False)
    album_id = Column(Integer, ForeignKey("albums.id"), nullable=False)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    expires_at = Column(DateTime, nullable=False)
    is_revoked = Column(Boolean, nullable=False, default=False)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    album = relationship("Album", back_populates="share_links")
    creator = relationship("User")

    __table_args__ = (
        Index("idx_share_token", "token"),
        Index("idx_share_album", "album_id"),
    )


class LoginLog(Base):
    __tablename__ = "login_logs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    email = Column(String(255), nullable=False)
    ip_address = Column(String(64), nullable=True)
    user_agent = Column(Text, nullable=True)
    logged_in_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    user = relationship("User")

    __table_args__ = (
        Index("idx_login_logs_user_id", "user_id"),
        Index("idx_login_logs_logged_in_at", "logged_in_at"),
    )


class RequestLog(Base):
    __tablename__ = "request_logs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    email = Column(String(255), nullable=True)
    method = Column(String(10), nullable=False)
    path = Column(String(512), nullable=False)
    status_code = Column(Integer, nullable=False)
    response_time_ms = Column(Integer, nullable=True)
    ip_address = Column(String(64), nullable=True)
    requested_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    user = relationship("User")

    __table_args__ = (
        Index("idx_request_logs_user_id", "user_id"),
        Index("idx_request_logs_requested_at", "requested_at"),
        Index("idx_request_logs_path", "path"),
    )
