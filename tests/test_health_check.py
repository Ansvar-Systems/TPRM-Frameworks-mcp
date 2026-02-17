#!/usr/bin/env python3
"""Test the enhanced health check function."""

import asyncio
import json


async def test_health_check():
    """Test the health check function."""
    # Import after setting up path
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).parent / "src"))

    from tprm_frameworks_mcp.server import health_check

    print("Testing enhanced health check...")
    print("=" * 60)

    # Call health check
    result = await health_check()

    # Pretty print result
    print(json.dumps(result, indent=2))
    print("=" * 60)

    # Verify expected fields
    expected_fields = [
        "status",
        "version",
        "server",
        "uptime_seconds",
        "frameworks",
        "storage",
        "memory",
        "tools_available",
        "timestamp"
    ]

    missing_fields = [f for f in expected_fields if f not in result]
    if missing_fields:
        print(f"❌ Missing fields: {missing_fields}")
        return False

    print("✓ All expected fields present")

    # Verify nested structures
    if "frameworks" in result:
        frameworks = result["frameworks"]
        if "loaded" in frameworks and "frameworks" in frameworks:
            print(f"✓ Frameworks: {frameworks['loaded']} loaded")
            print(f"  - Available: {', '.join(frameworks['frameworks'])}")
        else:
            print("❌ Frameworks structure incomplete")
            return False

    if "storage" in result:
        storage = result["storage"]
        expected_storage_fields = [
            "status",
            "total_questionnaires",
            "total_assessments",
            "total_vendors",
            "database_size_mb",
            "database_path"
        ]
        missing_storage = [f for f in expected_storage_fields if f not in storage]
        if missing_storage:
            print(f"❌ Missing storage fields: {missing_storage}")
            return False
        print(f"✓ Storage status: {storage['status']}")
        print(f"  - Database: {storage.get('database_path', 'N/A')}")
        print(f"  - Size: {storage.get('database_size_mb', 0)}MB")
        print(f"  - Questionnaires: {storage.get('total_questionnaires', 0)}")
        print(f"  - Assessments: {storage.get('total_assessments', 0)}")
        print(f"  - Vendors: {storage.get('total_vendors', 0)}")

    if "memory" in result:
        memory = result["memory"]
        if "rss_mb" in memory and "vms_mb" in memory:
            print(f"✓ Memory: RSS={memory['rss_mb']}MB, VMS={memory['vms_mb']}MB")
        else:
            print("❌ Memory structure incomplete")
            return False

    if "uptime_seconds" in result:
        print(f"✓ Uptime: {result['uptime_seconds']} seconds")

    print("=" * 60)
    print("✓ Health check test PASSED")
    return True


if __name__ == "__main__":
    success = asyncio.run(test_health_check())
    exit(0 if success else 1)
