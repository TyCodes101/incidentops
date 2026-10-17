"""Integration coverage for common triage and security workflows."""


def new_item(client, headers, title="Suspicious sign-in", severity="high"):
    return client.post(
        "/incidents",
        headers=headers,
        json={
            "title": title,
            "description": "Repeated failed logins in the demo system",
            "severity": severity,
            "category": "identity",
        },
    )


def test_health_is_public(client):
    assert client.get("/health").json() == {"status": "ok"}


def test_api_requires_session(client):
    assert client.get("/incidents").status_code == 401
    assert client.get("/metrics", headers={"X-API-Key": "wrong"}).status_code == 401


def test_create_read_and_filter(client, headers):
    response = new_item(client, headers)
    assert response.status_code == 201
    assert response.json()["status"] == "open"
    incident_id = response.json()["id"]
    assert client.get(f"/incidents/{incident_id}", headers=headers).status_code == 200
    assert len(client.get("/incidents?severity=high", headers=headers).json()) == 1
    assert client.get("/incidents?severity=low", headers=headers).json() == []


def test_status_change_is_audited(client, headers):
    incident_id = new_item(client, headers).json()["id"]
    updated = client.patch(
        f"/incidents/{incident_id}", headers=headers, json={"status": "investigating"}
    )
    assert updated.status_code == 200
    assert updated.json()["status"] == "investigating"
    changes = client.get(f"/incidents/{incident_id}/history", headers=headers).json()
    assert [entry["action"] for entry in changes] == ["created", "status_changed"]
    assert changes[-1]["detail"] == "open -> investigating"
    # A no-op update must not create a duplicate audit event.
    client.patch(f"/incidents/{incident_id}", headers=headers, json={"status": "investigating"})
    assert len(client.get(f"/incidents/{incident_id}/history", headers=headers).json()) == 2


def test_metrics(client, headers):
    first = new_item(client, headers, severity="critical").json()["id"]
    new_item(client, headers, title="Phishing email", severity="medium")
    client.patch(f"/incidents/{first}", headers=headers, json={"status": "resolved"})
    data = client.get("/metrics", headers=headers).json()
    assert data["total"] == 2
    assert data["unresolved"] == 1
    assert data["by_severity"]["critical"] == 1
    assert data["by_status"]["resolved"] == 1


def test_validation_and_missing_incidents(client, headers):
    invalid = client.post(
        "/incidents", headers=headers, json={"title": "No", "severity": "extreme"}
    )
    assert invalid.status_code == 422
    assert client.get("/incidents/9999", headers=headers).status_code == 404
    assert (
        client.patch("/incidents/9999", headers=headers, json={"status": "resolved"}).status_code
        == 404
    )
    assert client.get("/incidents/9999/history", headers=headers).status_code == 404


def test_pagination_is_bounded(client, headers):
    for index in range(3):
        new_item(client, headers, title=f"Incident {index}")
    assert len(client.get("/incidents?limit=2", headers=headers).json()) == 2
    assert client.get("/incidents?limit=101", headers=headers).status_code == 422
