# 🚀 Project Overview

This project is a **FastAPI** application packaged in a **Docker** container for easy execution and distribution.
It exposes a local API with an interactive **Swagger UI** documentation, allowing developers to explore and test the endpoints conveniently.

> ⚠️ **Prerequisite**: You must have **Docker** installed on your machine to run this project.



## ▶️ How to Run

To run the application using Docker, follow the steps below:

```bash
# 1. Build the Docker image
docker build -t app-fastapi .

# 2. Run the container and expose it on port 8000
docker run --rm -p 8000:8000 app-fastapi
```

Once the container is running, the API will be available at:
👉 [http://localhost:8000](http://localhost:8000)

Interactive API docs (Swagger UI) can be accessed at:
👉 [http://localhost:8000/docs](http://localhost:8000/docs)

## ⚙️ Environment Configuration (`.env`)

The project requires environment variables to be set before running.
For security reasons, the actual `.env` file should **not** be committed to Git. Instead, the repository includes a `.env.example` file that developers can use as a template.

### Steps:

1. Copy the example file:

   ```bash
   cp .env.example .env
   ```
2. Edit `.env` and add your API Key:

   ```ini
   CURRENCY_API_BASE_URL=https://api.currencyapi.com/v3/latest
   CURRENCY_API_KEY=YOUR_API_KEY   # Replace with your valid key
   JWT_SECRET=dev-secret-change-me
   DATABASE_URL=sqlite:///./app.db
   ```

> 🔑 **Note:** Without a valid `CURRENCY_API_KEY`, requests to the Currency API will not work.

---
## Purpose of the Project
The project was created to provide currency conversion functionality. It is designed for people who want to stay updated with exchange rates and perform accurate currency conversions in a simple and efficient way.


## Architecture Decisions

* **Caching Strategy:** Implemented caching at two levels:

  * Exchange rate API requests are cached to speed up responses and reduce calls to the external API.
  * In-memory caching with *cachetools* stores temporary data efficiently, discarding old entries to prevent memory overuse.

* **Database:** Chose SQLite for its simplicity and ease of setup (no system installation required), which accelerated development and delivery. Added indexes on the `user_id` column of the `transactions` table to improve query performance.

* **Authentication Flow:** Implemented a simplified login that requires only the user’s email. If the email exists, it authenticates; otherwise, the user is automatically registered and logged in. This reduced development time for user management.

* **JWT Tokens:** Added JWT authentication for better performance and scalability. It allows fast validation without constant database lookups, saving resources and improving responsiveness for future growth.

* **Testing Utilities:** Used the *Faker* library to generate fake data (e.g., emails), which streamlined testing and eliminated the need to manually create new records for each test.



# Organization of Layers

**Architecture:** Routers → Services → Repositories → DB/Models. Cross-cutting: Config, Security, Logging, Rate limiting, Error handling.

## API (Routers) - `app/api/routers/*`

* **`auth.py`**: `POST /api/v1/auth/login` - email login, auto-provision user, issues JWT (HttpOnly cookie).
* **`convert.py`**: `POST /api/v1/convert` - converts amount and persists a transaction. Requires auth.
* **`transactions.py`**: `GET /api/v1/transactions?userId=` - lists user transactions (newest first). Requires auth.
* **Deps** (`deps.py`): `get_db()` per-request session; `get_current_user()` reads/validates JWT and loads `User`.

## Schemas - `app/schemas/*`

* `ConvertRequest`, `TransactionDTO`, `LoginRequest`, and `TokenResponse`.
* Pydantic for validation and I/O.

## Services - `app/services/*`

* **`TransactionService`**: validates amount, fetches FX rate, computes `to_value` (banker’s rounding, 10dp), persists snapshot.
* **`CurrencyService`**: CurrencyAPI via `httpx`, supports `BRL/USD/EUR/JPY`, in-memory cache (TTL), retries, stale-if-error; `quantize_for_display` (JPY=0 dp, others=2 dp).

## Repositories - `app/repositories/*`

* **`TransactionRepository`**: `create(...)`, `list_by_user(...)`. Encapsulates DB writes/queries using provided session.

## Data / ORM - `app/db/*`

* **Models**: `User`, `Transaction` (+ index on `user_id, timestamp DESC`).
* **Session**: engine & `SessionLocal` from `DATABASE_URL`.
* **Base**: SQLAlchemy declarative base.

## Core & Middleware - `app/core/*`, `app/middlewares/*`

* **Config**: env-driven settings (DB, JWT, CurrencyAPI, cache TTL, rate limits, etc.).
* **Security**: JWT (HS256) - `sub`, `email`, `iat`, `exp`.
* **Logging**: structlog (JSON) + `RequestIdMiddleware`.
* **Rate limiting**: simple in-process limiter (per IP & Authorization).
* **Errors**: middleware returns `{ error: { code, message, details } }` for app/validation/unexpected errors.

## Request Flow (example)

`Router → (Deps: auth + db) → Service (rules + CurrencyAPI + rounding) → Repository → DB → DTO response`

**Key policies:** supported currencies `BRL, USD, EUR, JPY`; store values/rates at **10 dp** (ROUND_HALF_EVEN); display uses currency-aware decimals; auth via HttpOnly cookie.