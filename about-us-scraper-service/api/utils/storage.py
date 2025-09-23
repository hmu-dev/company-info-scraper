"""
Storage utility for S3 and CloudFront.

This module provides a storage utility for handling file operations with
S3 and CloudFront, including file uploads, downloads, and URL generation.

Classes:
    Storage: Main storage class for S3 and CloudFront operations
    StorageError: Custom exception for storage operations
"""


class StorageError(Exception):
    """Custom exception for storage operations."""
    pass

import io
import time
from datetime import datetime
from typing import Optional, Union

import boto3
from botocore.exceptions import ClientError
from botocore.signers import CloudFrontSigner
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding


class MediaStorage:
    """
    Storage utility for S3 and CloudFront operations.

    This class handles file operations with S3 and CloudFront, including
    file uploads, downloads, and URL generation.

    Attributes:
        bucket_name: S3 bucket name
        cloudfront_domain: CloudFront domain name
        region: AWS region
        s3: S3 client
    """

    def __init__(
        self,
        bucket_name: str,
        cloudfront_domain: str,
        region: str = "us-west-2"
    ) -> None:
        """
        Initialize storage utility.

        Args:
            bucket_name: S3 bucket name
            cloudfront_domain: CloudFront domain name
            region: AWS region
        """
        self.bucket_name = bucket_name
        self.cloudfront_domain = cloudfront_domain
        self.region = region
        self.s3 = boto3.client("s3", region_name=region)

    def upload(
        self,
        key: str,
        data: Union[bytes, io.BytesIO],
        content_type: str
    ) -> str:
        """
        Upload file to S3.

        Args:
            key: S3 object key
            data: File data
            content_type: File content type

        Returns:
            CloudFront URL for the uploaded file

        Raises:
            Exception: If upload fails
        """
        try:
            self.s3.put_object(
                Bucket=self.bucket_name,
                Key=key,
                Body=data,
                ContentType=content_type
            )
            return self.get_url(key)
        except ClientError as e:
            raise Exception(f"Failed to upload file: {str(e)}")

    def download(self, key: str) -> bytes:
        """
        Download file from S3.

        Args:
            key: S3 object key

        Returns:
            File data

        Raises:
            Exception: If download fails
        """
        try:
            response = self.s3.get_object(
                Bucket=self.bucket_name,
                Key=key
            )
            return response["Body"].read()
        except ClientError as e:
            raise Exception(f"Failed to download file: {str(e)}")

    def delete(self, key: str) -> None:
        """
        Delete file from S3.

        Args:
            key: S3 object key
        """
        try:
            self.s3.delete_object(
                Bucket=self.bucket_name,
                Key=key
            )
        except ClientError:
            # Ignore errors on delete
            pass

    def get_url(self, key: str, expiry: Optional[int] = None) -> str:
        """
        Get CloudFront URL for file.

        Args:
            key: S3 object key
            expiry: Optional URL expiry in seconds

        Returns:
            CloudFront URL
        """
        url = f"https://{self.cloudfront_domain}/{key}"

        if expiry is not None:
            # Create CloudFront signer
            key_id = "CLOUDFRONT_KEY_ID"
            key_path = "path/to/private_key.pem"

            with open(key_path, "rb") as key_file:
                private_key = serialization.load_pem_private_key(
                    key_file.read(),
                    password=None
                )

            signer = CloudFrontSigner(key_id, lambda x: private_key.sign(
                x,
                padding.PKCS1v15(),
                hashes.SHA1()
            ))

            # Generate signed URL
            expiry_date = datetime.fromtimestamp(time.time() + expiry)
            url = signer.generate_presigned_url(
                url,
                date_less_than=expiry_date
            )

        return url

    async def store_media(self, url: str, media_type: str) -> tuple[str, dict]:
        """
        Store media from URL in S3.

        Args:
            url: Media URL
            media_type: Media type (image/video)

        Returns:
            Tuple of (CloudFront URL, metadata)

        Raises:
            StorageError: If storage operation fails
        """
        try:
            # Download and process media
            # This is a placeholder - actual implementation would download and process media
            raise Exception("Storage error: Failed to store media")
        except Exception as e:
            raise StorageError(str(e)) from e