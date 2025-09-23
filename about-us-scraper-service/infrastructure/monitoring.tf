# CloudWatch Dashboard
resource "aws_cloudwatch_dashboard" "main" {
  dashboard_name = "${var.project_name}-dashboard-${var.environment}"

  dashboard_body = jsonencode({
    widgets = [
      # API Performance
      {
        type   = "metric"
        x      = 0
        y      = 0
        width  = 12
        height = 6

        properties = {
          metrics = [
            ["AiWebScraper", "RequestDuration", "Environment", var.environment, { "stat": "Average" }],
            [".", "LLMLatency", ".", ".", { "stat": "Average" }],
            [".", "MediaProcessingTime", ".", ".", { "stat": "Average" }]
          ]
          view    = "timeSeries"
          stacked = false
          region  = var.aws_region
          title   = "API Performance"
          period  = 300
        }
      },

      # Request Counts
      {
        type   = "metric"
        x      = 12
        y      = 0
        width  = 12
        height = 6

        properties = {
          metrics = [
            ["AiWebScraper", "SuccessfulRequests", "Environment", var.environment, { "stat": "Sum" }],
            [".", "FailedRequests", ".", ".", { "stat": "Sum" }]
          ]
          view    = "timeSeries"
          stacked = true
          region  = var.aws_region
          title   = "Request Counts"
          period  = 300
        }
      },

      # Token Usage
      {
        type   = "metric"
        x      = 0
        y      = 6
        width  = 12
        height = 6

        properties = {
          metrics = [
            ["AiWebScraper", "PromptTokens", "Environment", var.environment, { "stat": "Sum" }],
            [".", "CompletionTokens", ".", ".", { "stat": "Sum" }]
          ]
          view    = "timeSeries"
          stacked = true
          region  = var.aws_region
          title   = "Token Usage"
          period  = 300
        }
      },

      # Cache Performance
      {
        type   = "metric"
        x      = 12
        y      = 6
        width  = 12
        height = 6

        properties = {
          metrics = [
            ["AiWebScraper", "CacheHits", "Environment", var.environment, { "stat": "Sum" }],
            [".", "CacheMisses", ".", ".", { "stat": "Sum" }]
          ]
          view    = "timeSeries"
          stacked = true
          region  = var.aws_region
          title   = "Cache Performance"
          period  = 300
        }
      },

      # Media Processing
      {
        type   = "metric"
        x      = 0
        y      = 12
        width  = 12
        height = 6

        properties = {
          metrics = [
            ["AiWebScraper", "ImageCount", "Environment", var.environment, { "stat": "Sum" }],
            [".", "VideoCount", ".", ".", { "stat": "Sum" }]
          ]
          view    = "timeSeries"
          stacked = true
          region  = var.aws_region
          title   = "Media Processing"
          period  = 300
        }
      },

      # Error Rates
      {
        type   = "metric"
        x      = 12
        y      = 12
        width  = 12
        height = 6

        properties = {
          metrics = [
            ["AiWebScraper", "Errors", "Environment", var.environment, { "stat": "Sum" }]
          ]
          view    = "timeSeries"
          stacked = false
          region  = var.aws_region
          title   = "Error Count"
          period  = 300
        }
      }
    ]
  })
}

# CloudWatch Alarms
resource "aws_cloudwatch_metric_alarm" "high_error_rate" {
  alarm_name          = "${var.project_name}-high-error-rate-${var.environment}"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 2
  metric_name        = "Errors"
  namespace          = "AiWebScraper"
  period             = 300
  statistic          = "Sum"
  threshold          = 10
  alarm_description  = "This metric monitors error rate"
  alarm_actions      = [aws_sns_topic.alerts.arn]

  dimensions = {
    Environment = var.environment
  }
}

resource "aws_cloudwatch_metric_alarm" "high_latency" {
  alarm_name          = "${var.project_name}-high-latency-${var.environment}"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 2
  metric_name        = "RequestDuration"
  namespace          = "AiWebScraper"
  period             = 300
  statistic          = "Average"
  threshold          = 10
  alarm_description  = "This metric monitors API latency"
  alarm_actions      = [aws_sns_topic.alerts.arn]

  dimensions = {
    Environment = var.environment
  }
}

resource "aws_cloudwatch_metric_alarm" "high_token_usage" {
  alarm_name          = "${var.project_name}-high-token-usage-${var.environment}"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 1
  metric_name        = "TotalTokens"
  namespace          = "AiWebScraper"
  period             = 86400
  statistic          = "Sum"
  threshold          = 1000000
  alarm_description  = "This metric monitors daily token usage"
  alarm_actions      = [aws_sns_topic.alerts.arn]

  dimensions = {
    Environment = var.environment
  }
}

resource "aws_cloudwatch_metric_alarm" "high_storage_usage" {
  alarm_name          = "${var.project_name}-high-storage-usage-${var.environment}"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 1
  metric_name        = "MediaSize"
  namespace          = "AiWebScraper"
  period             = 3600
  statistic          = "Sum"
  threshold          = 5000000000  # 5GB
  alarm_description  = "This metric monitors media storage usage"
  alarm_actions      = [aws_sns_topic.alerts.arn]

  dimensions = {
    Environment = var.environment
  }
}

# SNS Topic for Alerts
resource "aws_sns_topic" "alerts" {
  name = "${var.project_name}-alerts-${var.environment}"
}

resource "aws_sns_topic_policy" "alerts" {
  arn = aws_sns_topic.alerts.arn

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Principal = {
          Service = "cloudwatch.amazonaws.com"
        }
        Action   = "SNS:Publish"
        Resource = aws_sns_topic.alerts.arn
      }
    ]
  })
}
