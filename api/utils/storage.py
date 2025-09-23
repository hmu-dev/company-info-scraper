import hashlib
import mimetypes
import os
from datetime import datetime, timedelta
from typing import Dict, Optional, Tuple

import boto3

from .logging import log_event

# Initialize S3 client
s3 = boto3.client("s3")


class MediaStorage:
    def __init__(self, bucket_name: str, cloudfront_domain: str):
        """Initialize storage with S3 bucket and CloudFront domain"""
        self.bucket_name = bucket_name
        self.cloudfront_domain = cloudfront_domain

    def _get_file_hash(self, content: bytes, url: str) -> str:
        """Generate unique file hash based on content and URL"""
        hasher = hashlib.sha256()
        hasher.update(content)
        hasher.update(url.encode())
        return hasher.hexdigest()[:32]

    def _get_content_type(self, filename: str) -> str:
        """Get content type based on file extension"""
        content_type, _ = mimetypes.guess_type(filename)
        return content_type or "application/octet-stream"

    async def store_media(
        self, content: bytes, url: str, media_type: str
    ) -> Tuple[str, Dict[str, str]]:
        """
        Store media in S3 and return CloudFront URL and metadata
        Returns (url, metadata)
        """
        try:
            # Generate unique file hash
            file_hash = self._get_file_hash(content, url)

            # Determine file extension
            _, ext = os.path.splitext(url)
            if not ext:
                ext = ".jpg" if media_type == "image" else ".mp4"

            # Generate S3 key
            key = f"{media_type}s/{file_hash}{ext}"

            # Get content type
            content_type = self._get_content_type(key)

            # Upload to S3
            s3.put_object(
                Bucket=self.bucket_name,
                Key=key,
                Body=content,
                ContentType=content_type,
                CacheControl="public, max-age=31536000",  # 1 year cache
                Metadata={
                    "source_url": url,
                    "media_type": media_type,
                    "upload_date": datetime.now().isoformat(),
                },
            )

            # Generate CloudFront URL
            cdn_url = f"https://{self.cloudfront_domain}/{key}"

            # Log successful upload
            log_event(
                "media_upload",
                {
                    "url": url,
                    "cdn_url": cdn_url,
                    "media_type": media_type,
                    "size_bytes": len(content),
                    "content_type": content_type,
                },
            )

            return cdn_url, {
                "content_type": content_type,
                "size_bytes": len(content),
                "cdn_url": cdn_url,
                "original_url": url,
            }

        except Exception as e:
            # Log upload error
            log_event(
                "media_upload_error",
                {"url": url, "error": str(e), "media_type": media_type},
            )
            raise

    async def delete_media(self, url: str) -> bool:
        """Delete media from S3"""
        try:
            # Extract key from CloudFront URL
            key = url.split(self.cloudfront_domain + "/")[-1]

            # Delete from S3
            s3.delete_object(Bucket=self.bucket_name, Key=key)

            # Log successful deletion
            log_event("media_delete", {"url": url, "key": key})

            return True

        except Exception as e:
            # Log deletion error
            log_event("media_delete_error", {"url": url, "error": str(e)})
            raise

    async def get_presigned_url(
        self, url: str, expires_in: int = 3600
    ) -> Optional[str]:
        """Get presigned URL for private media access"""
        try:
            # Extract key from CloudFront URL
            key = url.split(self.cloudfront_domain + "/")[-1]

            # Generate presigned URL
            presigned_url = s3.generate_presigned_url(
                "get_object",
                Params={"Bucket": self.bucket_name, "Key": key},
                ExpiresIn=expires_in,
            )

            # Log URL generation
            log_event("presigned_url_generated", {"url": url, "expires_in": expires_in})

            return presigned_url

        except Exception as e:
            # Log URL generation error
            log_event("presigned_url_error", {"url": url, "error": str(e)})
            return None

    async def get_media_metadata(self, url: str) -> Optional[Dict[str, str]]:
        """Get media metadata from S3"""
        try:
            # Extract key from CloudFront URL
            key = url.split(self.cloudfront_domain + "/")[-1]

            # Get object metadata
            response = s3.head_object(Bucket=self.bucket_name, Key=key)

            metadata = {
                "content_type": response.get("ContentType"),
                "size_bytes": response.get("ContentLength"),
                "last_modified": response.get("LastModified").isoformat(),
                "source_url": response.get("Metadata", {}).get("source_url"),
                "media_type": response.get("Metadata", {}).get("media_type"),
                "upload_date": response.get("Metadata", {}).get("upload_date"),
            }

            return metadata

        except Exception as e:
            # Log metadata retrieval error
            log_event("media_metadata_error", {"url": url, "error": str(e)})
            return None
