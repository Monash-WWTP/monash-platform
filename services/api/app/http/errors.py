from typing import Any

from pydantic import BaseModel
from starlette.exceptions import HTTPException
from starlette.requests import Request
from starlette.responses import JSONResponse


class ApiError(Exception):
    def __init__(self, status_code: int, code: str, message: str, details: object | None = None):
        self.status_code = status_code
        self.code = code
        self.message = message
        self.details = details


class ErrorBody(BaseModel):
    code: str
    message: str
    request_id: str
    details: Any | None = None


class ErrorEnvelope(BaseModel):
    error: ErrorBody


def error_response(request: Request, status_code: int, code: str, message: str,
                   details: object | None = None, headers: dict | None = None) -> JSONResponse:
    request_id = getattr(request.state, "request_id", "")
    response_headers = dict(headers or {})
    response_headers["X-Request-ID"] = request_id
    return JSONResponse(
        status_code=status_code,
        content={"error": {"code": code, "message": message,
                           "request_id": request_id, "details": details}},
        headers=response_headers,
    )


def http_error_code(exc: HTTPException) -> str:
    return {
        400: "bad_request", 401: "unauthorized", 403: "forbidden",
        404: "not_found", 405: "method_not_allowed", 503: "service_unavailable",
    }.get(exc.status_code, "http_error")
