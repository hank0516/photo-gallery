import asyncio
import time
from concurrent.futures import ThreadPoolExecutor

from starlette.requests import Request
from starlette.types import ASGIApp, Receive, Scope, Send

from app.core.auth import decode_access_token
from app.core.database import SessionLocal
from app.models.models import RequestLog

_executor = ThreadPoolExecutor(max_workers=4)


def _get_client_ip(headers: dict, client_host) -> str | None:
    forwarded_for = headers.get(b"x-forwarded-for", b"").decode()
    if forwarded_for:
        return forwarded_for.split(",")[0].strip()
    return client_host


def _write_log(user_id, email, method, path, status_code, elapsed_ms, ip_address):
    db = SessionLocal()
    try:
        db.add(RequestLog(
            user_id=user_id,
            email=email,
            method=method,
            path=path,
            status_code=status_code,
            response_time_ms=elapsed_ms,
            ip_address=ip_address,
        ))
        db.commit()
    except Exception:
        db.rollback()
    finally:
        db.close()


class RequestLoggingMiddleware:
    def __init__(self, app: ASGIApp):
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        start = time.monotonic()
        status_code = 500

        async def send_wrapper(message):
            nonlocal status_code
            if message["type"] == "http.response.start":
                status_code = message["status"]
            await send(message)

        try:
            await self.app(scope, receive, send_wrapper)
        finally:
            elapsed_ms = int((time.monotonic() - start) * 1000)
            request = Request(scope)

            user_id, email = None, None
            token = request.cookies.get("pg_session")
            if token:
                payload = decode_access_token(token)
                if payload:
                    user_id = payload.get("user_id")
                    email = payload.get("email")

            headers = dict(scope.get("headers", []))
            client = scope.get("client")
            client_host = client[0] if client else None
            ip_address = _get_client_ip(headers, client_host)

            qs = scope.get("query_string", b"").decode()
            path = scope.get("path", "")
            full_path = f"{path}?{qs}" if qs else path

            asyncio.get_event_loop().run_in_executor(
                _executor,
                _write_log,
                user_id, email, request.method, full_path,
                status_code, elapsed_ms, ip_address,
            )
