import base64
import json
from typing import List, TypeVar, Generic, Optional, Tuple
from ..models import PaginationMeta

T = TypeVar("T")


class PaginatedResult(Generic[T]):
    def __init__(
        self, items: List[T], total_count: int, limit: int, cursor: Optional[str] = None
    ):
        self.items = items
        self.total_count = total_count
        self.limit = limit
        self.cursor = cursor

        # Calculate pagination metadata
        self._calculate_pagination()

    def _calculate_pagination(self):
        """Calculate pagination metadata"""
        if not self.cursor:
            # First page
            start_index = 0
        else:
            try:
                # Decode cursor
                cursor_data = json.loads(base64.b64decode(self.cursor).decode("utf-8"))
                start_index = cursor_data.get("offset", 0)
            except:
                start_index = 0

        # Calculate remaining items
        remaining_count = max(0, self.total_count - (start_index + self.limit))

        # Determine if there are more pages
        has_more = remaining_count > 0

        # Generate cursors
        next_cursor = None
        previous_cursor = None

        if has_more:
            # Create next cursor
            next_cursor = base64.b64encode(
                json.dumps({"offset": start_index + self.limit}).encode("utf-8")
            ).decode("utf-8")

        if start_index > 0:
            # Create previous cursor
            prev_offset = max(0, start_index - self.limit)
            previous_cursor = base64.b64encode(
                json.dumps({"offset": prev_offset}).encode("utf-8")
            ).decode("utf-8")

        # Create pagination metadata
        self.pagination = PaginationMeta(
            total_count=self.total_count,
            remaining_count=remaining_count,
            has_more=has_more,
            next_cursor=next_cursor,
            previous_cursor=previous_cursor,
        )


def paginate_items(
    items: List[T], limit: int = 10, cursor: Optional[str] = None
) -> PaginatedResult[T]:
    """
    Paginate a list of items using cursor-based pagination

    Args:
        items: List of items to paginate
        limit: Number of items per page
        cursor: Base64 encoded cursor for pagination

    Returns:
        PaginatedResult containing items and pagination metadata
    """
    total_count = len(items)

    # Get start index from cursor
    if cursor:
        try:
            cursor_data = json.loads(base64.b64decode(cursor).decode("utf-8"))
            start_index = cursor_data.get("offset", 0)
        except:
            start_index = 0
    else:
        start_index = 0

    # Get paginated items
    paginated_items = items[start_index : start_index + limit]

    return PaginatedResult(
        items=paginated_items, total_count=total_count, limit=limit, cursor=cursor
    )


def decode_cursor(cursor: Optional[str]) -> Tuple[int, bool]:
    """
    Decode a pagination cursor

    Args:
        cursor: Base64 encoded cursor

    Returns:
        Tuple of (offset, is_valid)
    """
    if not cursor:
        return 0, True

    try:
        cursor_data = json.loads(base64.b64decode(cursor).decode("utf-8"))
        offset = cursor_data.get("offset", 0)
        return offset, True
    except:
        return 0, False
