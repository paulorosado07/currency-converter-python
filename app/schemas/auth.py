from pydantic import BaseModel, EmailStr


class LoginRequest(BaseModel):
    email: EmailStr


class TokenResponse(BaseModel):
    access_token: str
    message: str
