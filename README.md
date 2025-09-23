# 🕵️‍♂️ AI Web Scraper

A powerful AI-driven web scraping tool that extracts comprehensive company profiles including text content and media files. Built with Streamlit for the UI and FastAPI for programmatic access.

## ✨ Features

- **🤖 AI-Powered Content Extraction**: Uses OpenAI's GPT models to intelligently extract company information
- **📱 Beautiful Streamlit UI**: Interactive web interface for easy scraping
- **🚀 FastAPI Backend**: RESTful API for programmatic access
- **🖼️ Media Extraction**: Downloads and processes images and videos
- **🔍 Smart Navigation**: Automatically finds relevant "About Us" pages
- **📊 Structured Output**: Organized company profiles in four sections:
  - About Us (including locations)
  - Our Culture
  - Our Team
  - Noteworthy & Differentiated
- **🔐 Secure Configuration**: API keys managed through Streamlit secrets
- **🌐 Public Hosting**: Easy deployment with multiple hosting options

## 🔬 How It Works

The AI Web Scraper uses a sophisticated multi-stage approach to extract comprehensive company information from websites:

### 🎯 **Stage 1: Smart Page Discovery**

The service intelligently navigates websites to find the most relevant "About Us" content:

1. **URL Analysis**: Examines the provided URL to determine if it already contains about content
2. **Navigation Scanning**: Searches through website navigation menus for about-related links
3. **Common Path Detection**: Checks standard about page paths like `/about`, `/about-us`, `/company`, `/our-story`
4. **Content Validation**: Verifies pages contain relevant keywords like "about us", "our team", "founded", etc.

**Example Navigation Logic:**

```python
# Searches for links containing about keywords
about_keywords = ['about', 'about-us', 'company', 'our-story', 'our-team']
# Checks common paths like /about, /about-us, /company
# Validates content relevance before proceeding
```

### 🧠 **Stage 2: AI-Powered Content Extraction**

Once the optimal page is found, the service uses OpenAI's GPT models to intelligently extract structured information:

1. **Content Analysis**: The AI analyzes the entire page content, understanding context and relationships
2. **Structured Extraction**: Uses a specialized prompt to extract information into four key categories:

   - **About Us**: Company overview, mission, locations, founding story
   - **Our Culture**: Values, working environment, company philosophy
   - **Our Team**: Key individuals, leadership, team structure
   - **Noteworthy & Differentiated**: Unique selling points, awards, special features

3. **Context Understanding**: The AI can distinguish between:
   - Main company information vs. product details
   - Current information vs. historical content
   - Primary content vs. navigation/footer text

**AI Prompt Strategy:**

```python
# The AI is instructed to:
# - Extract ONLY relevant company information
# - Organize content into the four sections
# - Use "Not available" for missing sections
# - Focus on company identity and culture
# - Ignore product catalogs and sales content
```

### 🖼️ **Stage 3: Intelligent Media Discovery**

The service employs a dual approach to find relevant media assets:

#### **A. HTML-Based Media Extraction**

```python
# Searches for images with relevant context
img_tags = soup.find_all('img')
for img in img_tags:
    alt_text = img.get('alt', '').lower()
    src = img.get('src', '').lower()

    # Prioritizes company/branding images
    if any(keyword in alt_text for keyword in
           ['logo', 'brand', 'company', 'team', 'about']):
        # High priority: Company branding
    elif not any(ui_element in src for ui_element in
                 ['icon', 'button', 'arrow', 'cart']):
        # Medium priority: Content images
```

#### **B. AI-Enhanced Media Discovery**

The AI analyzes the extracted content to identify mentioned media:

- Logos and branding materials
- Team photos and founder images
- Office and workplace images
- Product and service visuals

#### **C. Smart Media Prioritization**

Each discovered media item receives a priority score:

```python
# Priority scoring system
if 'logo' in context or 'brand' in context:
    priority = 100  # Highest priority
elif 'team' in context or 'founder' in context:
    priority = 80   # High priority
elif 'office' in context or 'location' in context:
    priority = 60   # Medium priority
else:
    priority = 10   # Default priority
```

### 🔍 **Stage 4: Content Filtering & Quality Control**

The service applies intelligent filtering to ensure high-quality results:

1. **Relevance Filtering**: Removes navigation elements, ads, and unrelated content
2. **Duplicate Detection**: Identifies and removes duplicate media items
3. **Size Optimization**: Only processes media files under 5MB for base64 encoding
4. **Format Validation**: Ensures media files are in supported formats
5. **Context Preservation**: Maintains the relationship between text and media

### 📊 **Stage 5: Structured Output Generation**

Finally, the service organizes all extracted information into a clean, structured format:

```json
{
  "profile": {
    "about_us": "Company overview with locations...",
    "our_culture": "Values and working environment...",
    "our_team": "Key individuals and leadership...",
    "noteworthy_and_differentiated": "Unique selling points..."
  },
  "media": [
    {
      "url": "https://company.com/logo.png",
      "type": "image",
      "context": "Company logo",
      "priority": 100,
      "metadata": {
        "width": 200,
        "height": 200,
        "size_bytes": 15420
      }
    }
  ]
}
```

### 🎯 **Key Intelligence Features**

- **Context Awareness**: Understands the difference between company information and product details
- **Location Extraction**: Automatically identifies and extracts company locations from text
- **Media Relevance**: Prioritizes logos, team photos, and company branding over generic images
- **Error Recovery**: Falls back to alternative pages if the primary about page fails
- **Content Validation**: Ensures extracted information is actually about the company, not products or services

This multi-stage approach ensures that the AI Web Scraper delivers comprehensive, accurate, and well-organized company profiles suitable for recruiting platforms, market research, and business intelligence applications.

## 🚀 Quick Start

### Prerequisites

- Python 3.8+
- OpenAI API key

### Installation

1. **Clone or download this project**

   ```bash
   cd ai-web-scraper
   ```

2. **Set up virtual environment**

   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Choose your installation type**

   **Option A: Full Service (UI + API)**

   ```bash
   pip install -r requirements.txt
   ```

   **Option B: API Only (Lightweight)**

   ```bash
   pip install -r requirements-api.txt
   ```

4. **Configure API key**

   **For Streamlit UI:**

   - Create `.streamlit/secrets.toml` file:

   ```toml
   [secrets]
   OPENAI_API_KEY = "your-openai-api-key-here"
   ```

   **For API Only:**

   ```bash
   export OPENAI_API_KEY="your-openai-api-key-here"
   ```

### Running the Application

#### Option 1: Streamlit UI (Full Service)

```bash
streamlit run ai_scrapper.py
```

Access at: `http://localhost:8501`

#### Option 2: FastAPI Only (Lightweight)

```bash
# Quick start
./start_api.sh

# Or manually
uvicorn api:app --reload --host 0.0.0.0 --port 8000
```

- API: `http://localhost:8000`
- Docs: `http://localhost:8000/docs`
- Health: `http://localhost:8000/health`

#### Option 3: Docker (API Only)

```bash
# Build and run
docker build -f Dockerfile.api -t ai-scraper-api .
docker run -p 8000:8000 -e OPENAI_API_KEY="your-key" ai-scraper-api

# Or use docker-compose
docker-compose -f docker-compose.api.yml up
```

#### Option 4: Public Access (Full Service)

```bash
./start_public_server.sh
```

Creates a public URL for remote access.

## 📖 Usage

### Streamlit UI

1. Open the web interface
2. Enter a company website URL
3. The default company profile prompt is pre-loaded
4. Click "Start Scraping" to extract information
5. View extracted content and downloaded media

### API Usage

```python
import requests

response = requests.post("http://localhost:8000/scrape", json={
    "url": "https://example-company.com",
    "model": "gpt-3.5-turbo"
})

result = response.json()
print(f"Content: {result['content']}")
print(f"Media files: {len(result['media'])}")
```

## 📁 Project Structure

```
ai-web-scraper/
├── ai_scrapper.py              # Main Streamlit application (UI)
├── api.py                      # FastAPI backend (API service)
├── requirements.txt            # Full dependencies (UI + API)
├── requirements-api.txt        # API-only dependencies (lightweight)
├── start_api.sh               # API service startup script
├── Dockerfile.api             # Docker image for API service
├── docker-compose.api.yml     # Docker Compose for API service
├── .streamlit/
│   ├── config.toml            # Streamlit configuration
│   └── secrets.toml           # API key storage
├── .gitignore                 # Git ignore rules
├── start_public_server.sh     # Public hosting script
├── test_api_simple.py         # API testing script
├── README.md                  # This file
├── API_SERVICE_README.md      # API-only service documentation
├── API_README.md              # API documentation
├── DEPLOYMENT_GUIDE.md        # Deployment instructions
└── PUBLIC_HOSTING_GUIDE.md    # Public hosting options
```

## 🔧 Configuration

### Default Company Profile Prompt

The application comes with a comprehensive pre-configured prompt that extracts:

- Company overview and locations
- Culture and values
- Team information
- Unique differentiators
- Relevant branding media

### API Key Management

- **Streamlit**: Uses `st.secrets` for secure key storage
- **FastAPI**: Hardcoded default key with optional override
- **Environment**: Can also use environment variables

## 🌐 Deployment Options

1. **Streamlit Community Cloud**: Free cloud hosting
2. **Local Public Access**: Using serveo.net or ngrok
3. **Docker**: Containerized deployment
4. **Cloud Platforms**: AWS, GCP, Azure

See `DEPLOYMENT_GUIDE.md` for detailed instructions.

## 🧪 Testing

### Test the API

```bash
python test_api_simple.py
```

### Test with curl

```bash
curl -X POST http://localhost:8000/scrape \
  -H "Content-Type: application/json" \
  -d '{"url": "https://openai.com"}'
```

## 📚 Documentation

- **API Documentation**: `API_README.md`
- **Deployment Guide**: `DEPLOYMENT_GUIDE.md`
- **Public Hosting**: `PUBLIC_HOSTING_GUIDE.md`
- **Interactive API Docs**: `http://localhost:8000/docs` (when API is running)

## 🤝 Contributing

This project was developed through collaborative AI-assisted programming. The codebase includes:

- Robust error handling
- Media extraction and processing
- Smart website navigation
- Comprehensive documentation

## 📄 License

This project is open source and available under standard open source licensing.

## 🆘 Support

For issues or questions:

1. Check the documentation files
2. Review the test scripts for usage examples
3. Examine the API documentation at `/docs`

---

**Built with ❤️ using AI-assisted development**
