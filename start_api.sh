#!/bin/bash

# AI Web Scraper API Service Startup Script
# This script starts only the API service without the Streamlit UI

set -e

echo "🚀 Starting AI Web Scraper API Service..."

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source venv/bin/activate

# Install API dependencies only
echo "📥 Installing API dependencies..."
pip install -r requirements-api.txt

# Check for OpenAI API key
if [ -z "$OPENAI_API_KEY" ]; then
    echo "⚠️  Warning: OPENAI_API_KEY environment variable not set"
    echo "   You can set it with: export OPENAI_API_KEY='your-key-here'"
    echo "   Or create a .env file with: OPENAI_API_KEY=your-key-here"
fi

# Set default values
export PORT=${PORT:-8000}
export HOST=${HOST:-0.0.0.0}

echo "🌐 Starting API server on http://$HOST:$PORT"
echo "📚 API Documentation: http://$HOST:$PORT/docs"
echo "❤️  Health Check: http://$HOST:$PORT/health"
echo ""
echo "Press Ctrl+C to stop the server"
echo ""

# Start the API server
uvicorn api:app --host $HOST --port $PORT --reload
