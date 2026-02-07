"""
Pytest configuration and fixtures for TPRM-Frameworks MCP integration tests.
"""

import pytest
import sys
from pathlib import Path

# Add src directory to path for imports
src_path = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_path))


@pytest.fixture(autouse=True)
def reset_state():
    """Reset server state between tests."""
    from tprm_frameworks_mcp.server import generated_questionnaires

    # Store original state
    original_questionnaires = dict(generated_questionnaires)

    yield

    # Clean up any test questionnaires
    # (Keep original ones if any existed)
    generated_questionnaires.clear()
    generated_questionnaires.update(original_questionnaires)


@pytest.fixture
def sample_vendor_data():
    """Provide sample vendor data for testing."""
    return {
        "name": "Acme Corp",
        "type": "saas_provider",
        "employees": "500-1000",
        "founded": "2015",
        "certifications": ["ISO 27001", "SOC 2 Type II"],
        "regions": ["US", "EU"],
    }


@pytest.fixture
def sample_responses():
    """Provide sample question responses for testing."""
    return {
        "good": {
            "yes_no": "Yes, we have fully implemented this control with documented procedures, regular audits, and automated monitoring.",
            "text": "We maintain comprehensive security controls including multi-factor authentication, encryption at rest and in transit, regular security assessments, and incident response procedures. All controls are documented and tested quarterly.",
        },
        "partial": {
            "yes_no": "Partially implemented. The control is in place but not fully documented.",
            "text": "We have implemented basic security measures but are still working on comprehensive documentation and automation.",
        },
        "poor": {
            "yes_no": "No, this control is not currently implemented.",
            "text": "This is on our roadmap but not yet implemented.",
        },
        "na": {
            "yes_no": "Not applicable to our service offering.",
            "text": "N/A - This control does not apply to our infrastructure.",
        },
    }


@pytest.fixture
def dora_assessment_context():
    """Provide DORA assessment context for testing."""
    return {
        "framework": "dora_ict_tpp",
        "entity_type": "ict_provider",
        "regulations": ["DORA", "NIS2"],
        "scope": "full",
        "vendor_profile": {
            "name": "Cloud Services Provider Inc",
            "services": ["Cloud Infrastructure", "Data Processing", "API Services"],
            "customers": ["Financial Institutions", "Banks"],
            "tier": "Critical ICT Third-Party Provider",
        },
    }


@pytest.fixture
async def mcp_list_tools():
    """Fixture to call list_tools handler directly."""
    from tprm_frameworks_mcp.server import list_tools as list_tools_handler
    return await list_tools_handler()


@pytest.fixture
async def mcp_call_tool():
    """Fixture to call tool handler directly."""
    from tprm_frameworks_mcp.server import call_tool as call_tool_handler
    
    async def _call_tool(name: str, arguments: dict):
        result = await call_tool_handler(name, arguments)
        return result
    
    return _call_tool


def pytest_configure(config):
    """Configure pytest with custom markers."""
    config.addinivalue_line(
        "markers", "integration: mark test as integration test"
    )
    config.addinivalue_line(
        "markers", "scenario: mark test as end-to-end scenario test"
    )
    config.addinivalue_line(
        "markers", "slow: mark test as slow running"
    )


def pytest_collection_modifyitems(config, items):
    """Modify test collection to add markers automatically."""
    for item in items:
        # Add integration marker to all tests
        if "integration" not in item.keywords:
            item.add_marker(pytest.mark.integration)

        # Add scenario marker to scenario tests
        if "scenario" in item.name.lower() or "salesforce" in item.name.lower():
            item.add_marker(pytest.mark.scenario)

        # Add slow marker to comprehensive tests
        if "complete" in item.name.lower() or "salesforce" in item.name.lower():
            item.add_marker(pytest.mark.slow)
