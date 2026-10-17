"""Retain high/critical findings and block release when any critical finding remains."""

import json
import sys
from pathlib import Path

critical = []
for filename in sys.argv[1:]:
    report = json.loads(Path(filename).read_text(encoding="utf-8"))
    if not report.get("Metadata", {}).get("OS", {}).get("Family") or not report.get("Results"):
        raise SystemExit(f"Incomplete or unsupported image report: {Path(filename).name}")
    findings = [
        item
        for result in report.get("Results", [])
        for item in (result.get("Vulnerabilities") or [])
    ]
    print(
        Path(filename).name,
        {
            severity: sum(item["Severity"] == severity for item in findings)
            for severity in ["HIGH", "CRITICAL"]
        },
    )
    critical.extend(
        (filename, item["VulnerabilityID"], item["PkgName"])
        for item in findings
        if item["Severity"] == "CRITICAL"
    )
if len(sys.argv) < 2:
    raise SystemExit("No container reports supplied")
if critical:
    print("Unresolved critical findings:", critical)
    raise SystemExit(1)
print(f"PASS: no critical vulnerabilities in {len(sys.argv) - 1} complete image reports")
