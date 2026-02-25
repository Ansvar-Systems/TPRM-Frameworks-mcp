# TPRM Frameworks MCP Server
# Python-based MCP server for vendor assessment questionnaires

FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy package files
COPY pyproject.toml ./
COPY src/ ./src/

# Install Python dependencies
RUN pip install --upgrade pip && pip install --no-cache-dir --timeout=120 --retries=5 -e .

# Create data directory for future SQLite storage (Phase 1)
RUN mkdir -p /app/data

# Expose MCP server port (HTTP transport)
EXPOSE 8309

# Health check using HTTP /health endpoint
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
  CMD curl -sf http://localhost:8309/health || exit 1

# Run the MCP server with HTTP transport (stdio also available via --transport stdio)
CMD ["python", "-m", "tprm_frameworks_mcp", "--transport", "http", "--port", "8309"]
