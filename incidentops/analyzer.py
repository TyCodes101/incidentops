"""Transparent rules over authorized example CSV; flags are not intrusion verdicts."""

import csv
import io
from collections import defaultdict
from datetime import datetime, timedelta
from ipaddress import ip_address

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from incidentops.models import User
from incidentops.security import writer

router = APIRouter()


class CSVInput(BaseModel):
    csv_text: str = Field(max_length=50000)


def analyze(text):
    reader = csv.DictReader(io.StringIO(text))
    if reader.fieldnames != ["timestamp", "username", "source_ip", "success"]:
        raise ValueError("Required header: timestamp,username,source_ip,success")
    records = []
    for row in reader:
        if len(records) >= 1000:
            raise ValueError("Maximum 1000 records per analysis")
        if None in row or any(v is None for v in row.values()):
            raise ValueError("Each record must contain exactly four columns")
        stamp = datetime.fromisoformat(row["timestamp"].replace("Z", "+00:00"))
        if stamp.tzinfo is None:
            raise ValueError("Timestamps must include a timezone")
        name = row["username"].strip()
        if not name or len(name) > 80:
            raise ValueError("Usernames must be 1–80 characters")
        ip_address(row["source_ip"])
        success = row["success"].lower()
        if success not in {"true", "false"}:
            raise ValueError("success must be true or false")
        records.append((stamp, name, row["source_ip"], success == "true"))
    if not records:
        raise ValueError("CSV has no records")
    failures = defaultdict(list)
    flagged = {}
    for stamp, name, ip, success in sorted(records):
        failures[name] = [r for r in failures[name] if stamp - r[0] <= timedelta(minutes=10)]
        if not success:
            failures[name].append((stamp, ip))
        if len(failures[name]) >= 5:
            previous = flagged.get(name)
            followed = success or bool(previous and previous["success_after_failures"])
            flagged[name] = {
                "username": name,
                "failure_count": max(
                    len(failures[name]), previous["failure_count"] if previous else 0
                ),
                "window_minutes": 10,
                "success_after_failures": followed,
                "source_ips": sorted({r[1] for r in failures[name]}),
                "timestamp": stamp.isoformat(),
                "rule": "Five or more failed logins for one account within ten minutes",
            }
    return {
        "records": len(records),
        "flags": list(flagged.values()),
        "notice": "Informational flags for authorized example data; not proof of intrusion.",
    }


@router.post("/analyzer")
def analyze_csv(payload: CSVInput, user: User = Depends(writer)):
    try:
        return analyze(payload.csv_text)
    except (ValueError, csv.Error) as exc:
        raise HTTPException(422, str(exc)) from exc
