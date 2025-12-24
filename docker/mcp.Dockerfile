# ===========================
# Travel Photo MCP Server - Dockerfile
# ===========================
# For use with Claude Desktop or other MCP clients

# ---- Builder Stage ----
FROM python:3.11-slim AS builder

WORKDIR /app

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt ./

# Install dependencies using pip into a virtual environment
RUN python -m venv /app/.venv && \
    /app/.venv/bin/pip install --no-cache-dir --upgrade pip && \
    /app/.venv/bin/pip install --no-cache-dir -r requirements.txt

# ---- Runtime Stage ----
FROM python:3.11-slim AS runtime

WORKDIR /app

# Install runtime dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgl1 \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender1 \
    && rm -rf /var/lib/apt/lists/*

# Copy virtualenv from builder
COPY --from=builder /app/.venv /app/.venv

# Add venv to PATH
ENV PATH="/app/.venv/bin:$PATH"
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# Copy application code
COPY agents/ ./agents/
COPY mcp/ ./mcp/
COPY utils/ ./utils/
COPY config.yaml ./

# Create directories
RUN mkdir -p /app/output/logs /app/cache

# MCP servers communicate via stdio, no port needed
# The entrypoint runs the MCP server script

# Run the MCP server (expects stdio communication)
CMD ["python", "mcp/photo_analysis_server.py"]
