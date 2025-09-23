# Cost monitoring
resource "aws_cloudwatch_metric_alarm" "daily_cost" {
  alarm_name          = "${var.project_name}-daily-cost-${var.environment}"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 1
  metric_name        = "EstimatedCharges"
  namespace          = "AWS/Billing"
  period             = 86400  # 24 hours
  statistic          = "Maximum"
  threshold          = var.daily_cost_threshold
  alarm_description  = "Daily cost exceeded threshold"
  alarm_actions      = [aws_sns_topic.alerts.arn]

  dimensions = {
    Currency = "USD"
  }
}

resource "aws_cloudwatch_metric_alarm" "bedrock_cost" {
  alarm_name          = "${var.project_name}-bedrock-cost-${var.environment}"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 1
  metric_name        = "cost_estimate_usd"
  namespace          = "AiWebScraper"
  period             = 3600  # 1 hour
  statistic          = "Sum"
  threshold          = var.hourly_bedrock_cost_threshold
  alarm_description  = "Hourly Bedrock cost exceeded threshold"
  alarm_actions      = [aws_sns_topic.alerts.arn]

  dimensions = {
    Environment = var.environment
    Model      = "anthropic.claude-instant-v1"
  }
}

# Cost metrics dashboard
resource "aws_cloudwatch_dashboard" "cost" {
  dashboard_name = "${var.project_name}-cost-${var.environment}"

  dashboard_body = jsonencode({
    widgets = [
      {
        type   = "metric"
        x      = 0
        y      = 0
        width  = 12
        height = 6

        properties = {
          metrics = [
            ["AWS/Billing", "EstimatedCharges", "Currency", "USD", { "stat": "Maximum" }]
          ]
          view    = "timeSeries"
          stacked = false
          region  = "us-east-1"  # Billing metrics are in us-east-1
          title   = "Total AWS Cost"
          period  = 3600
        }
      },
      {
        type   = "metric"
        x      = 12
        y      = 0
        width  = 12
        height = 6

        properties = {
          metrics = [
            ["AiWebScraper", "cost_estimate_usd", "Model", "anthropic.claude-instant-v1", { "stat": "Sum" }]
          ]
          view    = "timeSeries"
          stacked = false
          region  = var.aws_region
          title   = "Bedrock Cost"
          period  = 3600
        }
      },
      {
        type   = "metric"
        x      = 0
        y      = 6
        width  = 12
        height = 6

        properties = {
          metrics = [
            ["AiWebScraper", "PromptTokens", { "stat": "Sum" }],
            [".", "CompletionTokens", { "stat": "Sum" }]
          ]
          view    = "timeSeries"
          stacked = true
          region  = var.aws_region
          title   = "Token Usage"
          period  = 3600
        }
      },
      {
        type   = "metric"
        x      = 12
        y      = 6
        width  = 12
        height = 6

        properties = {
          metrics = [
            ["AiWebScraper", "RequestDuration", { "stat": "Average" }]
          ]
          view    = "timeSeries"
          stacked = false
          region  = var.aws_region
          title   = "API Latency"
          period  = 60
        }
      }
    ]
  })
}

# AWS Budget
resource "aws_budgets_budget" "monthly" {
  name              = "${var.project_name}-monthly-budget-${var.environment}"
  budget_type       = "COST"
  limit_amount      = "100"  # $100 per month
  limit_unit        = "USD"
  time_unit         = "MONTHLY"
  time_period_start = "2024-01-01_00:00"

  notification {
    comparison_operator        = "GREATER_THAN"
    threshold                 = 80
    threshold_type            = "PERCENTAGE"
    notification_type         = "ACTUAL"
    subscriber_email_addresses = ["support@example.com"]  # Update this
  }

  notification {
    comparison_operator        = "GREATER_THAN"
    threshold                 = 100
    threshold_type            = "PERCENTAGE"
    notification_type         = "FORECASTED"
    subscriber_email_addresses = ["support@example.com"]  # Update this
  }
}

# Cost and Usage Report
resource "aws_cur_report_definition" "monthly" {
  report_name                = "${var.project_name}-monthly-cur-${var.environment}"
  time_unit                 = "HOURLY"
  format                    = "Parquet"
  compression               = "Parquet"
  additional_schema_elements = ["RESOURCES"]
  s3_bucket                = aws_s3_bucket.cost_reports.id
  s3_region                = var.aws_region
  s3_prefix                = "cost-reports"
  report_versioning        = "OVERWRITE_REPORT"
  refresh_closed_reports   = true
  report_frequency         = "MONTHLY"
}

# S3 bucket for cost reports
resource "aws_s3_bucket" "cost_reports" {
  bucket = "${var.project_name}-cost-reports-${var.environment}"
}

resource "aws_s3_bucket_public_access_block" "cost_reports" {
  bucket = aws_s3_bucket.cost_reports.id

  block_public_acls       = true
  block_public_policy    = true
  ignore_public_acls     = true
  restrict_public_buckets = true
}

resource "aws_s3_bucket_policy" "cost_reports" {
  bucket = aws_s3_bucket.cost_reports.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid    = "AWSBillingDelivery"
        Effect = "Allow"
        Principal = {
          Service = "billingreports.amazonaws.com"
        }
        Action = [
          "s3:PutObject"
        ]
        Resource = [
          "${aws_s3_bucket.cost_reports.arn}/*"
        ]
      }
    ]
  })
}
