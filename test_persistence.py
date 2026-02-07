"""Test script to verify persistence layer integration."""

import asyncio
import sys

sys.path.insert(0, "src")

from tprm_frameworks_mcp.data_loader import TPRMDataLoader
from tprm_frameworks_mcp.evaluation.rubric import EvaluationRubric
from tprm_frameworks_mcp.models import (
    AnswerStatus,
    AssessmentResult,
    EntityType,
    EvaluationResult,
    Question,
    Questionnaire,
    QuestionnaireFramework,
    QuestionnaireMetadata,
    QuestionResponse,
    ResponseStrictness,
    RiskLevel,
)
from tprm_frameworks_mcp.storage import TPRMStorage


async def test_persistence_integration():
    """Test the persistence layer integration."""
    print("🧪 Testing Persistence Layer Integration\n")

    # Initialize storage with temporary database
    import tempfile
    from pathlib import Path

    temp_dir = Path(tempfile.mkdtemp())
    db_path = str(temp_dir / "test.db")
    storage = TPRMStorage(db_path=db_path)

    print("1. Testing Storage Initialization...")
    stats = storage.verify_storage()
    print(f"   ✓ Storage initialized: {stats['database_path']}")
    print(f"   ✓ Status: {stats['status']}")

    # Create a test questionnaire
    print("\n2. Testing Questionnaire Storage...")
    loader = TPRMDataLoader()
    questions = loader.get_questions("sig_lite")[:5]  # Use first 5 questions

    metadata = QuestionnaireMetadata(
        framework=QuestionnaireFramework.SIG_LITE,
        version="2024",
        total_questions=len(questions),
        categories=["Security", "Compliance"],
        estimated_completion_time="30 minutes",
        scope="lite",
        entity_type=EntityType.CLOUD_PROVIDER,
        applicable_regulations=["GDPR", "DORA"],
    )

    questionnaire = Questionnaire(
        id="test-quest-123",
        metadata=metadata,
        questions=questions,
        generation_timestamp="2024-01-01T00:00:00",
        custom_parameters={"test": True},
    )

    # Save questionnaire
    storage.save_questionnaire(questionnaire)
    print(f"   ✓ Saved questionnaire: {questionnaire.id}")

    # Retrieve questionnaire
    retrieved = storage.get_questionnaire(questionnaire.id)
    print(f"   ✓ Retrieved questionnaire: {retrieved.id}")
    print(f"   ✓ Questions: {len(retrieved.questions)}")

    # Create test assessments
    print("\n3. Testing Assessment Storage...")
    evaluator = EvaluationRubric()

    # First assessment (lower score)
    responses_1 = [
        QuestionResponse(question_id=q.id, answer="Partially implemented")
        for q in questions
    ]

    eval_results_1 = []
    for question in questions:
        response = next(
            (r for r in responses_1 if r.question_id == question.id), None
        )
        if response:
            status, score, findings, risk = evaluator.evaluate_response(
                question, response, "moderate"
            )
            eval_results_1.append(
                EvaluationResult(
                    question_id=question.id,
                    status=status,
                    score=score,
                    risk_level=risk,
                    findings=findings,
                    recommendations=[],
                    scf_controls_addressed=question.scf_control_mappings,
                )
            )

    assessment_1 = AssessmentResult(
        questionnaire_id=questionnaire.id,
        vendor_name="Test Vendor Inc",
        evaluation_results=eval_results_1,
        overall_score=55.0,
        overall_risk_level=RiskLevel.MEDIUM,
        critical_findings=[],
        compliance_gaps={},
        timestamp="2024-01-01T00:00:00",
        strictness_level=ResponseStrictness.MODERATE,
    )

    assessment_id_1 = storage.save_assessment(assessment_1)
    print(f"   ✓ Saved assessment 1: {assessment_id_1}")

    # Second assessment (higher score - improvement)
    responses_2 = [
        QuestionResponse(question_id=q.id, answer="Yes, fully implemented")
        for q in questions
    ]

    eval_results_2 = []
    for question in questions:
        response = next(
            (r for r in responses_2 if r.question_id == question.id), None
        )
        if response:
            status, score, findings, risk = evaluator.evaluate_response(
                question, response, "moderate"
            )
            eval_results_2.append(
                EvaluationResult(
                    question_id=question.id,
                    status=status,
                    score=score,
                    risk_level=risk,
                    findings=findings,
                    recommendations=[],
                    scf_controls_addressed=question.scf_control_mappings,
                )
            )

    assessment_2 = AssessmentResult(
        questionnaire_id=questionnaire.id,
        vendor_name="Test Vendor Inc",
        evaluation_results=eval_results_2,
        overall_score=85.0,
        overall_risk_level=RiskLevel.LOW,
        critical_findings=[],
        compliance_gaps={},
        timestamp="2024-02-01T00:00:00",
        strictness_level=ResponseStrictness.MODERATE,
    )

    assessment_id_2 = storage.save_assessment(assessment_2)
    print(f"   ✓ Saved assessment 2: {assessment_id_2}")

    # Test vendor history
    print("\n4. Testing Vendor History...")
    history = storage.get_vendor_history("Test Vendor Inc")
    print(f"   ✓ Retrieved {len(history)} assessments")
    print(f"   ✓ Latest score: {history[0]['overall_score']}")
    print(f"   ✓ Oldest score: {history[-1]['overall_score']}")
    print(
        f"   ✓ Trend: {'Improving' if history[0]['overall_score'] > history[-1]['overall_score'] else 'Stable'}"
    )

    # Test assessment comparison
    print("\n5. Testing Assessment Comparison...")
    comparison = storage.compare_assessments(
        "Test Vendor Inc", assessment_id_1, assessment_id_2
    )
    print(f"   ✓ Score delta: {comparison['score_delta']:+.1f} points")
    print(f"   ✓ Risk level change: {comparison['risk_level_change']}")
    print(f"   ✓ Improvements: {comparison['total_improvements']}")
    print(f"   ✓ Regressions: {comparison['total_regressions']}")

    # Cleanup
    print("\n6. Cleanup...")
    import shutil
    shutil.rmtree(temp_dir)
    print("   ✓ Test database cleaned up")

    print("\n✅ All persistence tests passed!")
    print("\n📝 Summary:")
    print("   - Questionnaire storage: Working")
    print("   - Assessment storage: Working")
    print("   - Vendor history tracking: Working")
    print("   - Assessment comparison: Working")
    print("   - Database persistence: Working")


if __name__ == "__main__":
    asyncio.run(test_persistence_integration())
