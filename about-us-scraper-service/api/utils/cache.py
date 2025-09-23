"""
Cache utility for DynamoDB.

This module provides a caching utility using DynamoDB, including TTL
handling and error handling.

Classes:
    Cache: Main cache class for DynamoDB operations
"""

import json
import time
from typing import Any, Dict, Optional

import boto3
from botocore.exceptions import ClientError

from .logging import log_cache_metrics


class Cache:
    """
    Cache utility for DynamoDB.

    This class handles caching operations using DynamoDB, including
    TTL handling and error handling.

    Attributes:
        table_name: DynamoDB table name
        ttl_seconds: Cache TTL in seconds
        region: AWS region
        dynamodb: DynamoDB client
    """

    def __init__(
        self, table_name: str, region: str = "us-west-2", ttl_seconds: int = 3600
    ) -> None:
        """
        Initialize cache.

        Args:
            table_name: DynamoDB table name
            region: AWS region
            ttl_seconds: Cache TTL in seconds
        """
        self.table_name = table_name
        self.ttl_seconds = ttl_seconds
        self.region = region
        self.dynamodb = boto3.client("dynamodb", region_name=region)

    def get(self, key: str) -> Optional[Dict[str, Any]]:
        """
        Get item from cache.

        Args:
            key: Cache key

        Returns:
            Cached value or None if not found
        """
        start_time = time.time()
        try:
            # Get item from DynamoDB
            response = self.dynamodb.get_item(
                TableName=self.table_name, Key={"key": {"S": key}}
            )

            # Check if item exists
            if "Item" not in response:
                log_cache_metrics(
                    operation="get", hit=False, latency=time.time() - start_time
                )
                return None

            # Parse item
            item = response["Item"]
            value = json.loads(item["value"]["S"])
            ttl = int(item["ttl"]["N"])

            # Check if expired
            if ttl < time.time():
                log_cache_metrics(
                    operation="get", hit=False, latency=time.time() - start_time
                )
                return None

            # Return value
            log_cache_metrics(
                operation="get", hit=True, latency=time.time() - start_time
            )
            return value

        except ClientError:
            # Log error and return None
            log_cache_metrics(
                operation="get", hit=False, latency=time.time() - start_time
            )
            return None

    def set(self, key: str, value: Dict[str, Any]) -> None:
        """
        Set item in cache.

        Args:
            key: Cache key
            value: Value to cache
        """
        start_time = time.time()
        try:
            # Calculate TTL
            ttl = int(time.time()) + self.ttl_seconds

            # Put item in DynamoDB
            self.dynamodb.put_item(
                TableName=self.table_name,
                Item={
                    "key": {"S": key},
                    "value": {"S": json.dumps(value)},
                    "ttl": {"N": str(ttl)},
                },
            )

            # Log success
            log_cache_metrics(
                operation="set", hit=True, latency=time.time() - start_time
            )

        except ClientError:
            # Log error
            log_cache_metrics(
                operation="set", hit=False, latency=time.time() - start_time
            )

    def delete(self, key: str) -> None:
        """
        Delete item from cache.

        Args:
            key: Cache key
        """
        start_time = time.time()
        try:
            # Delete item from DynamoDB
            self.dynamodb.delete_item(
                TableName=self.table_name, Key={"key": {"S": key}}
            )

            # Log success
            log_cache_metrics(
                operation="delete", hit=True, latency=time.time() - start_time
            )

        except ClientError:
            # Log error
            log_cache_metrics(
                operation="delete", hit=False, latency=time.time() - start_time
            )
