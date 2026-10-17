"""Vercel adapter; the original API and its security middleware stay intact."""

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from incidentops.config import validate_environment
from incidentops.main import app as api

validate_environment()
app = FastAPI(docs_url=None, redoc_url=None, openapi_url=None)
app.mount("/api", api)
# Declare the build output as a static mount so the platform's Python builder
# discovers and packages the assets. Keep /api first in route precedence.
app.mount("/", StaticFiles(directory="frontend/dist", html=True, check_dir=False))
