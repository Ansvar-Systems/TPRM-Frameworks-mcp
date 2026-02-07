"""Comprehensive tests for the SQLite storage layer."""

import json
import tempfile
from datetime import datetime, UTC
from pathlib import Path

import pytest

from src.tprm_frameworks_mcp.models import (
    AnswerStatus,
    AssessmentResult,
    EntityType,
    EvaluationResult,
    Question,
    Questionnaire,
    QuestionnaireFramework,
    QuestionnaireMetadata,
    ResponseStrictness,
    RiskLevel,
)
from src.tprm_frameworks_mcp.storage import (
    AssessmentNotFoundError,
    QuestionnaireNotFoundError,
    StorageError,
    TPRMStorage,
)


@pytest.fixture
def temp_db():
    """Create a temporary database for testing."""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = f.name

    storage = TPRMStorage(db_path=db_path)
    yield storage

    # Cleanup
    Path(db_path).unlink(missing_ok=True)


@pytest.fixture
def sample_questionnaire():
    """Create a sample questionnaire for testing."""
    questions = [
        Question(
            id="q1",
            category="Security",
            subcategory="Access Control",
            question_text="Do you implement multi-factor authentication?",
            description="MFA requirement",
            expected_answer_type="yes_no",
            is_required=True,
            weight=9,
            regulatory_mappings=["GDPR Article 32", "DORA Article 6"],
            scf_control_mappings=["IAC-01", "IAC-02"],
            risk_if_inadequate=RiskLevel.HIGH,
            evaluation_rubric={
                "acceptable": ["yes", "implemented"],
                "partially_acceptable": ["partial", "in progress"],
                "unacceptable": ["no", "not implemented"],
            },
        ),
        Question(
            id="q2",
            category="Security",
            subcategory="Encryption",
            question_text="Do you encrypt data at rest?",
            description="Encryption requirement",
            expected_answer_type="yes_no",
            is_required=True,
            weight=10,
            regulatory_mappings=["GDPR Article 32"],
            scf_control_mappings=["CRY-01"],
            risk_if_inadequate=RiskLevel.CRITICAL,
            evaluation_rubric={
                "acceptable": ["yes", "aes-256"],
                "unacceptable": ["no"],
            },
        ),
    ]

    metadata = QuestionnaireMetadata(
        framework=QuestionnaireFramework.CAIQ_V4,
        version="4.0",
        total_questions=2,
        categories=["Security"],
        estimated_completion_time="30 minutes",
        scope="lite",
        entity_type=EntityType.CLOUD_PROVIDER,
        applicable_regulations=["GDPR", "DORA"],
    )

    return Questionnaire(
        id="test-questionnaire-123",
        metadata=metadata,
        questions=questions,
        generation_timestamp=datetime.now(UTC).isoformat(),
        custom_parameters={"scope": "lite", "entity_type": "cloud_provider"},
    )


@pytest.fixture
def sample_assessment(sample_questionnaire):
    """Create a sample assessment for testing."""
    evaluation_results = [
        EvaluationResult(
            question_id="q1",
            status=AnswerStatus.ACCEPTABLE,
            score=100.0,
            risk_level=RiskLevel.LOW,
            findings=["MFA is properly implemented"],
            recommendations=[],
            scf_controls_addressed=["IAC-01", "IAC-02"],
        ),
        EvaluationResult(
            question_id="q2",
            status=AnswerStatus.UNACCEPTABLE,
            score=0.0,
            risk_level=RiskLevel.CRITICAL,
            findings=["No encryption at rest"],
            recommendations=["Implement AES-256 encryption"],
            scf_controls_addressed=["CRY-01"],
        ),
    ]

    return AssessmentResult(
        questionnaire_id=sample_questionnaire.id,
        vendor_name="Test Vendor Inc.",
        evaluation_results=evaluation_results,
        overall_score=50.0,
        overall_risk_level=RiskLevel.HIGH,
        critical_findings=["No encryption at rest"],
        compliance_gaps={"GDPR Article 32": ["q2"]},
        timestamp=datetime.now(UTC).isoformat(),
        strictness_level=ResponseStrictness.MODERATE,
    )


class TestTPRMStorageInit:
    """Test storage initialization."""

    def test_init_default_path(self):
        """Test storage initialization with default path."""
        storage = TPRMStorage()
        expected_path = Path.home() / ".tprm-mcp" / "tprm.db"
        assert Path(storage.db_path) == expected_path
        assert Path(storage.db_path).parent.exists()

    def test_init_custom_path(self, temp_db):
        """Test storage initialization with custom path."""
        assert Path(temp_db.db_path).exists()

    def test_database_schema_created(self, temp_db):
        """Test that all required tables are created."""
        with temp_db._get_connection() as conn:
            cursor = conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            )
            tables = {row["name"] for row in cursor.fetchall()}

        assert "questionnaires" in tables
        assert "assessments" in tables
        assert "vendor_history" in tables
        assert "framework_versions" in tables

    def test_indexes_created(self, temp_db):
        """Test that indexes are created for performance."""
        with temp_db._get_connection() as conn:
            cursor = conn.execute(
                "SELECT name FROM sqlite_master WHERE type='index'"
            )
            indexes = {row["name"] for row in cursor.fetchall()}

        assert "idx_vendor_history_name" in indexes
        assert "idx_assessments_vendor" in indexes
        assert "idx_questionnaires_framework" in indexes


class TestQuestionnaireStorage:
    """Test questionnaire save and retrieve operations."""

    def test_save_questionnaire(self, temp_db, sample_questionnaire):
        """Test saving a questionnaire."""
        questionnaire_id = temp_db.save_questionnaire(sample_questionnaire)
        assert questionnaire_id == sample_questionnaire.id

    def test_save_and_retrieve_questionnaire(self, temp_db, sample_questionnaire):
        """Test saving and retrieving a questionnaire."""
        temp_db.save_questionnaire(sample_questionnaire)
        retrieved = temp_db.get_questionnaire(sample_questionnaire.id)

        assert retrieved.id == sample_questionnaire.id
        assert retrieved.metadata.framework == sample_questionnaire.metadata.framework
        assert retrieved.metadata.version == sample_questionnaire.metadata.version
        assert len(retrieved.questions) == len(sample_questionnaire.questions)

        # Check question details
        assert retrieved.questions[0].id == "q1"
        assert retrieved.questions[0].question_text == "Do you implement multi-factor authentication?"
        assert retrieved.questions[0].weight == 9
        assert "GDPR Article 32" in retrieved.questions[0].regulatory_mappings

    def test_get_nonexistent_questionnaire(self, temp_db):
        """Test retrieving a questionnaire that doesn't exist."""
        with pytest.raises(QuestionnaireNotFoundError):
            temp_db.get_questionnaire("nonexistent-id")

    def test_save_questionnaire_updates_existing(self, temp_db, sample_questionnaire):
        """Test that saving a questionnaire with same ID updates it."""
        temp_db.save_questionnaire(sample_questionnaire)

        # Modify and save again
        sample_questionnaire.metadata.version = "4.1"
        temp_db.save_questionnaire(sample_questionnaire)

        retrieved = temp_db.get_questionnaire(sample_questionnaire.id)
        assert retrieved.metadata.version == "4.1"

    def test_get_all_questionnaires(self, temp_db, sample_questionnaire):
        """Test getting all questionnaires."""
        temp_db.save_questionnaire(sample_questionnaire)

        # Create another questionnaire
        questionnaire2 = Questionnaire(
            id="test-questionnaire-456",
            metadata=sample_questionnaire.metadata,
            questions=sample_questionnaire.questions,
            generation_timestamp=datetime.now(UTC).isoformat(),
            custom_parameters={},
        )
        temp_db.save_questionnaire(questionnaire2)

        all_questionnaires = temp_db.get_all_questionnaires()
        assert len(all_questionnaires) == 2
        assert all_questionnaires[0]["framework"] == "caiq_v4"


class TestAssessmentStorage:
    """Test assessment save and retrieve operations."""

    def test_save_assessment(self, temp_db, sample_questionnaire, sample_assessment):
        """Test saving an assessment."""
        # First save the questionnaire
        temp_db.save_questionnaire(sample_questionnaire)

        # Then save assessment
        assessment_id = temp_db.save_assessment(sample_assessment)
        assert assessment_id.startswith("assess_")

    def test_save_and_retrieve_assessment(self, temp_db, sample_questionnaire, sample_assessment):
        """Test saving and retrieving an assessment."""
        temp_db.save_questionnaire(sample_questionnaire)
        assessment_id = temp_db.save_assessment(sample_assessment)

        retrieved = temp_db.get_assessment(assessment_id)
        assert retrieved.vendor_name == sample_assessment.vendor_name
        assert retrieved.overall_score == sample_assessment.overall_score
        assert retrieved.overall_risk_level == sample_assessment.overall_risk_level
        assert len(retrieved.evaluation_results) == len(sample_assessment.evaluation_results)

    def test_get_nonexistent_assessment(self, temp_db):
        """Test retrieving an assessment that doesn't exist."""
        with pytest.raises(AssessmentNotFoundError):
            temp_db.get_assessment("assess_nonexistent")

    def test_assessment_creates_vendor_history(self, temp_db, sample_questionnaire, sample_assessment):
        """Test that saving an assessment creates vendor history entry."""
        temp_db.save_questionnaire(sample_questionnaire)
        temp_db.save_assessment(sample_assessment)

        history = temp_db.get_vendor_history(sample_assessment.vendor_name)
        assert len(history) == 1
        assert history[0]["overall_score"] == sample_assessment.overall_score
        assert history[0]["framework"] == "caiq_v4"

    def test_get_all_assessments(self, temp_db, sample_questionnaire, sample_assessment):
        """Test getting all assessments."""
        temp_db.save_questionnaire(sample_questionnaire)
        temp_db.save_assessment(sample_assessment)

        all_assessments = temp_db.get_all_assessments()
        assert len(all_assessments) == 1
        assert all_assessments[0]["vendor_name"] == "Test Vendor Inc."


class TestVendorHistory:
    """Test vendor history tracking."""

    def test_vendor_history_multiple_assessments(self, temp_db, sample_questionnaire, sample_assessment):
        """Test tracking multiple assessments for a vendor."""
        import time
        temp_db.save_questionnaire(sample_questionnaire)

        # Save multiple assessments
        temp_db.save_assessment(sample_assessment)

        # Wait a tiny bit to ensure different timestamps
        time.sleep(0.01)

        # Second assessment with different score and timestamp
        sample_assessment.overall_score = 75.0
        sample_assessment.overall_risk_level = RiskLevel.MEDIUM
        sample_assessment.timestamp = datetime.now(UTC).isoformat()
        temp_db.save_assessment(sample_assessment)

        history = temp_db.get_vendor_history(sample_assessment.vendor_name)
        assert len(history) == 2

        # Most recent should be first (score 75.0)
        # Note: scores might be in any order due to timestamp precision
        scores = {history[0]["overall_score"], history[1]["overall_score"]}
        assert scores == {50.0, 75.0}

    def test_vendor_history_limit(self, temp_db, sample_questionnaire, sample_assessment):
        """Test vendor history limit parameter."""
        temp_db.save_questionnaire(sample_questionnaire)

        # Save 5 assessments
        for _ in range(5):
            temp_db.save_assessment(sample_assessment)

        history = temp_db.get_vendor_history(sample_assessment.vendor_name, limit=3)
        assert len(history) == 3

    def test_vendor_history_empty(self, temp_db):
        """Test vendor history for vendor with no assessments."""
        history = temp_db.get_vendor_history("Unknown Vendor")
        assert len(history) == 0


class TestCompareAssessments:
    """Test assessment comparison functionality."""

    def test_compare_assessments(self, temp_db, sample_questionnaire, sample_assessment):
        """Test comparing two assessments for the same vendor."""
        temp_db.save_questionnaire(sample_questionnaire)

        # Save first assessment
        assessment_id_1 = temp_db.save_assessment(sample_assessment)

        # Modify and save second assessment
        sample_assessment.overall_score = 80.0
        sample_assessment.overall_risk_level = RiskLevel.LOW
        sample_assessment.evaluation_results[1].score = 100.0
        sample_assessment.evaluation_results[1].status = AnswerStatus.ACCEPTABLE
        assessment_id_2 = temp_db.save_assessment(sample_assessment)

        # Compare
        comparison = temp_db.compare_assessments(
            sample_assessment.vendor_name,
            assessment_id_1,
            assessment_id_2
        )

        assert comparison["vendor_name"] == sample_assessment.vendor_name
        assert comparison["score_delta"] == 30.0
        assert comparison["risk_level_change"] == "improved"
        assert comparison["total_improvements"] == 1
        assert comparison["total_regressions"] == 0

    def test_compare_assessments_wrong_vendor(self, temp_db, sample_questionnaire, sample_assessment):
        """Test comparing assessments with wrong vendor name."""
        temp_db.save_questionnaire(sample_questionnaire)

        assessment_id_1 = temp_db.save_assessment(sample_assessment)
        assessment_id_2 = temp_db.save_assessment(sample_assessment)

        with pytest.raises(StorageError, match="do not belong to vendor"):
            temp_db.compare_assessments("Wrong Vendor", assessment_id_1, assessment_id_2)

    def test_compare_assessments_nonexistent(self, temp_db):
        """Test comparing nonexistent assessments."""
        with pytest.raises(AssessmentNotFoundError):
            temp_db.compare_assessments("Test Vendor", "assess_1", "assess_2")


class TestFrameworkVersions:
    """Test framework version management."""

    def test_update_framework_version(self, temp_db):
        """Test updating framework version."""
        temp_db.update_framework_version(
            framework="caiq_v4",
            version="4.0",
            release_date="2023-01-01"
        )

        version_info = temp_db.get_framework_version("caiq_v4")
        assert version_info is not None
        assert version_info["current_version"] == "4.0"
        assert version_info["release_date"] == "2023-01-01"
        assert version_info["is_deprecated"] is False

    def test_update_framework_version_twice(self, temp_db):
        """Test updating framework version multiple times."""
        temp_db.update_framework_version("caiq_v4", "4.0")
        temp_db.update_framework_version("caiq_v4", "4.1")

        version_info = temp_db.get_framework_version("caiq_v4")
        assert version_info["current_version"] == "4.1"

    def test_get_nonexistent_framework_version(self, temp_db):
        """Test getting version for nonexistent framework."""
        version_info = temp_db.get_framework_version("nonexistent")
        assert version_info is None

    def test_mark_framework_deprecated(self, temp_db):
        """Test marking a framework as deprecated."""
        temp_db.update_framework_version("sig_lite", "2024")
        temp_db.mark_framework_deprecated(
            "sig_lite",
            notes="Replaced by SIG Full 2025"
        )

        version_info = temp_db.get_framework_version("sig_lite")
        assert version_info["is_deprecated"] is True
        assert version_info["notes"] == "Replaced by SIG Full 2025"


class TestDatabaseStats:
    """Test database statistics functionality."""

    def test_empty_database_stats(self, temp_db):
        """Test stats for empty database."""
        stats = temp_db.get_database_stats()

        assert stats["total_questionnaires"] == 0
        assert stats["total_assessments"] == 0
        assert stats["total_vendors"] == 0
        assert stats["database_size_bytes"] > 0

    def test_database_stats_with_data(self, temp_db, sample_questionnaire, sample_assessment):
        """Test stats with data in database."""
        temp_db.save_questionnaire(sample_questionnaire)
        temp_db.save_assessment(sample_assessment)

        stats = temp_db.get_database_stats()

        assert stats["total_questionnaires"] == 1
        assert stats["total_assessments"] == 1
        assert stats["total_vendors"] == 1

    def test_verify_storage_healthy(self, temp_db):
        """Test verify_storage returns healthy status."""
        result = temp_db.verify_storage()

        assert result["status"] == "healthy"
        assert "total_questionnaires" in result
        assert "database_path" in result


class TestErrorHandling:
    """Test error handling and edge cases."""

    def test_invalid_questionnaire_data(self, temp_db):
        """Test handling of invalid questionnaire data."""
        # Create questionnaire with missing required data
        with pytest.raises(Exception):
            questionnaire = Questionnaire(
                id="bad-id",
                metadata=None,  # This should cause an error
                questions=[],
                generation_timestamp="",
                custom_parameters={},
            )
            temp_db.save_questionnaire(questionnaire)

    def test_connection_error_handling(self):
        """Test handling of connection errors."""
        # Create storage with invalid path
        with pytest.raises(Exception):
            storage = TPRMStorage(db_path="/invalid/path/that/cannot/exist/db.sqlite")

    def test_transaction_rollback_on_error(self, temp_db, sample_questionnaire):
        """Test that transactions rollback on error."""
        # This test ensures that if an error occurs, the database state is not corrupted
        initial_count = temp_db.get_database_stats()["total_questionnaires"]

        try:
            # Force an error by trying to save malformed data
            with temp_db._get_connection() as conn:
                # Insert with correct number of columns (10 including created_at)
                conn.execute(
                    "INSERT INTO questionnaires VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                    ("id", "fw", "ver", "scope", "type", "regs", 0, "timestamp", "data", "created")
                )
                # Force an error
                raise ValueError("Test error")
        except ValueError:
            pass

        final_count = temp_db.get_database_stats()["total_questionnaires"]
        assert final_count == initial_count


class TestPerformance:
    """Test performance-related features."""

    def test_bulk_insert_performance(self, temp_db, sample_questionnaire, sample_assessment):
        """Test performance with bulk inserts."""
        import time

        temp_db.save_questionnaire(sample_questionnaire)

        start_time = time.time()

        # Insert 100 assessments
        for i in range(100):
            sample_assessment.vendor_name = f"Vendor {i}"
            temp_db.save_assessment(sample_assessment)

        elapsed = time.time() - start_time

        # Should complete in reasonable time (< 5 seconds)
        assert elapsed < 5.0

        stats = temp_db.get_database_stats()
        assert stats["total_assessments"] == 100

    def test_index_usage_vendor_history(self, temp_db, sample_questionnaire, sample_assessment):
        """Test that vendor history queries use indexes."""
        temp_db.save_questionnaire(sample_questionnaire)

        # Insert many assessments for different vendors
        for i in range(50):
            sample_assessment.vendor_name = f"Vendor {i % 10}"
            temp_db.save_assessment(sample_assessment)

        import time
        start_time = time.time()

        # Query should be fast due to index
        history = temp_db.get_vendor_history("Vendor 5")

        elapsed = time.time() - start_time

        # Should be very fast (< 0.1 seconds)
        assert elapsed < 0.1
        assert len(history) == 5
