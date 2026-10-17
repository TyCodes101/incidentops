import time
from pathlib import Path

from playwright.sync_api import expect, sync_playwright

case_title = f"Verified account review {time.time_ns()}"

root = Path(__file__).resolve().parents[1]
with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page(viewport={"width": 1440, "height": 1080}, device_scale_factor=1)
    errors = []
    page.on("pageerror", lambda e: errors.append(str(e)))
    page.goto("http://localhost:5173")
    page.wait_for_load_state("networkidle")
    print(page.locator("body").inner_text()[:1000])
    page.get_by_label("Username", exact=True).fill("demo.admin")
    page.get_by_label("Password", exact=True).fill("Demo-Only-Change-Me!")
    page.get_by_role("button", name="Sign in", exact=True).click()
    expect(page.get_by_role("heading", name="Security overview")).to_be_visible()
    expect(page.get_by_text("Incident reporting trend")).to_be_visible()
    page.wait_for_load_state("networkidle")
    (root / "docs/screenshots").mkdir(parents=True, exist_ok=True)
    page.screenshot(path=str(root / "docs/screenshots/dashboard.png"), full_page=True)
    print("DASHBOARD PASS")
    page.get_by_role("button", name="Report incident", exact=True).click()
    expect(page.get_by_label("Incident title")).to_be_visible()
    page.get_by_label("Incident title").fill(case_title)
    page.get_by_label("Description", exact=True).fill(
        "Synthetic smoke test: account owner reported unfamiliar sign-in. Validate activity before containment."
    )
    page.get_by_label("Severity", exact=True).select_option("high")
    page.get_by_role("button", name="Create incident", exact=True).click()
    expect(page.get_by_role("heading", name=case_title)).to_be_visible()
    page.get_by_label("Status", exact=True).select_option("investigating")
    expect(page.get_by_text("open -> investigating", exact=True)).to_be_visible()
    page.get_by_label("Severity", exact=True).select_option("critical")
    expect(page.get_by_text("high -> critical", exact=True)).to_be_visible()
    page.get_by_label("Assigned analyst", exact=True).select_option(label="demo.admin")
    page.get_by_label("Add a note", exact=True).fill(
        "Owner contacted. Credentials reset with authorization; sessions revoked in the fictional source system."
    )
    page.get_by_role("button", name="Add investigation note", exact=True).click()
    expect(page.get_by_role("heading", name="Investigation notes 1")).to_be_visible()
    page.once("dialog", lambda d: d.accept())
    page.get_by_role("button", name="Resolve incident", exact=True).click()
    expect(page.get_by_label("Status", exact=True)).to_have_value("resolved")
    page.screenshot(path=str(root / "docs/screenshots/investigation.png"), full_page=True)
    print("CREATE / STATUS / SEVERITY / ASSIGNMENT / NOTE / RESOLVE PASS")
    page.get_by_role("button", name="Incidents", exact=False).first.click()
    page.get_by_label("Search incidents").fill(case_title)
    expect(page.get_by_text(case_title, exact=True)).to_be_visible()
    page.get_by_label("Filter status").select_option("resolved")
    expect(page.get_by_text(case_title, exact=True)).to_be_visible()
    print("SEARCH / FILTER PASS")
    page.get_by_role("button", name="Activity", exact=True).click()
    expect(page.get_by_role("heading", name="Audit activity")).to_be_visible()
    page.get_by_role("button", name="Analyzer", exact=True).click()
    page.get_by_label("CSV records").fill((root / "docs/example-logins.csv").read_text())
    page.get_by_role("button", name="Analyze example records").click()
    expect(page.get_by_text("12 records analyzed · 1 flagged accounts", exact=True)).to_be_visible()
    page.get_by_role("button", name="Create investigation incident").click()
    expect(
        page.get_by_role("heading", name="Review login pattern for demo.finance")
    ).to_be_visible()
    print("CSV ANALYZER / FLAG TO INCIDENT PASS")
    page.get_by_role("button", name="Dashboard", exact=True).click()
    page.set_viewport_size({"width": 390, "height": 844})
    page.wait_for_load_state("networkidle")
    page.get_by_label("Search incidents").wait_for()
    page.get_by_role("button", name="Next", exact=True).wait_for()
    expect(page.get_by_text("Loading incidents…")).not_to_be_visible()
    page.screenshot(path=str(root / "docs/screenshots/mobile.png"), full_page=True)
    assert page.evaluate("document.documentElement.scrollWidth <= window.innerWidth"), (
        "Mobile page overflows"
    )
    page.get_by_role("button", name="Sign out", exact=True).click()
    expect(page.get_by_role("heading", name="Welcome back")).to_be_visible()
    assert not errors, errors
    print("MOBILE / LOGOUT / NO JS ERRORS PASS")
    browser.close()
