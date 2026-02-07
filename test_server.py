"""Simple test script for TPRM Frameworks MCP server."""

import asyncio
import json

from src.tprm_frameworks_mcp.data_loader import TPRMDataLoader
from src.tprm_frameworks_mcp.evaluation.rubric import EvaluationRubric
from src.tprm_frameworks_mcp.models import QuestionResponse


async def test_basic_functionality():
    """Test basic server functionality."""
    print("🧪 Testing TPRM Frameworks MCP Server\n")

    # Test data loader
    print("1. Testing Data Loader...")
    loader = TPRMDataLoader()
    frameworks = loader.get_all_frameworks()
    print(f"   ✓ Loaded {len(frameworks)} frameworks")

    for fw in frameworks:
        print(f"   - {fw['name']}: {fw['question_count']} questions ({fw['status']})")

    # Test questionnaire loading
    print("\n2. Testing Questionnaire Loading...")
    sig_lite_questions = loader.get_questions("sig_lite")
    print(f"   ✓ Loaded {len(sig_lite_questions)} SIG Lite questions")

    # Test evaluation rubric
    print("\n3. Testing Evaluation Rubric...")
    evaluator = EvaluationRubric()

    # Get a test question
    test_question = sig_lite_questions[3]  # MFA question
    print(f"   Testing question: {test_question.id}")
    print(f"   Question: {test_question.question_text}")

    # Test good response
    good_response = QuestionResponse(
        question_id=test_question.id,
        answer="Yes, MFA is required for all remote access and privileged accounts using Duo.",
    )
    status, score, findings, risk = evaluator.evaluate_response(
        test_question, good_response, "moderate"
    )
    print(f"\n   Good Response:")
    print(f"   - Status: {status.value}")
    print(f"   - Score: {score:.1f}/100")
    print(f"   - Risk: {risk.value}")
    print(f"   - Findings: {findings}")

    # Test poor response
    poor_response = QuestionResponse(
        question_id=test_question.id,
        answer="No, MFA is not currently implemented.",
    )
    status, score, findings, risk = evaluator.evaluate_response(
        test_question, poor_response, "moderate"
    )
    print(f"\n   Poor Response:")
    print(f"   - Status: {status.value}")
    print(f"   - Score: {score:.1f}/100")
    print(f"   - Risk: {risk.value}")
    print(f"   - Findings: {findings}")

    # Test control mappings
    print("\n4. Testing Control Mappings...")
    mappings = loader.get_control_mappings("sig_lite", test_question.id)
    print(f"   ✓ Question {test_question.id} maps to SCF controls: {mappings}")

    # Test search
    print("\n5. Testing Question Search...")
    search_results = loader.search_questions("encryption", "sig_lite")
    print(f"   ✓ Found {len(search_results)} questions about 'encryption'")
    for q in search_results[:3]:
        print(f"   - {q.id}: {q.question_text[:60]}...")

    print("\n✅ All tests passed!")
    print("\n📝 Next Steps:")
    print("   1. Replace placeholder data with licensed content")
    print("   2. Run: python -m tprm_frameworks_mcp")
    print("   3. Add to MCP configuration")


if __name__ == "__main__":
    asyncio.run(test_basic_functionality())
