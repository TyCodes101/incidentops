"""Cookie-authenticated incident command API."""

import os
import time
from collections import defaultdict, deque
from enum import Enum

from fastapi import Depends, FastAPI, HTTPException, Query, Request, Response
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from incidentops.analyzer import router as analyzer_router
from incidentops.db import get_db
from incidentops.models import Incident, IncidentEvent, LoginSession, Note, User, utcnow
from incidentops.schemas import (
    EventRead,
    IncidentCreate,
    IncidentRead,
    IncidentUpdate,
    Severity,
    Status,
)
from incidentops.security import (
    DUMMY_HASH,
    admin,
    current_user,
    digest,
    hasher,
    start_session,
    verify,
    writer,
)

app = FastAPI(title="IncidentOps", version="1.0.0")
app.include_router(analyzer_router)
attempts = defaultdict(deque)


@app.middleware("http")
async def guard(request: Request, call_next):
    if request.method not in {"GET", "HEAD", "OPTIONS"}:
        origin = request.headers.get("origin")
        allowed = os.getenv("APP_ORIGIN", "http://localhost:5173")
        if origin and origin != allowed:
            from starlette.responses import JSONResponse

            return JSONResponse({"detail": "Origin rejected"}, status_code=403)
        if len(await request.body()) > 65536:
            from starlette.responses import JSONResponse

            return JSONResponse({"detail": "Request too large"}, status_code=413)
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "same-origin"
    response.headers["Cache-Control"] = "no-store"
    return response


class Login(BaseModel):
    username: str = Field(min_length=1, max_length=80)
    password: str = Field(min_length=1, max_length=200)


class UserCreate(Login):
    password: str = Field(min_length=12, max_length=200)
    role: str = Field(pattern="^(admin|analyst|viewer)$")


class NoteCreate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)
    body: str = Field(min_length=1, max_length=3000)


def user_read(user):
    return {"id": user.id, "username": user.username, "role": user.role}


@app.get("/health")
def health(db: Session = Depends(get_db)):
    db.execute(select(1))
    return {"status": "ok"}


@app.post("/auth/login")
def login(payload: Login, request: Request, response: Response, db: Session = Depends(get_db)):
    key = request.client.host
    now = time.monotonic()
    queue = attempts[key]
    while queue and queue[0] < now - 60:
        queue.popleft()
    if len(queue) >= 10:
        raise HTTPException(429, "Too many attempts; retry in one minute")
    queue.append(now)
    user = db.scalar(select(User).where(User.username == payload.username))
    valid = verify(payload.password, user.password_hash if user else DUMMY_HASH)
    if not user or not valid:
        raise HTTPException(401, "Incorrect username or password")
    start_session(db, user, response)
    return user_read(user)


@app.get("/auth/me")
def me(user: User = Depends(current_user)):
    return user_read(user)


@app.post("/auth/logout", status_code=204)
def logout(
    request: Request,
    response: Response,
    user: User = Depends(current_user),
    db: Session = Depends(get_db),
):
    session = db.get(LoginSession, digest(request.cookies.get("session", "")))
    db.delete(session)
    db.commit()
    response.delete_cookie("session")
    response.delete_cookie("csrf")


@app.get("/users")
def users(user: User = Depends(current_user), db: Session = Depends(get_db)):
    return [user_read(u) for u in db.scalars(select(User).order_by(User.username))]


@app.post("/users", status_code=201)
def create_user(payload: UserCreate, user: User = Depends(admin), db: Session = Depends(get_db)):
    if db.scalar(select(User).where(User.username == payload.username)):
        raise HTTPException(409, "Username already exists")
    item = User(
        username=payload.username, password_hash=hasher.hash(payload.password), role=payload.role
    )
    db.add(item)
    db.commit()
    return user_read(item)


def find(db, incident_id):
    item = db.get(Incident, incident_id)
    if item is None:
        raise HTTPException(404, "Incident not found")
    return item


def audit(db, item, user, action, detail):
    db.add(IncidentEvent(incident_id=item.id, actor=user.username, action=action, detail=detail))


@app.post("/incidents", response_model=IncidentRead, status_code=201)
def create_incident(
    payload: IncidentCreate, user: User = Depends(writer), db: Session = Depends(get_db)
):
    item = Incident(**payload.model_dump(mode="json"), status="open")
    db.add(item)
    db.flush()
    audit(db, item, user, "created", "Incident opened")
    db.commit()
    return item


@app.get("/incidents", response_model=list[IncidentRead])
def list_incidents(
    response: Response,
    status: Status | None = None,
    severity: Severity | None = None,
    category: str | None = None,
    q: str = Query(default="", max_length=120),
    sort: str = Query(default="newest", pattern="^(newest|oldest|title)$"),
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    user: User = Depends(current_user),
    db: Session = Depends(get_db),
):
    stmt = select(Incident)
    if status:
        stmt = stmt.where(Incident.status == status.value)
    if severity:
        stmt = stmt.where(Incident.severity == severity.value)
    if category:
        stmt = stmt.where(Incident.category == category)
    if q:
        stmt = stmt.where(or_(Incident.title.ilike(f"%{q}%"), Incident.description.ilike(f"%{q}%")))
    response.headers["X-Total-Count"] = str(
        db.scalar(select(func.count()).select_from(stmt.subquery()))
    )
    order = {
        "newest": Incident.id.desc(),
        "oldest": Incident.id.asc(),
        "title": Incident.title.asc(),
    }[sort]
    return db.scalars(stmt.order_by(order).limit(limit).offset(offset)).all()


@app.get("/incidents/{incident_id}", response_model=IncidentRead)
def get_incident(
    incident_id: int, user: User = Depends(current_user), db: Session = Depends(get_db)
):
    return find(db, incident_id)


@app.patch("/incidents/{incident_id}", response_model=IncidentRead)
def update_incident(
    incident_id: int,
    payload: IncidentUpdate,
    user: User = Depends(writer),
    db: Session = Depends(get_db),
):
    item = find(db, incident_id)
    changes = payload.model_dump(exclude_unset=True)
    for field, value in changes.items():
        if value is None and field != "assignee_id":
            raise HTTPException(422, f"{field} cannot be null")
    if "assignee_id" in changes:
        if user.role != "admin":
            raise HTTPException(403, "Admin permission required for assignment")
        owner = db.get(User, changes["assignee_id"]) if changes["assignee_id"] else None
        if changes["assignee_id"] and (not owner or owner.role == "viewer"):
            raise HTTPException(422, "Assign an admin or analyst")
    for field, value in changes.items():
        value = value.value if isinstance(value, Enum) else value
        old = getattr(item, field)
        if old != value:
            setattr(item, field, value)
            item.updated_at = utcnow()
            audit(db, item, user, f"{field}_changed", f"{old} -> {value}")
    db.commit()
    return item


@app.get("/incidents/{incident_id}/history", response_model=list[EventRead])
def incident_history(
    incident_id: int, user: User = Depends(current_user), db: Session = Depends(get_db)
):
    find(db, incident_id)
    return db.scalars(
        select(IncidentEvent)
        .where(IncidentEvent.incident_id == incident_id)
        .order_by(IncidentEvent.id)
    ).all()


@app.get("/incidents/{incident_id}/notes")
def notes(incident_id: int, user: User = Depends(current_user), db: Session = Depends(get_db)):
    find(db, incident_id)
    return db.scalars(select(Note).where(Note.incident_id == incident_id).order_by(Note.id)).all()


@app.post("/incidents/{incident_id}/notes", status_code=201)
def add_note(
    incident_id: int,
    payload: NoteCreate,
    user: User = Depends(writer),
    db: Session = Depends(get_db),
):
    item = find(db, incident_id)
    note = Note(incident_id=incident_id, author=user.username, body=payload.body)
    db.add(note)
    item.updated_at = utcnow()
    audit(db, item, user, "note_added", payload.body)
    db.commit()
    return {"id": note.id, "body": note.body, "author": note.author, "created_at": note.created_at}


@app.get("/activity", response_model=list[EventRead])
def activity(
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    user: User = Depends(current_user),
    db: Session = Depends(get_db),
):
    return db.scalars(
        select(IncidentEvent).order_by(IncidentEvent.id.desc()).limit(limit).offset(offset)
    ).all()


@app.get("/metrics")
def metrics(user: User = Depends(current_user), db: Session = Depends(get_db)):
    total = db.scalar(select(func.count()).select_from(Incident)) or 0
    severity = dict(
        db.execute(select(Incident.severity, func.count()).group_by(Incident.severity)).all()
    )
    status = dict(db.execute(select(Incident.status, func.count()).group_by(Incident.status)).all())
    trends = db.execute(
        select(func.date(Incident.created_at), func.count())
        .group_by(func.date(Incident.created_at))
        .order_by(func.date(Incident.created_at))
    ).all()
    return {
        "total": total,
        "unresolved": total - status.get("resolved", 0),
        "by_severity": {s.value: severity.get(s.value, 0) for s in Severity},
        "by_status": {s.value: status.get(s.value, 0) for s in Status},
        "trends": [{"date": str(d), "count": c} for d, c in trends],
    }
