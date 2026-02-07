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
RUN pip install --no-cache-dir -e .

# Create data directory for future SQLite storage (Phase 1)
RUN mkdir -p /app/data

# Expose MCP server port
EXPOSE 3000

# Health check endpoint
# Note: MCP servers typically don't have HTTP health endpoints by default
# This will be added when HTTP transport is implemented
HEALTHCHECK --interval=10s --timeout=5s --start-period=10s --retries=3 \
  CMD pgrep -f "python.*tprm_frameworks_mcp" || exit 1

# Run the MCP server
CMD ["python", "-m", "tprm_frameworks_mcp"]
