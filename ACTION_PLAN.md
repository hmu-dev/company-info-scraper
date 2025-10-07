# 🎯 Action Plan - API Integration & Authentication

## Current Status

### ✅ Completed

- API v4.0 created and deployed
- Local SAM API running on `http://localhost:3001`
- Beautiful test UI created and running
- Schema matches remote team requirements (partially)

### 🔄 In Progress

1. Test HireMe API reference at https://hiremeup.teamjft.com/api/docs
2. Implement authentication
3. Match exact schema
4. Fix Montage URL scraping error
5. Recover Streamlit UI from git history

---

## 📋 Tasks Breakdown

### Task 1: Understand HireMe API Schema

**Reference**: https://hiremeup.teamjft.com/api/docs#/Profile/ProfileController_scrapeUrl

**Steps**:

1. ✅ Navigate to API docs
2. 🔄 Test `/auth/login` endpoint to get JWT token
3. 🔄 Use JWT to authorize in Swagger UI
4. 🔄 Test `/profile/scrape-url` endpoint
5. 🔄 Document exact request/response schema
6. 🔄 Compare with our current API v4.0 schema

**Expected Auth Flow**:

```bash
# 1. Login to get JWT
POST https://hiremeup.teamjft.com/api/auth/login
Body: {
  "email": "...",
  "password": "..."
}
Response: {
  "access_token": "eyJhbGc..."
}

# 2. Use JWT in subsequent requests
GET https://hiremeup.teamjft.com/api/profile/scrape-url
Headers: {
  "Authorization": "Bearer eyJhbGc..."
}
```

---

### Task 2: Implement Authentication in Our API

**Requirements**:

- JWT-based authentication
- Bearer token in Authorization header
- Secure token generation and validation
- User/API key management

**Implementation Plan**:

1. **Install Dependencies**:

```bash
pip install python-jose[cryptography] passlib[bcrypt] python-multipart
```

2. **Create Auth Module** (`api/auth/`):

   - `jwt.py` - JWT token generation/validation
   - `models.py` - User and token models
   - `routes.py` - Login/register endpoints
   - `dependencies.py` - FastAPI dependencies for protected routes

3. **Add Auth Middleware**:

   - Token validation
   - User context injection
   - Rate limiting per user/token

4. **Update Main API**:
   - Add auth routes
   - Protect scraping endpoints with JWT
   - Add API key support as alternative

**Example Code Structure**:

```python
# api/auth/jwt.py
from jose import JWTError, jwt
from datetime import datetime, timedelta

SECRET_KEY = "your-secret-key"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def verify_token(token: str):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        return None
```

```python
# api/auth/dependencies.py
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

security = HTTPBearer()

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    token = credentials.credentials
    payload = verify_token(token)
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return payload
```

```python
# Updated main_v4.py
from api.auth.dependencies import get_current_user

@app.post("/auth/login")
async def login(email: str, password: str):
    # Validate user credentials
    # Generate JWT token
    access_token = create_access_token(data={"sub": email})
    return {"access_token": access_token, "token_type": "bearer"}

@app.get("/scrape/text", dependencies=[Depends(get_current_user)])
async def scrape_text_v4(...):
    # Now protected with JWT
    ...
```

---

### Task 3: Fix Montage URL Scraping Error

**Issue**: API error when scraping `https://www.montageinternational.com/careers/`

**Investigation Steps**:

1. Test the URL locally with curl
2. Check if it's a timeout issue
3. Check if the site blocks scrapers
4. Add proper error handling and logging

**Debug Commands**:

```bash
# Test with curl
curl -I "https://www.montageinternational.com/careers/"

# Test with our API
curl "http://localhost:3001/scrape/text?url=https://www.montageinternational.com/careers/"

# Check logs
# Look at SAM local output for errors
```

**Potential Fixes**:

- Add User-Agent header
- Add timeout handling
- Add retry logic
- Add better error messages

---

### Task 4: Recover Streamlit UI from Git History

**Goal**: Find and restore the Streamlit UI that was removed

**Steps**:

```bash
# 1. Find commits that deleted streamlit files
git log --all --full-history -- "*streamlit*"
git log --all --full-history -- "*.streamlit*"
git log --all --full-history --diff-filter=D -- "*.py" | grep -i streamlit

# 2. Search for streamlit in commit history
git log --all --grep="streamlit" -i

# 3. Find when streamlit was removed
git log --all --oneline | grep -i "remove\|delete\|clean" | head -20

# 4. Once found, checkout the file
git show <commit-hash>:path/to/streamlit_app.py > streamlit_app.py

# 5. Or restore from specific commit
git checkout <commit-hash> -- path/to/streamlit_files
```

**Alternative**: If Streamlit was never committed, create new UI based on current test-ui.html but with Streamlit

---

### Task 5: Schema Alignment

**Current Our Schema** (v4.0):

```json
{
  "statusCode": 200,
  "message": "URL scraping completed successfully",
  "scrapingData": {
    "page_title": "...",
    "url": "...",
    "language": "...",
    "summary": "...",
    "sections": [...],
    "key_values": [...],
    "media": {...},
    "notes": "..."
  }
}
```

**Need to verify HireMe API schema**:

- Request format
- Response format
- Required fields
- Optional fields
- Error handling

---

## 🚀 Immediate Next Steps

1. **Manual Testing** (Do Now):

   - Open https://hiremeup.teamjft.com/api/docs in browser
   - Find correct login credentials (might be test account)
   - Get JWT token
   - Test scrapeUrl endpoint
   - Document exact schema

2. **Fix Montage URL** (Quick Fix):

   - Add better error handling
   - Add timeout configuration
   - Test locally

3. **Implement Auth** (Priority):

   - Create auth module structure
   - Add JWT dependencies
   - Implement login endpoint
   - Protect scraping endpoints

4. **Find Streamlit** (Git Search):
   - Search git history
   - Restore or recreate UI

---

## 📝 Notes

- Local API is running and working for basic URLs
- Test UI is functional at http://localhost:8080/test-ui.html
- Need test credentials for HireMe API
- Schema appears similar but need to verify exact match

---

## 🔑 API Credentials Needed

For testing HireMe API, we need:

- Test email/username
- Test password
- Or API documentation with test credentials

**Where to find**:

- API documentation
- Team communication
- Environment variables
- README or docs folder

---

## ✅ Success Criteria

1. ✅ HireMe API tested and understood
2. ✅ Schema documented and matched
3. ✅ Auth implemented in our API
4. ✅ All URLs scraping successfully
5. ✅ Streamlit UI recovered or recreated
6. ✅ Full integration tested
