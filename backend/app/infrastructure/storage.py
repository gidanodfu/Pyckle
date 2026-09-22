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

import asyncio
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol

import boto3
from botocore.config import Config
from botocore.exceptions import ClientError

from app.core.config import Settings, get_settings
from app.core.exceptions import BadRequestError, NotFoundError, StorageError


@dataclass(slots=True)
class StoredFile:
    storage_key: str


def detect_image_type(data: bytes) -> str | None:
    if data[:3] == b"\xff\xd8\xff":
        return "image/jpeg"
    if data[:8] == b"\x89PNG\r\n\x1a\n":
        return "image/png"
    if data[:4] == b"RIFF" and data[8:12] == b"WEBP":
        return "image/webp"
    return None


class StorageBackend(Protocol):
    async def save(self, *, data: bytes, content_type: str, folder: str) -> StoredFile: ...

    async def save_at(self, *, data: bytes, content_type: str, storage_key: str) -> StoredFile: ...

    async def delete(self, storage_key: str) -> None: ...

    async def get(self, storage_key: str) -> bytes: ...

    async def exists(self, storage_key: str) -> bool: ...


def validate_image(data: bytes, content_type: str, settings: Settings) -> str:
    if content_type not in settings.allowed_image_types_list:
        allowed = ", ".join(settings.allowed_image_types_list)
        raise BadRequestError(f"Tipo de archivo no permitido. Permitidos: {allowed}")
    if len(data) == 0:
        raise BadRequestError("El archivo está vacío")
    if len(data) > settings.max_upload_size_bytes:
        raise BadRequestError(f"La imagen supera el límite de {settings.max_upload_size_mb} MB")
    detected = detect_image_type(data)
    if detected is None:
        raise BadRequestError("El archivo no es una imagen válida (JPEG, PNG o WEBP)")
    if detected != content_type:
        raise BadRequestError("El contenido del archivo no coincide con su tipo declarado")
    return detected


_EXTENSIONS = {"image/jpeg": "jpg", "image/png": "png", "image/webp": "webp"}


def build_storage_key(folder: str, content_type: str) -> str:
    return f"{folder.strip('/')}/{uuid.uuid4().hex}.{_EXTENSIONS.get(content_type, 'bin')}"


class LocalStorage:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.base = Path(settings.storage_local_dir)

    def _resolve(self, key: str) -> Path:
        # Se resuelve el path y se confina a la base de almacenamiento: una
        # clave con ``..`` no puede escapar del directorio permitido.
        base = self.base.resolve()
        target = (base / key).resolve()
        if target != base and base not in target.parents:
            raise BadRequestError("Ruta de archivo inválida")
        return target

    async def save(self, *, data: bytes, content_type: str, folder: str) -> StoredFile:
        key = build_storage_key(folder, content_type)
        return await self.save_at(data=data, content_type=content_type, storage_key=key)

    async def save_at(self, *, data: bytes, content_type: str, storage_key: str) -> StoredFile:
        try:
            target = self._resolve(storage_key)
            target.parent.mkdir(parents=True, exist_ok=True)
            await asyncio.to_thread(target.write_bytes, data)
        except OSError as exc:
            raise StorageError("No se pudo guardar el archivo") from exc
        return StoredFile(storage_key=storage_key)

    async def delete(self, storage_key: str) -> None:
        try:
            target = self._resolve(storage_key)
            if target.exists():
                await asyncio.to_thread(target.unlink)
        except OSError as exc:
            raise StorageError("No se pudo eliminar el archivo") from exc

    async def get(self, storage_key: str) -> bytes:
        target = self._resolve(storage_key)
        if not target.is_file():
            raise NotFoundError("Imagen no encontrada")
        try:
            return await asyncio.to_thread(target.read_bytes)
        except OSError as exc:
            raise StorageError("No se pudo leer el archivo") from exc

    async def exists(self, storage_key: str) -> bool:
        return self._resolve(storage_key).is_file()


class S3Storage:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        try:
            self.client = boto3.client(
                "s3",
                endpoint_url=settings.supabase_s3_endpoint,
                region_name=settings.supabase_s3_region or "us-east-1",
                aws_access_key_id=settings.supabase_s3_access_key_id,
                aws_secret_access_key=settings.supabase_s3_secret_access_key,
                config=Config(signature_version="s3v4", s3={"addressing_style": "path"}),
            )
        except Exception as exc:  # noqa: BLE001
            raise StorageError("No se pudo inicializar el almacenamiento S3") from exc

    async def _put(self, *, key: str, data: bytes, content_type: str, cache: str) -> None:
        try:
            await asyncio.to_thread(
                self.client.put_object,
                Bucket=self.settings.supabase_s3_bucket,
                Key=key,
                Body=data,
                ContentType=content_type,
                CacheControl=cache,
            )
        except ClientError as exc:
            raise StorageError("No se pudo subir el archivo al almacenamiento") from exc

    async def save(self, *, data: bytes, content_type: str, folder: str) -> StoredFile:
        key = build_storage_key(folder, content_type)
        await self._put(
            key=key, data=data, content_type=content_type, cache="public, max-age=31536000"
        )
        if not await self.exists(key):
            raise StorageError("No se pudo verificar la subida de la imagen")
        return StoredFile(storage_key=key)

    async def save_at(self, *, data: bytes, content_type: str, storage_key: str) -> StoredFile:
        # Los documentos (p. ej. informes PDF) son privados: se suben con
        # ``no-store`` aunque el bucket sirva las imágenes como públicas.
        await self._put(
            key=storage_key,
            data=data,
            content_type=content_type,
            cache="private, max-age=0, no-store",
        )
        if not await self.exists(storage_key):
            raise StorageError("No se pudo verificar la subida del documento")
        return StoredFile(storage_key=storage_key)

    async def delete(self, storage_key: str) -> None:
        try:
            await asyncio.to_thread(
                self.client.delete_object,
                Bucket=self.settings.supabase_s3_bucket,
                Key=storage_key,
            )
        except ClientError as exc:
            raise StorageError("No se pudo eliminar el archivo") from exc

    async def get(self, storage_key: str) -> bytes:
        try:
            response = await asyncio.to_thread(
                self.client.get_object,
                Bucket=self.settings.supabase_s3_bucket,
                Key=storage_key,
            )
            return await asyncio.to_thread(response["Body"].read)
        except ClientError as exc:
            error_code = exc.response.get("Error", {}).get("Code")
            if error_code in {"NoSuchKey", "404", "NoSuchBucket"}:
                raise NotFoundError("Imagen no encontrada") from exc
            raise StorageError("No se pudo leer el archivo del almacenamiento") from exc

    async def exists(self, storage_key: str) -> bool:
        try:
            await asyncio.to_thread(
                self.client.head_object,
                Bucket=self.settings.supabase_s3_bucket,
                Key=storage_key,
            )
            return True
        except ClientError:
            return False


def build_storage(settings: Settings | None = None) -> StorageBackend:
    settings = settings or get_settings()
    if settings.storage_backend == "s3":
        if not settings.s3_configured:
            raise BadRequestError("El almacenamiento S3 no está configurado correctamente")
        return S3Storage(settings)
    return LocalStorage(settings)
