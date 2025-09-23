"""
Pagination utility for cursor-based pagination.

This module provides utilities for cursor-based pagination, including
cursor encoding/decoding and pagination result handling.

Classes:
    Paginator: Generic paginator for any sequence type
    PaginationResult: Result of a pagination operation
    PaginationError: Error raised by pagination operations
"""

import base64
import json
from typing import Generic, List, Optional, TypeVar

from ..models import PaginationMeta


class PaginationError(Exception):
    """Error raised by pagination operations."""
    pass


T = TypeVar('T')


def encode_cursor(data: dict) -> str:
    """
    Encode cursor data as base64.

    Args:
        data: Cursor data to encode

    Returns:
        Base64-encoded cursor string
    """
    json_str = json.dumps(data)
    return base64.b64encode(json_str.encode()).decode()


class PaginationResult(Generic[T]):
    """
    Result of a pagination operation.

    Attributes:
        items: List of items for current page
        has_more: Whether more items exist
        next_cursor: Token for next page
    """
    def __init__(
        self,
        items: List[T],
        has_more: bool,
        next_cursor: Optional[str] = None
    ) -> None:
        """
        Initialize pagination result.

        Args:
            items: List of items for current page
            has_more: Whether more items exist
            next_cursor: Token for next page
        """
        self.items = items
        self.has_more = has_more
        self.next_cursor = next_cursor

    def to_dict(self) -> dict:
        """Convert to dictionary format."""
        return {
            "items": self.items,
            "pagination": PaginationMeta(
                next_cursor=self.next_cursor,
                has_more=self.has_more
            ).dict()
        }


def paginate_items(
    items: List[T],
    limit: int = 10,
    cursor: Optional[str] = None
) -> PaginationResult[T]:
    """
    Paginate a list of items.

    Args:
        items: List of items to paginate
        limit: Number of items per page
        cursor: Optional cursor from previous page

    Returns:
        Pagination result with items and metadata
    """
    paginator = Paginator(items_per_page=limit)
    return paginator.paginate(items, cursor)


def decode_cursor(cursor: str) -> dict:
    """
    Decode base64 cursor data.

    Args:
        cursor: Base64-encoded cursor string

    Returns:
        Decoded cursor data

    Raises:
        PaginationError: If cursor is invalid
    """
    try:
        json_str = base64.b64decode(cursor).decode()
        return json.loads(json_str)
    except Exception as e:
        raise PaginationError(f"Invalid cursor: {str(e)}")


class PaginationResult(Generic[T]):
    """
    Result of a pagination operation.

    Attributes:
        items: List of items for current page
        has_more: Whether more items exist
        next_cursor: Token for next page
    """
    def __init__(
        self,
        items: List[T],
        has_more: bool,
        next_cursor: Optional[str] = None
    ) -> None:
        """
        Initialize pagination result.

        Args:
            items: List of items for current page
            has_more: Whether more items exist
            next_cursor: Token for next page
        """
        self.items = items
        self.has_more = has_more
        self.next_cursor = next_cursor

    def to_dict(self) -> dict:
        """Convert to dictionary format."""
        return {
            "items": self.items,
            "pagination": PaginationMeta(
                next_cursor=self.next_cursor,
                has_more=self.has_more
            ).dict()
        }


def paginate_items(
    items: List[T],
    limit: int = 10,
    cursor: Optional[str] = None
) -> PaginationResult[T]:
    """
    Paginate a list of items.

    Args:
        items: List of items to paginate
        limit: Number of items per page
        cursor: Optional cursor from previous page

    Returns:
        Pagination result with items and metadata
    """
    paginator = Paginator(items_per_page=limit)
    return paginator.paginate(items, cursor)


def decode_cursor(cursor: str) -> dict:
    """
    Decode base64 cursor data.

    Args:
        cursor: Base64-encoded cursor string

    Returns:
        Decoded cursor data

    Raises:
        PaginationError: If cursor is invalid
    """
    try:
        json_str = base64.b64decode(cursor).decode()
        return json.loads(json_str)
    except Exception as e:
        raise PaginationError(f"Invalid cursor: {str(e)}")


class Paginator(Generic[T]):
    """
    Generic paginator for any sequence type.

    This class handles cursor-based pagination for any sequence of items.
    It uses base64-encoded cursors for pagination state.

    Attributes:
        items_per_page: Number of items per page
    """
    def __init__(self, items_per_page: int = 10) -> None:
        """
        Initialize paginator.

        Args:
            items_per_page: Number of items per page
        """
        self.items_per_page = items_per_page

    def paginate(
        self,
        items: List[T],
        cursor: Optional[str] = None
    ) -> PaginationResult[T]:
        """
        Paginate items.

        Args:
            items: List of items to paginate
            cursor: Optional cursor from previous page

        Returns:
            Pagination result with items and metadata

        Raises:
            PaginationError: If cursor is invalid
        """
        # Get starting offset
        offset = 0
        if cursor:
            try:
                cursor_data = decode_cursor(cursor)
                offset = cursor_data.get("offset", 0)
            except PaginationError:
                raise
            except Exception as e:
                raise PaginationError(f"Invalid cursor: {str(e)}")

        # Get items for current page
        start = offset
        end = offset + self.items_per_page
        page_items = items[start:end]

        # Check if more items exist
        has_more = end < len(items)

        # Generate next cursor if needed
        next_cursor = None
        if has_more:
            next_cursor = encode_cursor({"offset": end})

        return PaginationResult(
            items=page_items,
            has_more=has_more,
            next_cursor=next_cursor
        )