# 🌐 AI Web Scraper Deployment Guide

## Quick Public Access with ngrok (5 minutes)

### Step 1: Start the Streamlit App

```bash
cd /Users/allanjohnson/Documents/Code/awesome-llm-apps/starter_ai_agents/web_scrapping_ai_agent
source venv/bin/activate
streamlit run ai_scrapper.py --server.port 8501
```

### Step 2: Open a New Terminal and Start ngrok

```bash
ngrok http 8501
```

### Step 3: Get Your Public URL

After running ngrok, you'll see output like:

```
Web Interface                 http://127.0.0.1:4040
Forwarding                    https://abcd-1234.ngrok.app -> http://localhost:8501
```

**Share this URL:** `https://abcd-1234.ngrok.app` - Anyone can access your app!

---

## 🚀 Production Deployment Options

### Option 1: Streamlit Community Cloud (Free & Easy)

**Benefits:**

- Free hosting
- Automatic deployments from GitHub
- Built-in HTTPS
- No server management

**Steps:**

1. **Push to GitHub:**

```bash
git init
git add .
git commit -m "AI Web Scraper App"
git remote add origin https://github.com/yourusername/ai-web-scraper.git
git push -u origin main
```

2. **Deploy:**

- Visit [share.streamlit.io](https://share.streamlit.io)
- Connect GitHub
- Select repository and `ai_scrapper.py`
- Deploy!

**Result:** `https://yourapp.streamlit.app`

---

### Option 2: Railway (Easy with Custom Domain)

**Benefits:**

- Free tier available
- Custom domains
- Environment variables
- Automatic deployments

**Steps:**

1. **Create `railway.toml`:**

```toml
[build]
builder = "nixpacks"

[deploy]
startCommand = "streamlit run ai_scrapper.py --server.port $PORT --server.address 0.0.0.0"
```

2. **Deploy:**

```bash
npm install -g @railway/cli
railway login
railway init
railway up
```

---

### Option 3: Heroku

**Create these files:**

**`Procfile`:**

```
web: streamlit run ai_scrapper.py --server.port $PORT --server.address 0.0.0.0 --server.enableCORS false --server.enableXsrfProtection false
```

**`setup.sh`:**

```bash
mkdir -p ~/.streamlit/
echo "\
[server]\n\
headless = true\n\
port = $PORT\n\
enableCORS = false\n\
\n\
" > ~/.streamlit/config.toml
```

**Deploy:**

```bash
heroku create your-app-name
git push heroku main
```

---

### Option 4: DigitalOcean App Platform

**`app.yaml`:**

```yaml
name: ai-web-scraper
services:
  - name: web
    source_dir: /
    github:
      repo: yourusername/ai-web-scraper
      branch: main
    run_command: streamlit run ai_scrapper.py --server.port $PORT --server.address 0.0.0.0
    environment_slug: python
    instance_count: 1
    instance_size_slug: basic-xxs
    http_port: 8080
```

---

## 🔧 Configuration for Public Access

### Update Streamlit for Public Access

Create `.streamlit/config.toml`:

```toml
[server]
headless = true
port = 8501
enableCORS = false
enableXsrfProtection = false

[browser]
gatherUsageStats = false
```

### Environment Variables

For production, set:

```bash
export STREAMLIT_SERVER_HEADLESS=true
export STREAMLIT_SERVER_ENABLE_CORS=false
export STREAMLIT_BROWSER_GATHER_USAGE_STATS=false
```

---

## 🛡️ Security Considerations

### For ngrok (temporary testing):

- ✅ Quick and easy
- ⚠️ Tunnel URLs change on restart
- ⚠️ Anyone with URL can access

### For production:

- 🔐 Use HTTPS (most platforms provide this)
- 🛡️ Consider adding authentication
- 📊 Monitor usage and costs
- 🔒 Set up environment variables for API keys

---

## 📱 Testing Your Deployment

### Health Check Endpoints

Visit these URLs to test:

- `/` - Main app
- `/_stcore/health` - Streamlit health check

### Test with Different Devices

- Desktop browsers
- Mobile browsers
- Different networks

---

## 🚨 Quick Start (Right Now!)

**Option A: ngrok (Immediate Access)**

```bash
# Terminal 1
streamlit run ai_scrapper.py

# Terminal 2
ngrok http 8501
```

**Option B: Streamlit Cloud (Permanent)**

1. Push code to GitHub
2. Go to share.streamlit.io
3. Deploy in 2 clicks

---

## 💡 Pro Tips

1. **For Testing:** Use ngrok for quick sharing with specific people
2. **For Demo:** Use Streamlit Cloud for permanent demo URLs
3. **For Production:** Use Railway/Heroku with custom domain
4. **API Version:** Deploy the FastAPI version (`api.py`) for integration

## 🔗 Links

- [Streamlit Cloud](https://share.streamlit.io)
- [Railway](https://railway.app)
- [Heroku](https://heroku.com)
- [DigitalOcean](https://digitalocean.com)
- [ngrok](https://ngrok.com)

