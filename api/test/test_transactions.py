import pytest

def _register_and_token(client, email="txn@nairaflow.com"):
    res = client.post("/v1/auth/register", json={
        "email": email,
        "password": "password123",
        "full_name": "Txn User",
    })
    return res.json()["access_token"]

def _auth(token):
    return {"Authorization": f"Bearer {token}"}

def test_create_transaction(client):
    token = _register_and_token(client)
    res = client.post("/v1/transactions", headers=_auth(token), json={
        "description": "Salary Credit",
        "amount": 850000,
        "type": "income",
    })
    assert res.status_code == 201
    assert res.json()["description"] == "Salary Credit"


def test_list_transactions(client):
    token = _register_and_token(client, "list@nairaflow.com")
    client.post("/v1/transactions", headers=_auth(token), json={
        "description": "Rent", "amount": 150000, "type": "expense"
    })
    res = client.get("/v1/transactions", headers=_auth(token))
    assert res.status_code == 200
    assert res.json()["total"] >= 1


def test_delete_transaction(client):
    token = _register_and_token(client, "del@nairaflow.com")
    create_res = client.post("/v1/transactions", headers=_auth(token), json={
        "description": "Test", "amount": 1000, "type": "expense"
    })
    txn_id = create_res.json()["id"]
    del_res = client.delete(f"/v1/transactions/{txn_id}", headers=_auth(token))
    assert del_res.status_code == 204


def test_get_nonexistent_transaction(client):
    token = _register_and_token(client, "none@nairaflow.com")
    res = client.get("/v1/transactions/99999", headers=_auth(token))
    assert res.status_code == 404