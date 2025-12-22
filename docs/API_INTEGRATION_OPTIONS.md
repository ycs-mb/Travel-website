# API Integration Options

This document outlines various ways to expose the travel photo analysis agents for use in external applications.

## Table of Contents

1. [REST API (FastAPI/Flask)](#1-rest-api-fastapিflask)
2. [MCP (Model Context Protocol) Server](#2-mcp-model-context-protocol-server)
3. [gRPC Service](#3-grpc-service)
4. [Serverless Functions (Cloud Functions/Lambda)](#4-serverless-functions)
5. [Docker Container Service](#5-docker-container-service)
6. [Python Package/SDK](#6-python-packagesdk)
7. [Message Queue Integration](#7-message-queue-integration)
8. [GraphQL API](#8-graphql-api)

---

## 1. REST API (FastAPI/Flask)

**Best for**: Web applications, mobile apps, microservices

### Implementation Options

#### Option A: FastAPI (Recommended - Modern, Fast, Auto-docs)

**Features**:
- Automatic OpenAPI documentation
- Type validation with Pydantic
- Async support for high performance
- Built-in authentication

**Endpoints**:
```
POST /api/v1/analyze/image          - Analyze single image
POST /api/v1/analyze/batch           - Batch analyze multiple images
GET  /api/v1/analyze/status/{job_id} - Check job status
GET  /api/v1/analyze/result/{job_id} - Get analysis results
POST /api/v1/agents/aesthetic        - Run aesthetic assessment only
POST /api/v1/agents/filtering        - Run filtering only
POST /api/v1/agents/caption          - Run caption generation only
GET  /api/v1/usage/tokens            - Get token usage statistics
```

**File**: `api/fastapi_server.py`

#### Option B: Flask REST API (Simpler, established)

**File**: `api/flask_api.py`

### Advantages
- ✅ Industry standard
- ✅ Easy to integrate with any platform
- ✅ Language-agnostic clients
- ✅ Can use HTTP caching, load balancing
- ✅ Swagger/OpenAPI documentation

### Disadvantages
- ❌ HTTP overhead for large images
- ❌ Requires separate deployment
- ❌ Need to manage sessions/authentication

---

## 2. MCP (Model Context Protocol) Server

**Best for**: Claude Desktop integration, AI-native applications, LLM workflows

### What is MCP?

MCP is Anthropic's protocol for connecting AI assistants to external data sources and tools. Perfect for making your agents available to Claude Desktop, IDEs, and other MCP-compatible applications.

### Implementation

**File**: `mcp/photo_analysis_server.py`

**Tools Exposed**:
- `analyze_photo` - Full analysis pipeline
- `assess_aesthetic_quality` - Aesthetic scoring only
- `categorize_photo` - Categorization only
- `generate_caption` - Caption generation only
- `get_token_usage` - Cost tracking

**Resources Provided**:
- `photo-analysis://results/{job_id}` - Analysis results
- `photo-analysis://stats/tokens` - Token usage stats
- `photo-analysis://config` - Current configuration

### Usage Example

```json
// Claude Desktop config (~/.config/claude/claude_desktop_config.json)
{
  "mcpServers": {
    "photo-analysis": {
      "command": "uv",
      "args": ["run", "python", "/path/to/mcp/photo_analysis_server.py"]
    }
  }
}
```

Then in Claude Desktop:
```
User: "Analyze this travel photo and give me a caption"
Claude: [Uses analyze_photo tool] "This is a stunning sunset..."
```

### Advantages
- ✅ Native Claude Desktop integration
- ✅ Perfect for AI workflows
- ✅ Standardized protocol
- ✅ Supports streaming responses
- ✅ Built-in error handling

### Disadvantages
- ❌ New protocol (limited ecosystem)
- ❌ Requires MCP-compatible clients
- ❌ Not suitable for non-AI applications

---

## 3. gRPC Service

**Best for**: High-performance microservices, language-agnostic RPC

### Implementation

**Files**:
- `grpc/photo_analysis.proto` - Service definition
- `grpc/server.py` - gRPC server
- `grpc/client.py` - Example client

**Features**:
- Binary protocol (faster than JSON)
- Bi-directional streaming
- Strong typing with Protocol Buffers
- HTTP/2 multiplexing

### Advantages
- ✅ Very fast (binary protocol)
- ✅ Strong typing
- ✅ Supports streaming
- ✅ Language-agnostic (auto-generate clients)

### Disadvantages
- ❌ More complex than REST
- ❌ Not browser-friendly
- ❌ Requires code generation

---

## 4. Serverless Functions

**Best for**: Event-driven processing, auto-scaling, pay-per-use

### Implementation Options

#### A. AWS Lambda + API Gateway

**File**: `serverless/aws_lambda_handler.py`

```python
def lambda_handler(event, context):
    """Process photo analysis request"""
    # Initialize agents
    # Process image from S3
    # Return results
```

**Deployment**: `serverless/aws_sam_template.yaml`

#### B. Google Cloud Functions

**File**: `serverless/gcp_function.py`

```python
def analyze_photo(request):
    """HTTP Cloud Function for photo analysis"""
```

**Deployment**: `gcloud functions deploy`

#### C. Azure Functions

**File**: `serverless/azure_function.py`

### Advantages
- ✅ Auto-scaling
- ✅ Pay only for execution time
- ✅ No server management
- ✅ Built-in monitoring

### Disadvantages
- ❌ Cold start latency
- ❌ Execution time limits
- ❌ Vendor lock-in

---

## 5. Docker Container Service

**Best for**: Cloud deployment, Kubernetes, consistent environments

### Implementation

**Files**:
- `docker/Dockerfile` - Container image
- `docker/docker-compose.yml` - Multi-service setup
- `docker/api_server.py` - Containerized API

**Features**:
- Includes all dependencies
- Redis for job queue
- PostgreSQL for results storage
- Nginx reverse proxy

### Deployment Options

```bash
# Standalone
docker run -p 8000:8000 photo-analysis-api

# Docker Compose (with queue + DB)
docker-compose up

# Kubernetes
kubectl apply -f k8s/deployment.yaml
```

### Advantages
- ✅ Consistent deployment
- ✅ Easy to scale horizontally
- ✅ Works anywhere (cloud, on-prem)
- ✅ Isolation and security

### Disadvantages
- ❌ Requires container orchestration
- ❌ Resource overhead

---

## 6. Python Package/SDK

**Best for**: Python applications, direct integration, local use

### Implementation

**File**: `sdk/photo_analysis_client.py`

**Installation**:
```bash
pip install photo-analysis-sdk
```

**Usage**:
```python
from photo_analysis import PhotoAnalysisClient

client = PhotoAnalysisClient(
    api_key="your-key",
    project_id="your-gcp-project"
)

# Analyze single image
result = client.analyze_image("photo.jpg")

# Batch processing
results = client.analyze_batch(["img1.jpg", "img2.jpg"])

# Individual agents
aesthetic = client.assess_aesthetic("photo.jpg")
caption = client.generate_caption("photo.jpg")
```

### Distribution

```bash
# PyPI package
poetry build
poetry publish

# Private package server
pip install --index-url https://your-server/simple/ photo-analysis-sdk
```

### Advantages
- ✅ Easiest for Python users
- ✅ No network overhead (can run locally)
- ✅ Type hints and IDE support
- ✅ Offline capable

### Disadvantages
- ❌ Python-only
- ❌ Requires installation
- ❌ Must manage dependencies

---

## 7. Message Queue Integration

**Best for**: Asynchronous processing, high-volume workloads, decoupled systems

### Implementation Options

#### A. RabbitMQ Worker

**Files**:
- `queue/rabbitmq_worker.py` - Consumer
- `queue/rabbitmq_publisher.py` - Producer example

**Message Flow**:
```
Producer → RabbitMQ → Worker → Results Queue → Consumer
```

#### B. AWS SQS + SNS

**Files**:
- `queue/sqs_worker.py` - SQS consumer
- `queue/sns_notifier.py` - SNS notifications

#### C. Google Pub/Sub

**Files**:
- `queue/pubsub_worker.py`

### Message Format

```json
{
  "job_id": "uuid",
  "image_url": "gs://bucket/photo.jpg",
  "agents": ["aesthetic", "caption"],
  "callback_url": "https://api.example.com/webhook"
}
```

### Advantages
- ✅ Asynchronous processing
- ✅ Handles traffic spikes
- ✅ Decoupled architecture
- ✅ Retry mechanisms

### Disadvantages
- ❌ More complex architecture
- ❌ Eventual consistency
- ❌ Requires queue infrastructure

---

## 8. GraphQL API

**Best for**: Flexible queries, mobile apps, single endpoint

### Implementation

**File**: `api/graphql_server.py` (using Strawberry/Ariadne)

**Schema**:
```graphql
type Query {
  analyzePhoto(imageUrl: String!, agents: [AgentType!]): AnalysisResult!
  getJobStatus(jobId: ID!): JobStatus!
  getTokenUsage(dateRange: DateRange): TokenUsageStats!
}

type Mutation {
  submitPhotoAnalysis(input: AnalysisInput!): Job!
}

type Subscription {
  analysisProgress(jobId: ID!): AnalysisProgress!
}

type AnalysisResult {
  aesthetic: AestheticAssessment
  filtering: FilteringResult
  caption: CaptionResult
  tokenUsage: TokenUsage
}
```

### Advantages
- ✅ Flexible queries (request only what you need)
- ✅ Single endpoint
- ✅ Strong typing
- ✅ Subscriptions for real-time updates

### Disadvantages
- ❌ More complex than REST
- ❌ Caching is harder
- ❌ Learning curve

---

## Comparison Matrix

| Option | Ease of Setup | Performance | Scalability | Best Use Case |
|--------|---------------|-------------|-------------|---------------|
| **REST API (FastAPI)** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ | General purpose web/mobile apps |
| **MCP Server** | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐ | Claude Desktop, AI workflows |
| **gRPC** | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | Microservices, high-performance |
| **Serverless** | ⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ | Event-driven, variable load |
| **Docker Service** | ⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | Cloud deployment, Kubernetes |
| **Python SDK** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐ | Python apps, local use |
| **Message Queue** | ⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | Async processing, high volume |
| **GraphQL** | ⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ | Flexible queries, mobile apps |

---

## Recommended Approaches by Scenario

### Scenario 1: Integration with Claude Desktop
→ **MCP Server** (Option 2)

### Scenario 2: Public API for multiple clients
→ **FastAPI REST API** (Option 1A) + **Docker** (Option 5)

### Scenario 3: Internal microservices
→ **gRPC** (Option 3) + **Kubernetes**

### Scenario 4: Mobile app backend
→ **GraphQL** (Option 8) or **REST API** (Option 1)

### Scenario 5: Python-only integration
→ **Python SDK** (Option 6)

### Scenario 6: High-volume batch processing
→ **Message Queue** (Option 7) + **Serverless** (Option 4)

### Scenario 7: Quick prototype
→ **Flask API** (Option 1B) + **Docker** (Option 5)

---

## Next Steps

1. **Choose your integration approach** based on your use case
2. **Review the implementation guide** for your chosen option
3. **Set up authentication** (API keys, OAuth, etc.)
4. **Deploy to your target environment**
5. **Monitor and optimize** token usage and costs

Each option can be implemented - let me know which one(s) you'd like me to build out!
