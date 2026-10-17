import os
import time
from pathlib import Path

from playwright.sync_api import expect, sync_playwright

root = Path(__file__).resolve().parents[1]
base = os.getenv("INCIDENTOPS_URL", "http://localhost:5173")
shots = root / "docs/screenshots/states"
shots.mkdir(parents=True, exist_ok=True)
run = str(time.time_ns())[-10:]
password = "Test-Only-Password-42!"
with sync_playwright() as p:
    browser = p.chromium.launch()
    page = browser.new_page(viewport={"width": 1440, "height": 900}, device_scale_factor=2)
    errors = []
    page.on("pageerror", lambda e: errors.append(str(e)))

    def visit(route):
        page.goto(base + "/#" + route)
        page.wait_for_load_state("networkidle")

    def login(username, secret):
        page.goto(base)
        page.get_by_label("Username", exact=True).fill(username)
        page.get_by_label("Password", exact=True).fill(secret)
        page.get_by_role("button", name="Sign in", exact=True).click()
        expect(page.get_by_role("heading", name="Security overview")).to_be_visible()

    def shot(name):
        page.evaluate("document.fonts.ready")
        page.screenshot(path=str(shots / (name + ".png")), full_page=True)

    login("demo.admin", "Demo-Only-Change-Me!")
    for role in ["viewer", "analyst"]:
        visit("team")
        page.get_by_role("button", name="Add member", exact=True).click()
        page.get_by_label("Username", exact=True).fill("test." + role + run)
        page.get_by_label("Initial password", exact=False).fill(password)
        page.get_by_label("Role", exact=True).select_option(role)
        if role == "analyst":
            shot("team-add-member")
        page.get_by_role("button", name="Create account", exact=True).click()
        expect(page.get_by_role("status")).to_have_text("Workspace member created.")
    visit("new")
    expect(page.get_by_text("Workspace member created.", exact=True)).to_have_count(0)
    title = "Account review " + run
    page.get_by_label("Incident title").fill(title)
    page.get_by_label("Description", exact=True).fill(
        "Synthetic browser verification. Confirm the sign-in with the account owner."
    )
    page.get_by_role("button", name="Create incident", exact=True).click()
    expect(page.get_by_role("heading", name=title)).to_be_visible()
    expect(page.get_by_text("Incident created. Ready for triage.", exact=True)).to_be_visible()
    expect(page.get_by_text("Workspace member created.", exact=True)).to_have_count(0)
    detail_url = page.url
    page.get_by_label("Status", exact=True).select_option("investigating")
    expect(page.get_by_text("open -> investigating", exact=True)).to_be_visible()
    page.get_by_label("Severity", exact=True).select_option("critical")
    expect(page.get_by_text("medium -> critical", exact=True)).to_be_visible()
    page.get_by_label("Assigned analyst", exact=True).select_option(label="test.analyst" + run)
    expect(page.get_by_label("Assigned analyst", exact=True)).to_be_enabled()
    page.get_by_label("Add a note", exact=True).fill(
        "Account owner contacted. Evidence retained for review."
    )
    page.get_by_role("button", name="Add investigation note", exact=True).click()
    expect(page.get_by_role("heading", name="Investigation notes 1")).to_be_visible()
    page.get_by_role("button", name="Edit incident summary").click()
    page.get_by_label("Title", exact=True).fill(title + " updated")
    page.route(
        "**/api/incidents/*",
        lambda route: (
            route.fulfill(status=500, json={"detail": "Temporary save failure"})
            if route.request.method == "PATCH"
            else route.continue_()
        ),
    )
    page.get_by_role("button", name="Save summary", exact=True).click()
    expect(page.get_by_role("alert")).to_have_text("Temporary save failure")
    expect(page.get_by_label("Title", exact=True)).to_have_value(title + " updated")
    shot("summary-error-preserves-draft")
    page.unroute("**/api/incidents/*")
    page.get_by_role("button", name="Save summary", exact=True).click()
    expect(page.get_by_role("heading", name=title + " updated")).to_be_visible()
    page.once("dialog", lambda d: d.accept())
    page.get_by_role("button", name="Resolve incident", exact=True).click()
    expect(page.get_by_label("Status", exact=True)).to_have_value("resolved")
    page.once("dialog", lambda d: d.accept())
    page.get_by_role("button", name="Reopen incident", exact=True).click()
    expect(page.get_by_label("Status", exact=True)).to_have_value("open")
    shot("investigation-evidence")
    page.reload()
    expect(page.get_by_role("heading", name=title + " updated")).to_be_visible()
    visit("incidents")
    page.get_by_label("Search incidents").fill(title)
    expect(page.get_by_text(title + " updated", exact=True)).to_be_visible()
    page.get_by_label("Filter severity").select_option("critical")
    expect(page.get_by_text(title + " updated", exact=True)).to_be_visible()
    page.get_by_label("Search incidents").fill("no-matching-case-" + run)
    expect(page.get_by_text("No incidents match.", exact=False)).to_be_visible()
    shot("queue-empty")
    page.get_by_role("button", name="Clear filters").click()
    expect(page.locator(".case-link").first).to_be_visible()
    page.route(
        "**/api/incidents?*",
        lambda route: route.fulfill(status=503, json={"detail": "Unavailable"}),
    )
    page.get_by_label("Filter status").select_option("resolved")
    expect(page.get_by_role("alert")).to_be_visible()
    shot("queue-error")
    page.unroute("**/api/incidents?*")
    page.get_by_role("button", name="Retry", exact=True).click()
    expect(page.locator(".case-link").first).to_be_visible()
    visit("analyzer")
    page.get_by_label("CSV records").fill("invalid,csv")
    page.get_by_role("button", name="Analyze example records").click()
    expect(page.get_by_role("alert")).to_be_visible()
    shot("analyzer-invalid")
    page.get_by_label("Import example CSV").set_input_files(root / "docs/example-logins.csv")
    page.get_by_role("button", name="Analyze example records").click()
    expect(page.get_by_text("12 records analyzed · 1 flagged accounts", exact=True)).to_be_visible()
    shot("analyzer-results")
    page.get_by_role("button", name="Create investigation incident").click()
    expect(
        page.get_by_role("heading", name="Review login pattern for demo.finance")
    ).to_be_visible()
    page.get_by_role("button", name="Sign out").click()
    for role in ["viewer", "analyst"]:
        login("test." + role + run, password)
        page.goto(detail_url)
        expect(page.get_by_role("heading", name=title + " updated")).to_be_visible()
        expect(page.get_by_label("Assigned analyst")).to_be_disabled()
        if role == "viewer":
            expect(page.get_by_label("Status", exact=True)).to_be_disabled()
            expect(page.get_by_role("button", name="Add investigation note")).to_have_count(0)
            visit("analyzer")
            expect(
                page.get_by_text("Analyst permission is required to analyze records.")
            ).to_be_visible()
        else:
            expect(page.get_by_label("Status", exact=True)).to_be_enabled()
            page.get_by_label("Add a note", exact=True).fill("Analyst role browser verification.")
            page.get_by_role("button", name="Add investigation note").click()
            expect(page.get_by_role("heading", name="Investigation notes 2")).to_be_visible()
        shot(role + "-permissions")
        visit("team")
        expect(page.get_by_role("button", name="Add member")).to_have_count(0)
        page.get_by_role("button", name="Sign out").click()
    login("demo.admin", "Demo-Only-Change-Me!")
    page.set_viewport_size({"width": 390, "height": 844})
    page.get_by_role("button", name="Open navigation").click()
    expect(page.get_by_role("dialog")).to_be_visible()
    page.keyboard.press("Escape")
    expect(page.get_by_role("dialog")).not_to_be_visible()
    page.get_by_role("button", name="Open navigation").click()
    page.get_by_role("dialog").get_by_role("link", name="Incidents", exact=False).click()
    expect(page.get_by_role("heading", name="Incidents", exact=True)).to_be_visible()
    expect(page.locator(".case-link").first).to_be_visible()
    assert page.evaluate("document.documentElement.scrollWidth<=innerWidth")
    page.emulate_media(reduced_motion="reduce")
    assert (
        page.locator(".page-heading button").evaluate(
            "(el)=>getComputedStyle(el).transitionDuration"
        )
        == "0s"
    )
    page.get_by_role("button", name="Open navigation").click()
    page.get_by_role("dialog").get_by_role("button", name="Sign out").click()
    expect(page.get_by_role("heading", name="Welcome back")).to_be_visible()
    assert not errors, errors
    browser.close()
print(
    "PASS: auth; create; edit; failed draft recovery; status; severity; assignment; notes; resolve/reopen; route persistence; search/filter/clear; empty/error/retry; CSV validation/import/analyze/convert; admin/analyst/viewer; mobile navigation/Escape; reduced motion; logout; no JS errors"
)
