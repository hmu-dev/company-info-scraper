# 🕵️‍♂️ AI Web Scraper

A powerful AI-driven web scraping tool that extracts comprehensive company profiles including text content and media files. Built with FastAPI for robust API access and AWS Lambda serverless deployment.

## ✨ Features

- **🧠 Hybrid Intelligence**: Combines fast programmatic extraction with smart AI enhancement
- **🚀 FastAPI Service**: High-performance API service with automatic documentation
- **⚡ Speed Optimized**: Fast endpoints (0.2-0.3s) for high-volume requests
- **🖼️ Media Extraction**: Downloads and processes images, videos, and documents
- **🔍 Smart Navigation**: Automatically finds relevant "About Us" pages
- **📊 Structured Output**: Organized company profiles with confidence scoring
- **🌐 AWS Deployed**: Live at https://cjp6f8947h.execute-api.us-east-1.amazonaws.com/
- **📚 Comprehensive Docs**: Interactive API documentation with examples

## 🔬 How It Works

The AI Web Scraper uses a **hybrid approach** that combines the speed of programmatic extraction with the intelligence of AI analysis:

### 🎯 **Hybrid Intelligence Strategy**

Our API offers multiple endpoints optimized for different use cases:

#### 🧠 **`/scrape/intelligent`** - **RECOMMENDED**
- ⚡ Starts with fast programmatic extraction
- 🧠 Falls back to AI when results are poor
- 🔍 Auto-discovers About Us pages
- 📸 Extracts all media assets
- 🎯 Perfect for comprehensive company analysis

#### ⚡ **`/scrape/fast`** - **SPEED FOCUSED**
- 🏃‍♂️ Pure programmatic approach (no AI)
- ⚡ Fastest response times (0.2-0.3s)
- 📊 Good for basic company info
- 💰 Most cost-effective

#### 🔄 **`/scrape` & `/scrape/about`** - **LEGACY**
- 📜 Simple programmatic extraction
- 🔗 Use for existing integrations

## 🚀 Quick Start

### 🌐 **Live API Usage**

**Base URL**: `https://cjp6f8947h.execute-api.us-east-1.amazonaws.com/`

**Interactive Documentation**: [https://cjp6f8947h.execute-api.us-east-1.amazonaws.com/docs](https://cjp6f8947h.execute-api.us-east-1.amazonaws.com/docs)

#### **Example API Calls:**

```bash
# Intelligent scraping (recommended)
curl "https://cjp6f8947h.execute-api.us-east-1.amazonaws.com/scrape/intelligent?url=github.com&include_media=true"

# Fast scraping (speed optimized)
curl "https://cjp6f8947h.execute-api.us-east-1.amazonaws.com/scrape/fast?url=example.com&include_media=true"

# Health check
curl "https://cjp6f8947h.execute-api.us-east-1.amazonaws.com/health"
```

#### **Python Example:**

```python
import requests

# Intelligent scraping with media
response = requests.get(
    "https://cjp6f8947h.execute-api.us-east-1.amazonaws.com/scrape/intelligent",
    params={
        "url": "github.com",
        "include_media": True,
        "max_about_pages": 3
    }
)

result = response.json()
print(f"Company: {result['title']}")
print(f"Media assets: {result['media_summary']['total_assets']}")
print(f"Processing time: {result['processing_time_seconds']}s")
```

## 🚀 Local Development

### Prerequisites

- Python 3.9+
- AWS CLI (for deployment)
- AWS SAM CLI (for local testing)

### Installation

1. **Clone the project**

   ```bash
   git clone https://github.com/hmu-dev/company-info-scraper.git
   cd company-info-scraper
   ```

2. **Set up virtual environment**

   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**

   ```bash
   pip install -r requirements-api.txt
   ```

4. **Local testing with SAM**

   ```bash
   cd about-us-scraper-service
   sam build --use-container
   sam local start-api
   ```

   Access at: `http://localhost:3000`

### Running the Application

#### Option 1: Local SAM Development

```bash
cd about-us-scraper-service
sam local start-api
```

- API: `http://localhost:3000`
- Docs: `http://localhost:3000/docs`
- Health: `http://localhost:3000/health`

#### Option 2: Direct FastAPI (Development)

```bash
cd about-us-scraper-service/api
python main_hybrid.py
```

- API: `http://localhost:8000`
- Docs: `http://localhost:8000/docs`

#### Option 3: Docker (API Only)

```bash
# Build and run
docker build -f Dockerfile.api -t ai-scraper-api .
docker run -p 8000:8000 ai-scraper-api
```

## 📖 Usage

### API Endpoints

#### 🧠 **Intelligent Scraping** (Recommended)

```bash
curl "https://cjp6f8947h.execute-api.us-east-1.amazonaws.com/scrape/intelligent?url=github.com&include_media=true"
```

**Features:**
- Auto-discovers About Us pages
- Extracts company info and media assets
- Uses AI enhancement when needed
- Confidence scoring

#### ⚡ **Fast Scraping** (Speed Optimized)

```bash
curl "https://cjp6f8947h.execute-api.us-east-1.amazonaws.com/scrape/fast?url=example.com&include_media=true"
```

**Features:**
- Pure programmatic extraction
- Fastest response times (0.2-0.3s)
- No AI costs
- Good for high-volume requests

#### 🔄 **Legacy Endpoints**

```bash
# Basic scraping
curl "https://cjp6f8947h.execute-api.us-east-1.amazonaws.com/scrape?url=company.com"

# About page scraping
curl "https://cjp6f8947h.execute-api.us-east-1.amazonaws.com/scrape/about?url=company.com/about"
```

### Python Usage

```python
import requests

# Intelligent scraping with media
response = requests.get(
    "https://cjp6f8947h.execute-api.us-east-1.amazonaws.com/scrape/intelligent",
    params={
        "url": "github.com",
        "include_media": True,
        "max_about_pages": 3
    }
)

result = response.json()
print(f"Company: {result['title']}")
print(f"Media assets: {result['media_summary']['total_assets']}")
print(f"Processing time: {result['processing_time_seconds']}s")
```

## 📁 Project Structure

```
ai-web-scraper/
├── about-us-scraper-service/   # Main AWS SAM service directory
│   ├── api/                   # FastAPI application code
│   │   ├── main_hybrid.py     # Hybrid API implementation
│   │   ├── lambda_handler_hybrid.py # AWS Lambda handler
│   │   ├── endpoints/         # API endpoints
│   │   ├── services/          # Business logic
│   │   ├── middleware/        # Request/response middleware
│   │   └── utils/             # Helper functions
│   ├── template-simple.yaml  # AWS SAM template
│   ├── samconfig.toml        # SAM configuration
│   ├── requirements.txt      # Lambda dependencies
│   └── docs/                 # Service documentation
├── .github/workflows/        # CI/CD pipelines
│   ├── ci.yml               # Continuous integration
│   └── deploy.yml           # AWS deployment
├── docs/                    # Project documentation
│   ├── DEPLOYMENT_GUIDE.md  # AWS deployment guide
│   ├── API_README.md        # API documentation
│   └── PUBLIC_HOSTING_GUIDE.md # Hosting options
├── tests/                   # Testing scripts
├── requirements-api.txt     # API dependencies
├── README.md               # This file
└── .gitignore             # Git ignore rules
```

## 🌐 Deployment

### AWS Lambda (Production)

The API is deployed on AWS Lambda using SAM (Serverless Application Model):

- **Live URL**: https://cjp6f8947h.execute-api.us-east-1.amazonaws.com/
- **Region**: us-east-1
- **Auto-deployment**: GitHub Actions CI/CD pipeline
- **Monitoring**: CloudWatch dashboards and alerts

### Local Development

```bash
cd about-us-scraper-service
sam build --use-container
sam local start-api
```

### Manual Deployment

```bash
cd about-us-scraper-service
sam build --use-container
sam deploy --guided
```

## 🧪 Testing

### Test the Live API

```bash
# Health check
curl "https://cjp6f8947h.execute-api.us-east-1.amazonaws.com/health"

# Intelligent scraping
curl "https://cjp6f8947h.execute-api.us-east-1.amazonaws.com/scrape/intelligent?url=github.com"

# Fast scraping
curl "https://cjp6f8947h.execute-api.us-east-1.amazonaws.com/scrape/fast?url=example.com"
```

### Local Testing

```bash
cd about-us-scraper-service
sam local invoke ScraperFunction -e events/test_event.json
```

## 📚 Documentation

- **Interactive API Docs**: [https://cjp6f8947h.execute-api.us-east-1.amazonaws.com/docs](https://cjp6f8947h.execute-api.us-east-1.amazonaws.com/docs)
- **Deployment Guide**: `docs/DEPLOYMENT_GUIDE.md`
- **API Documentation**: `docs/API_README.md`
- **Development Guide**: `about-us-scraper-service/docs/DEVELOPMENT.md`

## 🤝 Contributing

This project was developed through collaborative AI-assisted programming. The codebase includes:

- Hybrid intelligence approach (programmatic + AI)
- Robust error handling and fallback mechanisms
- Comprehensive media extraction and processing
- Smart website navigation and About page discovery
- AWS serverless deployment with monitoring

## 📄 License

This project is open source and available under standard open source licensing.

## 🆘 Support

For issues or questions:

1. Check the [live API documentation](https://cjp6f8947h.execute-api.us-east-1.amazonaws.com/docs)
2. Review the test scripts for usage examples
3. Examine the project documentation files

---

**Built with ❤️ using AI-assisted development**
