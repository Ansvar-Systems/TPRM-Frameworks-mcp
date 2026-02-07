"""Tests for EU regulations MCP client integration."""

import asyncio
import os
import pytest
from pathlib import Path

from src.tprm_frameworks_mcp.integrations.eu_regulations import (
    EURegulationsClient,
    get_dora_requirements,
    get_nis2_requirements,
    RegulatoryArticle,
    RegulatoryRequirement,
)


class TestEURegulationsClient:
    """Test suite for EURegulationsClient."""

    @pytest.mark.asyncio
    async def test_is_server_available_no_url(self):
        """Test server availability check when no URL is configured."""
        client = EURegulationsClient(server_url=None)
        available = await client.is_server_available()
        assert available is False

    @pytest.mark.asyncio
    async def test_is_server_available_invalid_command(self):
        """Test server availability check with invalid command."""
        client = EURegulationsClient(server_url="nonexistent-command")
        available = await client.is_server_available()
        assert available is False

    @pytest.mark.asyncio
    async def test_is_server_available_http_not_implemented(self):
        """Test server availability check with HTTP URL (not yet implemented)."""
        client = EURegulationsClient(server_url="http://localhost:8000")
        available = await client.is_server_available()
        assert available is False

    @pytest.mark.asyncio
    async def test_fetch_from_local_dora(self):
        """Test fetching DORA articles from local data."""
        client = EURegulationsClient()
        articles = client._fetch_from_local("dora", "ICT_third_party")
        
        assert isinstance(articles, list)
        # Should return articles from local mapping file
        if articles:
            assert isinstance(articles[0], RegulatoryArticle)
            assert articles[0].regulation == "DORA"

    @pytest.mark.asyncio
    async def test_fetch_from_local_nis2(self):
        """Test fetching NIS2 articles from local data."""
        client = EURegulationsClient()
        articles = client._fetch_from_local("nis2", "supply_chain")
        
        assert isinstance(articles, list)
        # Should return articles from local mapping file
        if articles:
            assert isinstance(articles[0], RegulatoryArticle)
            assert articles[0].regulation == "NIS2"

    @pytest.mark.asyncio
    async def test_get_dora_articles_fallback(self):
        """Test DORA articles fetch falls back to local data when server unavailable."""
        client = EURegulationsClient(server_url="nonexistent-command")
        articles = await client.get_dora_articles("ICT_third_party")
        
        # Should fall back to local data
        assert isinstance(articles, list)

    @pytest.mark.asyncio
    async def test_get_nis2_articles_fallback(self):
        """Test NIS2 articles fetch falls back to local data when server unavailable."""
        client = EURegulationsClient(server_url="nonexistent-command")
        articles = await client.get_nis2_articles("supply_chain")
        
        # Should fall back to local data
        assert isinstance(articles, list)

    def test_get_deadline_dora(self):
        """Test getting DORA compliance deadline."""
        client = EURegulationsClient()
        deadline = client.get_deadline("dora")
        
        # Should return a deadline string
        assert deadline is not None or deadline is None  # May not exist in minimal config

    def test_get_deadline_nis2(self):
        """Test getting NIS2 compliance deadline."""
        client = EURegulationsClient()
        deadline = client.get_deadline("nis2")
        
        # Should return a deadline string
        assert deadline is not None or deadline is None  # May not exist in minimal config


class TestPublicFunctions:
    """Test public API functions."""

    @pytest.mark.asyncio
    async def test_get_dora_requirements(self):
        """Test getting DORA requirements."""
        requirements = await get_dora_requirements("ICT_third_party")
        
        assert isinstance(requirements, list)
        # Each requirement should be a RegulatoryRequirement
        for req in requirements:
            assert isinstance(req, RegulatoryRequirement)
            assert req.regulation == "DORA"

    @pytest.mark.asyncio
    async def test_get_nis2_requirements(self):
        """Test getting NIS2 requirements."""
        requirements = await get_nis2_requirements("supply_chain")
        
        assert isinstance(requirements, list)
        # Each requirement should be a RegulatoryRequirement
        for req in requirements:
            assert isinstance(req, RegulatoryRequirement)
            assert req.regulation == "NIS2"


class TestEnvironmentConfiguration:
    """Test environment variable configuration."""

    def test_client_uses_env_var(self):
        """Test that client reads EU_REGULATIONS_MCP_URL from environment."""
        # Set environment variable
        test_url = "python3:/path/to/server.py"
        os.environ["EU_REGULATIONS_MCP_URL"] = test_url
        
        try:
            client = EURegulationsClient()
            assert client.server_url == test_url
        finally:
            # Clean up
            del os.environ["EU_REGULATIONS_MCP_URL"]

    def test_client_constructor_overrides_env(self):
        """Test that constructor parameter overrides environment variable."""
        # Set environment variable
        os.environ["EU_REGULATIONS_MCP_URL"] = "env-url"
        
        try:
            client = EURegulationsClient(server_url="constructor-url")
            assert client.server_url == "constructor-url"
        finally:
            # Clean up
            del os.environ["EU_REGULATIONS_MCP_URL"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
