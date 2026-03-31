from __future__ import annotations

import time

import pytest


def register_and_login(client, creds: dict) -> str:
    r = client.post("/auth/register", json=creds)
    assert r.status_code == 201
    r = client.post(
        "/auth/login",
        json={"username_or_email": creds["email"], "password": creds["password"]},
    )
    assert r.status_code == 200
    return r.json()["access_token"]


@pytest.mark.parametrize("vote_type", ["like", "dislike"])
def test_upsert_vote_and_aggregation_top_voters(client, make_user_credentials, vote_type):
    author = make_user_credentials()
    author_token = register_and_login(client, author)

    voters = [make_user_credentials() for _ in range(6)]
    voter_tokens = [register_and_login(client, v) for v in voters]

    # Create a post (author upsert).
    image_bytes = b"fake-image-bytes"
    r = client.post(
        "/posts",
        headers={"Authorization": f"Bearer {author_token}"},
        data={"post_key": "post_1", "title": "Hello", "content": "World"},
        files={"image": ("pic.png", image_bytes, "image/png")},
    )
    assert r.status_code == 201
    post_id = r.json()["id"]

    # Cast votes. We vote sequentially so voted_at ordering is stable.
    for i, t in enumerate(voter_tokens):
        vt = vote_type  # all six voters use the same vote type in this test
        client.post(
            f"/posts/{post_id}/vote",
            headers={"Authorization": f"Bearer {t}"},
            json={"vote_type": vt},
        )
        time.sleep(0.01)

    # Fetch author id from /users.
    ru = client.get("/users", headers={"Authorization": f"Bearer {author_token}"})
    assert ru.status_code == 200
    author_id = next(u["id"] for u in ru.json() if u["username"] == author["username"])

    # Read posts by author with aggregates.
    r = client.get(
        "/posts/by-user",
        headers={"Authorization": f"Bearer {author_token}"},
        params={"user_id": author_id},
    )

    assert r.status_code == 200
    body = r.json()
    assert body["total"] == 1
    assert len(body["posts"]) == 1
    post = body["posts"][0]

    expected_likes = 6 if vote_type == "like" else 0
    expected_dislikes = 6 if vote_type == "dislike" else 0
    assert post["likes_count"] == expected_likes
    assert post["dislikes_count"] == expected_dislikes

    if vote_type == "like":
        assert len(post["recently_liked_users"]) == 5
        assert len(post["recently_disliked_users"]) == 0
    else:
        assert len(post["recently_disliked_users"]) == 5
        assert len(post["recently_liked_users"]) == 0

    # Top posts endpoint.
    r = client.get(
        "/posts/top",
        headers={"Authorization": f"Bearer {author_token}"},
        params={"vote_type": vote_type, "limit": 10, "user_id": author_id},
    )
    assert r.status_code == 200
    top = r.json()
    assert top["vote_type"] == vote_type
    assert len(top["posts"]) == 1
    assert top["posts"][0]["likes_count"] == (6 if vote_type == "like" else 0)
    assert top["posts"][0]["dislikes_count"] == (6 if vote_type == "dislike" else 0)

