#!/bin/bash

# TPRM Frameworks MCP Server Startup Script
# For Ansvar AI Platform Integration

set -e

# Color codes for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${GREEN}=== TPRM Frameworks MCP Server ===${NC}"
echo -e "${GREEN}Starting on port 8309...${NC}\n"

# Set environment variables
export TPRM_PORT=8309
export TPRM_LOG_LEVEL=${TPRM_LOG_LEVEL:-INFO}
export PYTHONUNBUFFERED=1

# Check if Python 3 is available
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}Error: python3 not found${NC}"
    echo "Please install Python 3.10 or higher"
    exit 1
fi

# Check Python version
PYTHON_VERSION=$(python3 --version | cut -d' ' -f2)
echo -e "${GREEN}✓ Python version: ${PYTHON_VERSION}${NC}"

# Check if package is installed
if ! python3 -c "import tprm_frameworks_mcp" 2>/dev/null; then
    echo -e "${YELLOW}⚠ Package not installed. Installing in editable mode...${NC}"
    pip3 install -e . --quiet --break-system-packages || pip3 install -e . --quiet --user
    echo -e "${GREEN}✓ Package installed${NC}"
fi

# Verify data files exist
DATA_DIR="src/tprm_frameworks_mcp/data"
if [ ! -d "$DATA_DIR" ]; then
    echo -e "${RED}Error: Data directory not found: $DATA_DIR${NC}"
    exit 1
fi

REQUIRED_FILES=(
    "$DATA_DIR/sig_lite.json"
    "$DATA_DIR/caiq_v4.json"
    "$DATA_DIR/dora_ict_tpp.json"
    "$DATA_DIR/nis2_supply_chain.json"
    "$DATA_DIR/questionnaire-to-scf.json"
)

for file in "${REQUIRED_FILES[@]}"; do
    if [ ! -f "$file" ]; then
        echo -e "${RED}Error: Required data file not found: $file${NC}"
        exit 1
    fi
done

echo -e "${GREEN}✓ All data files present${NC}"

# Check configuration
if [ ! -f "server.json" ]; then
    echo -e "${YELLOW}⚠ server.json not found${NC}"
fi

if [ ! -f "mcp-config.json" ]; then
    echo -e "${YELLOW}⚠ mcp-config.json not found${NC}"
fi

echo -e "\n${GREEN}Starting TPRM Frameworks MCP Server...${NC}\n"

# Run the server
exec python3 -m tprm_frameworks_mcp
