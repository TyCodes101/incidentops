"""Explicit account bootstrap and opt-in synthetic demo seed."""

import argparse
import getpass
import os
from datetime import timedelta

from sqlalchemy import select

from incidentops.db import SessionLocal
from incidentops.models import Incident, IncidentEvent, User, utcnow
from incidentops.security import hasher


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=["demo", "admin"])
    parser.add_argument("--username", default="admin")
    args = parser.parse_args()
    if args.command == "demo" and os.getenv("APP_ENV") == "production":
        raise SystemExit("Demo seeding is forbidden in production")
    password = (
        "Demo-Only-Change-Me!"
        if args.command == "demo"
        else getpass.getpass("New password (12+ chars): ")
    )
    if len(password) < 12:
        raise SystemExit("Password must have at least 12 characters")
    with SessionLocal() as db:
        name = "demo.admin" if args.command == "demo" else args.username
        if db.scalar(select(User).where(User.username == name)):
            if args.command == "demo":
                print("Demo account already exists; nothing changed")
                return
            raise SystemExit("Account already exists; nothing changed")
        user = User(username=name, password_hash=hasher.hash(password), role="admin")
        db.add(user)
        db.flush()
        if args.command == "demo":
            titles = [
                "Repeated sign-in failures for finance account",
                "Credential lure reported by employee",
                "Unexpected endpoint protection alert",
                "Public sharing link requires review",
                "Unrecognized OAuth application consent",
                "Mailbox forwarding rule investigated",
                "Suspicious attachment quarantined",
                "Privileged access review completed",
                "New device sign-in reported",
                "Possible data export anomaly",
                "Account recovery request reviewed",
                "Legacy service account failures",
            ]
            for i, title in enumerate(titles):
                date = utcnow() - timedelta(days=11 - i)
                item = Incident(
                    title=title,
                    description="Fictional demo report. Validate the report, document evidence, and coordinate containment with the account owner.",
                    severity=["high", "critical", "medium", "low"][i % 4],
                    status=["open", "investigating", "resolved"][i % 3],
                    category=["Identity & Access", "Phishing", "Endpoint", "Data Exposure"][i % 4],
                    assignee_id=user.id,
                    created_at=date,
                    updated_at=date,
                )
                db.add(item)
                db.flush()
                db.add(
                    IncidentEvent(
                        incident_id=item.id,
                        actor=name,
                        action="created",
                        detail="Synthetic demonstration incident opened",
                        occurred_at=date,
                    )
                )
        db.commit()
        print(
            "Account created" + (" with synthetic demo incidents" if args.command == "demo" else "")
        )


if __name__ == "__main__":
    main()
