"""Exercise actual local email verification and OIDC. Creates only a local QA identity, no reports."""

import json, re, secrets, time
import pyotp
from pathlib import Path
from urllib.request import urlopen
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
path = ROOT / "infra/staging/identity-qa.local"
if not path.exists():
    with path.open("x") as stream:
        path.chmod(0o600)
        json.dump(
            {
                "username": "local-release-review",
                "email": "local-release-review@monash.localhost",
                "password": secrets.token_urlsafe(24),
                "registered": False,
            },
            stream,
        )
creds = json.loads(path.read_text())
with sync_playwright() as pw:
    browser = pw.chromium.launch(
        executable_path="/usr/bin/google-chrome", headless=True
    )
    context = browser.new_context()
    page = context.new_page()
    if not creds["registered"]:
        page.goto("http://localhost:8180/api/v1/auth/register")
        page.locator('input[name="username"]').fill(creds["username"])
        page.locator('input[name="email"]').fill(creds["email"])
        page.locator('input[name="password"]').fill(creds["password"])
        page.locator('input[name="password_repeat"]').fill(creds["password"])
        page.get_by_role("button", name="Continue", exact=True).click()
        link = None
        for _ in range(60):
            inbox = json.load(urlopen("http://localhost:8125/api/v1/messages"))
            for message in inbox.get("messages", []):
                if any(
                    r.get("Address") == creds["email"] for r in message.get("To", [])
                ):
                    detail = json.load(
                        urlopen("http://localhost:8125/api/v1/message/" + message["ID"])
                    )
                    urls = re.findall(
                        r'https?://[^\s"<>]+',
                        detail.get("HTML", "") + detail.get("Text", ""),
                    )
                    link = next(
                        (
                            u.replace("&amp;", "&")
                            for u in urls
                            if u.startswith("http://localhost:9100/") and "token=" in u
                        ),
                        None,
                    )
                    if link:
                        break
            if link:
                break
            time.sleep(0.5)
        if not link:
            page.screenshot(path="/tmp/monash-registration-failure.png")
            raise RuntimeError(
                "No verification mail captured; inspect local registration flow"
            )
        page.goto(link)
        page.get_by_role("button", name="Continue", exact=True).click()
        page.wait_for_timeout(1500)
        creds["registered"] = True
        path.write_text(json.dumps(creds))
    page.goto("http://localhost:8180/api/v1/auth/login")
    deadline = time.monotonic() + 90
    last_code = None
    while time.monotonic() < deadline:
        if page.url.startswith("http://localhost:8180/dashboard"):
            break
        uid = page.locator('input[name="uidField"]:visible')
        password = page.get_by_placeholder("Please enter your password", exact=True)
        code_input = page.locator('input[name="code"]:visible')
        if uid.count():
            uid.fill(creds["username"])
            page.get_by_role("button", name="Log in", exact=True).click()
            uid.wait_for(state="hidden", timeout=15000)
        elif password.count():
            password.fill(creds["password"])
            page.get_by_role("button", name="Continue", exact=True).click()
            password.wait_for(state="hidden", timeout=15000)
        elif code_input.count() and creds.get("totp_secret"):
            code = pyotp.TOTP(creds["totp_secret"]).now()
            if code != last_code:
                code_input.fill(code)
                page.get_by_role("button", name="Continue", exact=True).click()
                last_code = code
        page.wait_for_timeout(500)
    assert page.url.startswith("http://localhost:8180/dashboard"), (
        "Local login did not complete; inspect identity service flow"
    )
    response = context.request.get("http://localhost:8180/api/v1/auth/me")
    assert response.status == 200
    account = response.json()
    assert account["email"] == creds["email"] and account["capabilities"] == [
        "report:own"
    ]
    cookies = context.cookies()
    session = next(c for c in cookies if c["name"] == "monash_session")
    assert session["httpOnly"]
    denied = context.request.post("http://localhost:8180/api/v1/auth/logout")
    assert denied.status == 403
    csrf = next(c["value"] for c in cookies if c["name"] == "monash_csrf")
    logout = context.request.post(
        "http://localhost:8180/api/v1/auth/logout",
        headers={"Origin": "http://localhost:8180", "X-CSRF-Token": csrf},
    )
    assert logout.status == 204
    assert context.request.get("http://localhost:8180/api/v1/auth/me").status == 401
    browser.close()
print(
    "Local identity acceptance passed: verified registration, OIDC login, citizen-only role, HTTP-only session, CSRF and logout. No reports created."
)
