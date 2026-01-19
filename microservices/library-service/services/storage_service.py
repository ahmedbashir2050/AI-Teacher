import aioboto3
from core.config import settings
from botocore.exceptions import ClientError
import logging

logger = logging.getLogger(__name__)

class StorageService:
    def __init__(self):
        self.session = aioboto3.Session()
        self.endpoint_url = settings.S3_ENDPOINT_URL
        self.aws_access_key_id = settings.S3_ACCESS_KEY
        self.aws_secret_access_key = settings.S3_SECRET_KEY
        self.region_name = settings.S3_REGION
        self.bucket_name = settings.S3_BUCKET_NAME

    async def upload_file(self, file_data: bytes, file_key: str):
        async with self.session.client(
            "s3",
            endpoint_url=self.endpoint_url,
            aws_access_key_id=self.aws_access_key_id,
            aws_secret_access_key=self.aws_secret_access_key,
            region_name=self.region_name,
        ) as s3:
            try:
                await s3.put_object(Bucket=self.bucket_name, Key=file_key, Body=file_data)
                return True
            except ClientError as e:
                logger.error(f"Failed to upload file to S3: {e}")
                return False

    async def generate_presigned_url(self, file_key: str, expiration: int = 900):
        async with self.session.client(
            "s3",
            endpoint_url=self.endpoint_url,
            aws_access_key_id=self.aws_access_key_id,
            aws_secret_access_key=self.aws_secret_access_key,
            region_name=self.region_name,
        ) as s3:
            try:
                url = await s3.generate_presigned_url(
                    "get_object",
                    Params={"Bucket": self.bucket_name, "Key": file_key},
                    ExpiresIn=expiration,
                )
                return url
            except ClientError as e:
                logger.error(f"Failed to generate presigned URL: {e}")
                return None

storage_service = StorageService()
