# AI Web Scraper Service - Split API

A serverless API service with **ultra-fast text extraction** and **paginated media processing**. The service uses a split strategy for optimal performance, separating text extraction from media processing.

## Features

- **⚡ Ultra-Fast Text**: Split endpoints for lightning-fast text extraction (0.2-0.3s)
- **📸 Smart Pagination**: Cursor-based pagination for efficient media loading
- **🧠 AI Enhancement**: Optional AI-powered content analysis when needed
- **🔍 Smart Navigation**: Automatically finds relevant About Us pages
- **📊 Confidence Scoring**: Provides quality metrics for extracted data
- **🌐 Live Deployment**: Available at https://cjp6f8947h.execute-api.us-east-1.amazonaws.com/

## API Endpoints

### ⚡ **`/scrape/text`** - **ULTRA-FAST TEXT**
- 🏃‍♂️ Pure programmatic extraction (0.2-0.3s)
- 📊 Company information and about pages
- 💰 Most cost-effective for text-only needs
- 🎯 Perfect for initial app loading

### 📸 **`/scrape/media`** - **PAGINATED MEDIA**
- 🔄 Cursor-based pagination for infinite scroll
- 🖼️ Images, videos, documents, icons
- 📊 Smart prioritization (logos first)
- ⚡ Progressive loading support

### 🧠 **`/scrape/enhance`** - **AI ENHANCEMENT**
- 🧠 AI-powered content analysis when needed
- 📈 Enhanced insights and summaries
- 🎯 Use when programmatic results are insufficient
- 💡 Smart confidence scoring

### 🔄 **`/scrape` & `/scrape/about`** - **LEGACY**
- 📜 Backward compatibility endpoints
- 🔗 Redirect to `/scrape/text`
- 🔗 Use for existing integrations

## Architecture Decisions

1. **Hybrid Intelligence Approach**:

   - Fast programmatic extraction for speed
   - AI enhancement only when needed
   - Cost-effective for high-volume usage
   - Best of both worlds: speed + accuracy

2. **AWS SAM Deployment**:

   - Focused on AWS-only deployment
   - Better local development experience
   - Simpler configuration for serverless
   - Native AWS service integration

3. **Bedrock with Claude-Instant**:

   - Pay-as-you-go pricing
   - Lower latency than GPT-3.5
   - Better cost-effectiveness for our use case
   - Native AWS integration

4. **Smart Media Processing**:

   - Prioritized media extraction (logos first)
   - Efficient caching and storage
   - Multiple media types support
   - CloudFront CDN for delivery

5. **Monitoring & Cost Control**:
   - Comprehensive CloudWatch metrics
   - Cost-based alerts
   - Usage tracking
   - Performance monitoring

## Getting Started

### Live API (Recommended)

The API is deployed and ready to use:

- **Base URL**: `https://cjp6f8947h.execute-api.us-east-1.amazonaws.com/`
- **Interactive Docs**: `https://cjp6f8947h.execute-api.us-east-1.amazonaws.com/docs`
- **Health Check**: `https://cjp6f8947h.execute-api.us-east-1.amazonaws.com/health`

### Local Development

1. Prerequisites:

   ```bash
   # Install AWS SAM CLI
   brew tap aws/tap
   brew install aws-sam-cli

   # Install dependencies
   pip install -r requirements-api.txt
   ```

2. Local Development:

   ```bash
   # Start API locally
   cd about-us-scraper-service
   sam build --use-container
   sam local start-api

   # Run tests
   python -m pytest tests/
   ```

3. Deployment:

   ```bash
   # Build
   sam build --use-container

   # Deploy
   sam deploy --guided
   ```

### API Usage Examples

```bash
# Intelligent scraping (recommended)
curl "https://cjp6f8947h.execute-api.us-east-1.amazonaws.com/scrape/intelligent?url=github.com&include_media=true"

# Fast scraping (speed optimized)
curl "https://cjp6f8947h.execute-api.us-east-1.amazonaws.com/scrape/fast?url=example.com&include_media=true"

# Health check
curl "https://cjp6f8947h.execute-api.us-east-1.amazonaws.com/health"
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
