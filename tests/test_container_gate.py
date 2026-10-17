import json
import subprocess
import sys
from pathlib import Path


def run_gate(tmp_path, value):
    report = tmp_path / "api-vulnerabilities.json"
    report.write_text(json.dumps(value), encoding="utf-8")
    return subprocess.run(
        [
            sys.executable,
            str(Path(__file__).resolve().parents[1] / "scripts/check_container_reports.py"),
            str(report),
        ],
        capture_output=True,
        text=True,
        check=False,
    )


def test_container_gate_rejects_an_empty_report(tmp_path):
    assert run_gate(tmp_path, {}).returncode != 0


def test_container_gate_blocks_unresolved_critical_findings(tmp_path):
    report = {
        "Metadata": {"OS": {"Family": "alpine"}},
        "Results": [
            {
                "Vulnerabilities": [
                    {
                        "Severity": "CRITICAL",
                        "VulnerabilityID": "synthetic-test-finding",
                        "PkgName": "synthetic-package",
                    }
                ]
            }
        ],
    }
    assert run_gate(tmp_path, report).returncode != 0


def test_container_gate_accepts_a_complete_report_without_critical_findings(tmp_path):
    report = {
        "Metadata": {"OS": {"Family": "alpine"}},
        "Results": [{"Target": "test-os", "Class": "os-pkgs", "Vulnerabilities": []}],
    }
    result = run_gate(tmp_path, report)
    assert result.returncode == 0
    assert "1 complete image reports" in result.stdout
