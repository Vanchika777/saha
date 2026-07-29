"""
Cloudflare R2 storage helpers (S3-compatible API via boto3).
Falls back to local disk storage (`./uploads`) if R2 credentials are not set or unavailable.
"""
import boto3
from botocore.config import Config as BotoConfig
from botocore.exceptions import ClientError
from typing import Optional
import uuid
import os

from app.config import Config

LOCAL_UPLOAD_DIR = os.path.join(os.getcwd(), "uploads")
os.makedirs(LOCAL_UPLOAD_DIR, exist_ok=True)


def _is_r2_configured() -> bool:
    return bool(Config.R2_ACCOUNT_ID and Config.R2_ACCESS_KEY_ID and Config.R2_SECRET_ACCESS_KEY)


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
    Upload bytes to R2 or local disk fallback.

    Returns:
        (object_key, public_url)
    """
    key = f"{folder}/{uuid.uuid4()}.{extension}"

    if _is_r2_configured():
        try:
            client = _get_r2_client()
            client.put_object(
                Bucket=Config.R2_BUCKET_NAME,
                Key=key,
                Body=file_bytes,
                ContentType=content_type,
            )
            public_url = f"{Config.R2_PUBLIC_URL}/{key}" if Config.R2_PUBLIC_URL else ""
            return key, public_url
        except Exception as e:
            print(f"[R2 Upload Warning] R2 upload failed, falling back to local disk: {e}")

    # Local Disk Fallback
    local_path = os.path.join(LOCAL_UPLOAD_DIR, key.replace("/", "_"))
    with open(local_path, "wb") as f:
        f.write(file_bytes)

    public_url = f"/api/books/file/{key.replace('/', '_')}"
    return key, public_url


def get_presigned_url(object_key: str, expires_in: int = 3600) -> str:
    """Generate presigned GET URL or return local fallback path."""
    if _is_r2_configured():
        try:
            client = _get_r2_client()
            url = client.generate_presigned_url(
                "get_object",
                Params={"Bucket": Config.R2_BUCKET_NAME, "Key": object_key},
                ExpiresIn=expires_in,
            )
            return url
        except Exception:
            pass

    return f"/api/books/file/{object_key.replace('/', '_')}"


def delete_file(object_key: str) -> bool:
    """Delete an object from R2 or local disk."""
    if _is_r2_configured():
        try:
            client = _get_r2_client()
            client.delete_object(Bucket=Config.R2_BUCKET_NAME, Key=object_key)
        except Exception:
            pass

    local_path = os.path.join(LOCAL_UPLOAD_DIR, object_key.replace("/", "_"))
    if os.path.exists(local_path):
        try:
            os.remove(local_path)
        except Exception:
            pass
    return True


def get_file_bytes(object_key: str) -> Optional[bytes]:
    """Get object bytes from R2 or local disk."""
    if _is_r2_configured():
        try:
            client = _get_r2_client()
            response = client.get_object(Bucket=Config.R2_BUCKET_NAME, Key=object_key)
            return response["Body"].read()
        except Exception:
            pass

    local_path = os.path.join(LOCAL_UPLOAD_DIR, object_key.replace("/", "_"))
    if os.path.exists(local_path):
        with open(local_path, "rb") as f:
            return f.read()
    return None
