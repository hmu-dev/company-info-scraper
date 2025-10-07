#!/bin/bash
echo "🧪 Testing Multiple URLs..."
echo "================================"

urls=(
  "github.com/about"
  "stripe.com/about"
  "ambiancesf.com/pages/about"
)

for url in "${urls[@]}"; do
  echo ""
  echo "Testing: $url"
  response=$(curl -m 25 -s "http://localhost:3001/scrape/text?url=$url&max_sections=3&max_key_values=3")
  if echo "$response" | python3 -c "import sys, json; data=json.load(sys.stdin); print(f\"✅ Status {data['statusCode']} | {len(data['scrapingData']['sections'])} sections | {len(data['scrapingData']['key_values'])} key-values | {len(data['scrapingData']['media']['images'])} images\")" 2>/dev/null; then
    :
  else
    echo "❌ Failed or error"
  fi
done

echo ""
echo "================================"
echo "✅ Testing Complete!"
