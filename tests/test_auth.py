from __future__ import annotations

from typing import Any


def test_register_login_and_user_privacy(client, make_user_credentials):
    creds = make_user_credentials()

    r = client.post("/auth/register", json=creds)
    assert r.status_code == 201
    data = r.json()
    assert "id" in data
    assert data["username"] == creds["username"]

    r = client.post(
        "/auth/login",
        json={"username_or_email": creds["email"], "password": creds["password"]},
    )
    assert r.status_code == 200
    token = r.json()["access_token"]

    # Unauthorized: limited info only.
    r = client.get("/users")
    assert r.status_code == 200
    users = r.json()
    assert len(users) == 1
    assert users[0]["username"] == creds["username"]
    assert users[0]["email"] is None

    # Authorized: full info.
    r = client.get("/users", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 200
    users = r.json()
    assert users[0]["email"] == creds["email"]

