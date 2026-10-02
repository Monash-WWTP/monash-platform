"""Browser check with synthetic services; blocks all external network requests."""
import argparse
import struct
import zlib
from urllib.parse import urlparse

from playwright.sync_api import sync_playwright

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("--url", default="http://127.0.0.1:5173")
parser.add_argument("--browser-executable")
args = parser.parse_args()
origin = args.url.rstrip("/")
style = {
    "version": 8,
    "sources": {
        "openmaptiles": {"type": "geojson", "data": {"type": "FeatureCollection", "features": []}},
        "synthetic": {"type": "raster", "tiles": [origin + "/synthetic/{z}/{x}/{y}.png"],
                      "tileSize": 256, "attribution": '<span>Synthetic attribution</span><details open onload="1" ontoggle="window.__xss=1">Attack</details>'},
    },
    "layers": [{"id": "synthetic", "type": "raster", "source": "synthetic"},
               {"id": "building", "type": "fill-extrusion", "source": "openmaptiles", "paint": {"fill-extrusion-height": 1}}],
}


def chunk(kind, data):
    return struct.pack("!I", len(data)) + kind + data + struct.pack("!I", zlib.crc32(kind + data))


png = (b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack("!2I5B", 1, 1, 8, 6, 0, 0, 0))
       + chunk(b"IDAT", zlib.compress(b"\x00\x00\x00\x00\xff")) + chunk(b"IEND", b""))


def intercept(route):
    url = route.request.url
    path = urlparse(url).path
    cors = {"Access-Control-Allow-Origin": "*"}
    if "tiles.openfreemap.org/styles/" in url:
        route.fulfill(json=style, headers=cors)
    elif path.startswith("/synthetic/"):
        route.fulfill(body=png, content_type="image/png")
    elif path.startswith("/rest/v1/stations"):
        route.fulfill(json=[{"code": "DEMO001", "name": "Synthetic smoke station", "stp_type": "synthetic", "category": "B", "latitude": 3.1012, "longitude": 101.6394}], headers=cors)
    elif path.startswith(("/rest/v1/", "/api/", "/auth/v1/")):
        route.fulfill(json=[], headers=cors)
    elif url.startswith(origin + "/"):
        route.continue_()
    else:
        route.abort()


with sync_playwright() as playwright:
    browser = playwright.chromium.launch(executable_path=args.browser_executable, headless=True,
                                        args=["--use-angle=swiftshader", "--enable-unsafe-swiftshader"])
    page = browser.new_page()
    errors = []
    page.on("pageerror", lambda error: errors.append(str(error)))
    page.on("console", lambda message: errors.append(message.text) if message.type == "error" else None)
    page.route("**/*", intercept)
    page.goto(origin + "/", wait_until="networkidle")
    page.locator(".maplibregl-canvas").wait_for()
    page.locator(".maplibregl-ctrl-attrib").get_by_text("Synthetic attribution").wait_for()
    assert page.evaluate("window.__xss") is None
    assert page.locator(".maplibregl-ctrl-attrib [ontoggle], .maplibregl-ctrl-attrib [onload]").count() == 0
    assert not errors, errors
    browser.close()
    print("Map smoke passed: canvas, bundled worker, sanitized synthetic attribution; no browser errors")
