# 🧪 AI Web Scraper - Testing Guide

## 🚀 Services Running

### ✅ Local API (SAM Local)

- **URL**: `http://localhost:3001`
- **Status**: Running in background
- **Version**: API v4.0 (Remote Team Compatible)

### ✅ Testing UI

- **File**: `test-ui.html`
- **Status**: Opened in browser
- **Features**: Beautiful web interface for testing both local and deployed APIs

### ✅ Deployed API (AWS)

- **URL**: `https://45tieavbu6.execute-api.us-east-1.amazonaws.com`
- **Stack**: `ai-web-scraper-v4`
- **Status**: Deployed (routing issue being investigated)

---

## 📍 API v4.0 Endpoints

### Health Check

```bash
GET /health
```

**Example:**

```bash
curl http://localhost:3001/health
```

**Response:**

```json
{
  "status": "healthy",
  "version": "4.0.0",
  "approach": "remote_team_compatible"
}
```

---

### Text Scraping (v4.0 Schema)

```bash
GET /scrape/text?url={url}&max_sections={num}&max_key_values={num}&use_ai_enhancement={bool}
```

**Parameters:**

- `url` (required): Website URL to scrape (e.g., `ambiancesf.com/pages/about`)
- `max_sections` (optional): Maximum number of sections to return (1-10, default: 5)
- `max_key_values` (optional): Maximum number of key-value pairs (1-5, default: 3)
- `use_ai_enhancement` (optional): Use AI to improve content (true/false, default: false)

**Example:**

```bash
curl "http://localhost:3001/scrape/text?url=ambiancesf.com/pages/about&max_sections=2&max_key_values=2"
```

**Response Schema (Remote Team Compatible):**

```json
{
  "statusCode": 200,
  "message": "URL scraping completed successfully",
  "scrapingData": {
    "page_title": "About Ambiance San Francisco | Women's Boutique Locations – Ambiance SF",
    "url": "https://ambiancesf.com/pages/about",
    "language": "en",
    "summary": "Company description...",
    "sections": [
      {
        "name": "Location",
        "content_summary": "Summary of the section...",
        "raw_excerpt": "Raw text excerpt..."
      }
    ],
    "key_values": [
      {
        "key": "Founded",
        "value": "1996"
      },
      {
        "key": "Location",
        "value": "San Francisco"
      }
    ],
    "media": {
      "images": [
        "https://example.com/image1.jpg",
        "https://example.com/image2.jpg"
      ],
      "videos": ["https://example.com/video1.mp4"]
    },
    "notes": "Processed in 0.50 seconds"
  }
}
```

---

## 🧪 Testing with the UI

The testing UI (`test-ui.html`) is now open in your browser and provides:

### Features:

1. **API v4.0 Tab**:

   - Enter any URL to scrape
   - Quick example URLs (Ambiance SF, GitHub, Stripe, OpenAI)
   - Configure max sections and key-value pairs
   - Optional AI enhancement
   - Beautiful JSON response viewer
   - Copy to clipboard button

2. **Health Check Tab**:
   - Quick health status check
   - Works with both local and deployed APIs

### How to Use:

1. The UI is already open in your browser
2. Select "API v4.0" tab
3. Choose an example URL or enter your own
4. Click "🚀 Scrape with v4.0"
5. View the formatted JSON response

### Switch Between Local and Deployed:

- **Local API**: Use `http://localhost:3001` in the endpoint field
- **Deployed API**: Use `https://45tieavbu6.execute-api.us-east-1.amazonaws.com`

---

## 🧪 Testing with cURL

### Test Local API:

```bash
# Health check
curl http://localhost:3001/health | python3 -m json.tool

# Scrape Ambiance SF
curl "http://localhost:3001/scrape/text?url=ambiancesf.com/pages/about&max_sections=3&max_key_values=3" | python3 -m json.tool

# Scrape GitHub
curl "http://localhost:3001/scrape/text?url=github.com/about" | python3 -m json.tool

# With AI enhancement
curl "http://localhost:3001/scrape/text?url=stripe.com/about&use_ai_enhancement=true" | python3 -m json.tool
```

---

## 📊 Example Test URLs

### E-commerce:

- `ambiancesf.com/pages/about` - Boutique store
- `shopify.com/about` - E-commerce platform

### Tech Companies:

- `github.com/about` - Developer platform
- `stripe.com/about` - Payment processor
- `openai.com/about` - AI research company

### General:

- `example.com` - Simple test site
- `wikipedia.org` - Encyclopedia

---

## 🔍 What to Test

### ✅ Core Features:

1. **Health Check**: Verify API is running
2. **Basic Scraping**: Test with simple URLs
3. **Schema Compliance**: Verify response matches remote team schema
4. **Error Handling**: Test with invalid URLs
5. **Parameter Testing**: Try different max_sections and max_key_values
6. **AI Enhancement**: Test with and without AI

### ✅ Data Quality:

1. **Page Title**: Check if correctly extracted
2. **Summary**: Verify meaningful content summary
3. **Sections**: Check section extraction and naming
4. **Key-Values**: Verify extracted company information
5. **Media**: Check image and video URLs
6. **Language**: Verify language detection

### ✅ Performance:

1. **Response Time**: Should be < 5 seconds for text-only
2. **Processing Notes**: Check processing time in response
3. **Error Messages**: Should be clear and helpful

---

## 🐛 Troubleshooting

### Local API not responding:

```bash
# Check if SAM is running
ps aux | grep "sam local"

# Restart SAM local
pkill -f "sam local"
cd about-us-scraper-service
sam build --use-container --template-file template-v4.yaml
sam local start-api --template-file .aws-sam/build/template.yaml --port 3001
```

### UI not working:

```bash
# Reopen the UI
open test-ui.html
```

### Check logs:

- SAM Local logs appear in the terminal where you started `sam local start-api`
- Check for any error messages or stack traces

---

## 📝 Notes

- **Local API**: Uses containerized Lambda runtime for accurate testing
- **Schema**: Matches remote team requirements exactly
- **Media Extraction**: Basic programmatic extraction (no AI overhead for speed)
- **AI Enhancement**: Optional, adds LLM processing for better quality
- **Processing Time**: Typically 0.5-2 seconds for text extraction

---

## ✨ Quick Start

1. **Open UI**: Already open in your browser
2. **Test Health**: Click "Health Check" tab → "🔍 Check Health"
3. **Scrape URL**: Click "API v4.0" tab → Choose example → Click "🚀 Scrape"
4. **View Results**: JSON response appears below with copy button

**Everything is ready for testing!** 🎉
