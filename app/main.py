from __future__ import annotations

from fastapi import FastAPI

from dotenv import load_dotenv

from app.config import get_app_title
from app.db import init_db
from app.routes import router as api_router


def create_app() -> FastAPI:
    # Load local .env for development convenience.
    # Env vars still take precedence if already set.
    load_dotenv(override=False)

    app = FastAPI(title=get_app_title())
    app.include_router(api_router)

    @app.on_event("startup")
    def _startup() -> None:
        init_db()

    return app


app = create_app()

