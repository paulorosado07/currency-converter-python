from fastapi import Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.core.security import JWTService
from app.db.session import SessionLocal
from app.db.models import User
from app.core.config import settings
from app.core.logging import log


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


async def _get_token_from_cookie_or_header(request: Request) -> str | None:

    token = request.cookies.get(settings.JWT_COOKIE_NAME)
    if token:
        log.info("deps.token.source.cookie", cookie_name=settings.JWT_COOKIE_NAME)
        return token

    log.info("deps.token.missing")
    return None


async def get_current_user(
    token: str | None = Depends(_get_token_from_cookie_or_header),
    db: Session = Depends(get_db),
) -> User:

    if not token:
        log.warning("deps.auth.missing_token")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated"
        )

    try:
        payload = JWTService.verify_token(token)
    except Exception:
        log.warning("deps.auth.invalid_token_signature")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token"
        )

    sub = payload.get("sub")

    user_id = (
        int(payload["sub"])
        if (
            "sub" in payload
            and (isinstance(sub, int) or (isinstance(sub, str) and sub.isdigit()))
        )
        else None
    )

    if not user_id:
        log.warning("deps.auth.invalid_token_payload", missing_claim="sub")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token"
        )

    user = db.get(User, user_id)
    if not user:
        log.warning("deps.auth.user_not_found", user_id=user_id)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found"
        )

    log.info("deps.auth.ok", user_id=user.id)
    return user
