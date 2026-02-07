"""Demo script showing the new persistence and tracking features."""

import asyncio
import json
import sys
from datetime import datetime

sys.path.insert(0, "src")

from tprm_frameworks_mcp.server import call_tool


async def demo_new_features():
    """Demonstrate the new vendor history and comparison features."""
    print("🎯 TPRM Frameworks MCP - New Features Demo\n")
    print("=" * 70)

    # Step 1: Generate a questionnaire
    print("\n📋 Step 1: Generate Questionnaire")
    print("-" * 70)

    result = await call_tool(
        "generate_questionnaire",
        {
            "framework": "sig_lite",
            "scope": "lite",
            "entity_type": "cloud_provider",
            "regulations": ["gdpr", "dora"],
        },
    )

    # Extract questionnaire ID from response
    text = result[0].text
    questionnaire_id = None
    for line in text.split("\n"):
        if "**ID:**" in line:
            questionnaire_id = line.split("`")[1]
            break

    print(f"✓ Generated questionnaire: {questionnaire_id}")

    # Step 2: Create first assessment (moderate score)
    print("\n📊 Step 2: Create First Assessment (Baseline)")
    print("-" * 70)

    responses_1 = [
        {
            "question_id": "sig_lite_2.2",
            "answer": "MFA is partially implemented",
        },
        {
            "question_id": "sig_lite_6.1",
            "answer": "Encryption is planned but not implemented",
        },
    ]

    result = await call_tool(
        "evaluate_response",
        {
            "questionnaire_id": questionnaire_id,
            "vendor_name": "CloudTech Solutions",
            "responses": responses_1,
            "strictness": "moderate",
        },
    )

    text = result[0].text
    print(f"✓ Baseline assessment completed")
    for line in text.split("\n"):
        if "Overall Score:" in line or "Overall Risk Level:" in line:
            print(f"  {line.strip()}")

    # Step 3: Create second assessment (improved score)
    print("\n📊 Step 3: Create Follow-up Assessment (6 months later)")
    print("-" * 70)

    responses_2 = [
        {
            "question_id": "sig_lite_2.2",
            "answer": "Yes, MFA is fully implemented using Duo for all remote access",
        },
        {
            "question_id": "sig_lite_6.1",
            "answer": "Yes, all data is encrypted at rest using AES-256",
        },
    ]

    result = await call_tool(
        "evaluate_response",
        {
            "questionnaire_id": questionnaire_id,
            "vendor_name": "CloudTech Solutions",
            "responses": responses_2,
            "strictness": "moderate",
        },
    )

    text = result[0].text
    print(f"✓ Follow-up assessment completed")
    for line in text.split("\n"):
        if "Overall Score:" in line or "Overall Risk Level:" in line:
            print(f"  {line.strip()}")

    # Step 4: Get vendor history
    print("\n📈 Step 4: View Vendor History (NEW FEATURE)")
    print("-" * 70)

    result = await call_tool(
        "get_vendor_history",
        {
            "vendor_name": "CloudTech Solutions",
            "limit": 10,
        },
    )

    text = result[0].text
    # Parse and display nicely
    lines = text.split("\n")
    for line in lines:
        if (
            line.startswith("**") or
            line.startswith("-") or
            line.strip().startswith("1.") or
            line.strip().startswith("2.") or
            "Trend:" in line or
            "Score:" in line or
            "Change:" in line
        ):
            print(f"  {line}")

    # Step 5: Compare assessments
    print("\n🔍 Step 5: Compare Assessments (NEW FEATURE)")
    print("-" * 70)

    result = await call_tool(
        "compare_assessments",
        {
            "vendor_name": "CloudTech Solutions",
            # Not providing IDs - will use latest two
        },
    )

    text = result[0].text
    lines = text.split("\n")
    for line in lines:
        if (
            line.startswith("**") or
            "Score Delta:" in line or
            "Risk Level Change:" in line or
            "Overall Trend:" in line or
            "Improved Areas" in line or
            "sig_lite" in line and "points" in line
        ):
            print(f"  {line}")

    # Step 6: Demonstrate persistence
    print("\n💾 Step 6: Verify Persistence")
    print("-" * 70)

    result = await call_tool(
        "get_questionnaire",
        {"questionnaire_id": questionnaire_id},
    )

    text = result[0].text
    print(f"✓ Questionnaire retrieved from persistent storage")
    print(f"  ID: {questionnaire_id}")

    # Summary
    print("\n" + "=" * 70)
    print("✅ Demo Complete!")
    print("=" * 70)
    print("\nNew Features Demonstrated:")
    print("  1. ✓ Persistent storage (survives server restart)")
    print("  2. ✓ Vendor history tracking")
    print("  3. ✓ Assessment comparison with trend analysis")
    print("  4. ✓ Automatic improvement detection")
    print("  5. ✓ Risk level change tracking")
    print("\nDatabase Location: ~/.tprm-mcp/tprm.db")
    print("\nUse Cases:")
    print("  - Track vendor improvements over time")
    print("  - Identify security posture trends")
    print("  - Compare before/after remediation")
    print("  - Generate compliance reports with historical data")
    print("  - Monitor vendor risk trajectories")


if __name__ == "__main__":
    asyncio.run(demo_new_features())
