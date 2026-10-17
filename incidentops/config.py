"""Fail closed on production configuration mistakes without logging secrets."""

import os
from urllib.parse import urlsplit


def validate_environment():
    mode = os.getenv("APP_ENV", "development")
    if mode not in {"development", "test", "production"}:
        raise ValueError("APP_ENV must be development, test, or production")
    if mode != "production":
        return
    origin = urlsplit(os.getenv("APP_ORIGIN", ""))
    if (
        origin.scheme != "https"
        or not origin.hostname
        or origin.path
        or origin.query
        or origin.fragment
        or origin.username
        or origin.password
    ):
        raise ValueError("Production APP_ORIGIN must be an exact HTTPS origin without a path")
    if not os.getenv("DATABASE_URL", "").startswith(("postgresql://", "postgresql+psycopg://")):
        raise ValueError("Production requires an explicit PostgreSQL DATABASE_URL")
