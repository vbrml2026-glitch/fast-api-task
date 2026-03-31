# FastAPI Social Task (Users, Posts, Likes/Dislikes)

This project implements the requested FastAPI + PostgreSQL demo:
- Register/Login with JWT authentication (`HS256` by default; `RS256` optional)
- Users listing (public vs authorized detail)
- Post create/update (single protected upsert endpoint with optional image upload)
- Vote (like/dislike) on posts
- Aggregations:
  - Posts by user with total likes/dislikes + recently voted top 5 users (like/dislike)
  - Top liked/disliked posts (top 10/50) with optional author filter
- Unit tests (pytest)

## Tech
- FastAPI (OpenAPI v3 generated automatically)
- PostgreSQL (verification script in `db/init.sql`)
- SQLAlchemy ORM
- JWT + password hashing (passlib)

## Requirements
- Python 3.11+
- PostgreSQL 13+
- Docker (optional, easiest way to run PostgreSQL locally)

## Environment Variables
The app reads configuration from `.env` at startup.

To run with your chosen database, copy the correct template into `.env`:
- SQLite: copy `.env.sqlite.example` -> `.env`
- PostgreSQL: copy `.env.postgres.example` -> `.env`

### Required
- `DATABASE_URL` (PostgreSQL connection string for the app)
- `JWT_SECRET` (used for HS256)

### Optional
- `JWT_ALGORITHM` (`HS256` default, `RS256` supported if keys are provided)
- `JWT_PRIVATE_KEY_PEM`, `JWT_PUBLIC_KEY_PEM` (needed only for `RS256`)
- `ACCESS_TOKEN_EXPIRE_MINUTES`

## PostgreSQL Setup + Seed Data
The repository includes a verification script:
- `db/init.sql` (creates tables + inserts sample users/posts/votes)

Example (adjust credentials/database name):
```bash
psql -U postgres -d fastapi_task -f db/init.sql
```

### Recommended: Run PostgreSQL with Docker Compose
```bash
docker compose up -d
docker exec -i fastapi-pg psql -U postgres -d fastapi_task < db/init.sql
```

## Quick DB Switching (SQLite <-> PostgreSQL)
Two ready env templates are included:
- `.env.sqlite.example`
- `.env.postgres.example`

Switch to SQLite:
```bash
cp .env.sqlite.example .env
```

Switch to PostgreSQL:
```bash
cp .env.postgres.example .env
docker compose up -d
docker exec -i fastapi-pg psql -U postgres -d fastapi_task < db/init.sql
```

## Run with SQLite (recommended for quick testing)
```bash
cp .env.sqlite.example .env
./.venv/bin/uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

## Run with PostgreSQL (recommended for verification)
```bash
cp .env.postgres.example .env
docker compose up -d
docker exec -i fastapi-pg psql -U postgres -d fastapi_task < db/init.sql
./.venv/bin/uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

## Run the API
```bash
./.venv/bin/uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

OpenAPI docs:
- http://localhost:8000/docs
- http://localhost:8000/openapi.json

## Endpoints (high level)
- `POST /auth/register`
- `POST /auth/login`
- `GET /users` (optional `ids`, paging + sorting; returns limited info when unauthenticated)
- `POST /posts` (protected; form-data upsert with `post_key`, `title`, `content`, optional `image`)
- `GET /posts/by-user` (protected; filters + paging + sorting; includes aggregates and recent voter top 5)
- `POST /posts/{post_id}/vote` (protected; like/dislike)
- `GET /posts/top` (protected; top liked/disliked posts; `limit` 10-50; optional `user_id` filter)

## Testing
```bash
./.venv/bin/pytest -q
```

