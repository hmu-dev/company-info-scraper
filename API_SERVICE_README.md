# 🚀 AI Web Scraper API Service

A production-ready FastAPI service with hybrid intelligence for extracting company information and media from websites.

## 🎯 **Hybrid API Service**

This service provides a smart, hybrid approach combining speed and intelligence. Perfect for:

- **Production deployments**
- **High-volume applications**
- **Cost-sensitive projects**
- **Real-time processing**
- **Serverless functions**

## 📦 **Core Dependencies**

The API service includes essential dependencies for hybrid processing:

```bash
# Core API framework
fastapi>=0.104.0
uvicorn[standard]>=0.24.0
python-multipart>=0.0.6

# Web scraping and processing
requests>=2.31.0
beautifulsoup4>=4.12.0

# AWS integration
boto3>=1.34.0
mangum>=0.17.0

# Data validation
pydantic>=2.4.0
```

## 🚀 **Quick Start**

### 1. **Live API (Recommended)**

The API is already deployed and ready to use:

- **Base URL**: `https://cjp6f8947h.execute-api.us-east-1.amazonaws.com/`
- **Interactive Docs**: `https://cjp6f8947h.execute-api.us-east-1.amazonaws.com/docs`
- **Health Check**: `https://cjp6f8947h.execute-api.us-east-1.amazonaws.com/health`

### 2. **Local Development**

```bash
# Install dependencies
pip install -r requirements-api.txt

# Run with SAM (recommended)
cd about-us-scraper-service
sam build --use-container
sam local start-api

# Or run directly
cd about-us-scraper-service/api
python main_hybrid.py
```

### 3. **Test the API**

```bash
# Health check
curl "https://cjp6f8947h.execute-api.us-east-1.amazonaws.com/health"

# Intelligent scraping
curl "https://cjp6f8947h.execute-api.us-east-1.amazonaws.com/scrape/intelligent?url=github.com"
```

## 📡 **API Endpoints**

### **🧠 Intelligent Scraping** (Recommended)

```bash
GET /scrape/intelligent?url=github.com&include_media=true
```

**Features:**
- Auto-discovers About Us pages
- Extracts company info and media assets
- Uses AI enhancement when needed
- Confidence scoring

### **⚡ Fast Scraping** (Speed Optimized)

```bash
GET /scrape/fast?url=example.com&include_media=true
```

**Features:**
- Pure programmatic extraction
- Fastest response times (0.2-0.3s)
- No AI costs
- Good for high-volume requests

### **🔄 Legacy Endpoints**

```bash
# Basic scraping
GET /scrape?url=company.com

# About page scraping
GET /scrape/about?url=company.com/about
```

## 🔧 **Configuration**

### **Environment Variables**

| Variable         | Description                      | Default   |
| ---------------- | -------------------------------- | --------- |
| `AWS_REGION`     | AWS region for deployment        | `us-east-1` |
| `ENVIRONMENT`    | Deployment environment           | `dev`     |
| `RATE_LIMIT_RPM` | Requests per minute limit        | `60`      |

### **API Request Format**

```bash
# Intelligent scraping
GET /scrape/intelligent?url=github.com&include_media=true&max_about_pages=3

# Fast scraping  
GET /scrape/fast?url=example.com&include_media=true
```

## 🏗️ **Production Deployment**

### **AWS Lambda (Current)**

The service is deployed on AWS Lambda using SAM:

- **Live URL**: https://cjp6f8947h.execute-api.us-east-1.amazonaws.com/
- **Region**: us-east-1
- **Auto-deployment**: GitHub Actions CI/CD pipeline

### **Manual Deployment**

```bash
cd about-us-scraper-service
sam build --use-container
sam deploy --guided
```

### **Local Development**

```bash
cd about-us-scraper-service
sam local start-api
```

## 📊 **Performance Characteristics**

### **Intelligent Endpoint** (`/scrape/intelligent`)
- **Typical Response**: 1-3 seconds
- **Fast Path**: 0.2-0.5 seconds (when AI not needed)
- **Smart Path**: 2-5 seconds (when AI enhancement used)
- **Memory Usage**: ~100-200MB

### **Fast Endpoint** (`/scrape/fast`)
- **Response Time**: 0.2-0.3 seconds typically
- **Memory Usage**: ~50-100MB
- **No AI costs**: Pure programmatic processing
- **High throughput**: Can handle high request volumes

## 🔒 **Security Features**

- **Environment-based API keys** (no hardcoded secrets)
- **Input validation** with Pydantic models
- **Rate limiting** middleware (configurable)
- **CORS support** for web applications
- **Request/response logging** for monitoring

## 📈 **Monitoring & Observability**

- **Health check endpoint** (`/health`)
- **Structured logging** with request IDs
- **Performance metrics** (response times, success rates)
- **Error tracking** with detailed error messages

## 🧪 **Testing**

```bash
# Test the live API
curl "https://cjp6f8947h.execute-api.us-east-1.amazonaws.com/health"

# Test intelligent scraping
curl "https://cjp6f8947h.execute-api.us-east-1.amazonaws.com/scrape/intelligent?url=github.com"

# Test fast scraping
curl "https://cjp6f8947h.execute-api.us-east-1.amazonaws.com/scrape/fast?url=example.com"

# Local testing
cd about-us-scraper-service
sam local invoke ScraperFunction -e events/test_event.json
```

## 🚫 **What's Not Included**

This API service intentionally excludes:

- ❌ **Interactive UI** (API-only service)
- ❌ **Complex AI dependencies** (uses hybrid approach)
- ❌ **Advanced video processing** (basic media extraction only)
- ❌ **Development tools** (pytest, black, etc.)

## 🔄 **Migration from Legacy Service**

If you're currently using the legacy endpoints:

1. **Update endpoints**: Use `/scrape/intelligent` instead of `/scrape`
2. **Add parameters**: Include `include_media=true` for media extraction
3. **Handle responses**: New response format includes confidence scoring
4. **Deploy**: Use the current AWS Lambda deployment

## 📚 **Documentation**

- **Interactive API Docs**: [https://cjp6f8947h.execute-api.us-east-1.amazonaws.com/docs](https://cjp6f8947h.execute-api.us-east-1.amazonaws.com/docs)
- **Main Project README**: See `README.md` for complete feature overview
- **Deployment Guide**: See `docs/DEPLOYMENT_GUIDE.md`

---

**Perfect for production deployments, high-volume applications, and cost-sensitive projects!** 🚀
