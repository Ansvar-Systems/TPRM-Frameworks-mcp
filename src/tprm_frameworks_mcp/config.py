"""Centralized configuration management."""
import os
from dataclasses import dataclass
from pathlib import Path


@dataclass
class ServerConfig:
    """Server configuration."""
    version: str = "0.1.0"
    port: int = int(os.getenv("TPRM_PORT", "8309"))
    log_level: str = os.getenv("TPRM_LOG_LEVEL", "INFO")


@dataclass
class EvaluationConfig:
    """Evaluation thresholds configuration."""
    risk_low_threshold: float = float(os.getenv("RISK_LOW_THRESHOLD", "80.0"))
    risk_medium_threshold: float = float(os.getenv("RISK_MEDIUM_THRESHOLD", "60.0"))
    risk_high_threshold: float = float(os.getenv("RISK_HIGH_THRESHOLD", "40.0"))


@dataclass
class StorageConfig:
    """Storage configuration."""
    database_path: Path = Path(os.getenv("TPRM_DB_PATH", str(Path.home() / ".tprm-mcp" / "tprm.db")))


@dataclass
class IntegrationConfig:
    """Integration configuration for external MCP servers."""
    # EU Regulations MCP server URL
    # Format: "command:args" for stdio transport or "http://..." for HTTP transport
    # Example: "python3:/path/to/eu-regulations-mcp/server.py"
    eu_regulations_mcp_url: str = os.getenv("EU_REGULATIONS_MCP_URL", "")


class Config:
    """Main configuration object."""
    def __init__(self):
        self.server = ServerConfig()
        self.evaluation = EvaluationConfig()
        self.storage = StorageConfig()
        self.integration = IntegrationConfig()


# Global config instance
config = Config()
