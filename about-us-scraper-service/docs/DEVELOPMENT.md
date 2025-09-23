# Development Guide

## Overview

This guide covers development practices, testing procedures, and deployment workflows for the About Us Scraper Service.

## Development Environment

1. Python Setup:

   ```bash
   # Create virtual environment
   python -m venv venv
   source venv/bin/activate

   # Install dependencies
   pip install -r requirements.txt
   ```

2. AWS Setup:

   ```bash
   # Configure AWS CLI
   aws configure

   # Install SAM CLI
   brew tap aws/tap
   brew install aws-sam-cli
   ```

3. Environment Variables:

   ```bash
   # Copy template
   cp env.example.json env.json

   # Edit variables
   nano env.json
   ```

## Code Style

1. Python Standards:

   - Follow PEP 8
   - Use type hints
   - Maximum line length: 88 characters
   - Use f-strings for string formatting

2. Documentation:

   - Docstrings for all public functions
   - Type hints for parameters
   - Examples in docstrings
   - Update API.md for endpoint changes

3. Code Organization:
   ```
   api/
   ├── config/       # Configuration files
   ├── endpoints/    # API endpoints
   ├── middleware/   # Request/response middleware
   ├── models/       # Pydantic models
   ├── services/     # Business logic
   └── utils/        # Helper functions
   ```

## Testing

1. Unit Tests:

   ```bash
   # Run all tests
   pytest

   # Run specific test file
   pytest tests/unit/test_llm.py

   # Run with coverage
   pytest --cov=api tests/
   ```

2. Integration Tests:

   ```bash
   # Start local API
   sam local start-api

   # Run integration tests
   pytest tests/integration/
   ```

3. Load Tests:

   ```bash
   # Install artillery
   npm install -g artillery

   # Run load tests
   artillery run tests/load/scenarios.yml
   ```

## Debugging

1. Local API:

   ```bash
   # Start API with debugging
   sam local start-api -d 5858

   # Attach debugger
   # Configure IDE to connect to port 5858
   ```

2. Lambda Function:

   ```bash
   # Debug single invocation
   sam local invoke -d 5858 ScraperFunction \
     -e events/test_event.json
   ```

3. Logging:

   ```bash
   # View logs
   sam logs -n ScraperFunction --tail

   # Filter errors
   sam logs -n ScraperFunction --filter "ERROR"
   ```

## CI/CD Pipeline

1. GitHub Actions:

   ```yaml
   # .github/workflows/main.yml
   name: CI/CD
   on: [push, pull_request]
   jobs:
     test:
       runs-on: ubuntu-latest
       steps:
         - uses: actions/checkout@v2
         - name: Test
           run: |
             pip install -r requirements.txt
             pytest
     deploy:
       needs: test
       if: github.ref == 'refs/heads/main'
       runs-on: ubuntu-latest
       steps:
         - uses: actions/checkout@v2
         - name: Deploy
           run: sam deploy
   ```

2. Environments:

   - Development: Manual deployment
   - Staging: Auto-deploy on main
   - Production: Manual approval

3. Monitoring:
   - CloudWatch dashboards
   - Error alerts
   - Cost alerts

## Performance Optimization

1. Caching:

   - DynamoDB for responses
   - CloudFront for media
   - Local memory cache

2. Media Processing:

   - Async processing
   - Size limits
   - Format conversion

3. Cost Control:
   - Token usage monitoring
   - Storage cleanup
   - Request throttling

## Security

1. Code Security:

   - Input validation
   - Output sanitization
   - Error handling

2. Infrastructure:

   - IAM roles
   - Network isolation
   - Encryption

3. Monitoring:
   - Access logs
   - Error tracking
   - Rate limiting

## Deployment

1. Development:

   ```bash
   # Build
   sam build

   # Deploy to dev
   sam deploy --config-env dev
   ```

2. Staging:

   ```bash
   # Deploy to staging
   sam deploy --config-env staging
   ```

3. Production:
   ```bash
   # Deploy to prod
   sam deploy --config-env prod
   ```

## Troubleshooting

1. Common Issues:

   - Rate limiting
   - Token usage
   - Media processing

2. Debugging:

   - CloudWatch logs
   - X-Request-ID tracking
   - Error stack traces

3. Performance:
   - Response times
   - Cache hit rates
   - Error rates

## Best Practices

1. Code Review:

   - Unit tests required
   - Documentation updated
   - Performance considered

2. Git Workflow:

   - Feature branches
   - Pull requests
   - Squash merges

3. Documentation:
   - Keep API.md updated
   - Document decisions
   - Update examples

## Resources

1. Documentation:

   - [SAM CLI Guide](https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/serverless-sam-cli-command-reference.html)
   - [FastAPI Docs](https://fastapi.tiangolo.com/)
   - [Bedrock Guide](https://docs.aws.amazon.com/bedrock/)

2. Tools:

   - [pytest](https://docs.pytest.org/)
   - [black](https://black.readthedocs.io/)
   - [mypy](https://mypy.readthedocs.io/)

3. AWS Services:
   - [Lambda](https://aws.amazon.com/lambda/)
   - [API Gateway](https://aws.amazon.com/api-gateway/)
   - [CloudWatch](https://aws.amazon.com/cloudwatch/)
