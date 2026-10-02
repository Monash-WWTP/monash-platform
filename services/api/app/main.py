from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from starlette.exceptions import HTTPException

from .config import settings
from .http.errors import ApiError, ErrorEnvelope, error_response, http_error_code
from .http.request_id import assign_request_id
from .routers import plants, scenarios, simulations, readiness, auth, monitoring, reports

app = FastAPI(title="Monash WWTP Platform API", version="1.0.0")
app.middleware("http")(assign_request_id)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_methods=["*"],
    allow_headers=["*"],
)

standard_errors = {
    401: {"model": ErrorEnvelope},
    404: {"model": ErrorEnvelope},
    422: {"model": ErrorEnvelope},
}
for router in (plants.router, scenarios.router, simulations.router, readiness.router, auth.router, monitoring.router, reports.router):
    app.include_router(router, prefix="/api/v1", responses=standard_errors)


@app.exception_handler(ApiError)
async def api_error_handler(request: Request, exc: ApiError):
    return error_response(request, exc.status_code, exc.code, exc.message, exc.details)


@app.exception_handler(HTTPException)
async def http_error_handler(request: Request, exc: HTTPException):
    return error_response(request, exc.status_code, http_error_code(exc), str(exc.detail), headers=exc.headers)


@app.exception_handler(RequestValidationError)
async def validation_error_handler(request: Request, exc: RequestValidationError):
    details = [{"field": ".".join(map(str, item["loc"])), "message": item["msg"]}
               for item in exc.errors()]
    return error_response(request, 422, "validation_error", "Request validation failed", details)


@app.exception_handler(Exception)
async def unexpected_error_handler(request: Request, exc: Exception):
    return error_response(request, 500, "internal_error", "Internal server error")


@app.get("/api/v1/health")
def health():
    return {"status": "ok"}
