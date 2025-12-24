# Docker & Cloud Deployment Guide

This guide covers deploying the Travel Photo Analysis API and MCP Server using Docker.

---

## Quick Start (Docker Desktop)

```bash
# Build and start all services
docker compose up --build

# API available at http://localhost:8000
# Swagger docs at http://localhost:8000/docs
```

---

## Prerequisites

1. **Docker Desktop** installed and running
2. **Google Cloud credentials** (`keys.json`) in project root
3. **config.yaml** configured with your GCP project ID

---

## Services

### API Server (FastAPI)

| Property | Value |
|----------|-------|
| Port | 8000 |
| Endpoint | `/api/v1/analyze/image` |
| Health | `/health` |

**Build & Run standalone:**
```bash
docker build -t photo-api -f docker/api.Dockerfile .
docker run -p 8000:8000 \
  -v $(pwd)/keys.json:/app/secrets/keys.json:ro \
  -v $(pwd)/config.yaml:/app/config.yaml:ro \
  -e GOOGLE_APPLICATION_CREDENTIALS=/app/secrets/keys.json \
  -e API_KEY=your-api-key \
  photo-api
```

### MCP Server

The MCP server uses **stdio** for communication (not HTTP).

**Build:**
```bash
docker build -t photo-mcp -f docker/mcp.Dockerfile .
```

**Run interactively:**
```bash
docker run -i \
  -v $(pwd)/keys.json:/app/secrets/keys.json:ro \
  -v $(pwd)/config.yaml:/app/config.yaml:ro \
  -e GOOGLE_APPLICATION_CREDENTIALS=/app/secrets/keys.json \
  photo-mcp
```

**Claude Desktop Config:**
```json
{
  "mcpServers": {
    "photo-analysis": {
      "command": "docker",
      "args": [
        "run", "-i",
        "-v", "/path/to/keys.json:/app/secrets/keys.json:ro",
        "-v", "/path/to/config.yaml:/app/config.yaml:ro",
        "-e", "GOOGLE_APPLICATION_CREDENTIALS=/app/secrets/keys.json",
        "photo-mcp"
      ]
    }
  }
}
```

---

## GCP Cloud Run Deployment

### 1. Setup

```bash
# Authenticate
gcloud auth login
gcloud config set project YOUR_PROJECT_ID

# Enable APIs
gcloud services enable run.googleapis.com
gcloud services enable artifactregistry.googleapis.com
gcloud services enable secretmanager.googleapis.com
```

### 2. Create Secret for credentials

```bash
gcloud secrets create photo-api-keys --data-file=keys.json
```

### 3. Build & Push to Artifact Registry

```bash
# Create repository (once)
gcloud artifacts repositories create photo-api \
  --repository-format=docker \
  --location=us-central1

# Configure Docker auth
gcloud auth configure-docker us-central1-docker.pkg.dev

# Build and push
docker build -t us-central1-docker.pkg.dev/YOUR_PROJECT/photo-api/api:latest \
  -f docker/api.Dockerfile .

docker push us-central1-docker.pkg.dev/YOUR_PROJECT/photo-api/api:latest
```

### 4. Deploy to Cloud Run

```bash
gcloud run deploy photo-api \
  --image us-central1-docker.pkg.dev/YOUR_PROJECT/photo-api/api:latest \
  --region us-central1 \
  --platform managed \
  --allow-unauthenticated \
  --memory 2Gi \
  --cpu 2 \
  --timeout 300 \
  --set-secrets="/app/secrets/keys.json=photo-api-keys:latest" \
  --set-env-vars="GOOGLE_APPLICATION_CREDENTIALS=/app/secrets/keys.json,API_KEY=your-production-key"
```

### 5. Test Deployment

```bash
# Get service URL
gcloud run services describe photo-api --region us-central1 --format="value(status.url)"

# Test health endpoint
curl https://YOUR-SERVICE-URL/health
```

---

## Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `GOOGLE_APPLICATION_CREDENTIALS` | Path to GCP service account JSON | Yes |
| `API_KEY` | API authentication key | Yes |
| `PYTHONPATH` | Python module path (set to /app) | Auto |

---

## Volumes

| Mount Point | Purpose |
|-------------|---------|
| `/app/secrets/keys.json` | GCP credentials |
| `/app/config.yaml` | Application config |
| `/app/output` | Analysis results |
| `/app/cache` | Geocoding/embedding cache |

---

## Troubleshooting

**Build fails with memory issues:**
```bash
docker build --memory=4g -t photo-api -f docker/api.Dockerfile .
```

**Container exits immediately:**
```bash
docker logs photo-api
```

**Permission denied on mounted files:**
```bash
chmod 644 keys.json config.yaml
```
