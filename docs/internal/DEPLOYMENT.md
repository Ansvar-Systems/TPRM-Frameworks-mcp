# TPRM Frameworks MCP Server - Deployment Guide

## Overview

The TPRM Frameworks MCP server provides vendor risk assessment capabilities for the Ansvar AI platform. This server runs on **port 8309** and integrates with other MCP servers to deliver comprehensive third-party risk management workflows.

## Server Configuration

### Basic Information

| Property | Value |
|----------|-------|
| **Server Name** | tprm-frameworks |
| **Version** | 0.1.0 |
| **Port** | 8309 |
| **Protocol** | stdio (MCP) |
| **Python Version** | >= 3.10 |
| **Main Package** | tprm-frameworks-mcp |

### Capabilities

The server provides **7 tools** for TPRM workflows:

1. `list_frameworks` - List available questionnaire frameworks
2. `generate_questionnaire` - Generate tailored vendor assessments
3. `evaluate_response` - Score vendor responses with rubric-based evaluation
4. `map_questionnaire_to_controls` - Map questions to SCF controls
5. `generate_tprm_report` - Create comprehensive TPRM reports
6. `get_questionnaire` - Retrieve questionnaires by ID
7. `search_questions` - Search questions by keyword

### Integration Points

The TPRM server integrates with:

- **security-controls-mcp** (port 8308)
  - Maps questionnaire questions to SCF controls
  - Enables gap analysis and control coverage assessment
  - Tools: `get_control`, `map_frameworks`, `search_controls`

- **eu-regulations-mcp**
  - Sources DORA and NIS2 regulatory requirements
  - Filters questions based on regulatory applicability
  - Tools: `get_dora_requirements`, `get_nis2_requirements`

- **vendor-intel-mcp** (future)
  - Enriches TPRM reports with vendor intelligence data
  - Tools: `get_vendor_profile`, `get_breach_history`

## Installation

### Prerequisites

```bash
# System requirements
- Python 3.10 or higher
- pip package manager
- Git (for cloning repository)

# Python dependencies
- mcp >= 0.9.0
```

### Installation Steps

#### 1. Clone the Repository

```bash
cd ~/Projects
git clone https://github.com/Ansvar-Systems/tprm-frameworks-mcp.git
cd TPRM-Frameworks-mcp
```

#### 2. Install the Package

```bash
# Install in editable mode (recommended for development)
pip3 install -e .

# Or install with development dependencies
pip3 install -e ".[dev]"

# For macOS Homebrew Python (if needed)
pip3 install -e . --break-system-packages
# OR
pip3 install -e . --user
```

#### 3. Verify Installation

```bash
# Check package is installed
python3 -c "import tprm_frameworks_mcp; print('✓ Package installed successfully')"

# Run test suite
python3 test_server.py
```

Expected output:
```
🧪 Testing TPRM Frameworks MCP Server

1. Testing Data Loader...
   ✓ Loaded 4 frameworks
   - SIG Lite: 180 questions (placeholder)
   - CAIQ v4: 295 questions (placeholder)
   - DORA ICT TPP: 85 questions (placeholder)
   - NIS2 Supply Chain: 65 questions (placeholder)

[... more test output ...]

✅ All tests passed!
```

## Running the Server

### Method 1: Direct Execution (Recommended)

```bash
# Using the startup script
./start-server.sh

# Or run directly with Python
python3 -m tprm_frameworks_mcp
```

### Method 2: Using the CLI Command

```bash
# If installed system-wide
tprm-mcp
```

### Method 3: Background Process

```bash
# Run as background process with logging
nohup python3 -m tprm_frameworks_mcp > logs/tprm-mcp.log 2>&1 &

# Save PID for later management
echo $! > tprm-mcp.pid
```

## MCP Configuration

### For Ansvar AI Platform

Add to your MCP configuration file (typically `~/.config/mcp/config.json` or in your application's MCP settings):

```json
{
  "mcpServers": {
    "tprm-frameworks": {
      "command": "python3",
      "args": ["-m", "tprm_frameworks_mcp"],
      "env": {
        "TPRM_PORT": "8309",
        "TPRM_LOG_LEVEL": "INFO"
      },
      "description": "TPRM Frameworks MCP server for vendor risk assessments",
      "capabilities": {
        "tools": true,
        "resources": false,
        "prompts": false
      }
    }
  }
}
```

### For Claude Desktop

Add to `~/Library/Application Support/Claude/claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "tprm-frameworks": {
      "command": "python3",
      "args": ["-m", "tprm_frameworks_mcp"]
    }
  }
}
```

### Multi-Server Configuration (Recommended)

Configure all Ansvar AI MCP servers together:

```json
{
  "mcpServers": {
    "security-controls-mcp": {
      "command": "python3",
      "args": ["-m", "security_controls_mcp"],
      "env": {
        "PORT": "8308"
      }
    },
    "tprm-frameworks": {
      "command": "python3",
      "args": ["-m", "tprm_frameworks_mcp"],
      "env": {
        "TPRM_PORT": "8309"
      }
    },
    "eu-regulations-mcp": {
      "command": "python3",
      "args": ["-m", "eu_regulations_mcp"]
    }
  }
}
```

## Health Check

The server includes a built-in health check function that runs at startup and can be queried programmatically.

### Startup Health Check

The server performs automatic health checks on startup:

```
✓ TPRM Frameworks MCP Server v0.1.0 starting...
✓ Loaded 4 frameworks
✓ 7 tools available
✓ Protocol: stdio
✓ Port: 8309
```

### Programmatic Health Check

```python
import asyncio
from tprm_frameworks_mcp.server import health_check

async def check_server():
    health = await health_check()
    print(f"Status: {health['status']}")
    print(f"Frameworks: {health['frameworks_loaded']}")
    print(f"Tools: {health['tools_available']}")

asyncio.run(check_server())
```

Expected response:
```json
{
  "status": "healthy",
  "version": "0.1.0",
  "server": "tprm-frameworks-mcp",
  "port": 8309,
  "protocol": "stdio",
  "frameworks_loaded": 4,
  "tools_available": 7,
  "timestamp": "2026-02-07T12:00:00.000000"
}
```

## Data Directory Structure

The server requires the following data files:

```
src/tprm_frameworks_mcp/data/
├── sig_lite.json           # SIG Lite questionnaire (placeholder)
├── caiq_v4.json           # CAIQ v4 questionnaire (placeholder)
├── dora_ict_tpp.json      # DORA ICT TPP questionnaire (placeholder)
├── nis2_supply_chain.json # NIS2 Supply Chain questionnaire (placeholder)
└── questionnaire-to-scf.json  # Questionnaire to SCF control mappings
```

### Data File Requirements

All data files must be valid JSON and follow the schema defined in `src/tprm_frameworks_mcp/models.py`.

**IMPORTANT**: The current data files contain placeholder content for development. For production deployment:

1. **SIG Questionnaires**: Obtain licensed content from [Shared Assessments](https://sharedassessments.org)
   - Cost: ~$2,000-5,000/year depending on membership level
   - Files: SIG Full (~800 questions), SIG Lite (~180 questions)

2. **CAIQ v4**: Download free from [Cloud Security Alliance](https://cloudsecurityalliance.org)
   - Cost: Free
   - Questions: ~295

3. **DORA/NIS2**: Can be derived from eu-regulations-mcp server
   - Cost: Free (public regulation)
   - Requires mapping to questionnaire format

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `TPRM_PORT` | 8309 | Server port number |
| `TPRM_LOG_LEVEL` | INFO | Logging level (DEBUG, INFO, WARNING, ERROR) |
| `PYTHONUNBUFFERED` | 1 | Disable Python output buffering |

## Workflow Examples

### Example 1: Generate and Evaluate SIG Lite Questionnaire

```javascript
// 1. List available frameworks
const frameworks = await use_mcp_tool({
  server_name: "tprm-frameworks",
  tool_name: "list_frameworks",
  arguments: {}
});

// 2. Generate SIG Lite questionnaire for a cloud provider
const questionnaire = await use_mcp_tool({
  server_name: "tprm-frameworks",
  tool_name: "generate_questionnaire",
  arguments: {
    framework: "sig_lite",
    scope: "lite",
    entity_type: "cloud_provider",
    regulations: ["gdpr", "dora"]
  }
});

// 3. Evaluate vendor responses
const evaluation = await use_mcp_tool({
  server_name: "tprm-frameworks",
  tool_name: "evaluate_response",
  arguments: {
    questionnaire_id: questionnaire.questionnaire_id,
    vendor_name: "ExampleCloud Inc",
    responses: [
      {
        question_id: "SIG-001",
        answer: "Yes, MFA is required for all users...",
        supporting_documents: ["mfa-policy.pdf"]
      }
    ],
    strictness: "moderate"
  }
});

// 4. Map questions to SCF controls
const mappings = await use_mcp_tool({
  server_name: "tprm-frameworks",
  tool_name: "map_questionnaire_to_controls",
  arguments: {
    framework: "sig_lite"
  }
});
```

### Example 2: Cross-Server Integration

```javascript
// Generate DORA-focused questionnaire
const doraQuestionnaire = await use_mcp_tool({
  server_name: "tprm-frameworks",
  tool_name: "generate_questionnaire",
  arguments: {
    framework: "dora_ict_tpp",
    scope: "full",
    entity_type: "ict_provider"
  }
});

// Map to SCF controls
const controlMappings = await use_mcp_tool({
  server_name: "tprm-frameworks",
  tool_name: "map_questionnaire_to_controls",
  arguments: {
    framework: "dora_ict_tpp"
  }
});

// Get detailed control information from security-controls-mcp
const controlDetails = await use_mcp_tool({
  server_name: "security-controls-mcp",
  tool_name: "get_control",
  arguments: {
    control_id: "IAC-01",  // From mapping
    framework: "scf"
  }
});

// Get DORA requirements from eu-regulations-mcp
const doraRequirements = await use_mcp_tool({
  server_name: "eu-regulations-mcp",
  tool_name: "get_dora_requirements",
  arguments: {
    category: "ict_third_party_risk"
  }
});
```

## Monitoring and Logging

### Log Files

```bash
# Create logs directory
mkdir -p logs

# Run with logging
python3 -m tprm_frameworks_mcp > logs/tprm-mcp.log 2>&1
```

### Process Management

```bash
# Check if server is running
ps aux | grep tprm_frameworks_mcp

# Stop the server
kill $(cat tprm-mcp.pid)

# Restart the server
./start-server.sh
```

### Health Monitoring Script

```bash
#!/bin/bash
# health-check.sh

HEALTH_CHECK_SCRIPT="
import asyncio
from tprm_frameworks_mcp.server import health_check

async def check():
    health = await health_check()
    if health['status'] == 'healthy':
        print('OK')
        exit(0)
    else:
        print(f\"FAIL: {health.get('error')}\")
        exit(1)

asyncio.run(check())
"

python3 -c "$HEALTH_CHECK_SCRIPT"
```

## Troubleshooting

### Server Won't Start

**Issue**: `ModuleNotFoundError: No module named 'tprm_frameworks_mcp'`

**Solution**: Install the package
```bash
pip3 install -e .
```

---

**Issue**: `FileNotFoundError: [Errno 2] No such file or directory: 'data/sig_lite.json'`

**Solution**: Verify data directory structure and files
```bash
ls -la src/tprm_frameworks_mcp/data/
```

---

**Issue**: Homebrew Python error about system packages

**Solution**: Use one of these approaches
```bash
# Option 1: Break system packages (for isolated environments)
pip3 install -e . --break-system-packages

# Option 2: Install for user only
pip3 install -e . --user

# Option 3: Use virtual environment (recommended for production)
python3 -m venv venv
source venv/bin/activate
pip install -e .
```

### Connection Issues

**Issue**: MCP client can't connect to server

**Solution**:
1. Verify server is running: `ps aux | grep tprm_frameworks_mcp`
2. Check configuration file syntax (valid JSON)
3. Verify Python path in MCP config matches system: `which python3`
4. Check logs for errors: `tail -f logs/tprm-mcp.log`

### Data Loading Issues

**Issue**: Framework not found or questions not loading

**Solution**:
1. Verify all JSON files are valid: `python3 -m json.tool < data/sig_lite.json`
2. Check file permissions: `ls -l src/tprm_frameworks_mcp/data/`
3. Run test script: `python3 test_server.py`

## Production Deployment Checklist

- [ ] Python 3.10+ installed
- [ ] Package installed via pip
- [ ] All data files present and valid
- [ ] Licensed questionnaire content (SIG, CAIQ) obtained and loaded
- [ ] MCP configuration file created
- [ ] Integration with security-controls-mcp (8308) configured
- [ ] Integration with eu-regulations-mcp configured
- [ ] Health check passing
- [ ] Test script runs successfully
- [ ] Startup script tested
- [ ] Logging configured
- [ ] Process monitoring in place
- [ ] Backup strategy for questionnaire data

## Security Considerations

1. **Data Protection**: Questionnaire responses may contain sensitive vendor information
   - Store generated questionnaires securely
   - Implement access controls for evaluation results
   - Consider encryption for sensitive data at rest

2. **Licensed Content**: Ensure compliance with questionnaire licensing terms
   - SIG questionnaires require active license
   - Don't redistribute licensed content
   - Track license expiration dates

3. **Integration Security**: Validate data from integrated MCP servers
   - Don't trust external inputs without validation
   - Sanitize vendor-provided responses
   - Implement rate limiting for tool calls

## Support and Maintenance

### Regular Maintenance Tasks

- **Weekly**: Review logs for errors or warnings
- **Monthly**: Update questionnaire data if new versions available
- **Quarterly**: Review integration points with other MCP servers
- **Annually**: Renew SIG questionnaire licenses

### Getting Help

- **Documentation**: See README.md and inline code documentation
- **Issues**: GitHub Issues (if open source) or internal ticketing system
- **Contact**: Ansvar Systems support team

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 0.1.0 | 2026-02-07 | Initial release with 7 tools, 4 frameworks |

## License

Apache-2.0

Copyright 2026 Ansvar Systems

---

**Last Updated**: 2026-02-07
**Maintainer**: Ansvar Systems (hello@ansvar.eu)
**Server Port**: 8309
**Status**: Production Ready (with licensed content)
