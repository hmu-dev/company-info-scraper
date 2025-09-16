#!/usr/bin/env python3
"""
Simple test script for the AI Web Scraper API
"""
import requests
import json

# API endpoint
API_URL = "http://localhost:8000"

def test_api():
    """Test the API with a sample company URL"""
    
    # Test data - you can change this URL to any company website
    test_data = {
        "url": "https://www.example.com",  # Change this to test different companies
        "model": "gpt-3.5-turbo"
        # Note: No need to provide openai_api_key as it's hardcoded in the API
    }
    
    print("🚀 Testing AI Web Scraper API")
    print("=" * 50)
    print(f"📍 API URL: {API_URL}")
    print(f"🌐 Target URL: {test_data['url']}")
    print(f"🤖 Model: {test_data['model']}")
    print("\n⏳ Sending request...")
    
    try:
        # Send POST request to /scrape endpoint
        response = requests.post(
            f"{API_URL}/scrape",
            json=test_data,
            timeout=120  # 2 minute timeout for scraping
        )
        
        print(f"📊 Status Code: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            
            print("✅ Success!")
            print(f"🔗 URL Scraped: {result.get('url_scraped', 'N/A')}")
            print(f"📝 Content Length: {len(result.get('content', ''))}")
            print(f"🖼️  Media Items Found: {len(result.get('media', []))}")
            
            # Show first 500 characters of content
            content = result.get('content', '')
            if content:
                print("\n📄 Content Preview:")
                print("-" * 30)
                print(content[:500] + "..." if len(content) > 500 else content)
            
            # Show media info
            media = result.get('media', [])
            if media:
                print(f"\n🖼️  Media Files ({len(media)} found):")
                print("-" * 30)
                for i, item in enumerate(media[:3]):  # Show first 3 media items
                    print(f"{i+1}. Type: {item.get('type', 'unknown')}")
                    print(f"   URL: {item.get('url', 'N/A')}")
                    print(f"   Size: {len(item.get('data', ''))} bytes (base64)")
                    print()
                
                if len(media) > 3:
                    print(f"   ... and {len(media) - 3} more media files")
            
        else:
            print(f"❌ Error: {response.status_code}")
            try:
                error_data = response.json()
                print(f"Error details: {json.dumps(error_data, indent=2)}")
            except:
                print(f"Error response: {response.text}")
    
    except requests.exceptions.Timeout:
        print("⏰ Request timed out (this can happen with large websites)")
    except requests.exceptions.ConnectionError:
        print("🔌 Connection error - make sure the API server is running")
    except Exception as e:
        print(f"❌ Unexpected error: {str(e)}")

def test_health():
    """Test the health endpoint"""
    print("\n🏥 Testing Health Endpoint")
    print("-" * 30)
    try:
        response = requests.get(f"{API_URL}/")
        if response.status_code == 200:
            print("✅ API is healthy!")
            print(f"Response: {response.json()}")
        else:
            print(f"❌ Health check failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Health check error: {str(e)}")

if __name__ == "__main__":
    # Test health first
    test_health()
    
    # Then test scraping
    test_api()
    
    print("\n" + "=" * 50)
    print("💡 To test with a different URL, edit the 'url' in test_data above")
    print("💡 The API uses the hardcoded company profile prompt automatically")
    print("💡 No need to provide an OpenAI API key - it's already configured")
