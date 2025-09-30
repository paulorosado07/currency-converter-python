from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from pydantic import ValidationError


class AppError(Exception):
    def __init__(
        self,
        code: str,
        message: str,
        details: dict | None = None,
        status_code: int = 400,
    ):
        super().__init__(message)
        self.code = code
        self.message = message
        self.details = details or {}
        self.status_code = status_code


class ErrorHandlingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        try:
            return await call_next(request)
        except AppError as e:
            return JSONResponse(
                status_code=e.status_code,
                content={
                    "error": {
                        "code": e.code,
                        "message": e.message,
                        "details": e.details,
                    }
                },
            )
        except ValidationError as e:
            return JSONResponse(
                status_code=422,
                content={
                    "error": {
                        "code": "VALIDATION_ERROR",
                        "message": "Invalid input",
                        "details": e.errors(),
                    }
                },
            )
        except Exception as e:
            return JSONResponse(
                status_code=500,
                content={
                    "error": {"code": "INTERNAL_ERROR", "message": "Unexpected error"}
                },
            )
