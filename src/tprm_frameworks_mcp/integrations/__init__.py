"""Integration modules for external MCP servers."""

from .eu_regulations import (
    EURegulationsClient,
    RegulatoryRequirement,
    get_dora_requirements,
    get_nis2_requirements,
    generate_questions_from_articles,
    map_questions_to_articles,
)

__all__ = [
    "EURegulationsClient",
    "RegulatoryRequirement",
    "get_dora_requirements",
    "get_nis2_requirements",
    "generate_questions_from_articles",
    "map_questions_to_articles",
]
