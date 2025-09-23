"""
Unit tests for the storage utility.

This module tests the S3 and CloudFront storage implementation, including
file operations, URL generation, and error handling.
"""

import io
from unittest.mock import Mock, patch

import pytest
from botocore.exceptions import ClientError

from api.utils.storage import MediaStorage


@pytest.fixture
def mock_s3():
    """Mock S3 client."""
    with patch('boto3.client') as mock_client:
        yield mock_client.return_value


@pytest.fixture
def storage(mock_s3):
    """Storage instance with mocked S3."""
    return MediaStorage(
        bucket_name='test-bucket',
        cloudfront_domain='test.cloudfront.net',
        region='us-west-2'
    )


def test_upload_success(storage, mock_s3):
    """Test successful file upload."""
    # Given
    key = 'test/file.txt'
    data = b'test data'
    content_type = 'text/plain'

    # When
    result = storage.upload(key, data, content_type)

    # Then
    assert result == f'https://test.cloudfront.net/{key}'
    mock_s3.put_object.assert_called_once_with(
        Bucket='test-bucket',
        Key=key,
        Body=data,
        ContentType=content_type
    )


def test_upload_error(storage, mock_s3):
    """Test error handling in upload."""
    # Given
    key = 'test/file.txt'
    data = b'test data'
    content_type = 'text/plain'
    mock_s3.put_object.side_effect = ClientError(
        {'Error': {'Code': 'InternalServerError', 'Message': 'Test error'}},
        'PutObject'
    )

    # When/Then
    with pytest.raises(Exception):
        storage.upload(key, data, content_type)


def test_download_success(storage, mock_s3):
    """Test successful file download."""
    # Given
    key = 'test/file.txt'
    data = b'test data'
    mock_s3.get_object.return_value = {
        'Body': io.BytesIO(data),
        'ContentType': 'text/plain'
    }

    # When
    result = storage.download(key)

    # Then
    assert result == data
    mock_s3.get_object.assert_called_once_with(
        Bucket='test-bucket',
        Key=key
    )


def test_download_error(storage, mock_s3):
    """Test error handling in download."""
    # Given
    key = 'test/file.txt'
    mock_s3.get_object.side_effect = ClientError(
        {'Error': {'Code': 'NoSuchKey', 'Message': 'Test error'}},
        'GetObject'
    )

    # When/Then
    with pytest.raises(Exception):
        storage.download(key)


def test_delete_success(storage, mock_s3):
    """Test successful file deletion."""
    # Given
    key = 'test/file.txt'

    # When
    storage.delete(key)

    # Then
    mock_s3.delete_object.assert_called_once_with(
        Bucket='test-bucket',
        Key=key
    )


def test_delete_error(storage, mock_s3):
    """Test error handling in delete."""
    # Given
    key = 'test/file.txt'
    mock_s3.delete_object.side_effect = ClientError(
        {'Error': {'Code': 'InternalServerError', 'Message': 'Test error'}},
        'DeleteObject'
    )

    # When/Then
    storage.delete(key)  # Should not raise
    mock_s3.delete_object.assert_called_once_with(
        Bucket='test-bucket',
        Key=key
    )


def test_get_url(storage):
    """Test CloudFront URL generation."""
    # Given
    key = 'test/file.txt'

    # When
    url = storage.get_url(key)

    # Then
    assert url == f'https://test.cloudfront.net/{key}'


def test_get_url_with_expiry(storage):
    """Test presigned URL generation."""
    # Given
    key = 'test/file.txt'
    expiry = 3600

    # When
    # Mock file operations
    mock_file = Mock()
    mock_file.read.return_value = b'test key'
    mock_context = Mock()
    mock_context.__enter__ = Mock(return_value=mock_file)
    mock_context.__exit__ = Mock()
    mock_open = Mock(return_value=mock_context)
    mock_private_key = Mock()
    mock_private_key.sign.return_value = b'test signature'
    mock_load_key = Mock(return_value=mock_private_key)

    with patch('builtins.open', mock_open), \
         patch('cryptography.hazmat.primitives.serialization.load_pem_private_key', mock_load_key):
        url = storage.get_url(key, expiry)

    # Then
    assert url.startswith('https://test.cloudfront.net/')
    assert key in url
    assert 'Expires=' in url
    assert 'Signature=' in url
