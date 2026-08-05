from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config.settings import settings


def add_cors(app: FastAPI) -> None:
    origins = list(settings.cors.allow_origins)
    allow_credentials = settings.cors.allow_credentials
    # FastAPI forbids credentials with wildcard origin; demo stacks often set ["*"].
    if "*" in origins:
        origins = ["*"]
        allow_credentials = False
    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=allow_credentials,
        allow_methods=settings.cors.allow_methods,
        allow_headers=settings.cors.allow_headers,
    )
