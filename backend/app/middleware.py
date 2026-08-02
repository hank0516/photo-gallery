import time

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

from app.core.auth import decode_access_token
from app.core.database import SessionLocal
from app.models.models import RequestLog


def _get_client_ip(request: Request) -> str | None:
    forwarded_for = request.headers.get("X-Forwarded-For")
    if forwarded_for:
        return forwarded_for.split(",")[0].strip()
    return request.client.host if request.client else None


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        start = time.monotonic()
        response = await call_next(request)
        elapsed_ms = int((time.monotonic() - start) * 1000)

        user_id = None
        email = None
        token = request.cookies.get("pg_session")
        if token:
            payload = decode_access_token(token)
            if payload:
                user_id = payload.get("user_id")
                email = payload.get("email")

        db = SessionLocal()
        try:
            db.add(RequestLog(
                user_id=user_id,
                email=email,
                method=request.method,
                path=request.url.path,
                status_code=response.status_code,
                response_time_ms=elapsed_ms,
                ip_address=_get_client_ip(request),
            ))
            db.commit()
        except Exception:
            db.rollback()
        finally:
            db.close()

        return response
