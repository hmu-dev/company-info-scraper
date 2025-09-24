# AWS SAM Deployment Guide

## Overview

This guide covers deploying the AI Web Scraper API using AWS SAM (Serverless Application Model). The application uses a **split API strategy** with ultra-fast text extraction and paginated media processing, powered by Amazon Bedrock with Claude-Instant for AI enhancement when needed.

## Prerequisites

1. AWS Account with appropriate permissions
2. AWS CLI configured
3. SAM CLI installed
4. Python 3.9+
5. Access to Amazon Bedrock (request if needed)
6. Docker (for containerized builds)

## Local Development Setup

1. Install SAM CLI:

   ```bash
   brew tap aws/tap
   brew install aws-sam-cli
   ```

2. Install dependencies:

   ```bash
   pip install -r requirements-api.txt
   ```

3. Run locally:

   ```bash
   cd about-us-scraper-service
   sam build --use-container
   sam local start-api
   ```

4. Test split API endpoints:
   ```bash
   # Health check
   curl http://localhost:3000/health
   
   # Ultra-fast text extraction
   curl "http://localhost:3000/scrape/text?url=github.com"
   
   # Paginated media extraction
   curl "http://localhost:3000/scrape/media?url=github.com&limit=10"
   
   # AI enhancement when needed
   curl "http://localhost:3000/scrape/enhance?url=github.com"
   ```

## Configuration

1. Environment Variables:
   Create `samconfig.toml`:

   ```toml
   version = 0.1
   [default]
   [default.deploy]
   [default.deploy.parameters]
   stack_name = "ai-web-scraper-split"
   s3_bucket = "your-deployment-bucket"
   region = "us-east-1"
   confirm_changeset = true
   capabilities = "CAPABILITY_IAM"
   parameter_overrides = [
     "Environment=dev",
     "DailyCostThreshold=10.0",
     "HourlyBedrockCostThreshold=1.0",
     "RateLimitRPM=60",
     "RateLimitBurst=10",
     "LogRetentionDays=14"
   ]
   ```

2. Current Deployment:
   The API is currently deployed and available at:

   - **Live URL**: https://cjp6f8947h.execute-api.us-east-1.amazonaws.com/
   - **Interactive Docs**: https://cjp6f8947h.execute-api.us-east-1.amazonaws.com/docs
   - **Region**: us-east-1
   - **Stack Name**: ai-web-scraper-hybrid

3. Hybrid Configuration:
   The application uses a hybrid approach:
   - **Fast Path**: Programmatic extraction (0.2-0.3s)
   - **Smart Path**: AI enhancement when needed (2-5s)
   - **Bedrock Integration**: Claude-Instant for AI processing

## Deployment

1. Build:

   ```bash
   cd about-us-scraper-service
   sam build --use-container
   ```

2. Validate:

   ```bash
   sam validate
   ```

3. Deploy:

   ```bash
   sam deploy --guided
   ```

4. Update:
   ```bash
   sam deploy
   ```

### Current Deployment Status

The API is currently deployed and running:
- **Status**: ✅ Live and operational
- **Region**: us-east-1
- **Last Updated**: Recent deployment with hybrid approach
- **Health Check**: https://cjp6f8947h.execute-api.us-east-1.amazonaws.com/health

## Testing

1. Live API Testing:

   ```bash
   # Health check
   curl "https://cjp6f8947h.execute-api.us-east-1.amazonaws.com/health"
   
   # Intelligent scraping
   curl "https://cjp6f8947h.execute-api.us-east-1.amazonaws.com/scrape/intelligent?url=github.com"
   
   # Fast scraping
   curl "https://cjp6f8947h.execute-api.us-east-1.amazonaws.com/scrape/fast?url=example.com"
   ```

2. Local Testing:

   ```bash
   sam local invoke ScraperFunction -e events/test_event.json
   ```

3. Unit Tests:
   ```bash
   python -m pytest tests/
   ```

## Monitoring

1. View Logs:

   ```bash
   sam logs -n ScraperFunction --tail
   ```

2. Metrics:

   ```bash
   aws cloudwatch get-metric-statistics \
     --namespace AiWebScraper \
     --metric-name RequestDuration \
     --statistics Average \
     --period 300 \
     --start-time "2024-01-01T00:00:00" \
     --end-time "2024-01-02T00:00:00"
   ```

3. Dashboards:
   - Open AWS Console
   - Navigate to CloudWatch
   - Select "Dashboards"
   - Open "ai-web-scraper-metrics"

## Cost Control

1. View Costs:

   ```bash
   aws ce get-cost-and-usage \
     --time-period Start=2024-01-01,End=2024-02-01 \
     --granularity MONTHLY \
     --metrics "UnblendedCost" \
     --group-by Type=DIMENSION,Key=SERVICE
   ```

2. Budget Alerts:

   - Set in AWS Console
   - Navigate to AWS Budgets
   - Open "ai-web-scraper-monthly"

3. Cost Optimization:
   - Use caching effectively
   - Monitor token usage
   - Set appropriate alerts

## Troubleshooting

1. Common Issues:

   - Rate limiting: Check `RateLimitRPM`
   - Cost alerts: Review usage patterns
   - Latency: Monitor CloudWatch metrics

2. CloudWatch Logs:

   ```bash
   # View error logs
   sam logs -n ScraperFunction --filter "ERROR"

   # View high latency requests
   sam logs -n ScraperFunction --filter "duration > 5000"
   ```

3. Debugging:

   ```bash
   # Local debugging
   sam local invoke -d 5858 ScraperFunction

   # Attach debugger
   sam local start-api -d 5858
   ```

## Security

1. IAM Roles:

   - Review `template.yaml`
   - Check Lambda role permissions
   - Verify Bedrock access

2. Network Security:

   - API Gateway authorization
   - VPC configuration
   - CloudFront settings

3. Data Protection:
   - S3 encryption
   - CloudWatch encryption
   - No PII storage

## Best Practices

1. Development:

   - Use SAM CLI for local testing
   - Follow Python best practices
   - Write comprehensive tests

2. Deployment:

   - Use version control
   - Review changes before deploy
   - Test in staging first

3. Monitoring:
   - Check logs regularly
   - Review metrics
   - Set up alerts

## Resources

- [SAM CLI Documentation](https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/serverless-sam-cli-command-reference.html)
- [Bedrock Documentation](https://docs.aws.amazon.com/bedrock/)
- [CloudWatch Documentation](https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/)
