from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from app.api.deps import get_db
from app.db.models import User
from app.schemas.auth import LoginRequest, TokenResponse
from app.core.security import JWTService
from app.core.config import settings
from app.core.logging import log


router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=TokenResponse)
async def login(
    payload: LoginRequest, response: Response, db: Session = Depends(get_db)
):

    email = payload.email.strip().lower()
    log.info("auth.login.start", email=email)
    # find or create (auto-provision)
    user = db.query(User).filter(User.email == email).first()
    if not user:
        log.info("auth.user.autoprovision.begin", email=email)
        user = User(email=email)
        db.add(user)
        try:
            db.commit()
            log.info("auth.user.autoprovision.ok", user_id=user.id)
        except IntegrityError:
            db.rollback()
            log.warning("auth.user.autoprovision.race_condition", email=email)
            user = db.query(User).filter(User.email == email).first()

        db.refresh(user)
    else:
        log.info("auth.user.found", user_id=user.id)

    token = JWTService.create_access_token(user_id=user.id, email=user.email)
    log.info("auth.token.issued", user_id=user.id)

    response.set_cookie(
        key=settings.JWT_COOKIE_NAME,
        value=token,
        httponly=True,
        secure=False,  # Disabled for interview/testing: cookies must be sent over HTTP
        samesite="lax",
        path="/",
        max_age=(settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60),
    )

    log.info(
        "auth.cookie.set",
        cookie_name=settings.JWT_COOKIE_NAME,
        samesite="lax",
        httponly=True,
    )

    log.info("auth.login.success", user_id=user.id)

    return TokenResponse(access_token=token, message="Login successful")
