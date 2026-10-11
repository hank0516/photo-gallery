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


def download_to_file(key: str, path: str):
    """Stream an object from storage to a local file (no full in-memory load)."""
    get_client().download_file(settings.linode_bucket, key, path)


def create_multipart_upload(key: str, content_type: str) -> str:
    """Begin an S3 multipart upload; returns the UploadId used by subsequent part/complete calls."""
    resp = get_client().create_multipart_upload(
        Bucket=settings.linode_bucket, Key=key, ContentType=content_type,
    )
    return resp["UploadId"]


def upload_part(key: str, upload_id: str, part_number: int, body: bytes) -> str:
    """Upload one part; returns its ETag (needed to complete the multipart upload)."""
    resp = get_client().upload_part(
        Bucket=settings.linode_bucket, Key=key, UploadId=upload_id,
        PartNumber=part_number, Body=body,
    )
    return resp["ETag"]


def complete_multipart_upload(key: str, upload_id: str, parts: list[dict]):
    """Finalise the multipart upload. parts = [{"PartNumber": int, "ETag": str}, ...] in order."""
    get_client().complete_multipart_upload(
        Bucket=settings.linode_bucket, Key=key, UploadId=upload_id,
        MultipartUpload={"Parts": parts},
    )


def abort_multipart_upload(key: str, upload_id: str):
    """Discard an incomplete multipart upload (cleanup on failure/cancel)."""
    try:
        get_client().abort_multipart_upload(
            Bucket=settings.linode_bucket, Key=key, UploadId=upload_id,
        )
    except Exception:
        pass


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
