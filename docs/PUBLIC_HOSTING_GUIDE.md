# 🌐 Host AI Web Scraper from Your Computer

## 🚀 Quick Start (Recommended)

### Option 1: Run the Script
```bash
./start_public_server.sh
```

This will:
- Start Streamlit on your computer
- Create a public URL via serveo.net
- Give you a URL to share with coworkers

---

## 🔧 Manual Setup Options

### Option 1: serveo.net (No Signup Required)

**Terminal 1:**
```bash
cd /Users/allanjohnson/Documents/Code/awesome-llm-apps/starter_ai_agents/web_scrapping_ai_agent
source venv/bin/activate
streamlit run ai_scrapper.py --server.port 8501 --server.address 0.0.0.0
```

**Terminal 2:**
```bash
ssh -R 80:localhost:8501 serveo.net
```

**Result:** You'll get a URL like `https://abc123.serveo.net`

---

### Option 2: ngrok (With Free Account)

1. **Sign up:** https://ngrok.com/signup
2. **Get authtoken:** https://dashboard.ngrok.com/get-started/your-authtoken
3. **Setup:**
```bash
ngrok config add-authtoken YOUR_AUTHTOKEN
ngrok http 8501
```

**Result:** You'll get a URL like `https://abc123.ngrok.app`

---

### Option 3: localtunnel (NPM)

```bash
npm install -g localtunnel
lt --port 8501 --subdomain myai-scraper
```

**Result:** `https://myai-scraper.loca.lt`

---

### Option 4: Your Local Network

If coworkers are on the same network:

1. **Find your IP:**
```bash
ifconfig | grep "inet " | grep -v 127.0.0.1
```

2. **Start Streamlit:**
```bash
streamlit run ai_scrapper.py --server.port 8501 --server.address 0.0.0.0
```

3. **Share:** `http://YOUR_IP:8501`

---

## 🛡️ Security Considerations

### For Public Tunnels:
- ⚠️ Anyone with the URL can access your app
- 🔄 URLs may change when you restart
- 💻 Your computer needs to stay on
- 🌐 Works from anywhere in the world

### For Local Network:
- ✅ Only people on your network can access
- 🏢 Perfect for office environments
- 🔒 More secure than public tunnels

---

## 📱 What Your Coworkers Will See

When they visit the public URL, they'll see:
- 🕵️‍♂️ **AI Web Scraper** interface
- 📝 **Input fields** for URL and OpenAI API key
- 🎬 **Media extraction** options
- 📊 **Real-time results** with images and structured data

---

## 🚨 Troubleshooting

### App Won't Start:
```bash
# Check if port is busy
lsof -i :8501

# Kill existing processes
pkill -f streamlit
```

### Tunnel Won't Connect:
```bash
# Test local app first
curl http://localhost:8501/_stcore/health

# Restart tunnel
pkill -f serveo
ssh -R 80:localhost:8501 serveo.net
```

### Coworkers Can't Access:
- ✅ Check if your computer is awake
- ✅ Verify the public URL is correct
- ✅ Test the URL yourself first
- ✅ Check your firewall settings

---

## 💡 Pro Tips

1. **Keep Terminal Open:** Don't close the terminal running the tunnel
2. **Test First:** Always test the public URL yourself before sharing
3. **Monitor Usage:** Watch the terminal for access logs
4. **Backup Plan:** Have multiple tunnel options ready
5. **API Keys:** Coworkers need their own OpenAI API keys

---

## 📞 Quick Commands Reference

### Start Everything:
```bash
./start_public_server.sh
```

### Stop Everything:
```bash
pkill -f streamlit
pkill -f serveo
```

### Check Status:
```bash
ps aux | grep -E "(streamlit|serveo)"
curl http://localhost:8501/_stcore/health
```

---

## 🔗 Alternative Services

If serveo.net doesn't work:
- **ngrok.com** (requires free signup)
- **localtunnel** (requires Node.js)
- **bore.pub** (simple tunneling)
- **zrok.io** (modern alternative)

---

## 📧 Share with Coworkers

Send them:
1. **The public URL** (e.g., https://abc123.serveo.net)
2. **Instructions**: "Enter your OpenAI API key and any company URL"
3. **Timeline**: "Available now - keep checking if it goes down"

**Example message:**
```
🚀 AI Web Scraper is ready for testing!

URL: https://abc123.serveo.net

How to use:
1. Enter your OpenAI API key
2. Paste any company website URL  
3. Click "Scrape" and watch the magic!

The app extracts company info and downloads logos/images automatically.
Let me know what you think!
```

