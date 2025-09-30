import time
from typing import Dict, Tuple
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse
from app.core.config import settings
from cachetools import TTLCache


_last_seen: Dict[str, float] = TTLCache(maxsize=10_000, ttl=60)


class RateLimitMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        now = time.monotonic()
        ip = (
            request.headers.get("x-forwarded-for", request.client.host or "unknown")
            .split(",")[0]
            .strip()
        )
        user = request.headers.get("authorization", "unauthenticated")

        for key in (f"ip:{ip}", f"user:{user}"):
            last = _last_seen.get(key, 0.0)
            if now - last < 1.0 / settings.RATE_LIMIT_PER_SECOND:
                return JSONResponse(
                    status_code=429,
                    content={
                        "error": {
                            "code": "RATE_LIMIT_EXCEEDED",
                            "message": "Too many requests. Please retry shortly.",
                            "details": {"key": key},
                        }
                    },
                    headers={"Retry-After": str(settings.RATE_LIMIT_DELAY_SECONDS)},
                )
            _last_seen[key] = now
        response = await call_next(request)
        return response
