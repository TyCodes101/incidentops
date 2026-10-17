# Local API example

Start the API and explicitly seed the demo first. Run from a Python environment with httpx installed:

```python
import getpass
import httpx

with httpx.Client(base_url="http://127.0.0.1:8000") as client:
    response = client.post("/auth/login", json={"username": "demo.admin", "password": getpass.getpass("Demo password: ")})
    response.raise_for_status()
    headers = {"X-CSRF-Token": client.cookies["csrf"]}
    created = client.post("/incidents", headers=headers, json={"title": "Authorized account review", "description": "Synthetic example only", "severity": "high", "category": "Identity & Access"})
    created.raise_for_status()
    case_id = created.json()["id"]
    client.patch(f"/incidents/{case_id}", headers=headers, json={"status": "investigating"}).raise_for_status()
    client.post(f"/incidents/{case_id}/notes", headers=headers, json={"body": "Owner contacted; fictional validation complete."}).raise_for_status()
    client.patch(f"/incidents/{case_id}", headers=headers, json={"status": "resolved"}).raise_for_status()
    print(client.get(f"/incidents/{case_id}/history").json())
    print(client.get("/metrics").json())
    client.post("/auth/logout", headers=headers).raise_for_status()
```

The client sends session cookies automatically. Keep tokens out of logs. Assignment is a PATCH with `assignee_id` and requires an admin. The list remains a JSON array for starter compatibility; total count is in `X-Total-Count`.
