# About Us Scraper Service

A serverless API service that extracts company information from websites using AI. The service uses AWS Bedrock with Claude-Instant to analyze web content and return structured company information.

## Features

- **Company Profile Extraction**: Analyzes websites to extract:

  - About Us information
  - Company culture
  - Team details
  - Noteworthy and differentiated features
  - Company locations

- **Media Asset Processing**:

  - Extracts relevant images and videos
  - Converts SVGs to PNGs for better compatibility
  - Filters media by relevance and quality
  - Stores media in S3 with CloudFront CDN

- **Performance & Scalability**:
  - Serverless architecture using AWS Lambda
  - DynamoDB caching for improved response times
  - CloudFront CDN for media delivery
  - Rate limiting and request validation

## Architecture Decisions

1. **AWS SAM over Terraform**:

   - Focused on AWS-only deployment
   - Better local development experience
   - Simpler configuration for serverless
   - Native AWS service integration

2. **Bedrock with Claude-Instant**:

   - Pay-as-you-go pricing
   - Lower latency than GPT-3.5
   - Better cost-effectiveness for our use case
   - Native AWS integration

3. **Separate Media Processing**:

   - Paginated media responses
   - Independent scaling
   - Optimized mobile experience
   - Efficient caching

4. **Monitoring & Cost Control**:
   - Comprehensive CloudWatch metrics
   - Cost-based alerts
   - Usage tracking
   - Performance monitoring

## Getting Started

1. Prerequisites:

   ```bash
   # Install AWS SAM CLI
   brew tap aws/tap
   brew install aws-sam-cli

   # Install dependencies
   pip install -r api/requirements.txt
   ```

2. Local Development:

   ```bash
   # Start API locally
   sam local start-api

   # Run tests
   python -m pytest tests/
   ```

3. Deployment:

   ```bash
   # Build
   sam build

   # Deploy
   sam deploy --guided
   ```

## API Endpoints

1. Profile Extraction:

   ```bash
   POST /v1/profile
   {
     "url": "https://example.com"
   }
   ```

2. Media Assets:
   ```bash
   POST /v1/media
   {
     "url": "https://example.com",
     "cursor": "optional-pagination-cursor",
     "limit": 10
   }
   ```

## Configuration

1. Environment Variables:

   - `ENVIRONMENT`: Deployment environment (dev/staging/prod)
   - `RATE_LIMIT_RPM`: Requests per minute limit
   - `DAILY_COST_THRESHOLD`: Daily cost alert threshold
   - See `env.json` for full list

2. AWS Resources:
   - Lambda function
   - API Gateway
   - DynamoDB table
   - S3 bucket
   - CloudFront distribution
   - CloudWatch dashboards

## Monitoring

1. CloudWatch Metrics:

   - API latency
   - Token usage
   - Media processing time
   - Error rates
   - Cache performance

2. Cost Alerts:
   - Daily AWS cost
   - Hourly Bedrock usage
   - Storage utilization
   - Request volume

## Testing

1. Unit Tests:

   - API endpoints
   - Service logic
   - Utility functions
   - Error handling

2. Integration Tests:

   - End-to-end flows
   - Error scenarios
   - Rate limiting
   - Caching

3. Load Tests:
   - Concurrent requests
   - Response times
   - Error rates
   - Resource usage

## Security

1. API Security:

   - Rate limiting
   - Request validation
   - Input sanitization
   - Error handling

2. AWS Security:
   - IAM roles
   - Resource encryption
   - Network isolation
   - Access logging

## Contributing

1. Code Style:

   - Follow PEP 8
   - Use type hints
   - Add docstrings
   - Write tests

2. Pull Requests:
   - Create feature branch
   - Add tests
   - Update docs
   - Request review

## License

MIT License - see LICENSE file

## Support

For issues and feature requests, please use GitHub Issues.
