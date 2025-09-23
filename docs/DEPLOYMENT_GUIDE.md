# 🌐 AI Web Scraper Deployment Guide

## AWS Deployment with Bedrock

### Overview

This guide covers deploying the AI Web Scraper API to AWS using AWS SAM (Serverless Application Model). The API uses Amazon Bedrock with Claude-Instant for content extraction and provides comprehensive monitoring and cost control.

### Architecture

The deployment uses the following AWS services:

- API Gateway: HTTP API for request handling
- Lambda: Serverless compute for API endpoints
- Bedrock: LLM service (Claude-Instant model)
- DynamoDB: Caching layer
- S3 + CloudFront: Media storage and delivery
- CloudWatch: Logging and monitoring
- AWS Budgets: Cost control

### Prerequisites

1. AWS Account with appropriate permissions
2. AWS CLI configured
3. AWS SAM CLI installed
4. Access to Amazon Bedrock (request if needed)

### Environment Variables

Create a `.env` file with:

```bash
# AWS Configuration
AWS_REGION=us-west-2
AWS_PROFILE=default

# Environment
ENVIRONMENT=dev
PROJECT_NAME=ai-web-scraper

# API Configuration
MAX_URL_LENGTH=2048
MAX_CONTENT_LENGTH=10485760  # 10MB
BLOCKED_DOMAINS=""

# Rate Limiting
RATE_LIMIT_RPM=60
RATE_LIMIT_BURST=10

# Cost Thresholds
DAILY_COST_THRESHOLD=10.0  # $10/day
HOURLY_BEDROCK_COST_THRESHOLD=1.0  # $1/hour

# Monitoring
LOG_RETENTION_DAYS=14
```

### Deployment Steps

1. Build the SAM application:

   ```bash
   cd about-us-scraper-service
   sam build
   ```

2. Deploy the application:

   ```bash
   sam deploy --guided
   ```

3. Follow the guided deployment prompts to configure:
   - Stack name
   - AWS Region
   - Environment variables
   - IAM roles

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

## Alternative Deployment Options

## Quick Public Access with ngrok (5 minutes)

### Step 1: Start the Streamlit App

```bash
cd /Users/allanjohnson/Documents/Code/awesome-llm-apps/starter_ai_agents/web_scrapping_ai_agent
source venv/bin/activate
streamlit run ai_scrapper.py --server.port 8501
```

### Step 2: Open a New Terminal and Start ngrok

```bash
ngrok http 8501
```

### Step 3: Get Your Public URL

After running ngrok, you'll see output like:

```
Web Interface                 http://127.0.0.1:4040
Forwarding                    https://abcd-1234.ngrok.app -> http://localhost:8501
```

**Share this URL:** `https://abcd-1234.ngrok.app` - Anyone can access your app!

---

## 🚀 Production Deployment Options

### Option 1: Streamlit Community Cloud (Free & Easy)

**Benefits:**

- Free hosting
- Automatic deployments from GitHub
- Built-in HTTPS
- No server management

**Steps:**

1. **Push to GitHub:**

```bash
git init
git add .
git commit -m "AI Web Scraper App"
git remote add origin https://github.com/yourusername/ai-web-scraper.git
git push -u origin main
```

2. **Deploy:**

- Visit [share.streamlit.io](https://share.streamlit.io)
- Connect GitHub
- Select repository and `ai_scrapper.py`
- Deploy!

**Result:** `https://yourapp.streamlit.app`

---

### Option 2: Railway (Easy with Custom Domain)

**Benefits:**

- Free tier available
- Custom domains
- Environment variables
- Automatic deployments

**Steps:**

1. **Create `railway.toml`:**

```toml
[build]
builder = "nixpacks"

[deploy]
startCommand = "streamlit run ai_scrapper.py --server.port $PORT --server.address 0.0.0.0"
```

2. **Deploy:**

```bash
npm install -g @railway/cli
railway login
railway init
railway up
```

---

### Option 3: Heroku

**Create these files:**

**`Procfile`:**

```
web: streamlit run ai_scrapper.py --server.port $PORT --server.address 0.0.0.0 --server.enableCORS false --server.enableXsrfProtection false
```

**`setup.sh`:**

```bash
mkdir -p ~/.streamlit/
echo "\
[server]\n\
headless = true\n\
port = $PORT\n\
enableCORS = false\n\
\n\
" > ~/.streamlit/config.toml
```

**Deploy:**

```bash
heroku create your-app-name
git push heroku main
```

---

### Option 4: DigitalOcean App Platform

**`app.yaml`:**

```yaml
name: ai-web-scraper
services:
  - name: web
    source_dir: /
    github:
      repo: yourusername/ai-web-scraper
      branch: main
    run_command: streamlit run ai_scrapper.py --server.port $PORT --server.address 0.0.0.0
    environment_slug: python
    instance_count: 1
    instance_size_slug: basic-xxs
    http_port: 8080
```

---

## 🔧 Configuration for Public Access

### Update Streamlit for Public Access

Create `.streamlit/config.toml`:

```toml
[server]
headless = true
port = 8501
enableCORS = false
enableXsrfProtection = false

[browser]
gatherUsageStats = false
```

### Environment Variables

For production, set:

```bash
export STREAMLIT_SERVER_HEADLESS=true
export STREAMLIT_SERVER_ENABLE_CORS=false
export STREAMLIT_BROWSER_GATHER_USAGE_STATS=false
```

---

## 🛡️ Security Considerations

### For ngrok (temporary testing):

- ✅ Quick and easy
- ⚠️ Tunnel URLs change on restart
- ⚠️ Anyone with URL can access

### For production:

- 🔐 Use HTTPS (most platforms provide this)
- 🛡️ Consider adding authentication
- 📊 Monitor usage and costs
- 🔒 Set up environment variables for API keys

---

## 📱 Testing Your Deployment

### Health Check Endpoints

Visit these URLs to test:

- `/` - Main app
- `/_stcore/health` - Streamlit health check

### Test with Different Devices

- Desktop browsers
- Mobile browsers
- Different networks

---

## 🚨 Quick Start (Right Now!)

**Option A: ngrok (Immediate Access)**

```bash
# Terminal 1
streamlit run ai_scrapper.py

# Terminal 2
ngrok http 8501
```

**Option B: Streamlit Cloud (Permanent)**

1. Push code to GitHub
2. Go to share.streamlit.io
3. Deploy in 2 clicks

---

## 💡 Pro Tips

1. **For Testing:** Use ngrok for quick sharing with specific people
2. **For Demo:** Use Streamlit Cloud for permanent demo URLs
3. **For Production:** Use Railway/Heroku with custom domain
4. **API Version:** Deploy the FastAPI version (`api.py`) for integration

## 🔗 Links

- [Streamlit Cloud](https://share.streamlit.io)
- [Railway](https://railway.app)
- [Heroku](https://heroku.com)
- [DigitalOcean](https://digitalocean.com)
- [ngrok](https://ngrok.com)
