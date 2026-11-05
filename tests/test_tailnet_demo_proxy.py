import socket
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import importlib.util
from pathlib import Path
spec = importlib.util.spec_from_file_location('tailnet_demo_proxy', Path(__file__).resolve().parents[1] / 'scripts/serve_tailnet_demo.py')
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
Proxy, browser_html = module.Proxy, module.browser_html


def test_identity_frontend_uses_tailnet_without_changing_encoded_callback():
    page = b'base: "http://localhost:9100/", callback: "http%3A%2F%2Flocalhost%3A8180%2Fapi"'
    fixed = browser_html(page)
    assert b'base: "https://asus-dev.tail66f665.ts.net:10577/"' in fixed
    assert b'http%3A%2F%2Flocalhost%3A8180%2Fapi' in fixed


def test_websocket_upgrade_and_bidirectional_bytes_are_preserved():
    class Upstream(BaseHTTPRequestHandler):
        def log_message(self, *_):
            pass
        def do_GET(self):
            assert self.headers['Connection'] == 'Upgrade'
            assert self.headers['Upgrade'] == 'websocket'
            self.connection.sendall(b'HTTP/1.1 101 Switching Protocols\r\nUpgrade: websocket\r\nConnection: Upgrade\r\n\r\n')
            self.connection.sendall(self.connection.recv(4))
            self.close_connection = True
    upstream = ThreadingHTTPServer(('127.0.0.1', 0), Upstream)
    proxy = ThreadingHTTPServer(('127.0.0.1', 0), Proxy)
    proxy.upstream = upstream.server_port
    for server in (upstream, proxy):
        threading.Thread(target=server.serve_forever, daemon=True).start()
    try:
        with socket.create_connection(proxy.server_address, timeout=3) as client:
            client.sendall(b'GET /ws/client/ HTTP/1.1\r\nHost: demo.test\r\nUpgrade: websocket\r\nConnection: Upgrade\r\n\r\n')
            response = b''
            while not response.endswith(b'\r\n\r\n'):
                response += client.recv(1)
            assert response.startswith(b'HTTP/1.1 101')
            client.sendall(b'ping')
            assert client.recv(4) == b'ping'
    finally:
        for server in (proxy, upstream):
            server.shutdown()
            server.server_close()


def test_mobile_discovery_uses_remote_endpoints_but_preserves_signed_issuer():
    payload = {'issuer': 'http://localhost:9100/',
               'authorization_endpoint': 'http://localhost:9100/application/o/authorize/',
               'token_endpoint': 'http://localhost:9100/application/o/token/',
               'jwks_uri': 'http://localhost:9100/application/o/citizen-mobile/jwks/'}
    fixed = module.browser_json(payload, discovery=True)
    assert fixed['issuer'] == 'http://localhost:9100/'
    for key in ('authorization_endpoint', 'token_endpoint', 'jwks_uri'):
        assert fixed[key].startswith('https://asus-dev.tail66f665.ts.net:10577/')


def test_remote_account_actions_keep_same_origin_and_approved_paths():
    payload = {'origin': 'http://localhost:9100', 'actions': {
        'profile': 'http://localhost:9100/if/flow/monash-account-profile/',
        'other': 'https://other.example.test/path'}}
    fixed = module.browser_json(payload, account_settings=True)
    assert fixed['origin'] == 'https://asus-dev.tail66f665.ts.net:10577'
    assert fixed['actions']['profile'] == fixed['origin'] + '/if/flow/monash-account-profile/'
    assert fixed['actions']['other'] == 'https://other.example.test/path'
