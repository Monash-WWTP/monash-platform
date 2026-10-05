"""Exercise real operator MFA without granting roles or creating observations."""

import json, time
from pathlib import Path
from urllib.parse import urlparse, parse_qs
import pyotp
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
path = ROOT / "infra/staging/identity-qa.local"
creds = json.loads(path.read_text())
with sync_playwright() as pw:
    browser = pw.chromium.launch(
        executable_path="/usr/bin/google-chrome", headless=True
    )
    context = browser.new_context()
    page = context.new_page()

    def capture(response):
        if "/api/v3/flows/executor/" in response.url:
            try:
                challenge = response.json()
                uri = challenge.get("config_url") or challenge.get("data", {}).get(
                    "config_url"
                )
                if uri and uri.startswith("otpauth://"):
                    creds["totp_secret"] = parse_qs(urlparse(uri).query)["secret"][0]
                    path.write_text(json.dumps(creds))
            except Exception:
                pass

    page.on("response", capture)
    page.goto("http://localhost:8180/api/v1/auth/login?operator=true")
    deadline = time.monotonic() + 100
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
        elif password.count():
            password.fill(creds["password"])
            page.get_by_role("button", name="Continue", exact=True).click()
        elif code_input.count() and creds.get("totp_secret"):
            code = pyotp.TOTP(creds["totp_secret"]).now()
            if code != last_code:
                code_input.fill(code)
                page.get_by_role("button", name="Continue", exact=True).click()
                last_code = code
        page.wait_for_timeout(600)
    assert page.url.startswith("http://localhost:8180/dashboard"), (
        "MFA did not complete; inspect local flow diagnostics"
    )
    me = context.request.get("http://localhost:8180/api/v1/auth/me")
    assert me.status == 200 and me.json()["capabilities"] == ["report:own"]
    assert (
        context.request.get("http://localhost:8180/api/v1/moderation/reports").status
        == 403
    )
    browser.close()
print(
    "Operator MFA accepted by backend; MFA did not grant operator capabilities. No reports created."
)
