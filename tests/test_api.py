#!/usr/bin/env python3
"""
Test script for the AI Web Scraper API
"""
import base64
import json
import os

import requests

# API Configuration
API_BASE_URL = "http://localhost:8000"
OPENAI_API_KEY = "your-openai-api-key-here"  # Replace with your actual API key


def test_api():
    """Test the scraping API with a sample URL"""

    # Test data
    test_url = "https://flightclothingboutique.com/pages/about-us"

    payload = {
        "url": test_url,
        # "openai_api_key": OPENAI_API_KEY,  # Optional - using default key
        "model": "gpt-3.5-turbo",
    }

    print(f"🔍 Testing API with URL: {test_url}")
    print("⏳ Sending request to API...")

    try:
        # Make API request
        response = requests.post(f"{API_BASE_URL}/scrape", json=payload, timeout=120)

        if response.status_code == 200:
            result = response.json()

            print("✅ Success! API Response:")
            print(f"📄 Content extracted from: {result['url_scraped']}")
            print(f"🎬 Media items found: {len(result['media'])}")

            # Pretty print the content
            print("\n📝 Extracted Content:")
            print(json.dumps(result["content"], indent=2))

            # Show media information
            print(f"\n🖼️ Media Files ({len(result['media'])} found):")
            for i, media in enumerate(result["media"], 1):
                print(f"{i}. {media['type'].upper()}: {media['context']}")
                print(f"   URL: {media['url']}")
                print(f"   Filename: {media['filename']}")
                print(f"   Base64 size: {len(media['base64_data'])} characters")

                # Optionally save media files
                if media["base64_data"]:
                    save_media_file(media, i)
                print()

        else:
            print(f"❌ API Error: {response.status_code}")
            print(response.text)

    except requests.exceptions.Timeout:
        print(
            "⏰ Request timed out. The scraping process might take longer for complex sites."
        )
    except requests.exceptions.RequestException as e:
        print(f"🔥 Request failed: {e}")
    except Exception as e:
        print(f"💥 Unexpected error: {e}")


def save_media_file(media_item, index):
    """Save a media file from base64 data"""
    try:
        # Create media directory if it doesn't exist
        os.makedirs("api_media_output", exist_ok=True)

        # Decode base64 data
        media_data = base64.b64decode(media_item["base64_data"])

        # Save file
        file_path = f"api_media_output/{index}_{media_item['filename']}"
        with open(file_path, "wb") as f:
            f.write(media_data)

        print(f"💾 Saved: {file_path}")

    except Exception as e:
        print(f"⚠️ Failed to save media file: {e}")


def test_health():
    """Test the health endpoint"""
    try:
        response = requests.get(f"{API_BASE_URL}/health")
        if response.status_code == 200:
            print("✅ API Health Check Passed")
            print(json.dumps(response.json(), indent=2))
        else:
            print(f"❌ Health check failed: {response.status_code}")
    except Exception as e:
        print(f"💥 Health check error: {e}")


if __name__ == "__main__":
    print("🚀 AI Web Scraper API Test")
    print("=" * 50)

    # Check if API key is set
    if OPENAI_API_KEY == "your-openai-api-key-here":
        print("⚠️ Please set your OpenAI API key in the OPENAI_API_KEY variable")
        print("You can also set it as an environment variable:")
        print("export OPENAI_API_KEY='your-key-here'")

        # Try to get from environment
        env_key = os.getenv("OPENAI_API_KEY")
        if env_key:
            OPENAI_API_KEY = env_key
            print("✅ Found API key in environment variable")
        else:
            print("❌ No API key found. Exiting...")
            exit(1)

    # Test health first
    print("\n1. Testing API Health...")
    test_health()

    # Test scraping
    print("\n2. Testing Web Scraping...")
    test_api()

    print("\n✨ Test completed!")
