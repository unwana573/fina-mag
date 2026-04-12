import pytest


REGISTER_PAYLOAD = {
    "email": "test@nairaflow.com",
    "password": "securepassword123",
    "full_name": "Test User",
}


def test_register(client):
    res = client.post("/v1/auth/register", json=REGISTER_PAYLOAD)
    assert res.status_code == 201
    data = res.json()
    assert "access_token" in data
    assert "refresh_token" in data


def test_register_duplicate_email(client):
    client.post("/v1/auth/register", json=REGISTER_PAYLOAD)
    res = client.post("/v1/auth/register", json=REGISTER_PAYLOAD)
    assert res.status_code == 409


def test_login_success(client):
    client.post("/v1/auth/register", json=REGISTER_PAYLOAD)
    res = client.post("/v1/auth/login", json={
        "email": REGISTER_PAYLOAD["email"],
        "password": REGISTER_PAYLOAD["password"],
    })
    assert res.status_code == 200
    assert "access_token" in res.json()


def test_login_wrong_password(client):
    client.post("/v1/auth/register", json=REGISTER_PAYLOAD)
    res = client.post("/v1/auth/login", json={
        "email": REGISTER_PAYLOAD["email"],
        "password": "wrongpassword",
    })
    assert res.status_code == 401


def test_refresh_token(client):
    reg = client.post("/v1/auth/register", json={
        **REGISTER_PAYLOAD, "email": "refresh@nairaflow.com"
    })
    refresh_token = reg.json()["refresh_token"]
    res = client.post("/v1/auth/refresh", json={"refresh_token": refresh_token})
    assert res.status_code == 200
    assert "access_token" in res.json()


def test_get_me(client):
    reg = client.post("/v1/auth/register", json={
        **REGISTER_PAYLOAD, "email": "me@nairaflow.com"
    })
    token = reg.json()["access_token"]
    res = client.get("/v1/users/me", headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 200
    assert res.json()["email"] == "me@nairaflow.com"