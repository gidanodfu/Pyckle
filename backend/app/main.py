# Copyright (C) 2026 Josue David (gidanodfu)
# https://github.com/gidanodfu
#
# This file is part of Pyckle.
#
# Pyckle is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of
# the License, or (at your option) any later version.
#
# Pyckle is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with Pyckle. If not, see <https://www.gnu.org/licenses/>.

from __future__ import annotations

import os
from contextlib import asynccontextmanager

import redis
from fastapi import FastAPI, Request, status
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import text
from sqlalchemy.exc import DataError, IntegrityError, StatementError

from app.api import ws
from app.api.router import api_router
from app.core.config import get_settings
from app.core.exceptions import AppError
from app.core.logging import get_logger, setup_logging
from app.core.redis import close_redis, get_redis
from app.db.session import SessionLocal, engine
from app.models import User  # noqa: F401  # asegura el registro de modelos

settings = get_settings()
logger = get_logger("app")


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings.ensure_production_ready()
    setup_logging("DEBUG" if settings.debug else "INFO")
    os.makedirs(settings.storage_local_dir, exist_ok=True)
    logger.info("Iniciando %s (%s)", settings.app_name, settings.environment)
    yield
    await close_redis()
    await engine.dispose()
    logger.info("Aplicacion detenida")


# En producción se desactivan OpenAPI/docs para no exponer el contrato de la API.
_docs_enabled = not settings.is_production
app = FastAPI(
    title=settings.app_name,
    version="1.0.0",
    description="API del marketplace de reparación de dispositivos Pyckle",
    openapi_url=f"{settings.api_v1_prefix}/openapi.json" if _docs_enabled else None,
    docs_url="/docs" if _docs_enabled else None,
    redoc_url="/redoc" if _docs_enabled else None,
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
if settings.trusted_hosts_list:
    app.add_middleware(TrustedHostMiddleware, allowed_hosts=settings.trusted_hosts_list)


@app.exception_handler(AppError)
async def app_error_handler(request: Request, exc: AppError) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.message, "code": exc.code, "details": exc.details},
    )


@app.exception_handler(RequestValidationError)
async def validation_error_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "detail": "Datos de entrada inválidos",
            "code": "validation_error",
            "details": jsonable_encoder(exc.errors()),
        },
    )


@app.exception_handler(IntegrityError)
async def integrity_error_handler(request: Request, exc: IntegrityError) -> JSONResponse:
    logger.warning("Conflicto de integridad en %s %s: %s", request.method, request.url.path, exc)
    return JSONResponse(
        status_code=status.HTTP_409_CONFLICT,
        content={
            "detail": "La operación entra en conflicto con el estado actual.",
            "code": "conflict",
        },
    )


@app.exception_handler(redis.RedisError)
async def redis_error_handler(request: Request, exc: redis.RedisError) -> JSONResponse:
    logger.warning("Redis no disponible en %s %s: %s", request.method, request.url.path, exc)
    return JSONResponse(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        content={
            "detail": "Servicio temporalmente no disponible.",
            "code": "service_unavailable",
        },
    )


@app.exception_handler(DataError)
@app.exception_handler(StatementError)
async def data_error_handler(request: Request, exc: Exception) -> JSONResponse:
    logger.warning("Datos inválidos en %s %s: %s", request.method, request.url.path, exc)
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={"detail": "Datos de entrada inválidos.", "code": "unprocessable"},
    )


@app.exception_handler(Exception)
async def unhandled_error_handler(request: Request, exc: Exception) -> JSONResponse:
    logger.exception("Error no controlado en %s %s", request.method, request.url.path)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "Error interno del servidor", "code": "internal_error"},
    )


@app.get(f"{settings.api_v1_prefix}/health", tags=["health"])
async def health() -> JSONResponse:
    # Comprueba BD y Redis: un 200 con dependencias caídas daría un falso
    # positivo al orquestador y al healthcheck de contenedor.
    try:
        async with SessionLocal() as session:
            await session.execute(text("SELECT 1"))
        await get_redis().ping()
    except Exception as exc:  # noqa: BLE001
        logger.warning("Healthcheck fallido: %s", exc)
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={"status": "unhealthy"},
        )
    return JSONResponse(content={"status": "ok", "app": settings.app_name})


app.include_router(api_router, prefix=settings.api_v1_prefix)
app.include_router(ws.router)


@app.get("/", tags=["health"])
async def root() -> dict[str, str | None]:
    return {
        "app": settings.app_name,
        "docs": "/docs" if _docs_enabled else None,
        "health": f"{settings.api_v1_prefix}/health",
    }
