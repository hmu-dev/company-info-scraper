#!/bin/bash

# AI Web Scraper - Public Server Startup Script
echo "🚀 Starting AI Web Scraper for Public Access"
echo "=============================================="

# Kill any existing processes
echo "🧹 Cleaning up existing processes..."
pkill -f streamlit 2>/dev/null
pkill -f serveo 2>/dev/null
sleep 2

# Start Streamlit
echo "📱 Starting Streamlit app..."
cd "$(dirname "$0")"
source venv/bin/activate
streamlit run ai_scrapper.py --server.port 8501 --server.address 0.0.0.0 --server.headless true &
STREAMLIT_PID=$!

# Wait for Streamlit to start
echo "⏳ Waiting for Streamlit to start..."
sleep 5

# Test if Streamlit is running
if curl -s http://localhost:8501/_stcore/health > /dev/null; then
    echo "✅ Streamlit is running on http://localhost:8501"
else
    echo "❌ Streamlit failed to start"
    exit 1
fi

# Start serveo.net tunnel
echo "🌐 Creating public tunnel with serveo.net..."
ssh -o StrictHostKeyChecking=no -R 80:localhost:8501 serveo.net &
SERVEO_PID=$!

echo ""
echo "🎉 Setup Complete!"
echo "=================="
echo "📱 Local URL: http://localhost:8501"
echo "🌍 Public URL: Check the serveo.net output above for your public URL"
echo ""
echo "📝 To stop the servers:"
echo "   kill $STREAMLIT_PID $SERVEO_PID"
echo ""
echo "🔗 Share the public URL with your coworkers!"
echo "⚠️  Keep this terminal open to maintain the connection"

# Wait for user to stop
wait

