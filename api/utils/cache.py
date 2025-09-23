import boto3
import json
import time
from typing import Any, Dict, Optional, Tuple
from .logging import log_cache_metrics

# Initialize DynamoDB client
dynamodb = boto3.client("dynamodb")


class Cache:
    def __init__(self, table_name: str, ttl: int = 86400):
        """Initialize cache with DynamoDB table name and TTL"""
        self.table_name = table_name
        self.ttl = ttl

    def _get_expiry(self) -> int:
        """Get expiry timestamp"""
        return int(time.time()) + self.ttl

    async def get(
        self, url: str, cache_type: str = "profile"
    ) -> Tuple[Optional[Dict[str, Any]], bool]:
        """
        Get item from cache
        Returns (item, hit) where hit is True if cache hit, False if miss
        """
        start_time = time.time()
        try:
            response = dynamodb.get_item(
                TableName=self.table_name,
                Key={"url": {"S": url}, "type": {"S": cache_type}},
            )

            if "Item" in response:
                item = response["Item"]
                # Check if item is expired
                if int(item.get("expires_at", {}).get("N", 0)) > int(time.time()):
                    # Parse the cached data
                    data = json.loads(item["data"]["S"])

                    # Log cache hit
                    log_cache_metrics(
                        {
                            "operation": "Hit",
                            "success": True,
                            "duration": time.time() - start_time,
                        }
                    )

                    return data, True
                else:
                    # Delete expired item
                    await self.delete(url, cache_type)

            # Log cache miss
            log_cache_metrics(
                {
                    "operation": "Miss",
                    "success": True,
                    "duration": time.time() - start_time,
                }
            )

            return None, False

        except Exception as e:
            # Log cache error
            log_cache_metrics(
                {
                    "operation": "Get",
                    "success": False,
                    "duration": time.time() - start_time,
                }
            )
            raise

    async def set(
        self, url: str, data: Dict[str, Any], cache_type: str = "profile"
    ) -> bool:
        """Set item in cache"""
        start_time = time.time()
        try:
            # Convert data to JSON string
            data_str = json.dumps(data)

            # Store in DynamoDB
            dynamodb.put_item(
                TableName=self.table_name,
                Item={
                    "url": {"S": url},
                    "type": {"S": cache_type},
                    "data": {"S": data_str},
                    "expires_at": {"N": str(self._get_expiry())},
                    "created_at": {"N": str(int(time.time()))},
                },
            )

            # Log cache set
            log_cache_metrics(
                {
                    "operation": "Set",
                    "success": True,
                    "duration": time.time() - start_time,
                }
            )

            return True

        except Exception as e:
            # Log cache error
            log_cache_metrics(
                {
                    "operation": "Set",
                    "success": False,
                    "duration": time.time() - start_time,
                }
            )
            raise

    async def delete(self, url: str, cache_type: str = "profile") -> bool:
        """Delete item from cache"""
        start_time = time.time()
        try:
            dynamodb.delete_item(
                TableName=self.table_name,
                Key={"url": {"S": url}, "type": {"S": cache_type}},
            )

            # Log cache delete
            log_cache_metrics(
                {
                    "operation": "Delete",
                    "success": True,
                    "duration": time.time() - start_time,
                }
            )

            return True

        except Exception as e:
            # Log cache error
            log_cache_metrics(
                {
                    "operation": "Delete",
                    "success": False,
                    "duration": time.time() - start_time,
                }
            )
            raise

    async def get_or_set(
        self, url: str, getter: callable, cache_type: str = "profile"
    ) -> Tuple[Dict[str, Any], bool]:
        """
        Get from cache or call getter function and cache result
        Returns (data, cached) where cached is True if result was from cache
        """
        # Try to get from cache
        data, hit = await self.get(url, cache_type)
        if hit:
            return data, True

        # Call getter function
        data = await getter()

        # Cache the result
        await self.set(url, data, cache_type)

        return data, False
