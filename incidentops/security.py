import hashlib
import os
import secrets
from datetime import timedelta
from threading import BoundedSemaphore

from argon2 import PasswordHasher
from argon2.exceptions import VerificationError
from fastapi import Depends, HTTPException, Request
from sqlalchemy import delete
from sqlalchemy.orm import Session

from incidentops.db import get_db
from incidentops.models import LoginSession, User, utcnow

hasher = PasswordHasher()
DUMMY_HASH = hasher.hash(secrets.token_urlsafe(32))
# Bound concurrent Argon2 memory use on small demonstration hosts.
verification_slots = BoundedSemaphore(2)


def digest(token):
    return hashlib.sha256(token.encode()).hexdigest()


def current_user(request: Request, db: Session = Depends(get_db)):
    session = db.get(LoginSession, digest(request.cookies.get("session", "")))
    if not session:
        raise HTTPException(401, "Sign in to continue")
    expires_at = session.expires_at
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=utcnow().tzinfo)
    if expires_at <= utcnow():
        raise HTTPException(401, "Sign in to continue")
    user = db.get(User, session.user_id)
    if not user:
        raise HTTPException(401, "Session invalid")
    if request.method not in {"GET", "HEAD", "OPTIONS"}:
        csrf = request.headers.get("X-CSRF-Token", "")
        expected = request.cookies.get("csrf", "")
        if not expected or not secrets.compare_digest(csrf, expected):
            raise HTTPException(403, "CSRF verification failed; refresh and retry")
    return user


def writer(user: User = Depends(current_user)):
    if user.role not in {"admin", "analyst"}:
        raise HTTPException(403, "Analyst permission required")
    return user


def admin(user: User = Depends(current_user)):
    if user.role != "admin":
        raise HTTPException(403, "Admin permission required")
    return user


def start_session(db, user, response):
    db.execute(delete(LoginSession).where(LoginSession.expires_at <= utcnow()))
    token = secrets.token_urlsafe(32)
    db.add(
        LoginSession(
            token_hash=digest(token), user_id=user.id, expires_at=utcnow() + timedelta(hours=8)
        )
    )
    db.commit()
    secure = os.getenv("APP_ENV") == "production"
    response.set_cookie(
        "session", token, httponly=True, secure=secure, samesite="strict", max_age=28800
    )
    response.set_cookie(
        "csrf", secrets.token_urlsafe(32), secure=secure, samesite="strict", max_age=28800
    )


def verify(password, hashed):
    try:
        with verification_slots:
            return hasher.verify(hashed, password)
    except VerificationError:
        return False
