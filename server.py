"""Vercel adapter; the original API and its security middleware stay intact."""

from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse

from incidentops.config import validate_environment
from incidentops.main import app as api

validate_environment()
app = FastAPI(docs_url=None, redoc_url=None, openapi_url=None)
app.mount("/api", api)


@app.get("/", include_in_schema=False)
def frontend():
    return FileResponse(Path(__file__).parent / "public" / "index.html")
