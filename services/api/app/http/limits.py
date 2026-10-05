"""Bound HTTP request buffering before any endpoint/form parser runs."""

import json

MAX_BODY = 11 * 1024 * 1024


class RequestLimits:
    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            return await self.app(scope, receive, send)

        async def secured(message):
            if message["type"] == "http.response.start":
                headers = list(message.get("headers", []))
                names = {k.lower() for k, v in headers}
                headers.extend(
                    (k, v)
                    for k, v in [
                        (b"x-content-type-options", b"nosniff"),
                        (b"referrer-policy", b"no-referrer"),
                        (b"cache-control", b"no-store"),
                    ]
                    if k not in names
                )
                message = {**message, "headers": headers}
            await send(message)

        async def reject():
            body = json.dumps(
                {
                    "error": {
                        "code": "request_too_large",
                        "message": "Request exceeds the upload limit",
                        "details": [],
                    }
                }
            ).encode()
            await secured(
                {
                    "type": "http.response.start",
                    "status": 413,
                    "headers": [(b"content-type", b"application/json")],
                }
            )
            await secured({"type": "http.response.body", "body": body})

        headers = dict(scope.get("headers", []))
        try:
            length = int(headers.get(b"content-length", b"0"))
        except ValueError:
            length = MAX_BODY + 1
        if length < 0 or length > MAX_BODY:
            return await reject()
        messages = []
        size = 0
        while True:
            message = await receive()
            if message["type"] == "http.disconnect":
                return
            size += len(message.get("body", b""))
            if size > MAX_BODY:
                return await reject()
            messages.append(message)
            if not message.get("more_body", False):
                break
        index = 0

        async def bounded_receive():
            nonlocal index
            if index < len(messages):
                value = messages[index]
                index += 1
                return value
            return await receive()

        await self.app(scope, bounded_receive, secured)
