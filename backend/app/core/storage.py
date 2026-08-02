import boto3
from botocore.config import Config
from app.core.config import settings

_client = None


def get_client():
    global _client
    if _client is None:
        _client = boto3.client(
            "s3",
            endpoint_url=settings.linode_endpoint,
            aws_access_key_id=settings.linode_access_key,
            aws_secret_access_key=settings.linode_secret_key,
            config=Config(signature_version="s3v4"),
        )
    return _client


def upload_file(key: str, file_obj, content_type: str = "image/jpeg"):
    get_client().upload_fileobj(
        file_obj,
        settings.linode_bucket,
        key,
        ExtraArgs={"ContentType": content_type},
    )


def generate_presigned_url(key: str, expiry_seconds: int = 900) -> str:
    return get_client().generate_presigned_url(
        "get_object",
        Params={"Bucket": settings.linode_bucket, "Key": key},
        ExpiresIn=expiry_seconds,
    )


def generate_presigned_download_url(key: str, filename: str, expiry_seconds: int = 900) -> str:
    return get_client().generate_presigned_url(
        "get_object",
        Params={
            "Bucket": settings.linode_bucket,
            "Key": key,
            "ResponseContentDisposition": f'attachment; filename="{filename}"',
        },
        ExpiresIn=expiry_seconds,
    )


def delete_file(key: str):
    get_client().delete_object(Bucket=settings.linode_bucket, Key=key)
