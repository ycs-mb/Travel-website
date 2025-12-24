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

## Services Overview

| Service | Port | Protocol | Purpose |
|---------|------|----------|---------|
| **photo-api** | 8000 | HTTP | FastAPI REST server |
| **photo-mcp** | stdio | MCP | Claude Desktop integration |

---

## Service Details

### API Server (FastAPI)

| Property | Value |
|----------|-------|
| Container Name | `photo-api` |
| Port | 8000 |
| Health Check | `/health` |
| API Docs | `/docs` (Swagger UI) |
| API Docs | `/redoc` (ReDoc) |

**Endpoints:**
- `POST /analyze` - Full 5-agent pipeline
- `POST /analyze/metadata` - Agent 1 only
- `POST /analyze/quality` - Agent 2 only
- `POST /analyze/aesthetic` - Agent 3 only
- `POST /analyze/filter` - Agent 4 only
- `POST /analyze/caption` - Agent 5 only
- `GET /health` - Health check
- `GET /docs` - Interactive API documentation

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

**Test the API:**
```bash
# Health check
curl http://localhost:8000/health

# Full analysis (requires API key)
curl -X POST http://localhost:8000/analyze \
  -H "X-API-Key: your-api-key" \
  -F "file=@/path/to/image.jpg"

# View interactive docs
open http://localhost:8000/docs
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

## Docker Compose Commands

### Starting Services

```bash
# Build and start all services
docker compose up --build

# Start in detached mode (background)
docker compose up -d

# Start only specific service
docker compose up api
docker compose up mcp

# Rebuild without cache
docker compose build --no-cache
docker compose up
```

### Stopping Services

```bash
# Stop all services (keeps containers)
docker compose stop

# Stop and remove containers
docker compose down

# Stop and remove containers + volumes
docker compose down -v

# Stop specific service
docker compose stop api
```

### Viewing Logs

```bash
# View all logs
docker compose logs

# Follow logs (real-time)
docker compose logs -f

# Logs for specific service
docker compose logs -f api
docker compose logs -f mcp

# Last 100 lines
docker compose logs --tail=100 api
```

### Service Status

```bash
# View running services
docker compose ps

# View detailed service info
docker compose ps api

# Check resource usage
docker stats
```

### Accessing Containers

```bash
# Execute command in running container
docker compose exec api /bin/bash

# Run one-off command
docker compose run --rm api python -c "print('Hello')"

# View environment variables
docker compose exec api env
```

---

## Monitoring & Health Checks

### Built-in Health Checks

The API container includes automatic health monitoring:

```yaml
healthcheck:
  test: [ "CMD", "curl", "-f", "http://localhost:8000/health" ]
  interval: 30s      # Check every 30 seconds
  timeout: 10s       # Fail if takes > 10s
  retries: 3         # Retry 3 times before marking unhealthy
  start_period: 10s  # Grace period on startup
```

### Check Health Status

```bash
# View health status
docker compose ps

# Expected output:
# NAME        STATUS                      PORTS
# photo-api   Up (healthy)               0.0.0.0:8000->8000/tcp

# View health check logs
docker inspect --format='{{json .State.Health}}' photo-api | jq
```

### Manual Health Check

```bash
# Check API is responding
curl http://localhost:8000/health

# Expected response:
# {"status":"healthy","timestamp":"2024-12-24T..."}

# Check from inside container
docker compose exec api curl http://localhost:8000/health
```

### Viewing Metrics

```bash
# Resource usage
docker stats photo-api

# Output:
# CONTAINER ID   NAME        CPU %   MEM USAGE / LIMIT   MEM %   NET I/O
# a1b2c3d4e5f6   photo-api   5.2%    1.2GiB / 2GiB       60%     1MB / 2MB

# Container inspect
docker compose exec api ps aux
```

---

## Production Best Practices

### 1. Use .env File for Secrets

Create `.env` file (don't commit!):
```bash
API_KEY=your-secret-production-key
GOOGLE_APPLICATION_CREDENTIALS=/app/secrets/keys.json
```

Reference in docker-compose.yml:
```yaml
services:
  api:
    env_file:
      - .env
```

### 2. Resource Limits

Add to docker-compose.yml:
```yaml
services:
  api:
    deploy:
      resources:
        limits:
          cpus: '2.0'
          memory: 4G
        reservations:
          cpus: '1.0'
          memory: 2G
```

### 3. Persistent Volumes

For production, use named volumes:
```yaml
services:
  api:
    volumes:
      - output_data:/app/output
      - cache_data:/app/cache

volumes:
  output_data:
  cache_data:
```

### 4. Log Management

Configure logging:
```yaml
services:
  api:
    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "3"
```

### 5. Restart Policy

Auto-restart on failure:
```yaml
services:
  api:
    restart: unless-stopped  # Already configured in docker-compose.yml
```

### 6. Security Hardening

```yaml
services:
  api:
    read_only: false  # Set to true if possible
    security_opt:
      - no-new-privileges:true
    cap_drop:
      - ALL
    cap_add:
      - NET_BIND_SERVICE
```

---

## Integration with Other Services

### Nginx Reverse Proxy

Create `nginx.conf`:
```nginx
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        # Increase timeout for image processing
        proxy_read_timeout 300s;
        proxy_connect_timeout 75s;
    }

    # Increase max upload size
    client_max_body_size 100M;
}
```

Add nginx to docker-compose.yml:
```yaml
services:
  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
    volumes:
      - ./nginx.conf:/etc/nginx/conf.d/default.conf:ro
    depends_on:
      - api
```

### Redis Cache (Optional)

Add Redis for caching:
```yaml
services:
  redis:
    image: redis:alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data

volumes:
  redis_data:
```

Update API to use Redis in `config.yaml`:
```yaml
cache:
  enabled: true
  backend: redis
  redis_url: redis://redis:6379/0
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
