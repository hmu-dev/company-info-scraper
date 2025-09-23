"""
Unit tests for the logging utility.

This module tests the structured logging and metric publishing functions,
including event logging and CloudWatch metrics.
"""

import json
import logging
from datetime import datetime
from unittest.mock import Mock, patch

import pytest
from botocore.stub import Stubber, ANY

from api.utils.logging import log_event, publish_metrics


def test_log_event(capsys):
    """Test structured event logging."""
    # Given
    event_type = "test_event"
    data = {"key": "value"}
    request_id = "123"

    # When
    log_event(event_type, data, request_id)

    # Then
    captured = capsys.readouterr()
    log_data = json.loads(captured.out)
    assert log_data["event_type"] == event_type
    assert log_data["data"] == data
    assert log_data["request_id"] == request_id
    assert "timestamp" in log_data


def test_log_event_no_request_id(capsys):
    """Test event logging without request ID."""
    # Given
    event_type = "test_event"
    data = {"key": "value"}

    # When
    log_event(event_type, data)

    # Then
    captured = capsys.readouterr()
    log_data = json.loads(captured.out)
    assert log_data["event_type"] == event_type
    assert log_data["data"] == data
    assert log_data["request_id"] is None
    assert "timestamp" in log_data


def test_publish_metrics_success():
    """Test successful metric publishing."""
    # Given
    namespace = "TestNamespace"
    metrics = {
        "TestMetric1": (1.0, "Count"),
        "TestMetric2": (2.5, "Seconds")
    }

    # Mock CloudWatch client
    mock_client = Mock()
    mock_client.put_metric_data.return_value = {}

    # When
    with patch('boto3.client', return_value=mock_client):
        publish_metrics([
            {
                'name': 'TestMetric1',
                'value': 1.0,
                'unit': 'Count'
            },
            {
                'name': 'TestMetric2',
                'value': 2.5,
                'unit': 'Seconds'
            }
        ])

    # Then
    mock_client.put_metric_data.assert_called_once_with(
        Namespace='AboutUsScraper',
        MetricData=[
            {
                'MetricName': 'TestMetric1',
                'Value': 1.0,
                'Unit': 'Count'
            },
            {
                'MetricName': 'TestMetric2',
                'Value': 2.5,
                'Unit': 'Seconds'
            }
        ]
    )


def test_publish_metrics_error(capsys):
    """Test metric publishing error handling."""
    # Given
    metrics = [
        {
            "name": "TestMetric",
            "value": 1.0,
            "unit": "Count"
        }
    ]

    # Mock CloudWatch client to raise error
    mock_client = Mock()
    mock_client.put_metric_data.side_effect = Exception("Test error")

    # When
    with patch('boto3.client', return_value=mock_client):
        publish_metrics(metrics)

    # Then
    captured = capsys.readouterr()
    log_data = json.loads(captured.out)
    assert log_data["event_type"] == "metric_error"
    assert log_data["data"]["error"] == "Test error"


def test_publish_metrics_empty():
    """Test publishing empty metrics."""
    # Given
    namespace = "TestNamespace"
    metrics = {}

    # Mock CloudWatch client
    mock_client = Mock()
    mock_client.put_metric_data.return_value = {}

    # When
    with patch('boto3.client', return_value=mock_client):
        publish_metrics([])

    # Then
    mock_client.put_metric_data.assert_called_once_with(
        Namespace='AboutUsScraper',
        MetricData=[]
    )


def test_publish_metrics_invalid_unit():
    """Test publishing metrics with invalid unit."""
    # Given
    namespace = "TestNamespace"
    metrics = {
        "TestMetric": (1.0, "InvalidUnit")
    }

    # Mock CloudWatch client
    mock_client = Mock()
    mock_client.put_metric_data.side_effect = Exception("Invalid metric unit")

    # When
    with patch('boto3.client', return_value=mock_client):
        publish_metrics([
            {
                'name': 'TestMetric',
                'value': 1.0,
                'unit': 'InvalidUnit'
            }
        ])  # Should not raise

    # Then
    mock_client.put_metric_data.assert_called_once_with(
        Namespace='AboutUsScraper',
        MetricData=[
            {
                'MetricName': 'TestMetric',
                'Value': 1.0,
                'Unit': 'InvalidUnit'
            }
        ]
    )
