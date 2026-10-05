"""Public portal contract check with external requests blocked; no live data."""
import argparse
import json
from pathlib import Path
from urllib.parse import urlparse
from playwright.sync_api import sync_playwright

p = argparse.ArgumentParser(description=__doc__)
p.add_argument('--url', default='http://127.0.0.1:5173')
p.add_argument('--screenshots')
p.add_argument('--release-manifest', type=Path, default=Path(__file__).resolve().parents[1] / 'apps/dashboard/src/releases/current.json')
a = p.parse_args()
release = json.loads(a.release_manifest.read_text()) if a.release_manifest.exists() else None
origin = a.url.rstrip('/')
with sync_playwright() as pw:
    browser = pw.chromium.launch(executable_path='/usr/bin/google-chrome', headless=True)
    context = browser.new_context(permissions=['clipboard-read', 'clipboard-write'], viewport={'width':1505,'height':1045})
    page = context.new_page()
    page.set_default_timeout(5000)
    errors = []
    page.on('pageerror', lambda e: errors.append(str(e)))
    def intercept(route):
        # Same-origin hosting may proxy /api to a live backend. Keep this public
        # route check independent of operational data and backend availability.
        if urlparse(route.request.url).path.startswith('/api/'):
            route.fulfill(status=503, json={'error': 'Synthetic unavailable API'})
        elif route.request.url.startswith(origin + '/'):
            route.continue_()
        else:
            route.abort()
    page.route('**/*', intercept)
    page.goto(origin, wait_until='networkidle')
    page.get_by_role('heading', name='Water observations. A clearer shared picture.').wait_for()
    pdf_href = '/references/urban-water-carbon-accounting-guidelines.pdf'
    assert page.get_by_role('link', name='Open the guideline PDF').get_attribute('href') == pdf_href
    page.get_by_role('link', name='View all references').click()
    page.get_by_role('heading', name='References').wait_for()
    assert page.get_by_role('link', name='Open the hosted PDF').get_attribute('href') == pdf_href
    pdf_response = page.request.get(origin + pdf_href)
    assert pdf_response.status == 200
    assert pdf_response.headers.get('content-type', '').startswith('application/pdf')
    page.goto(origin)
    page.keyboard.press('Tab')
    assert page.get_by_role('link', name='Skip to content').evaluate('(e) => e === document.activeElement')
    page.keyboard.press('Enter')
    assert page.evaluate('window.location.hash') == '#public-main'
    if release:
        assert page.get_by_role('link', name='Download Android APK').get_attribute('href') == release['artifactUrl']
    else:
        assert not page.get_by_role('button', name='Download Android APK').is_enabled()
        assert page.locator('a[href$=".apk"]').count() == 0
    page.get_by_role('link', name='Installation guide', exact=True).click()
    page.get_by_role('heading', name='CitizenFlood for Android').wait_for()
    if release:
        assert page.get_by_role('link', name='Download Android APK').get_attribute('href') == release['artifactUrl']
        page.get_by_text(release['sha256'], exact=True).wait_for()
        page.get_by_text(release['versionName'], exact=True).wait_for()
    page.get_by_role('button', name='Copy download page link').click()
    page.get_by_role('status').get_by_text('Link copied.').wait_for()
    page.goto(origin + '/research')
    page.get_by_text('Approved publications will appear here.', exact=True).wait_for()
    page.goto(origin + '/research/missing')
    page.get_by_role('heading', name='Article not found').wait_for()
    for route in ('login', 'register'):
        page.goto(origin + '/' + route)
        assert page.locator('input[type="password"]').count() == 0
        page.get_by_text('Account service is in local staging', exact=True).wait_for()
    page.goto(origin + '/plants/987')
    page.wait_for_url('**/dashboard/plants/987')
    page.get_by_role('link', name='Back to map').click()
    page.wait_for_url('**/dashboard')
    page.goto(origin)
    if a.screenshots:
        out = Path(a.screenshots); out.mkdir(parents=True, exist_ok=True)
        page.screenshot(path=str(out/'desktop.png'), full_page=True)
    for width in (1101, 1200):
        page.set_viewport_size({'width':width,'height':1045})
        assert page.evaluate('document.documentElement.scrollWidth <= window.innerWidth'), width
    page.set_viewport_size({'width':390,'height':844})
    for route in ('/', '/download', '/research', '/research/references', '/login', '/register'):
        page.goto(origin + route)
        assert page.evaluate('document.documentElement.scrollWidth <= window.innerWidth'), route
    page.get_by_role('link', name='Create account', exact=True).wait_for()
    if a.screenshots:
        page.screenshot(path=str(out/'mobile.png'), full_page=True)
    assert not errors, errors
    browser.close()
print('Public portal passed: release/account states, reference PDF, research routes, legacy links and narrow-screen layout.')
