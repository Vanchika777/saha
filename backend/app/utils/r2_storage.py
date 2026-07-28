"""
Cloudflare R2 storage helpers (S3-compatible API via boto3).
Handles upload, signed URL generation, and deletion.
"""
import boto3
from botocore.config import Config as BotoConfig
from botocore.exceptions import ClientError
from typing import Optional
import uuid
import os

from app.config import Config


def _get_r2_client():
    """Return a boto3 S3 client pointed at Cloudflare R2."""
    endpoint = f"https://{Config.R2_ACCOUNT_ID}.r2.cloudflarestorage.com"
    return boto3.client(
        "s3",
        endpoint_url=endpoint,
        aws_access_key_id=Config.R2_ACCESS_KEY_ID,
        aws_secret_access_key=Config.R2_SECRET_ACCESS_KEY,
        config=BotoConfig(signature_version="s3v4"),
        region_name="auto",
    )


def upload_file(
    file_bytes: bytes,
    content_type: str,
    folder: str = "books",
    extension: str = "pdf",
) -> tuple[str, str]:
    """
    Upload bytes to R2.

    Returns:
        (object_key, public_url)
    """
    key = f"{folder}/{uuid.uuid4()}.{extension}"
    client = _get_r2_client()

    client.put_object(
        Bucket=Config.R2_BUCKET_NAME,
        Key=key,
        Body=file_bytes,
        ContentType=content_type,
    )

    # Build public URL (requires R2 public bucket or custom domain)
    public_url = f"{Config.R2_PUBLIC_URL}/{key}" if Config.R2_PUBLIC_URL else ""
    return key, public_url


def get_presigned_url(object_key: str, expires_in: int = 3600) -> str:
    """
    Generate a time-limited presigned GET URL for a private R2 object.
    Use this for PDF download links.
    """
    client = _get_r2_client()
    try:
        url = client.generate_presigned_url(
            "get_object",
            Params={"Bucket": Config.R2_BUCKET_NAME, "Key": object_key},
            ExpiresIn=expires_in,
        )
        return url
    except ClientError:
        return ""


def delete_file(object_key: str) -> bool:
    """Delete an object from R2. Returns True on success."""
    client = _get_r2_client()
    try:
        client.delete_object(Bucket=Config.R2_BUCKET_NAME, Key=object_key)
        return True
    except ClientError:
        return False


def get_file_bytes(object_key: str) -> Optional[bytes]:
    """Download an object from R2 and return its bytes (for PDF processing)."""
    client = _get_r2_client()
    try:
        response = client.get_object(
            Bucket=Config.R2_BUCKET_NAME, Key=object_key
        )
        return response["Body"].read()
    except ClientError:
        return None
