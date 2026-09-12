"""
FastAPI application entry point.
Configures middleware, routers, CORS, and OpenAPI documentation.
"""

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.utils import get_openapi

from src.api.middleware.audit_context_middleware import AuditContextMiddleware
from src.api.middleware.correlation_id import CorrelationIdMiddleware
from src.api.middleware.exception_handler import ExceptionHandlerMiddleware
from src.api.middleware.request_logging import RequestLoggingMiddleware
from src.api.v1.endpoints.darwin_ad_controller import router as darwin_ad_router
from src.api.v1.endpoints.esigner_published_controller import (
    router as esigner_published_router,
)
from src.api.v1.router import api_v1_router
from src.config.logging_config import configure_file_logging
from src.config.settings import settings
from src.observability.structured_logger import configure_logging


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan: startup and shutdown hooks."""
    # Startup
    configure_logging()
    configure_file_logging()
    yield
    # Shutdown (cleanup resources here)


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Enterprise-grade FastAPI application with Clean Architecture",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# ─── OpenAPI Security Scheme (enables Swagger Authorize button) ───
def custom_openapi() -> dict[str, Any]:
    if app.openapi_schema:
        return app.openapi_schema
    openapi_schema = get_openapi(
        title=app.title,
        version=app.version,
        description=app.description,
        routes=app.routes,
    )
    # Ensure the HTTPBearer scheme is defined (matches FastAPI's HTTPBearer dependency)
    if "components" not in openapi_schema:
        openapi_schema["components"] = {}
    if "securitySchemes" not in openapi_schema["components"]:
        openapi_schema["components"]["securitySchemes"] = {}
    openapi_schema["components"]["securitySchemes"]["HTTPBearer"] = {
        "type": "http",
        "scheme": "bearer",
        "bearerFormat": "JWT",
        "description": "Enter your JWT access token",
    }
    # Apply globally so all endpoints show the lock
    openapi_schema["security"] = [{"HTTPBearer": []}]
    app.openapi_schema = openapi_schema
    return app.openapi_schema


# Overriding the bound method is FastAPI's documented way to customise the
# schema; mypy flags any method assignment, so the ignore is scoped to this line.
app.openapi = custom_openapi  # type: ignore[method-assign]

# ─── Middleware (order matters: outermost first) ───
app.add_middleware(ExceptionHandlerMiddleware)
app.add_middleware(RequestLoggingMiddleware)
app.add_middleware(AuditContextMiddleware)
app.add_middleware(CorrelationIdMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─── Routers ───
app.include_router(api_v1_router)
# Published Darwin AD service — mounted at the legacy Mendix base path so
# consuming apps only change the host, not the endpoint paths.
app.include_router(darwin_ad_router)
# Published E-Signer service — mounted at the legacy base path so consuming
# apps (e.g. Catalyst) only change the host, not the endpoint paths.
app.include_router(esigner_published_router)


@app.get("/", tags=["Root"])
async def root() -> dict[str, Any]:
    """Root endpoint - application info."""
    return {
        "app": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "docs": "/docs",
    }
