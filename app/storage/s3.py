"""Penyimpanan file di S3 (LocalStack saat dev): terenkripsi, pre-signed URL, TTL."""
import uuid

import boto3
from botocore.exceptions import ClientError

from app.config import settings


def client():
    return boto3.client("s3", endpoint_url=settings.s3_endpoint_url)


def ensure_bucket() -> None:
    s3 = client()
    try:
        s3.head_bucket(Bucket=settings.s3_bucket)
    except ClientError:
        s3.create_bucket(Bucket=settings.s3_bucket)
    # Hapus otomatis setelah N hari (data minimization).
    s3.put_bucket_lifecycle_configuration(
        Bucket=settings.s3_bucket,
        LifecycleConfiguration={"Rules": [{
            "ID": "ttl",
            "Status": "Enabled",
            "Filter": {"Prefix": ""},
            "Expiration": {"Days": settings.file_ttl_days},
        }]},
    )
    s3.put_public_access_block(
        Bucket=settings.s3_bucket,
        PublicAccessBlockConfiguration={
            "BlockPublicAcls": True, "IgnorePublicAcls": True,
            "BlockPublicPolicy": True, "RestrictPublicBuckets": True,
        },
    )


def put_file(user: str, filename: str, data: bytes) -> str:
    key = f"{user}/{uuid.uuid4()}/{filename}"
    client().put_object(
        Bucket=settings.s3_bucket, Key=key, Body=data,
        ServerSideEncryption="AES256",
    )
    return key


def get_file(key: str) -> bytes:
    return client().get_object(Bucket=settings.s3_bucket, Key=key)["Body"].read()


def presigned_url(key: str, expires: int = 300) -> str:
    return client().generate_presigned_url(
        "get_object", Params={"Bucket": settings.s3_bucket, "Key": key}, ExpiresIn=expires
    )
