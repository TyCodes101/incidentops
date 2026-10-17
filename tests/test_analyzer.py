from pathlib import Path

import pytest

from incidentops.analyzer import analyze


def test_synthetic_pattern():
    data = Path(__file__).resolve().parents[1].joinpath("docs/example-logins.csv").read_text()
    result = analyze(data)
    assert result["records"] == 12
    assert len(result["flags"]) == 1
    assert result["flags"][0]["failure_count"] == 5
    assert result["flags"][0]["success_after_failures"] is True


@pytest.mark.parametrize(
    "row",
    [
        "bad",
        "timestamp,username,source_ip,success",
        "timestamp,username,source_ip,success\n2026-01-01,user,not-ip,false",
        "timestamp,username,source_ip,success\n2026-01-01T00:00:00Z,user,192.0.2.1,yes",
    ],
)
def test_invalid_csv(row):
    with pytest.raises(ValueError):
        analyze(row)


def test_windows_and_api(client, headers):
    data = "timestamp,username,source_ip,success\n" + "\n".join(
        f"2026-01-01T0{i}:00:00Z,user,192.0.2.1,false" for i in range(5)
    )
    assert analyze(data)["flags"] == []
    assert client.post("/analyzer", headers=headers, json={"csv_text": data}).status_code == 200
    assert client.post("/analyzer", headers=headers, json={"csv_text": "bad"}).status_code == 422
    assert (
        client.post("/analyzer", headers=headers, json={"csv_text": "x" * 70000}).status_code == 413
    )
