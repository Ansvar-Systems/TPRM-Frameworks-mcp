"""
NIS2 Supply Chain Questionnaire Integration Tests

Tests for NIS2 questionnaire generation, article mapping, and DORA/NIS2 overlap detection.
"""

import json
import pytest
from pathlib import Path


class TestNIS2QuestionnaireStructure:
    """Test NIS2 questionnaire data structure and completeness."""

    @pytest.fixture
    def nis2_data(self):
        """Load NIS2 questionnaire data."""
        data_path = Path(__file__).parent.parent / "src" / "tprm_frameworks_mcp" / "data" / "nis2_supply_chain.json"
        with open(data_path) as f:
            return json.load(f)

    def test_metadata_present(self, nis2_data):
        """Test that metadata is complete."""
        assert "metadata" in nis2_data
        metadata = nis2_data["metadata"]

        assert metadata["name"] == "NIS2 Supply Chain Security Assessment"
        assert metadata["version"] == "1.0"
        assert metadata["regulation"] == "EU Directive 2022/2555"
        assert metadata["status"] == "production"
        assert metadata["compliance_deadline"] == "2024-10-17"

    def test_question_count(self, nis2_data):
        """Test that we have 70 NIS2 questions."""
        assert len(nis2_data["questions"]) == 70
        assert nis2_data["metadata"]["total_questions"] == 70

    def test_article_coverage(self, nis2_data):
        """Test that all NIS2 Articles 20-23 are covered."""
        questions = nis2_data["questions"]

        # Articles covered
        articles_covered = set()
        for q in questions:
            if "regulatory_source" in q:
                article = q["regulatory_source"]["article"]
                articles_covered.add(article)

        # Should cover Articles 20, 21, 22, 23
        assert "20" in articles_covered
        assert "21" in articles_covered
        assert "22" in articles_covered
        assert "23" in articles_covered

    def test_question_structure(self, nis2_data):
        """Test that each question has required fields."""
        required_fields = [
            "id", "category", "subcategory", "question_text",
            "description", "expected_answer_type", "is_required",
            "weight", "regulatory_mappings", "scf_control_mappings",
            "risk_if_inadequate", "evaluation_rubric"
        ]

        for question in nis2_data["questions"]:
            for field in required_fields:
                assert field in question, f"Question {question.get('id')} missing {field}"

    def test_regulatory_source_structure(self, nis2_data):
        """Test regulatory_source field structure."""
        for question in nis2_data["questions"]:
            if "regulatory_source" in question:
                source = question["regulatory_source"]
                assert "regulation" in source
                assert source["regulation"] == "NIS2"
                assert "article" in source
                assert "requirement" in source


class TestNIS2SCFMappings:
    """Test NIS2 SCF control mappings."""

    @pytest.fixture
    def scf_mappings(self):
        """Load SCF mappings."""
        data_path = Path(__file__).parent.parent / "src" / "tprm_frameworks_mcp" / "data" / "questionnaire-to-scf.json"
        with open(data_path) as f:
            return json.load(f)

    @pytest.fixture
    def nis2_data(self):
        """Load NIS2 questionnaire data."""
        data_path = Path(__file__).parent.parent / "src" / "tprm_frameworks_mcp" / "data" / "nis2_supply_chain.json"
        with open(data_path) as f:
            return json.load(f)

    def test_nis2_mappings_exist(self, scf_mappings):
        """Test that NIS2 SCF mappings exist."""
        assert "nis2_supply_chain" in scf_mappings

    def test_all_questions_mapped(self, nis2_data, scf_mappings):
        """Test that all NIS2 questions have SCF mappings."""
        nis2_mappings = scf_mappings["nis2_supply_chain"]

        for question in nis2_data["questions"]:
            question_id = question["id"]
            assert question_id in nis2_mappings, f"Question {question_id} not in SCF mappings"
            assert len(nis2_mappings[question_id]) > 0, f"Question {question_id} has no SCF controls"

    def test_scf_control_format(self, scf_mappings):
        """Test that SCF controls follow correct format."""
        nis2_mappings = scf_mappings["nis2_supply_chain"]

        # Valid SCF control patterns (e.g., GOV-01, TPM-02)
        import re
        scf_pattern = re.compile(r'^[A-Z]{3}-\d{2}$')

        for question_id, controls in nis2_mappings.items():
            for control in controls:
                assert scf_pattern.match(control), f"Invalid SCF control format: {control}"

    def test_key_nis2_controls_mapped(self, scf_mappings):
        """Test that key NIS2-specific controls are mapped."""
        nis2_mappings = scf_mappings["nis2_supply_chain"]

        # Flatten all controls
        all_controls = set()
        for controls in nis2_mappings.values():
            all_controls.update(controls)

        # Key controls for NIS2
        assert "IAC-09" in all_controls  # MFA
        assert "TPM-01" in all_controls  # Third-party management
        assert "IRO-08" in all_controls  # Incident reporting
        assert "NET-01" in all_controls  # Network security
        assert "PES-01" in all_controls  # Physical security


class TestDORANIS2Overlap:
    """Test DORA/NIS2 overlap analysis."""

    @pytest.fixture
    def overlap_data(self):
        """Load DORA/NIS2 overlap data."""
        data_path = Path(__file__).parent.parent / "src" / "tprm_frameworks_mcp" / "data" / "dora-nis2-overlap.json"
        with open(data_path) as f:
            return json.load(f)

    def test_overlap_structure(self, overlap_data):
        """Test overlap file structure."""
        assert "overlapping_requirements" in overlap_data
        assert "unique_to_dora" in overlap_data
        assert "unique_to_nis2" in overlap_data
        assert "combined_assessment_strategy" in overlap_data

    def test_overlapping_areas_defined(self, overlap_data):
        """Test that key overlapping areas are defined."""
        overlapping = overlap_data["overlapping_requirements"]

        key_areas = [
            "governance_and_oversight",
            "supply_chain_security",
            "incident_response_and_reporting",
            "business_continuity_and_disaster_recovery",
            "cybersecurity_risk_management"
        ]

        for area in key_areas:
            assert area in overlapping, f"Missing overlap area: {area}"
            assert "dora_articles" in overlapping[area]
            assert "nis2_articles" in overlapping[area]
            assert "scf_controls" in overlapping[area]

    def test_unique_dora_requirements(self, overlap_data):
        """Test unique DORA requirements are documented."""
        unique_dora = overlap_data["unique_to_dora"]

        expected_unique = [
            "ict_concentration_risk",
            "ict_third_party_service_provider_exit_strategies",
            "threat_led_penetration_testing"
        ]

        for item in expected_unique:
            assert item in unique_dora, f"Missing unique DORA requirement: {item}"

    def test_unique_nis2_requirements(self, overlap_data):
        """Test unique NIS2 requirements are documented."""
        unique_nis2 = overlap_data["unique_to_nis2"]

        expected_unique = [
            "multi_factor_authentication_mandatory",
            "vulnerability_disclosure",
            "secured_emergency_communications",
            "physical_and_environmental_security"
        ]

        for item in expected_unique:
            assert item in unique_nis2, f"Missing unique NIS2 requirement: {item}"

    def test_reporting_timelines_compared(self, overlap_data):
        """Test that incident reporting timelines are compared."""
        overlap = overlap_data["overlapping_requirements"]["incident_response_and_reporting"]

        assert "reporting_timelines" in overlap
        assert "dora_major_incidents" in overlap["reporting_timelines"]
        assert "nis2_significant_incidents" in overlap["reporting_timelines"]

        # DORA should have 4-hour initial notification
        assert "4 hours" in overlap["reporting_timelines"]["dora_major_incidents"]["initial"]

        # NIS2 should have 24-hour early warning
        assert "24 hours" in overlap["reporting_timelines"]["nis2_significant_incidents"]["early_warning"]


class TestNIS2QuestionCategories:
    """Test NIS2 question categorization by article."""

    @pytest.fixture
    def nis2_data(self):
        """Load NIS2 questionnaire data."""
        data_path = Path(__file__).parent.parent / "src" / "tprm_frameworks_mcp" / "data" / "nis2_supply_chain.json"
        with open(data_path) as f:
            return json.load(f)

    def test_article_20_questions(self, nis2_data):
        """Test Article 20 (Governance) questions."""
        article_20_questions = [q for q in nis2_data["questions"] if q["id"].startswith("NIS2-20")]

        # Should have at least 2 governance questions
        assert len(article_20_questions) >= 2

        # Check for management oversight and training
        ids = [q["id"] for q in article_20_questions]
        assert "NIS2-20.1" in ids  # Management oversight
        assert "NIS2-20.2" in ids  # Management training

    def test_article_21_questions(self, nis2_data):
        """Test Article 21 (Cybersecurity risk management) questions."""
        article_21_questions = [q for q in nis2_data["questions"] if q["id"].startswith("NIS2-21")]

        # Should have most questions (covering 21(1) and 21(2)(a-n))
        assert len(article_21_questions) >= 30

        # Key Article 21 requirements
        question_ids = {q["id"] for q in article_21_questions}

        # Article 21(2)(e) - MFA requirement
        assert any("21.2.e" in qid for qid in question_ids)

        # Article 21(2)(g) - Vulnerability management
        assert any("21.2.g" in qid for qid in question_ids)

    def test_article_22_questions(self, nis2_data):
        """Test Article 22 (Supply chain security) questions."""
        article_22_questions = [q for q in nis2_data["questions"] if q["id"].startswith("NIS2-22")]

        # Should have at least 5 supply chain questions
        assert len(article_22_questions) >= 5

        # Check for key supply chain topics
        categories = {q["subcategory"] for q in article_22_questions}
        assert "Supply Chain Risk Assessment" in categories
        assert "Supplier Security Requirements" in categories

    def test_article_23_questions(self, nis2_data):
        """Test Article 23 (Reporting obligations) questions."""
        article_23_questions = [q for q in nis2_data["questions"] if q["id"].startswith("NIS2-23")]

        # Should have at least 5 reporting questions
        assert len(article_23_questions) >= 5

        # Check for timeline-specific questions
        text_content = " ".join([q["question_text"] + q["description"] for q in article_23_questions])
        assert "24 hours" in text_content  # Early warning
        assert "72 hours" in text_content  # Full notification


class TestNIS2EvaluationRubrics:
    """Test NIS2 evaluation rubric completeness."""

    @pytest.fixture
    def nis2_data(self):
        """Load NIS2 questionnaire data."""
        data_path = Path(__file__).parent.parent / "src" / "tprm_frameworks_mcp" / "data" / "nis2_supply_chain.json"
        with open(data_path) as f:
            return json.load(f)

    def test_all_questions_have_rubrics(self, nis2_data):
        """Test that all questions have evaluation rubrics."""
        for question in nis2_data["questions"]:
            assert "evaluation_rubric" in question
            rubric = question["evaluation_rubric"]

            # Required rubric fields
            assert "acceptable" in rubric
            assert "partially_acceptable" in rubric
            assert "unacceptable" in rubric
            assert "required_keywords" in rubric
            assert "weight_adjustment" in rubric

            # Should have at least one pattern in each category
            assert len(rubric["acceptable"]) > 0
            assert len(rubric["unacceptable"]) > 0

    def test_mfa_question_rubric(self, nis2_data):
        """Test MFA question rubric (NIS2-specific requirement)."""
        mfa_question = next((q for q in nis2_data["questions"] if q["id"] == "NIS2-21.2.e"), None)
        assert mfa_question is not None

        rubric = mfa_question["evaluation_rubric"]

        # Should have MFA in keywords
        assert any("mfa" in kw.lower() or "multi-factor" in kw.lower() for kw in rubric["required_keywords"])

        # Should reject single-factor
        assert any("single.*factor" in pattern for pattern in rubric["unacceptable"])


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
