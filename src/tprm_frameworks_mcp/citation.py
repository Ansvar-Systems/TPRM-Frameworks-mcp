"""
Citation metadata for the deterministic citation pipeline.

Provides structured identifiers (canonical_ref, display_text, aliases)
that the platform's entity linker uses to match references in agent
responses to MCP tool results -- without relying on LLM formatting.

See: docs/guides/law-mcp-golden-standard.md Section 4.9c
"""

from typing import Optional


def build_citation(
    canonical_ref: str,
    display_text: str,
    tool_name: str,
    tool_args: dict[str, str],
    source_url: Optional[str] = None,
    aliases: Optional[list[str]] = None,
) -> dict:
    """Build citation metadata for any retrieval tool response."""
    result: dict = {
        "canonical_ref": canonical_ref,
        "display_text": display_text,
        "lookup": {
            "tool": tool_name,
            "args": tool_args,
        },
    }
    if aliases:
        result["aliases"] = aliases
    if source_url:
        result["source_url"] = source_url
    return result
