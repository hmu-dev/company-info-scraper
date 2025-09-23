"""
Unit tests for the cache utility.

This module tests the DynamoDB-based caching implementation, including
cache operations, TTL handling, and error cases.
"""

import json
import time
from datetime import datetime, timedelta
from unittest.mock import Mock, patch

import pytest
from botocore.exceptions import ClientError

from api.utils.cache import Cache


@pytest.fixture
def mock_dynamodb():
    """Mock DynamoDB client."""
    with patch('boto3.client') as mock_client:
        yield mock_client.return_value


@pytest.fixture
def cache(mock_dynamodb):
    """Cache instance with mocked DynamoDB."""
    return Cache(
        table_name='test-table',
        ttl_seconds=3600,
        region='us-west-2'
    )


def test_get_cache_hit(cache, mock_dynamodb):
    """Test successful cache get."""
    # Given
    key = 'test-key'
    value = {'data': 'test-value'}
    mock_dynamodb.get_item.return_value = {
        'Item': {
            'key': {'S': key},
            'value': {'S': json.dumps(value)},
            'ttl': {'N': str(int(time.time()) + 3600)}
        }
    }

    # When
    result = cache.get(key)

    # Then
    assert result == value
    mock_dynamodb.get_item.assert_called_once_with(
        TableName='test-table',
        Key={'key': {'S': key}}
    )


def test_get_cache_miss(cache, mock_dynamodb):
    """Test cache miss."""
    # Given
    key = 'test-key'
    mock_dynamodb.get_item.return_value = {}

    # When
    result = cache.get(key)

    # Then
    assert result is None
    mock_dynamodb.get_item.assert_called_once_with(
        TableName='test-table',
        Key={'key': {'S': key}}
    )


def test_get_expired(cache, mock_dynamodb):
    """Test expired cache entry."""
    # Given
    key = 'test-key'
    value = {'data': 'test-value'}
    mock_dynamodb.get_item.return_value = {
        'Item': {
            'key': {'S': key},
            'value': {'S': json.dumps(value)},
            'ttl': {'N': str(int(time.time()) - 1)}  # Expired
        }
    }

    # When
    result = cache.get(key)

    # Then
    assert result is None
    mock_dynamodb.get_item.assert_called_once_with(
        TableName='test-table',
        Key={'key': {'S': key}}
    )


def test_get_error(cache, mock_dynamodb):
    """Test error handling in get."""
    # Given
    key = 'test-key'
    mock_dynamodb.get_item.side_effect = ClientError(
        {'Error': {'Code': 'InternalServerError', 'Message': 'Test error'}},
        'GetItem'
    )

    # When
    result = cache.get(key)

    # Then
    assert result is None
    mock_dynamodb.get_item.assert_called_once_with(
        TableName='test-table',
        Key={'key': {'S': key}}
    )


def test_set_success(cache, mock_dynamodb):
    """Test successful cache set."""
    # Given
    key = 'test-key'
    value = {'data': 'test-value'}

    # When
    cache.set(key, value)

    # Then
    mock_dynamodb.put_item.assert_called_once()
    call_args = mock_dynamodb.put_item.call_args[1]
    assert call_args['TableName'] == 'test-table'
    assert call_args['Item']['key']['S'] == key
    assert json.loads(call_args['Item']['value']['S']) == value
    assert isinstance(call_args['Item']['ttl']['N'], str)


def test_set_error(cache, mock_dynamodb):
    """Test error handling in set."""
    # Given
    key = 'test-key'
    value = {'data': 'test-value'}
    mock_dynamodb.put_item.side_effect = ClientError(
        {'Error': {'Code': 'InternalServerError', 'Message': 'Test error'}},
        'PutItem'
    )

    # When/Then
    cache.set(key, value)  # Should not raise
    mock_dynamodb.put_item.assert_called_once()


def test_delete_success(cache, mock_dynamodb):
    """Test successful cache delete."""
    # Given
    key = 'test-key'

    # When
    cache.delete(key)

    # Then
    mock_dynamodb.delete_item.assert_called_once_with(
        TableName='test-table',
        Key={'key': {'S': key}}
    )


def test_delete_error(cache, mock_dynamodb):
    """Test error handling in delete."""
    # Given
    key = 'test-key'
    mock_dynamodb.delete_item.side_effect = ClientError(
        {'Error': {'Code': 'InternalServerError', 'Message': 'Test error'}},
        'DeleteItem'
    )

    # When/Then
    cache.delete(key)  # Should not raise
    mock_dynamodb.delete_item.assert_called_once_with(
        TableName='test-table',
        Key={'key': {'S': key}}
    )
