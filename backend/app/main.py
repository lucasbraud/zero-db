import os
import sentry_sdk
from fastapi import FastAPI
from fastapi.routing import APIRoute
from starlette.middleware.cors import CORSMiddleware

from app.api.main import api_router
from app.core.config import settings

# IMPORTANT: Set DBMS_ADDRESS environment variable BEFORE any imports of api-auth or api-abstraction
# This is required for the MIRA client to work correctly
# For production MIRA, set explicitly; for dev, api-abstraction defaults to dev.mira.enlightra.com
if settings.ENVIRONMENT == "production" or "mira.enlightra.com" in settings.MIRA_BASE_URL:
    os.environ["DBMS_ADDRESS"] = settings.MIRA_BASE_URL
elif settings.ENVIRONMENT == "staging":
    os.environ["DBMS_ADDRESS"] = settings.MIRA_BASE_URL_DEV


def custom_generate_unique_id(route: APIRoute) -> str:
    return f"{route.tags[0]}-{route.name}"


if settings.SENTRY_DSN and settings.ENVIRONMENT != "local":
    sentry_sdk.init(dsn=str(settings.SENTRY_DSN), enable_tracing=True)

app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    generate_unique_id_function=custom_generate_unique_id,
)

# Set all CORS enabled origins
if settings.all_cors_origins:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.all_cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

app.include_router(api_router, prefix=settings.API_V1_STR)
