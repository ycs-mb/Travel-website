# API Key Guide

## What API Key Are We Talking About?

There are **TWO different API keys** in this project - don't confuse them!

### 1. 🔐 **Your REST API Key** (For FastAPI Server)
- **What**: A secret key YOU create to protect YOUR FastAPI server
- **Purpose**: Authenticate clients connecting to your photo analysis API
- **Where**: Used in HTTP requests to your server
- **Who creates it**: You generate it (instructions below)

### 2. 🔑 **Google Cloud Credentials** (For Vertex AI)
- **What**: Google Cloud authentication for Vertex AI API
- **Purpose**: Allow your agents to call Gemini Vision API
- **Where**: Used by the agents internally
- **Who creates it**: Google Cloud Platform

**Important**: These are completely separate!

---

## 1. Your REST API Key (FastAPI Server)

### What Is It?

When you run the FastAPI server, it's **your own API server**. The API key is a password that clients must provide to use your server.

Think of it like this:
- Your FastAPI server = Your web service
- API key = Password to use your service
- You decide the password

### How to Generate It

#### Option A: Automatic (Recommended)

The setup script generates a random API key automatically:

```bash
./scripts/setup_api.sh
```

This creates a `.env` file with a random API key:
```bash
# .env
API_KEY=your-secret-api-key-a1b2c3d4e5f6...
```

#### Option B: Manual Generation

**Method 1: Using OpenSSL (Recommended)**
```bash
# Generate a secure random key
openssl rand -hex 32
# Output: f3e8d9c2a1b4567890abcdef12345678...

# Save to .env file
echo "API_KEY=$(openssl rand -hex 32)" > .env
```

**Method 2: Using Python**
```python
import secrets

# Generate a secure random key
api_key = secrets.token_urlsafe(32)
print(f"API_KEY={api_key}")
```

**Method 3: Manual String (Less Secure)**
```bash
# Create your own (use something long and random)
echo "API_KEY=my-super-secret-key-12345-dont-share-this" > .env
```

### Where to Configure It

#### 1. Server Side (Your FastAPI Server)

**File**: `.env`
```bash
API_KEY=your-generated-api-key-here
```

The FastAPI server reads this on startup.

#### 2. Client Side (Applications Using Your API)

Clients must include the key in HTTP headers:

**Python:**
```python
import requests

headers = {"X-API-Key": "your-generated-api-key-here"}

response = requests.post(
    "http://localhost:8000/api/v1/analyze/image",
    headers=headers,
    files={"file": open("photo.jpg", "rb")}
)
```

**cURL:**
```bash
curl -X POST "http://localhost:8000/api/v1/analyze/image" \
  -H "X-API-Key: your-generated-api-key-here" \
  -F "file=@photo.jpg"
```

**JavaScript:**
```javascript
const response = await fetch('http://localhost:8000/api/v1/analyze/image', {
  method: 'POST',
  headers: {
    'X-API-Key': 'your-generated-api-key-here'
  },
  body: formData
});
```

### How It Works

```mermaid
┌─────────────┐                 ┌──────────────────┐
│   Client    │                 │  FastAPI Server  │
│             │                 │                  │
│  API Key:   │─── Request ────>│  1. Check if     │
│  abc123...  │   (with key)    │     X-API-Key    │
│             │                 │     matches      │
│             │                 │     .env file    │
│             │<── Response ────│  2. Allow or     │
│             │   (if valid)    │     reject       │
└─────────────┘                 └──────────────────┘
```

### Security Best Practices

✅ **DO:**
- Use a long, random key (32+ characters)
- Keep it in `.env` file (never commit to git)
- Use different keys for dev/staging/production
- Rotate keys periodically
- Use HTTPS in production

❌ **DON'T:**
- Use simple passwords like "password123"
- Commit `.env` to version control
- Share your API key publicly
- Use the same key everywhere

### Example: Complete Setup

**Step 1: Generate key**
```bash
cd /Users/ycs/photo-app/Travel-website

# Generate and save
echo "API_KEY=$(openssl rand -hex 32)" > .env

# Verify
cat .env
# Output: API_KEY=f3e8d9c2a1b4567890...
```

**Step 2: Start server**
```bash
./start_api.sh
# Server loads API_KEY from .env automatically
```

**Step 3: Use in client**
```python
import os
from dotenv import load_dotenv
import requests

# Load API key from .env
load_dotenv()
API_KEY = os.getenv("API_KEY")

# Make authenticated request
response = requests.post(
    "http://localhost:8000/api/v1/analyze/image",
    headers={"X-API-Key": API_KEY},
    files={"file": open("photo.jpg", "rb")}
)
```

---

## 2. Google Cloud Credentials (Vertex AI)

### What Is It?

This is **Google's authentication** to allow your code to call Vertex AI (Gemini) APIs.

### Two Authentication Methods

#### Method A: Application Default Credentials (Recommended)

**Easiest for development:**
```bash
# Login once
gcloud auth application-default login

# Follow browser prompts to authenticate
# Credentials saved automatically
```

**Pros:**
- ✅ Simple setup
- ✅ No files to manage
- ✅ Works locally and in Google Cloud

**Where it's stored:**
- Mac/Linux: `~/.config/gcloud/application_default_credentials.json`
- Windows: `%APPDATA%\gcloud\application_default_credentials.json`

#### Method B: Service Account Key (Production)

**For production/automation:**

**Step 1: Create Service Account**
```bash
# Create service account
gcloud iam service-accounts create photo-analysis \
    --display-name="Photo Analysis Service"

# Grant Vertex AI permissions
gcloud projects add-iam-policy-binding YOUR-PROJECT-ID \
    --member="serviceAccount:photo-analysis@YOUR-PROJECT-ID.iam.gserviceaccount.com" \
    --role="roles/aiplatform.user"
```

**Step 2: Create & Download Key**

Via Console:
1. Go to https://console.cloud.google.com/iam-admin/serviceaccounts
2. Select your service account
3. Click "Keys" tab
4. "Add Key" → "Create new key" → JSON
5. Download `key.json`

Via CLI:
```bash
gcloud iam service-accounts keys create key.json \
    --iam-account=photo-analysis@YOUR-PROJECT-ID.iam.gserviceaccount.com
```

**Step 3: Set Environment Variable**
```bash
export GOOGLE_APPLICATION_CREDENTIALS="/path/to/key.json"

# Make permanent (add to ~/.bashrc or ~/.zshrc)
echo 'export GOOGLE_APPLICATION_CREDENTIALS="/path/to/key.json"' >> ~/.zshrc
```

### How Agents Use It

The agents automatically use Google credentials:

```python
# In agents/aesthetic_assessment.py (already done)
from google import genai

# Client automatically finds credentials
self.client = genai.Client(
    vertexai=True,
    project=self.api_config.get('project'),  # From config.yaml
    location=self.api_config.get('location')
)

# Credentials discovery order:
# 1. GOOGLE_APPLICATION_CREDENTIALS environment variable
# 2. Application Default Credentials (~/.config/gcloud/...)
# 3. Compute Engine/Cloud Run metadata server
```

### Verify Google Credentials

```bash
# Check if authenticated
gcloud auth application-default print-access-token

# Should print a long token like:
# ya29.a0AfH6SMB...

# Check current project
gcloud config get-value project

# List available projects
gcloud projects list
```

### Update config.yaml

Make sure your GCP project ID matches:

```yaml
# config.yaml
api:
  google:
    project: "your-actual-gcp-project-id"  # ← Must match GCP project
    location: "us-central1"
```

Find your project ID:
```bash
gcloud config get-value project
# Or visit: https://console.cloud.google.com/
```

---

## Complete Setup Example

### Scenario: Setting Up Everything Fresh

```bash
# Navigate to project
cd /Users/ycs/photo-app/Travel-website

# 1. Generate YOUR API key for FastAPI
echo "API_KEY=$(openssl rand -hex 32)" > .env

# 2. Authenticate with Google Cloud
gcloud auth application-default login

# 3. Get your GCP project ID
PROJECT_ID=$(gcloud config get-value project)
echo "Your project ID: $PROJECT_ID"

# 4. Update config.yaml (manually edit the file)
# Set: api.google.project = "$PROJECT_ID"

# 5. Run setup
./scripts/setup_api.sh

# 6. Start server
./start_api.sh

# 7. Test (in another terminal)
python tests/test_api.py
```

---

## Environment Variables Summary

### Required for FastAPI Server

```bash
# .env file
API_KEY=your-generated-random-key-here  # YOU create this
API_HOST=0.0.0.0                        # Optional (default: 0.0.0.0)
API_PORT=8000                           # Optional (default: 8000)
```

### Required for Vertex AI (Google Cloud)

**Option 1: Use gcloud CLI**
```bash
gcloud auth application-default login
# No environment variable needed
```

**Option 2: Use service account key**
```bash
export GOOGLE_APPLICATION_CREDENTIALS="/path/to/key.json"
```

### Complete .env Example

```bash
# Your FastAPI server authentication
API_KEY=f3e8d9c2a1b4567890abcdef1234567890abcdef1234567890abcdef12345678

# Optional server settings
API_HOST=0.0.0.0
API_PORT=8000

# Optional: Google Cloud (if not using gcloud auth)
# GOOGLE_APPLICATION_CREDENTIALS=/path/to/service-account-key.json

# Optional: Logging
LOG_LEVEL=INFO
```

---

## Testing Authentication

### Test Your REST API Key

```bash
# 1. Start server
./start_api.sh

# 2. Test WITHOUT key (should fail with 401)
curl http://localhost:8000/api/v1/analyze/image

# Output: {"detail":"Invalid API key"}

# 3. Test WITH key (should work)
curl -H "X-API-Key: YOUR-KEY-FROM-ENV" \
     http://localhost:8000/health

# Output: {"status":"healthy",...}
```

### Test Google Cloud Credentials

```bash
# Run a simple test
python -c "
from google import genai

client = genai.Client(
    vertexai=True,
    project='YOUR-PROJECT-ID',
    location='us-central1'
)
print('✅ Google Cloud authentication successful!')
"
```

---

## Troubleshooting

### "Invalid API key" Error

**Problem**: Client gets 401 Unauthorized

**Solution**:
```bash
# 1. Check .env file exists
cat .env

# 2. Verify API key in request matches .env
echo $API_KEY  # Should match .env

# 3. Restart server after changing .env
./start_api.sh
```

### "Vertex AI client not initialized"

**Problem**: Agents can't connect to Google Cloud

**Solution**:
```bash
# 1. Authenticate
gcloud auth application-default login

# 2. Verify project
gcloud config get-value project

# 3. Update config.yaml with correct project ID

# 4. Test credentials
gcloud auth application-default print-access-token
```

### "Permission denied" for Vertex AI

**Problem**: Service account lacks permissions

**Solution**:
```bash
# Grant Vertex AI permissions
gcloud projects add-iam-policy-binding YOUR-PROJECT-ID \
    --member="serviceAccount:YOUR-SA@YOUR-PROJECT.iam.gserviceaccount.com" \
    --role="roles/aiplatform.user"
```

---

## Production Recommendations

### REST API Key Management

**Development:**
```bash
# .env.development
API_KEY=dev-key-12345
```

**Production:**
```bash
# Use environment variables (not .env file)
export API_KEY=$(openssl rand -hex 32)

# Or use secrets manager
export API_KEY=$(aws secretsmanager get-secret-value --secret-id api-key --query SecretString --output text)
```

### Google Cloud Authentication

**Development:**
```bash
gcloud auth application-default login
```

**Production (Docker/K8s):**
```dockerfile
# Use service account key
ENV GOOGLE_APPLICATION_CREDENTIALS=/app/key.json
COPY key.json /app/key.json
```

**Production (Cloud Run/GKE):**
```bash
# Use workload identity (no keys needed)
gcloud run deploy photo-analysis \
    --service-account=photo-analysis@PROJECT.iam.gserviceaccount.com
```

---

## Quick Reference

| Authentication | Purpose | How to Get |
|----------------|---------|------------|
| **REST API Key** | Protect YOUR FastAPI server | `openssl rand -hex 32` |
| **Google Cloud** | Call Vertex AI APIs | `gcloud auth application-default login` |
| **Service Account** | Production Google Cloud | GCP Console → IAM → Service Accounts |

**Remember**:
- ✅ REST API key = YOU create (protects your server)
- ✅ Google credentials = Google provides (access Vertex AI)
