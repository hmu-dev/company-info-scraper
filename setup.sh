#!/bin/bash

echo "🚀 AI Web Scraper Setup"
echo "======================="

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source venv/bin/activate

# Install dependencies
echo "📚 Installing dependencies..."
pip install -r requirements.txt

# Check if secrets.toml exists
if [ ! -f ".streamlit/secrets.toml" ]; then
    echo "⚠️  API key not configured!"
    echo "Please create .streamlit/secrets.toml with your OpenAI API key:"
    echo ""
    echo "[secrets]"
    echo "OPENAI_API_KEY = \"your-api-key-here\""
    echo ""
else
    echo "✅ API key configuration found"
fi

# Test imports
echo "🧪 Testing dependencies..."
python -c "import streamlit, scrapegraphai, fastapi; print('✅ All dependencies working')" || {
    echo "❌ Dependency test failed"
    exit 1
}

echo ""
echo "🎉 Setup Complete!"
echo "=================="
echo "📱 To run Streamlit UI: streamlit run ai_scrapper.py"
echo "🚀 To run FastAPI: uvicorn api:app --reload"
echo "🌐 To run publicly: ./scripts/start_public_server.sh"
echo "🧪 To test API: python tests/test_api_simple.py"
echo ""
echo "📖 See README.md for full documentation"

