FROM python:3.12-slim
WORKDIR /app
COPY pyproject.toml ./
COPY incidentops ./incidentops
RUN pip install --no-cache-dir . && useradd --system --create-home incidentops
COPY alembic.ini ./
COPY migrations ./migrations
USER incidentops
EXPOSE 8000
CMD ["sh", "-c", "python -m alembic upgrade head && python -m uvicorn incidentops.main:app --host 0.0.0.0 --port 8000"]
