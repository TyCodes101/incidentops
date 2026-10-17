"""Exercise a migrated Compose stack; retain only synthetic state in .runtime.

The before phase leaves its admin session in an ignored local cookie file. After
restarting containers, the after phase proves the same session and data survive.
Never point this script at a real operational workspace.
"""

import argparse
import http.cookiejar
import json
import os
import time
import urllib.error
import urllib.request
from pathlib import Path
from uuid import uuid4


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("phase", choices=["before", "after"])
    parser.add_argument("--base-url", default="http://localhost:8080")
    parser.add_argument("--state-file", default=".runtime/compose-smoke.json")
    args = parser.parse_args()
    base = args.base_url.rstrip("/")
    state_path = Path(args.state_file)
    state_path.parent.mkdir(parents=True, exist_ok=True)
    cookie_path = state_path.with_suffix(".cookies")
    jar = http.cookiejar.LWPCookieJar(str(cookie_path))
    if args.phase == "after":
        jar.load(ignore_discard=True, ignore_expires=True)
    opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(jar))

    def call(path, method="GET", data=None, expected=200, headers=None):
        request_headers = {"Origin": base}
        if data is not None:
            request_headers["Content-Type"] = "application/json"
        csrf = next((cookie.value for cookie in jar if cookie.name == "csrf"), "")
        if method != "GET":
            request_headers["X-CSRF-Token"] = csrf
        request_headers.update(headers or {})
        request = urllib.request.Request(
            base + path,
            data=json.dumps(data).encode() if data is not None else None,
            method=method,
            headers=request_headers,
        )
        try:
            response = opener.open(request, timeout=20)
        except urllib.error.HTTPError as error:
            response = error
        body = response.read()
        assert response.code == expected, (method, path, response.code, expected)
        content_type = response.headers.get("Content-Type", "")
        value = json.loads(body) if body and "application/json" in content_type else body
        return value, response.headers

    # The DB/API can take a few seconds to reconnect after a deliberate restart.
    for attempt in range(30):
        try:
            health, _ = call("/api/health")
            assert health == {"status": "ok"}
            break
        except (AssertionError, OSError):
            if attempt == 29:
                raise
            time.sleep(2)

    html, _ = call("/")
    assert b"IncidentOps" in html
    if args.phase == "after":
        state = json.loads(state_path.read_text(encoding="utf-8"))
        account, _ = call("/api/auth/me")
        assert account["username"] == state["admin"]
        incident, _ = call(f"/api/incidents/{state['case_id']}")
        assert incident["title"] == state["title"]
        assert incident["status"] == "open"
        notes, _ = call(f"/api/incidents/{state['case_id']}/notes")
        assert any(note["body"] == state["note"] for note in notes)
        history, _ = call(f"/api/incidents/{state['case_id']}/history")
        assert len(history) == state["history_count"]
        call("/api/auth/logout", "POST", expected=204)
        call("/api/auth/me", expected=401)
        print("PASS: PostgreSQL data, notes, audit and server session survived container restarts")
        return

    call("/api/incidents", expected=401)
    admin_name = os.getenv("SMOKE_ADMIN_USERNAME", "demo.admin")
    admin_password = os.getenv("SMOKE_ADMIN_PASSWORD", "Demo-Only-Change-Me!")
    admin, cookies = call(
        "/api/auth/login", "POST", {"username": admin_name, "password": admin_password}
    )
    assert "password_hash" not in admin
    assert any(
        "HttpOnly" in value and "SameSite=strict" in value
        for value in cookies.get_all("Set-Cookie")
    )
    call(
        "/api/incidents",
        "POST",
        {"title": "CSRF rejection check", "severity": "low"},
        expected=403,
        headers={"X-CSRF-Token": "incorrect"},
    )
    call(
        "/api/incidents",
        "POST",
        {"title": "Origin rejection check", "severity": "low"},
        expected=403,
        headers={"Origin": "https://untrusted.example"},
    )
    nonce = uuid4().hex[:10]
    password = "Synthetic-smoke-password-42!"
    accounts = {}
    for role in ["analyst", "viewer"]:
        accounts[role], _ = call(
            "/api/users",
            "POST",
            {"username": f"smoke.{role}.{nonce}", "password": password, "role": role},
            expected=201,
        )
    case, _ = call(
        "/api/incidents",
        "POST",
        {
            "title": f"PostgreSQL smoke review {nonce}",
            "severity": "high",
            "category": "Identity & Access",
            "description": "Fictional Compose verification only.",
        },
        expected=201,
    )
    case_id = case["id"]
    title = case["title"] + " updated"
    case, _ = call(
        f"/api/incidents/{case_id}",
        "PATCH",
        {
            "title": title,
            "status": "investigating",
            "severity": "critical",
            "assignee_id": accounts["analyst"]["id"],
        },
    )
    assert case["assignee_id"] == accounts["analyst"]["id"]
    note = "Synthetic owner review recorded; no external action performed."
    call(f"/api/incidents/{case_id}/notes", "POST", {"body": note}, expected=201)
    found, headers = call(f"/api/incidents?q={nonce}&severity=critical")
    assert [row["id"] for row in found] == [case_id]
    assert headers["X-Total-Count"] == "1"
    metrics, _ = call("/api/metrics")
    assert metrics["total"] >= 1 and metrics["trends"]
    csv_text = (
        Path(__file__)
        .resolve()
        .parents[1]
        .joinpath("docs/example-logins.csv")
        .read_text(encoding="utf-8")
    )
    result, _ = call("/api/analyzer", "POST", {"csv_text": csv_text})
    assert result["records"] == 12 and len(result["flags"]) == 1
    call("/api/analyzer", "POST", {"csv_text": "invalid"}, expected=422)
    for status in ["resolved", "open"]:
        updated, _ = call(f"/api/incidents/{case_id}", "PATCH", {"status": status})
        assert updated["status"] == status
    call("/api/auth/logout", "POST", expected=204)
    for role in ["viewer", "analyst"]:
        call(
            "/api/auth/login",
            "POST",
            {"username": accounts[role]["username"], "password": password},
        )
        call(f"/api/incidents/{case_id}")
        call(
            "/api/users",
            "POST",
            {"username": "forbidden", "password": password, "role": "admin"},
            expected=403,
        )
        call(f"/api/incidents/{case_id}", "PATCH", {"assignee_id": admin["id"]}, expected=403)
        if role == "viewer":
            call(
                "/api/incidents",
                "POST",
                {"title": "Forbidden mutation", "severity": "low"},
                expected=403,
            )
            call(f"/api/incidents/{case_id}/notes", "POST", {"body": "Forbidden"}, expected=403)
            call("/api/analyzer", "POST", {"csv_text": csv_text}, expected=403)
        else:
            call(
                f"/api/incidents/{case_id}/notes",
                "POST",
                {"body": "Analyst role validated."},
                expected=201,
            )
        call("/api/auth/logout", "POST", expected=204)
    call("/api/auth/login", "POST", {"username": admin_name, "password": admin_password})
    history, _ = call(f"/api/incidents/{case_id}/history")
    assert {
        "created",
        "title_changed",
        "status_changed",
        "severity_changed",
        "assignee_id_changed",
        "note_added",
    } <= {event["action"] for event in history}
    assert all(event["actor"] for event in history)
    state_path.write_text(
        json.dumps(
            {
                "admin": admin_name,
                "case_id": case_id,
                "title": title,
                "note": note,
                "history_count": len(history),
            }
        ),
        encoding="utf-8",
    )
    jar.save(ignore_discard=True, ignore_expires=True)
    print(
        "PASS: Compose web/API/PostgreSQL, auth/CSRF/origin, all roles, create/edit/search/assignment/notes/audit, analyzer, resolve/reopen"
    )


if __name__ == "__main__":
    main()
