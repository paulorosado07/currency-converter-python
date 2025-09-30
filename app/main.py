from fastapi import FastAPI
from app.core.config import settings
from app.core.logging import RequestIdMiddleware
from app.core.rate_limit import RateLimitMiddleware
from app.middlewares.error_handler import ErrorHandlingMiddleware
from app.api.routers import auth, convert, transactions
from app.db.session import engine
from app.db.base import Base

# Create tables (for dev). In prod, use Alembic migrations.
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Currency Converter API", version="1.0.0")

# Middlewares
app.add_middleware(RequestIdMiddleware)
app.add_middleware(RateLimitMiddleware)
app.add_middleware(ErrorHandlingMiddleware)

# Routers
app.include_router(auth.router, prefix=settings.API_V1_PREFIX)
app.include_router(convert.router, prefix=settings.API_V1_PREFIX)
app.include_router(transactions.router, prefix=settings.API_V1_PREFIX)


@app.get("/healthz")
async def healthz():
    return {"status": "ok"}
    
@app.get("/")
def root():
    return {"message": "FastAPI is up!"}
