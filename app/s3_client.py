import aioboto3
from contextlib import asynccontextmanager
from app.config import S3_CONFIG


class S3Client:
    def __init__(self):
        self.config = {
            "endpoint_url": S3_CONFIG.endpoint_url,
            "aws_access_key_id": S3_CONFIG.access_key,
            "aws_secret_access_key": S3_CONFIG.secret_key.get_secret_value(),
            "region_name": "us-east-1",
        }
        self.allowed_buckets = {S3_CONFIG.bucket_notes, S3_CONFIG.bucket_avatars}
        self.session = aioboto3.Session()

    @asynccontextmanager
    async def get_client(self):
        async with self.session.client("s3", **self.config) as client:
            yield client

    async def upload_file(self, file: bytes, bucket_name: str, object_name: str, content_type: str = "image/jpeg") -> str:
        if bucket_name not in self.allowed_buckets:
            raise ValueError(f"Bucket {bucket_name} is not allowed")

        async with self.get_client() as client:
            await client.put_object(
                Bucket=bucket_name,
                Key=object_name,
                Body=file,
                ContentType=content_type
            )

        return f"{self.config['endpoint_url']}/{bucket_name}/{object_name}"


s3_client = S3Client()
