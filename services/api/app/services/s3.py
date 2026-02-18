"""MinIO/S3 storage using boto3."""
import io
from typing import BinaryIO

import boto3
from botocore.config import Config
from botocore.exceptions import ClientError

from app.core.config import get_settings


def get_s3_client():
    """Get configured S3 client for MinIO."""
    settings = get_settings()
    return boto3.client(
        "s3",
        endpoint_url=settings.S3_ENDPOINT,
        aws_access_key_id=settings.S3_ACCESS_KEY,
        aws_secret_access_key=settings.S3_SECRET_KEY,
        config=Config(signature_version="s3v4"),
        region_name="us-east-1",
    )


def ensure_bucket():
    """Create bucket if it does not exist."""
    settings = get_settings()
    client = get_s3_client()
    try:
        client.head_bucket(Bucket=settings.S3_BUCKET)
    except ClientError as e:
        err = e.response.get("Error", {})
        if err.get("Code") in ("404", "NoSuchBucket"):
            client.create_bucket(Bucket=settings.S3_BUCKET)
        else:
            raise


def upload_file(key: str, body: BinaryIO, content_type: str = "application/octet-stream") -> str:
    """Upload file to MinIO. Returns the object key (path)."""
    settings = get_settings()
    ensure_bucket()
    client = get_s3_client()
    client.upload_fileobj(body, settings.S3_BUCKET, key, ExtraArgs={"ContentType": content_type})
    return key


def get_object_stream(key: str):
    """Get streaming response for object. Returns botocore stream."""
    settings = get_settings()
    client = get_s3_client()
    response = client.get_object(Bucket=settings.S3_BUCKET, Key=key)
    return response["Body"], response.get("ContentType", "application/octet-stream")
