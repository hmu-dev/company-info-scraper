variable "project_name" {
  description = "Name of the project"
  type        = string
  default     = "ai-web-scraper"
}

variable "environment" {
  description = "Environment (dev, staging, prod)"
  type        = string
  default     = "dev"
}

variable "aws_region" {
  description = "AWS region to deploy to"
  type        = string
  default     = "us-west-2"
}

variable "openai_api_key" {
  description = "OpenAI API key"
  type        = string
  sensitive   = true
}

variable "lambda_memory" {
  description = "Memory allocation for Lambda function (MB)"
  type        = number
  default     = 512
}

variable "lambda_timeout" {
  description = "Timeout for Lambda function (seconds)"
  type        = number
  default     = 30
}

variable "cache_ttl" {
  description = "TTL for cached items in DynamoDB (seconds)"
  type        = number
  default     = 86400  # 24 hours
}

variable "cloudfront_ttl" {
  description = "TTL for CloudFront cache (seconds)"
  type        = map(number)
  default     = {
    min     = 0
    default = 3600    # 1 hour
    max     = 86400   # 24 hours
  }
}

variable "log_retention_days" {
  description = "Number of days to retain CloudWatch logs"
  type        = number
  default     = 14
}

variable "daily_cost_threshold" {
  description = "Daily cost threshold in USD"
  type        = number
  default     = 10.0  # $10 per day
}

variable "hourly_bedrock_cost_threshold" {
  description = "Hourly Bedrock cost threshold in USD"
  type        = number
  default     = 1.0  # $1 per hour
}
