from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse
from starlette.types import ASGIApp, Receive, Scope, Send
from typing import Callable
from .auth import decode_token


class AdminAuthMiddleware(BaseHTTPMiddleware):
    def __init__(self, app: ASGIApp):
        super().__init__(app)

    async def dispatch(self, request, call_next: Callable):
        path = request.url.path
        # protect admin routes except login
        if path.startswith("/api/admin") and not path.startswith("/api/admin/login"):
            auth = request.headers.get("authorization")
            if not auth:
                return JSONResponse({"detail": "Missing authorization header"}, status_code=401)

            parts = auth.split()
            if len(parts) != 2 or parts[0].lower() != "bearer":
                return JSONResponse({"detail": "Invalid authorization format"}, status_code=401)

            token = parts[1]
            payload = decode_token(token)
            if not payload:
                return JSONResponse({"detail": "Invalid token"}, status_code=401)
            # attach user identity to request state
            request.state.user = payload.get("sub")
        return await call_next(request)
