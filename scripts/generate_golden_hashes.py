#!/usr/bin/env python3
"""Generate golden hashes for data drift detection."""

import hashlib
import json
from pathlib import Path


def generate_hashes() -> dict:
    """Generate SHA256 hashes for all data files."""
    data_dir = Path("src/tprm_frameworks_mcp/data")
    hashes = {}
    for f in sorted(data_dir.glob("*.json")):
        content = f.read_bytes()
        hashes[f.name] = {
            "sha256": hashlib.sha256(content).hexdigest(),
            "size_bytes": len(content),
            "generated_at": "2026-02-18",
        }
    return hashes


if __name__ == "__main__":
    hashes = generate_hashes()
    output = Path("fixtures/golden-hashes.json")
    output.write_text(json.dumps(hashes, indent=2) + "\n")
    print(f"Generated hashes for {len(hashes)} files -> {output}")
