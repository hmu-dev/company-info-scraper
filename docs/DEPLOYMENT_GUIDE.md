# 🌐 AI Web Scraper Deployment Guide

## AWS SAM Deployment

### Overview

This guide covers deploying the AI Web Scraper API to AWS using AWS SAM (Serverless Application Model). The API uses a hybrid approach combining programmatic extraction with AI enhancement and provides comprehensive monitoring and cost control.

### Architecture

The deployment uses the following AWS services:

- API Gateway: HTTP API for request handling
- Lambda: Serverless compute for API endpoints
- Bedrock: LLM service (Claude-Instant model) - for AI enhancement
- DynamoDB: Caching layer
- S3 + CloudFront: Media storage and delivery
- CloudWatch: Logging and monitoring
- AWS Budgets: Cost control

### Prerequisites

1. AWS Account with appropriate permissions
2. AWS CLI configured
3. AWS SAM CLI installed
4. Access to Amazon Bedrock (request if needed)
5. Python 3.9+

### Environment Variables

The deployment uses the following configuration in `samconfig.toml`:

```toml
version = 0.1
[default]
[default.deploy]
[default.deploy.parameters]
stack_name = "ai-web-scraper-hybrid"
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

### Deployment Steps

1. Build the SAM application:

   ```bash
   cd about-us-scraper-service
   sam build --use-container
   ```

2. Deploy the application:

   ```bash
   sam deploy --guided
   ```

3. Follow the guided deployment prompts to configure:
   - Stack name: `ai-web-scraper-hybrid`
   - AWS Region: `us-east-1`
   - S3 bucket for deployment artifacts
   - Environment variables

### Current Deployment

The API is currently deployed and available at:

- **Live URL**: https://cjp6f8947h.execute-api.us-east-1.amazonaws.com/
- **Interactive Docs**: https://cjp6f8947h.execute-api.us-east-1.amazonaws.com/docs
- **Region**: us-east-1
- **Stack Name**: ai-web-scraper-hybrid

### Monitoring Setup

The deployment includes:

1. CloudWatch Dashboards:

   - API performance metrics
   - Cost tracking
   - Token usage
   - Error rates

2. CloudWatch Alarms:

   - High error rate (>10% in 5 minutes)
   - High latency (>10 seconds)
   - Daily cost threshold
   - Hourly Bedrock cost threshold

3. Cost Reports:
   - Monthly AWS Cost and Usage reports
   - Hourly granularity
   - Resource-level details

### Cost Control

1. AWS Budgets:

   - Monthly budget with alerts
   - 80% actual usage alert
   - 100% forecasted usage alert

2. Bedrock Costs:

   - Claude-Instant pricing:
     - Input: $0.00163/1K tokens
     - Output: $0.00551/1K tokens
   - Hourly cost monitoring
   - Automatic alerts

3. DynamoDB Caching:
   - Reduces duplicate LLM calls
   - TTL-based expiration
   - Pay-per-request pricing

### Security

1. IAM Roles:

   - Least privilege access
   - Service-specific permissions
   - Resource-level restrictions

2. Network Security:

   - Private VPC configuration
   - CloudFront for media delivery
   - API Gateway authorization

3. Data Protection:
   - S3 encryption
   - CloudWatch log encryption
   - No PII storage

### Maintenance

1. Logging:

   - Structured JSON logs
   - Request tracing
   - Cost tracking
   - Performance metrics

2. Monitoring:

   - Real-time dashboards
   - Automated alerts
   - Cost forecasting
   - Usage trends

3. Updates:
   - Serverless deployment
   - Version control
   - CI/CD pipeline

### Troubleshooting

1. Common Issues:

   - Rate limiting: Check `RATE_LIMIT_RPM`
   - Cost alerts: Review usage patterns
   - Latency: Monitor CloudWatch metrics

2. CloudWatch Logs:

   - Lambda logs: `/aws/lambda/ai-web-scraper-*`
   - API Gateway logs: `/aws/apigateway/*`
   - Cost metrics: `AWS/Billing`

3. Support:
   - AWS Support
   - GitHub Issues
   - Documentation

### Best Practices

1. Cost Optimization:

   - Use caching effectively
   - Monitor token usage
   - Set appropriate alerts

2. Performance:

   - Enable compression
   - Use CloudFront
   - Implement retries

3. Maintenance:
   - Regular updates
   - Log review
   - Cost analysis

### Resources

- [Amazon Bedrock Documentation](https://docs.aws.amazon.com/bedrock/)
- [Claude-Instant Documentation](https://docs.anthropic.com/claude/docs)
- [AWS Lambda Best Practices](https://docs.aws.amazon.com/lambda/latest/dg/best-practices.html)
- [AWS SAM Documentation](https://docs.aws.amazon.com/serverless-application-model/)

### Support

For issues or questions:

1. Check CloudWatch logs
2. Review documentation
3. Contact support team

### License

MIT License - see LICENSE file for details

---

## 🧪 Testing Your Deployment

### Health Check Endpoints

Visit these URLs to test:

- `/health` - API health check
- `/docs` - Interactive API documentation

### Test with Different Devices

- Desktop browsers
- Mobile browsers
- Different networks

### API Testing

```bash
# Health check
curl "https://cjp6f8947h.execute-api.us-east-1.amazonaws.com/health"

# Intelligent scraping
curl "https://cjp6f8947h.execute-api.us-east-1.amazonaws.com/scrape/intelligent?url=github.com"

# Fast scraping
curl "https://cjp6f8947h.execute-api.us-east-1.amazonaws.com/scrape/fast?url=example.com"
```

---

## 💡 Pro Tips

1. **For Production:** Use the current AWS Lambda deployment
2. **For Development:** Use `sam local start-api` for local testing
3. **For Integration:** Use the `/scrape/intelligent` endpoint for best results
4. **For High Volume:** Use the `/scrape/fast` endpoint for speed

## 🔗 Links

- [AWS SAM Documentation](https://docs.aws.amazon.com/serverless-application-model/)
- [AWS Lambda Documentation](https://docs.aws.amazon.com/lambda/)
- [API Gateway Documentation](https://docs.aws.amazon.com/apigateway/)
- [Amazon Bedrock Documentation](https://docs.aws.amazon.com/bedrock/)
