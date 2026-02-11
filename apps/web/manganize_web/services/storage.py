"""S3-compatible object storage service."""

import asyncio
from functools import lru_cache
from typing import Protocol

import boto3
from botocore.config import Config as BotoConfig

from manganize_web.config import settings


class StorageBackend(Protocol):
    """Interface for object storage backends."""

    def put_object(
        self, object_key: str, data: bytes, content_type: str | None
    ) -> None:
        """Upload bytes to object storage."""

    def generate_presigned_get_url(self, object_key: str, expires_in: int) -> str:
        """Generate a temporary download URL."""


class S3CompatibleStorageBackend:
    """S3-compatible backend for AWS S3 / R2 / MinIO."""

    def __init__(self) -> None:
        boto_config = BotoConfig(
            signature_version="s3v4",
            s3={
                "addressing_style": (
                    "path" if settings.storage_force_path_style else "virtual"
                )
            },
        )

        self._bucket = settings.storage_bucket
        self._client = boto3.client(
            "s3",
            region_name=settings.storage_region,
            endpoint_url=settings.storage_endpoint_url,
            aws_access_key_id=settings.storage_access_key_id,
            aws_secret_access_key=settings.storage_secret_access_key,
            config=boto_config,
        )

    def put_object(
        self, object_key: str, data: bytes, content_type: str | None
    ) -> None:
        params: dict[str, object] = {
            "Bucket": self._bucket,
            "Key": object_key,
            "Body": data,
        }
        if content_type:
            params["ContentType"] = content_type
        self._client.put_object(**params)

    def generate_presigned_get_url(self, object_key: str, expires_in: int) -> str:
        return self._client.generate_presigned_url(
            "get_object",
            Params={"Bucket": self._bucket, "Key": object_key},
            ExpiresIn=expires_in,
        )


@lru_cache(maxsize=1)
def get_storage_backend() -> StorageBackend:
    """Return the configured object storage backend."""
    return S3CompatibleStorageBackend()


async def upload_object(
    object_key: str,
    data: bytes,
    content_type: str | None,
) -> None:
    """Upload bytes to object storage asynchronously."""
    backend = get_storage_backend()
    await asyncio.to_thread(backend.put_object, object_key, data, content_type)


async def generate_presigned_get_url(object_key: str, expires_in: int) -> str:
    """Generate a presigned GET URL asynchronously."""
    backend = get_storage_backend()
    return await asyncio.to_thread(
        backend.generate_presigned_get_url,
        object_key,
        expires_in,
    )
