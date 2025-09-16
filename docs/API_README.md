# 🚀 AI Web Scraper API

A FastAPI-based service that extracts company information and media content from websites using AI.

## Features

- 🧭 **Smart Navigation**: Automatically finds About/Company pages
- 🤖 **AI-Powered Extraction**: Uses OpenAI to extract structured company profiles
- 🎬 **Media Processing**: Downloads and base64-encodes images and videos
- 📊 **Structured Output**: Returns organized JSON with text content and media
- 🛡️ **Error Handling**: Robust error handling with fallback strategies

## Quick Start

### 1. Start the API Server

```bash
# Activate virtual environment
source venv/bin/activate

# Start the API server
python api.py
```

The API will be available at `http://localhost:8000`

### 2. API Documentation

Visit `http://localhost:8000/docs` for interactive API documentation (Swagger UI)

### 3. Basic Usage

**POST /scrape**

```bash
curl -X POST "http://localhost:8000/scrape" \
     -H "Content-Type: application/json" \
     -d '{
       "url": "https://flightclothingboutique.com",
       "openai_api_key": "your-openai-api-key",
       "model": "gpt-3.5-turbo"
     }'
```

## Request Format

```json
{
  "url": "https://example.com",
  "openai_api_key": "your-openai-api-key",
  "model": "gpt-3.5-turbo"
}
```

## Response Format

```json
{
  "success": true,
  "url_scraped": "https://example.com/about-us",
  "content": {
    "About Us (including locations)": {
      "overview": "Company description...",
      "locations": ["City, State"]
    },
    "Our Culture": {
      "core_values": "...",
      "working_environment": "..."
    },
    "Our Team": {
      "key_individuals": ["Name 1", "Name 2"]
    },
    "Noteworthy & Differentiated": {
      "unique_selling_propositions": "..."
    }
  },
  "media": [
    {
      "url": "https://example.com/logo.png",
      "type": "image",
      "context": "Company logo",
      "base64_data": "iVBORw0KGgoAAAANSUhEUgAA...",
      "filename": "logo.png"
    }
  ],
  "error": null
}
```

## Python Client Example

```python
import requests
import base64

# API request
response = requests.post("http://localhost:8000/scrape", json={
    "url": "https://example.com",
    "openai_api_key": "your-api-key",
    "model": "gpt-3.5-turbo"
})

result = response.json()

if result["success"]:
    # Access extracted content
    content = result["content"]
    print(f"Company info: {content}")

    # Save media files
    for media in result["media"]:
        if media["base64_data"]:
            # Decode and save
            media_data = base64.b64decode(media["base64_data"])
            with open(media["filename"], "wb") as f:
                f.write(media_data)
            print(f"Saved: {media['filename']}")
```

## Testing

Run the test script:

```bash
# Set your OpenAI API key
export OPENAI_API_KEY="your-openai-api-key"

# Run the test
python test_api.py
```

## API Endpoints

### GET /

Health check endpoint

### GET /health

Detailed health check with API information

### POST /scrape

Main scraping endpoint

**Parameters:**

- `url`: Website URL to scrape
- `openai_api_key`: Your OpenAI API key
- `model`: OpenAI model to use (default: "gpt-3.5-turbo")

## How It Works

1. **URL Analysis**: Takes any company URL as input
2. **Smart Navigation**: Automatically finds the best About/Company page
3. **AI Extraction**: Uses OpenAI to extract structured company information
4. **Media Discovery**: Finds images and videos from both AI results and HTML parsing
5. **Media Processing**: Downloads media and converts to base64 for easy transport
6. **Structured Response**: Returns everything in a clean JSON format

## Error Handling

The API includes comprehensive error handling:

- Network connectivity issues
- Invalid URLs
- AI processing errors
- Media download failures
- Authentication problems

Even if some components fail, the API will attempt to return partial results.

## Performance Notes

- Typical response time: 10-30 seconds
- Depends on website complexity and media size
- Includes timeout protection
- Optimized for company profile extraction

## Security

- API keys are not logged or stored
- Media content is processed in memory
- No persistent storage of scraped data
- Rate limiting recommended for production use

