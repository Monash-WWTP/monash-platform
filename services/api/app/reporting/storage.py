"""Private S3 access; no browser/client holds bucket credentials."""
import boto3
from botocore.config import Config
from ..config import settings


def client(*, timeout=10, retries=2):
    if not settings.storage_endpoint or not settings.storage_access_key or not settings.storage_secret_key:
        raise ValueError('Private object storage is not configured')
    return boto3.client('s3',endpoint_url=settings.storage_endpoint,region_name=settings.storage_region,
        aws_access_key_id=settings.storage_access_key,aws_secret_access_key=settings.storage_secret_key,
        config=Config(signature_version='s3v4',s3={'addressing_style':'path'},connect_timeout=min(3, timeout),read_timeout=timeout,
                      retries={'max_attempts':retries}))
