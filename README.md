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

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure API key**
   - Create `.streamlit/secrets.toml` file:
   ```toml
   [secrets]
   OPENAI_API_KEY = "your-openai-api-key-here"
   ```

### Running the Application

#### Option 1: Streamlit UI
```bash
streamlit run ai_scrapper.py
```
Access at: `http://localhost:8501`

#### Option 2: FastAPI
```bash
uvicorn api:app --reload
```
- API: `http://localhost:8000`
- Docs: `http://localhost:8000/docs`

#### Option 3: Public Access
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
├── ai_scrapper.py              # Main Streamlit application
├── api.py                      # FastAPI backend
├── requirements.txt            # Python dependencies
├── .streamlit/
│   ├── config.toml            # Streamlit configuration
│   └── secrets.toml           # API key storage
├── .gitignore                 # Git ignore rules
├── start_public_server.sh     # Public hosting script
├── test_api_simple.py         # API testing script
├── README.md                  # This file
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