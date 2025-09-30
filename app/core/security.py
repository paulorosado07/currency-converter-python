import time
from typing import Optional
import jwt
from fastapi import HTTPException, status

from app.core.config import settings


class JWTService:
    @staticmethod
    def create_access_token(*, user_id: int, email: str) -> str:
        now = int(time.time())
        exp = now + settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
        payload = {"sub": str(user_id), "email": email, "iat": now, "exp": exp}
        token = jwt.encode(
            payload, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM
        )
        return token

    @staticmethod
    def verify_token(token: str) -> dict:
        try:
            return jwt.decode(
                token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM]
            )
        except jwt.ExpiredSignatureError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="Token expired"
            )
        except jwt.PyJWTError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token"
            )
