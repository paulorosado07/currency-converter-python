from app.db.session import SessionLocal
from app.db.models import User
from sqlalchemy import inspect
from faker import Faker


def test_login_autoprovision(client):
    fake = Faker()
    email = fake.company_email()

    # ensure user does not exist yet
    with SessionLocal() as db:
        assert db.query(User).filter(User.email == email).first() is None

    res = client.post("/api/v1/auth/login", json={"email": email})
    assert res.status_code == 200, res.text
    data = res.json()
    assert "access_token" in data

    # user should now exist
    with SessionLocal() as db:
        u = db.query(User).filter(User.email == email).first()
        assert u is not None
