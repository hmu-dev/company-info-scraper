terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 4.0"
    }
  }
  
  backend "s3" {
    bucket = "ai-web-scraper-terraform-state"
    key    = "state/terraform.tfstate"
    region = "us-west-2"
  }
}

provider "aws" {
  region = var.aws_region
}

# Lambda function
resource "aws_lambda_function" "scraper_api" {
  filename         = "../api/deployment.zip"
  function_name    = "${var.project_name}-api-${var.environment}"
  role            = aws_iam_role.lambda_role.arn
  handler         = "api.lambda_handler.lambda_handler"
  runtime         = "python3.9"
  timeout         = 30
  memory_size     = 512

  environment {
    variables = {
      ENVIRONMENT = var.environment
      OPENAI_API_KEY = var.openai_api_key
      DYNAMODB_TABLE = aws_dynamodb_table.cache_table.name
      S3_BUCKET = aws_s3_bucket.media_bucket.id
    }
  }
}

# API Gateway
resource "aws_apigatewayv2_api" "api" {
  name          = "${var.project_name}-api-${var.environment}"
  protocol_type = "HTTP"
}

resource "aws_apigatewayv2_stage" "api" {
  api_id = aws_apigatewayv2_api.api.id
  name   = var.environment
  auto_deploy = true

  access_log_settings {
    destination_arn = aws_cloudwatch_log_group.api_logs.arn
    format = jsonencode({
      requestId               = "$context.requestId"
      sourceIp               = "$context.identity.sourceIp"
      requestTime            = "$context.requestTime"
      protocol              = "$context.protocol"
      httpMethod            = "$context.httpMethod"
      resourcePath          = "$context.resourcePath"
      routeKey              = "$context.routeKey"
      status                = "$context.status"
      responseLength        = "$context.responseLength"
      integrationErrorMessage = "$context.integrationErrorMessage"
    })
  }
}

# S3 bucket for media storage
resource "aws_s3_bucket" "media_bucket" {
  bucket = "${var.project_name}-media-${var.environment}"
}

resource "aws_s3_bucket_public_access_block" "media_bucket" {
  bucket = aws_s3_bucket.media_bucket.id

  block_public_acls       = true
  block_public_policy    = true
  ignore_public_acls     = true
  restrict_public_buckets = true
}

# CloudFront distribution
resource "aws_cloudfront_distribution" "media_cdn" {
  enabled = true
  
  origin {
    domain_name = aws_s3_bucket.media_bucket.bucket_regional_domain_name
    origin_id   = "S3Origin"

    s3_origin_config {
      origin_access_identity = aws_cloudfront_origin_access_identity.media_oai.cloudfront_access_identity_path
    }
  }

  default_cache_behavior {
    allowed_methods  = ["GET", "HEAD", "OPTIONS"]
    cached_methods   = ["GET", "HEAD"]
    target_origin_id = "S3Origin"

    forwarded_values {
      query_string = false
      cookies {
        forward = "none"
      }
    }

    viewer_protocol_policy = "redirect-to-https"
    min_ttl                = 0
    default_ttl            = 3600
    max_ttl                = 86400
  }

  restrictions {
    geo_restriction {
      restriction_type = "none"
    }
  }

  viewer_certificate {
    cloudfront_default_certificate = true
  }
}

# DynamoDB table for caching
resource "aws_dynamodb_table" "cache_table" {
  name           = "${var.project_name}-cache-${var.environment}"
  billing_mode   = "PAY_PER_REQUEST"
  hash_key       = "url"
  range_key      = "type"

  attribute {
    name = "url"
    type = "S"
  }

  attribute {
    name = "type"
    type = "S"
  }

  ttl {
    attribute_name = "expires_at"
    enabled        = true
  }
}

# CloudWatch Log Groups
resource "aws_cloudwatch_log_group" "lambda_logs" {
  name              = "/aws/lambda/${aws_lambda_function.scraper_api.function_name}"
  retention_in_days = 14
}

resource "aws_cloudwatch_log_group" "api_logs" {
  name              = "/aws/apigateway/${var.project_name}-${var.environment}"
  retention_in_days = 14
}

# Bedrock configuration
resource "aws_bedrock_model_access" "claude" {
  model_id = "anthropic.claude-instant-v1"
}

# IAM roles and policies
resource "aws_iam_role" "lambda_role" {
  name = "${var.project_name}-lambda-role-${var.environment}"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "lambda.amazonaws.com"
        }
      }
    ]
  })
}

resource "aws_iam_role_policy_attachment" "lambda_basic" {
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
  role       = aws_iam_role.lambda_role.name
}

resource "aws_iam_role_policy" "lambda_policy" {
  name = "${var.project_name}-lambda-policy-${var.environment}"
  role = aws_iam_role.lambda_role.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "dynamodb:GetItem",
          "dynamodb:PutItem",
          "dynamodb:UpdateItem",
          "dynamodb:DeleteItem",
          "dynamodb:Query"
        ]
        Resource = aws_dynamodb_table.cache_table.arn
      },
      {
        Effect = "Allow"
        Action = [
          "s3:PutObject",
          "s3:GetObject",
          "s3:DeleteObject"
        ]
        Resource = "${aws_s3_bucket.media_bucket.arn}/*"
      },
      {
        Effect = "Allow"
        Action = [
          "cloudwatch:PutMetricData"
        ]
        Resource = "*"
      },
      {
        Effect = "Allow"
        Action = [
          "bedrock:InvokeModel"
        ]
        Resource = "arn:aws:bedrock:${var.aws_region}::foundation-model/anthropic.claude-instant-v1"
      }
    ]
  })
}

# Outputs
output "api_endpoint" {
  value = aws_apigatewayv2_api.api.api_endpoint
}

output "cloudfront_domain" {
  value = aws_cloudfront_distribution.media_cdn.domain_name
}

output "media_bucket_name" {
  value = aws_s3_bucket.media_bucket.id
}

output "cache_table_name" {
  value = aws_dynamodb_table.cache_table.name
}
