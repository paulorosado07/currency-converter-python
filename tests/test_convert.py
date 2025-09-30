import respx
from httpx import Response
from app.db.session import SessionLocal
from app.db.models import User

API_URL = "https://api.currencyapi.com/v3/latest"


def login_and_get_user_id(client, email="conv@example.com"):

    client.post("/api/v1/auth/login", json={"email": email})
    with SessionLocal() as db:
        uid = db.query(User).filter(User.email == email).first().id
    return uid


@respx.mock
def test_convert_ok(client):
    user_id = login_and_get_user_id(client)
    mock = respx.get(API_URL).mock(
        return_value=Response(
            200, json={"data": {"BRL": {"code": "BRL", "value": 5.25}}}
        )
    )

    res = client.post(
        "/api/v1/convert",
        json={"fromCurrency": "USD", "toCurrency": "BRL", "amount": "100"},
    )
    assert res.status_code == 200, res.text
    body = res.json()
    assert round(float(body["toValue"]), 2) == 525.00
    assert mock.called


@respx.mock
def test_convert_uses_cache_on_error(client):
    _ = login_and_get_user_id(client)

    # First call returns good rate
    respx.get(API_URL).mock(
        return_value=Response(
            200, json={"data": {"EUR": {"code": "EUR", "value": 0.9}}}
        )
    )
    client.post(
        "/api/v1/convert",
        json={"fromCurrency": "USD", "toCurrency": "EUR", "amount": "10"},
    )

    # Next provider call fails; should use cached (fresh/stale)
    respx.get(API_URL).mock(return_value=Response(500))
    r2 = client.post(
        "/api/v1/convert",
        json={"fromCurrency": "USD", "toCurrency": "EUR", "amount": "2"},
    )
    assert r2.status_code == 200
