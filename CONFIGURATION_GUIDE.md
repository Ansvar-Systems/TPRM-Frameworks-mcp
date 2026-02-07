# Configuration Management Guide

## Overview

The TPRM Frameworks MCP server uses centralized configuration management with environment variable support. All configuration is managed through the `config.py` module, which provides a global `config` object.

## Configuration Structure

### Server Configuration

Located at `config.server`:

- **version** (str): Server version (default: "0.1.0")
- **port** (int): Server port (default: 8309)
  - Environment variable: `TPRM_PORT`
- **log_level** (str): Logging level (default: "INFO")
  - Environment variable: `TPRM_LOG_LEVEL`

### Evaluation Configuration

Located at `config.evaluation`:

- **risk_low_threshold** (float): Minimum score for LOW risk (default: 80.0)
  - Environment variable: `RISK_LOW_THRESHOLD`
- **risk_medium_threshold** (float): Minimum score for MEDIUM risk (default: 60.0)
  - Environment variable: `RISK_MEDIUM_THRESHOLD`
- **risk_high_threshold** (float): Minimum score for HIGH risk (default: 40.0)
  - Environment variable: `RISK_HIGH_THRESHOLD`

**Risk Level Mapping:**
- Scores >= 80.0: LOW risk
- Scores >= 60.0 and < 80.0: MEDIUM risk
- Scores >= 40.0 and < 60.0: HIGH risk
- Scores < 40.0: CRITICAL risk

### Storage Configuration

Located at `config.storage`:

- **database_path** (Path): SQLite database file path (default: ~/.tprm-mcp/tprm.db)
  - Environment variable: `TPRM_DB_PATH`

## Usage Examples

### In Code

```python
from tprm_frameworks_mcp.config import config

# Access server configuration
print(f"Server version: {config.server.version}")
print(f"Server port: {config.server.port}")

# Access evaluation thresholds
if score >= config.evaluation.risk_low_threshold:
    risk_level = RiskLevel.LOW
elif score >= config.evaluation.risk_medium_threshold:
    risk_level = RiskLevel.MEDIUM
elif score >= config.evaluation.risk_high_threshold:
    risk_level = RiskLevel.HIGH
else:
    risk_level = RiskLevel.CRITICAL

# Access storage configuration
db_path = config.storage.database_path
```

### Environment Variables

Create a `.env` file in the project root:

```bash
# Server Configuration
TPRM_PORT=8309
TPRM_LOG_LEVEL=INFO

# Evaluation Thresholds
RISK_LOW_THRESHOLD=80.0
RISK_MEDIUM_THRESHOLD=60.0
RISK_HIGH_THRESHOLD=40.0

# Storage Configuration
TPRM_DB_PATH=/path/to/custom/tprm.db
```

Or set them directly in your shell:

```bash
export TPRM_PORT=9000
export RISK_LOW_THRESHOLD=85.0
export TPRM_DB_PATH=/custom/path/tprm.db

python3 -m tprm_frameworks_mcp
```

### Testing with Custom Configuration

```bash
# Test with custom thresholds
RISK_LOW_THRESHOLD=85.0 RISK_MEDIUM_THRESHOLD=65.0 python3 test_server.py

# Test with custom database path
TPRM_DB_PATH=/tmp/test.db python3 -m tprm_frameworks_mcp
```

## Files Modified

### 1. config.py (NEW)

Location: `/src/tprm_frameworks_mcp/config.py`

Centralized configuration module with:
- `ServerConfig` dataclass
- `EvaluationConfig` dataclass
- `StorageConfig` dataclass
- `Config` class combining all configuration
- Global `config` instance

### 2. server.py

Changes:
- Import: `from .config import config`
- `SERVER_VERSION = config.server.version` (line 46)
- Risk level thresholds use `config.evaluation.*` (lines 712-719)
- Health check uses `config.server.port` (line 1380)

### 3. evaluation/rubric.py

Changes:
- Import: `from ..config import config`
- Risk threshold checks use `config.evaluation.*` (lines 216-224)

### 4. storage.py

Changes:
- Import: `from .config import config as global_config`
- Database path initialization uses `global_config.storage.database_path` (line 47)

## Configuration Validation

The configuration system includes:

1. **Type Safety**: All config values have type hints
2. **Default Values**: Sensible defaults for all settings
3. **Environment Variable Override**: All values can be overridden via environment variables
4. **Path Resolution**: Database path automatically creates parent directories

## Best Practices

1. **Development**: Use default values or `.env` file
2. **Production**: Set environment variables in deployment system
3. **Testing**: Override specific values per test as needed
4. **Documentation**: Keep `.env.example` up to date with all available options

## Adding New Configuration Options

To add a new configuration option:

1. **Add to appropriate dataclass in config.py**:
   ```python
   @dataclass
   class ServerConfig:
       new_option: str = os.getenv("NEW_OPTION", "default_value")
   ```

2. **Update .env.example**:
   ```bash
   # New Option Description
   NEW_OPTION=default_value
   ```

3. **Document in this guide**

4. **Use in code**:
   ```python
   value = config.server.new_option
   ```

## Troubleshooting

### Configuration not loading

Check that:
1. Environment variables are exported before running the server
2. `.env` file is in the project root (if using one)
3. Variable names match exactly (case-sensitive)

### Database path issues

If the database path is incorrect:
1. Check `TPRM_DB_PATH` environment variable
2. Ensure parent directory exists or has write permissions
3. Default path is `~/.tprm-mcp/tprm.db`

### Risk thresholds not working

Verify:
1. Thresholds are float values (use decimals)
2. Order: LOW > MEDIUM > HIGH > 0
3. Values are in range 0-100

## Future Enhancements

Potential additions to configuration system:

1. **Logging Configuration**:
   - Log file path
   - Log format (text/json)
   - Rotation settings

2. **Performance Configuration**:
   - Cache size
   - Connection pool size
   - Timeout values

3. **Integration Configuration**:
   - Other MCP server URLs
   - API keys (from secrets)
   - Retry settings

4. **Security Configuration**:
   - Rate limiting
   - Authentication tokens
   - CORS settings
