"""
Unit tests for the pagination utility.

This module tests the cursor-based pagination implementation, including
cursor encoding/decoding, limit handling, and error cases.
"""

import base64
import json
from typing import List, Optional

import pytest

from api.utils.pagination import (
    Paginator,
    PaginationError,
    PaginationResult,
    decode_cursor,
    encode_cursor,
)


def test_encode_cursor():
    """Test cursor encoding."""
    # Given
    cursor_data = {"key": "value", "number": 42}

    # When
    cursor = encode_cursor(cursor_data)

    # Then
    assert isinstance(cursor, str)
    decoded = json.loads(base64.b64decode(cursor))
    assert decoded == cursor_data


def test_decode_cursor():
    """Test cursor decoding."""
    # Given
    cursor_data = {"key": "value", "number": 42}
    cursor = base64.b64encode(json.dumps(cursor_data).encode()).decode()

    # When
    decoded = decode_cursor(cursor)

    # Then
    assert decoded == cursor_data


def test_decode_cursor_invalid():
    """Test invalid cursor decoding."""
    # Given
    cursor = "invalid-cursor"

    # When/Then
    with pytest.raises(PaginationError):
        decode_cursor(cursor)


class TestPaginator:
    """Test cases for Paginator class."""

    def test_paginate_first_page(self):
        """Test first page pagination."""
        # Given
        items = list(range(10))
        paginator = Paginator[int](items_per_page=3)

        # When
        result = paginator.paginate(items)

        # Then
        assert isinstance(result, PaginationResult)
        assert result.items == [0, 1, 2]
        assert result.has_more is True
        assert result.next_cursor is not None

    def test_paginate_middle_page(self):
        """Test middle page pagination."""
        # Given
        items = list(range(10))
        paginator = Paginator[int](items_per_page=3)
        first_page = paginator.paginate(items)

        # When
        result = paginator.paginate(items, first_page.next_cursor)

        # Then
        assert result.items == [3, 4, 5]
        assert result.has_more is True
        assert result.next_cursor is not None

    def test_paginate_last_page(self):
        """Test last page pagination."""
        # Given
        items = list(range(10))
        paginator = Paginator[int](items_per_page=3)
        first_page = paginator.paginate(items)
        second_page = paginator.paginate(items, first_page.next_cursor)
        third_page = paginator.paginate(items, second_page.next_cursor)

        # When
        result = paginator.paginate(items, third_page.next_cursor)

        # Then
        assert result.items == [9]
        assert result.has_more is False
        assert result.next_cursor is None

    def test_paginate_empty_list(self):
        """Test pagination with empty list."""
        # Given
        items: List[int] = []
        paginator = Paginator[int](items_per_page=3)

        # When
        result = paginator.paginate(items)

        # Then
        assert result.items == []
        assert result.has_more is False
        assert result.next_cursor is None

    def test_paginate_invalid_cursor(self):
        """Test pagination with invalid cursor."""
        # Given
        items = list(range(10))
        paginator = Paginator[int](items_per_page=3)

        # When/Then
        with pytest.raises(PaginationError):
            paginator.paginate(items, "invalid-cursor")

    def test_paginate_cursor_out_of_range(self):
        """Test pagination with cursor beyond list bounds."""
        # Given
        items = list(range(10))
        paginator = Paginator[int](items_per_page=3)
        cursor = encode_cursor({"offset": 20})

        # When
        result = paginator.paginate(items, cursor)

        # Then
        assert result.items == []
        assert result.has_more is False
        assert result.next_cursor is None

    def test_paginate_custom_items_per_page(self):
        """Test pagination with custom page size."""
        # Given
        items = list(range(10))
        paginator = Paginator[int](items_per_page=5)

        # When
        result = paginator.paginate(items)

        # Then
        assert result.items == [0, 1, 2, 3, 4]
        assert result.has_more is True
        assert result.next_cursor is not None
