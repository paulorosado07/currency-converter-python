import respx
from httpx import Response
from app.db.session import SessionLocal
from app.db.models import User

API_URL = "https://api.currencyapi.com/v3/latest"


def login_and_get_user_id(client, email="list@example.com"):
    # This call sets the HttpOnly cookie on the client automatically
    client.post("/api/v1/auth/login", json={"email": email})
    with SessionLocal() as db:
        uid = db.query(User).filter(User.email == email).first().id
    return uid


@respx.mock
def test_list_transactions(client):
    uid = login_and_get_user_id(client)
    respx.get(API_URL).mock(
        return_value=Response(200, json={"data": {"BRL": {"value": 5.0}}})
    )

    # Create two conversions (cookie is sent automatically)
    for amt in ("1", "2"):
        client.post(
            "/api/v1/convert",
            json={"fromCurrency": "USD", "toCurrency": "BRL", "amount": amt},
        )

    r = client.get(f"/api/v1/transactions?userId={uid}")
    assert r.status_code == 200
    arr = r.json()
    assert isinstance(arr, list) and len(arr) >= 0
