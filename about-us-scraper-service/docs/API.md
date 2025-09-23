# API Documentation

## Overview

The About Us Scraper Service provides RESTful endpoints for extracting company information and media assets from websites. The service uses AWS Bedrock with Claude-Instant for content analysis and returns structured data.

## Base URL

```
https://{api-id}.execute-api.{region}.amazonaws.com/
```

## Endpoints

### 1. Extract Company Profile

```http
POST /v1/profile
```

Extracts company information from a website.

#### Request

```json
{
  "url": "https://example.com"
}
```

#### Response

```json
{
  "success": true,
  "data": {
    "about_us": "Company description...",
    "our_culture": "Culture description...",
    "our_team": "Team description...",
    "noteworthy_and_differentiated": "Unique features...",
    "locations": "Company locations..."
  },
  "token_usage": {
    "prompt_tokens": 123,
    "completion_tokens": 456
  },
  "duration": 2.5
}
```

#### Error Response

```json
{
  "success": false,
  "error": "Error message",
  "error_type": "ValidationError"
}
```

### 2. Extract Media Assets

```http
POST /v1/media
```

Extracts images and videos from a website.

#### Request

```json
{
  "url": "https://example.com",
  "cursor": "optional-pagination-cursor",
  "limit": 10
}
```

#### Response

```json
{
  "success": true,
  "data": {
    "items": [
      {
        "url": "https://cdn.example.com/image.jpg",
        "type": "image",
        "metadata": {
          "width": 800,
          "height": 600,
          "size_bytes": 123456,
          "format": "jpeg",
          "priority": 0.8
        }
      }
    ],
    "pagination": {
      "next_cursor": "next-page-token",
      "has_more": true
    }
  },
  "duration": 1.5
}
```

## Rate Limiting

- Default: 60 requests per minute
- Burst: 10 requests
- Headers:
  - `X-RateLimit-Limit`
  - `X-RateLimit-Remaining`
  - `X-RateLimit-Reset`
  - `Retry-After` (when limit exceeded)

## Error Codes

| Code | Description                             |
| ---- | --------------------------------------- |
| 400  | Bad Request - Invalid input             |
| 401  | Unauthorized - Invalid API key          |
| 429  | Too Many Requests - Rate limit exceeded |
| 500  | Internal Server Error                   |
| 503  | Service Unavailable - Try again later   |

## Request Validation

1. URL:

   - Must be a valid HTTP(S) URL
   - Maximum length: 2048 characters
   - Must be publicly accessible

2. Media:
   - `limit`: 1-50 (default: 10)
   - `cursor`: Base64 encoded string

## Response Headers

- `X-Request-ID`: Unique request identifier
- `X-Version`: API version
- `X-Response-Time`: Processing time in ms
- `Cache-Control`: Caching directives

## Caching

- Profile data: 24 hours TTL
- Media data: 7 days TTL
- Cache-Control headers respected
- Conditional requests supported (If-None-Match)

## Best Practices

1. Error Handling:

   - Always check `success` field
   - Handle rate limits gracefully
   - Implement exponential backoff

2. Performance:

   - Use pagination for media requests
   - Cache responses when possible
   - Monitor response times

3. Resource Usage:
   - Track token usage
   - Monitor costs
   - Set up alerts

## Examples

### cURL

```bash
# Extract profile
curl -X POST https://api.example.com/v1/profile \
  -H "Content-Type: application/json" \
  -d '{"url": "https://example.com"}'

# Extract media
curl -X POST https://api.example.com/v1/media \
  -H "Content-Type: application/json" \
  -d '{"url": "https://example.com", "limit": 10}'
```

### Python

```python
import requests

# Extract profile
response = requests.post(
    "https://api.example.com/v1/profile",
    json={"url": "https://example.com"}
)
profile = response.json()

# Extract media
response = requests.post(
    "https://api.example.com/v1/media",
    json={
        "url": "https://example.com",
        "limit": 10
    }
)
media = response.json()
```

## Versioning

- Current version: v1
- Version in URL path
- Breaking changes in new versions
- Deprecation notices via headers

## Support

- GitHub Issues for bugs
- Email support for API keys
- Status page for outages
