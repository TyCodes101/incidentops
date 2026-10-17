import json
import os
from pathlib import Path

from playwright.sync_api import sync_playwright

project = Path(__file__).resolve().parents[1]
base = os.getenv("INCIDENTOPS_URL", "http://localhost:5173")
reports = []
probe = (
    (project / ".agents/skills/styleseed/workflows/ss-verify/scripts/inspect-appearance.mjs")
    .read_text()
    .replace("export function", "function", 1)
)
root = project / "docs/screenshots/after"
root.mkdir(parents=True, exist_ok=True)
with sync_playwright() as p:
    b = p.chromium.launch()
    page = b.new_page(device_scale_factor=2)
    for size, w, h in [("desktop", 1440, 900), ("laptop", 1280, 800), ("mobile", 390, 844)]:
        page.set_viewport_size({"width": w, "height": h})
        page.goto(base)
        page.wait_for_load_state("networkidle")
        page.evaluate("document.fonts.ready")
        page.screenshot(path=str(root / f"login-{size}.png"), full_page=True)
        page.get_by_label("Username", exact=True).fill("demo.admin")
        page.get_by_label("Password", exact=True).fill("Demo-Only-Change-Me!")
        page.get_by_role("button", name="Sign in", exact=True).click()
        page.get_by_role("heading", name="Security overview").wait_for()
        for name in ["dashboard", "incidents", "activity", "analyzer", "team", "incident/1", "new"]:
            page.goto(base + "/#" + name)
            page.wait_for_timeout(700)
            page.wait_for_load_state("networkidle")
            page.evaluate("document.fonts.ready")
            page.screenshot(path=str(root / f"{name.replace('/', '-')}-{size}.png"), full_page=True)
            assert page.evaluate("document.documentElement.scrollWidth<=window.innerWidth"), (
                name,
                size,
                "overflow",
            )
            if name == "incidents":
                report = page.evaluate(
                    "(" + probe + ")",
                    {
                        "artifactId": "incidentops",
                        "context": {
                            "theme": "light",
                            "state": "default",
                            "specimen": size,
                            "fontCondition": "normal",
                        },
                        "colors": [
                            {
                                "id": "queue-scope",
                                "role": "text",
                                "reason": "Queue scope subtitle",
                                "foreground": {
                                    "selector": ".queue .section-heading .muted",
                                    "property": "color",
                                },
                                "background": {"selector": ".queue"},
                            },
                            {
                                "id": "search-edge",
                                "role": "required-boundary",
                                "reason": "Search field identification",
                                "foreground": {
                                    "selector": ".search input",
                                    "property": "borderTopColor",
                                },
                                "background": {"selector": ".search input"},
                            },
                        ],
                        "typography": [
                            {
                                "id": "page-title",
                                "selector": "h1",
                                "role": "heading",
                                "sampleId": "incident-queue",
                            }
                        ],
                    },
                )
                report["fontLoaded"] = page.evaluate(
                    "document.fonts.check('14px \"Inter Variable\"')"
                )
                reports.append(report)

        if size == "mobile":
            page.get_by_role("button", name="Open navigation").click()
            page.screenshot(path=str(root / "navigation-mobile.png"))
        page.get_by_role("button", name="Sign out").last.click()
        page.get_by_role("heading", name="Welcome back").wait_for()
    b.close()
print("Captured all screens at three viewports; no horizontal page overflow")

(project / "docs/verification/appearance.json").write_text(json.dumps(reports, indent=2))
print([(r["context"]["specimen"], r["status"], r["fontLoaded"]) for r in reports])
