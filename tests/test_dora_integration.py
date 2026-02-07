"""
DORA Integration Tests

Tests for DORA (Digital Operational Resilience Act) questionnaire generation,
article tracking, compliance monitoring, and evidence requirements.
"""

import pytest
import json
from pathlib import Path
from datetime import datetime, timedelta


# Load DORA questionnaire data
DORA_DATA_PATH = Path(__file__).parent.parent / "src" / "tprm_frameworks_mcp" / "data" / "dora_ict_tpp.json"
SCF_MAPPINGS_PATH = Path(__file__).parent.parent / "src" / "tprm_frameworks_mcp" / "data" / "questionnaire-to-scf.json"


@pytest.fixture
def dora_data():
    """Load DORA questionnaire data."""
    with open(DORA_DATA_PATH) as f:
        return json.load(f)


@pytest.fixture
def scf_mappings():
    """Load SCF control mappings."""
    with open(SCF_MAPPINGS_PATH) as f:
        return json.load(f)


class TestDORAQuestionnaireGeneration:
    """Test DORA questionnaire structure and content."""

    def test_questionnaire_metadata(self, dora_data):
        """Test questionnaire metadata is complete."""
        metadata = dora_data["metadata"]

        assert metadata["name"] == "DORA ICT Third-Party Provider Assessment"
        assert metadata["version"] == "1.0"
        assert metadata["regulation"] == "EU 2022/2554"
        assert metadata["deadline"] == "2025-01-17"
        assert metadata["status"] == "production"
        assert metadata["total_questions"] == 72

        # Check focus articles
        assert "Article 28" in metadata["focus_articles"]
        assert "Article 29" in metadata["focus_articles"]
        assert "Article 30" in metadata["focus_articles"]

    def test_minimum_question_count(self, dora_data):
        """Test that questionnaire has at least 60 questions."""
        questions = dora_data["questions"]
        assert len(questions) >= 60, f"Expected at least 60 questions, got {len(questions)}"

    def test_all_questions_valid_structure(self, dora_data):
        """Test that all questions have required fields."""
        required_fields = [
            "id", "category", "subcategory", "question_text",
            "description", "expected_answer_type", "is_required",
            "weight", "regulatory_source", "regulatory_mappings",
            "scf_control_mappings", "risk_if_inadequate",
            "required_evidence", "evaluation_rubric"
        ]

        for question in dora_data["questions"]:
            for field in required_fields:
                assert field in question, f"Question {question.get('id', 'UNKNOWN')} missing field: {field}"

    def test_regulatory_source_structure(self, dora_data):
        """Test regulatory_source field structure."""
        for question in dora_data["questions"]:
            reg_source = question["regulatory_source"]

            assert "regulation" in reg_source
            assert "article" in reg_source
            assert "paragraph" in reg_source
            assert "requirement" in reg_source

            assert reg_source["regulation"] == "DORA"

    def test_question_id_format(self, dora_data):
        """Test question ID format matches DORA article structure."""
        questions = dora_data["questions"]

        # Check for proper ID format
        for question in questions:
            q_id = question["id"]
            assert q_id.startswith("DORA-"), f"Question ID {q_id} should start with 'DORA-'"

    def test_unique_question_ids(self, dora_data):
        """Test that all question IDs are unique."""
        questions = dora_data["questions"]
        question_ids = [q["id"] for q in questions]

        assert len(question_ids) == len(set(question_ids)), "Duplicate question IDs found"

    def test_evaluation_rubric_structure(self, dora_data):
        """Test evaluation rubric has correct structure."""
        for question in dora_data["questions"]:
            rubric = question["evaluation_rubric"]

            assert "acceptable" in rubric
            assert "partially_acceptable" in rubric
            assert "unacceptable" in rubric
            assert "required_keywords" in rubric
            assert "weight_adjustment" in rubric

            # Check that patterns are lists
            assert isinstance(rubric["acceptable"], list)
            assert isinstance(rubric["partially_acceptable"], list)
            assert isinstance(rubric["unacceptable"], list)
            assert isinstance(rubric["required_keywords"], list)


class TestDORAArticleTracking:
    """Test DORA article-level compliance tracking."""

    def test_article_28_coverage(self, dora_data):
        """Test coverage of Article 28 requirements."""
        article_28_questions = [
            q for q in dora_data["questions"]
            if q["regulatory_source"]["article"] == "28"
        ]

        # Article 28 has 4 main paragraphs
        # Should have questions covering each paragraph
        paragraphs = set(q["regulatory_source"]["paragraph"] for q in article_28_questions)

        assert "1" in paragraphs, "Missing Article 28(1) coverage"
        assert "2" in paragraphs, "Missing Article 28(2) coverage"
        assert "3" in paragraphs, "Missing Article 28(3) coverage"
        assert "4" in paragraphs, "Missing Article 28(4) coverage"

        # Should have at least 10 questions for Article 28
        assert len(article_28_questions) >= 10

    def test_article_29_coverage(self, dora_data):
        """Test coverage of Article 29 requirements."""
        article_29_questions = [
            q for q in dora_data["questions"]
            if q["regulatory_source"]["article"] == "29"
        ]

        # Article 29(1) has mandatory clauses (a)-(h)
        # Should have comprehensive coverage
        assert len(article_29_questions) >= 15, "Insufficient Article 29 coverage"

        # Check for specific mandatory clause coverage
        paragraphs = [q["regulatory_source"]["paragraph"] for q in article_29_questions]

        # Should cover Article 29(1) mandatory clauses
        assert any("1(a)" in p for p in paragraphs), "Missing Article 29(1)(a) - Service Description"
        assert any("1(b)" in p for p in paragraphs), "Missing Article 29(1)(b) - Data Locations"
        assert any("1(c)" in p for p in paragraphs), "Missing Article 29(1)(c) - SLAs"
        assert any("1(d)" in p for p in paragraphs), "Missing Article 29(1)(d) - Audit Rights"
        assert any("1(e)" in p for p in paragraphs), "Missing Article 29(1)(e) - Subcontracting"
        assert any("1(f)" in p for p in paragraphs), "Missing Article 29(1)(f) - Incident Notification"
        assert any("1(g)" in p for p in paragraphs), "Missing Article 29(1)(g) - Exit Clauses"
        assert any("1(h)" in p for p in paragraphs), "Missing Article 29(1)(h) - Data Security"

    def test_article_30_coverage(self, dora_data):
        """Test coverage of Article 30 requirements."""
        article_30_questions = [
            q for q in dora_data["questions"]
            if q["regulatory_source"]["article"] == "30"
        ]

        # Article 30 covers register of information
        # Should have questions on register maintenance and content
        assert len(article_30_questions) >= 8, "Insufficient Article 30 coverage"

        paragraphs = set(q["regulatory_source"]["paragraph"] for q in article_30_questions)

        assert "1" in paragraphs, "Missing Article 30(1) - Register Maintenance"
        assert "2" in paragraphs, "Missing Article 30(2) - Register Content"
        assert "3" in paragraphs, "Missing Article 30(3) - Register Updates"

    def test_all_articles_mapped(self, dora_data):
        """Test that all questions map to DORA articles."""
        for question in dora_data["questions"]:
            article = question["regulatory_source"]["article"]

            # Valid article numbers
            valid_articles = ["5", "6", "11", "18", "19", "26", "28", "29", "30", "31-40", "45", "General", "Integration"]

            assert article in valid_articles, f"Question {question['id']} has invalid article: {article}"


class TestDORADeadlineMonitoring:
    """Test DORA compliance deadline tracking."""

    def test_deadline_date(self, dora_data):
        """Test that deadline is correctly set to January 17, 2025."""
        deadline_str = dora_data["metadata"]["deadline"]
        deadline = datetime.strptime(deadline_str, "%Y-%m-%d").date()

        assert deadline.year == 2025
        assert deadline.month == 1
        assert deadline.day == 17

    def test_days_remaining_calculation(self, dora_data):
        """Test calculation of days remaining until DORA deadline."""
        deadline_str = dora_data["metadata"]["deadline"]
        deadline = datetime.strptime(deadline_str, "%Y-%m-%d").date()
        today = datetime.now().date()

        days_remaining = (deadline - today).days

        # This test will be relevant until the deadline
        if days_remaining > 0:
            print(f"Days remaining until DORA compliance deadline: {days_remaining}")
        else:
            print(f"DORA deadline passed {abs(days_remaining)} days ago")

    def test_critical_questions_identified(self, dora_data):
        """Test that critical risk questions are identified for priority remediation."""
        critical_questions = [
            q for q in dora_data["questions"]
            if q["risk_if_inadequate"] == "critical"
        ]

        # Should have substantial number of critical questions
        assert len(critical_questions) >= 20, "Expected at least 20 critical risk questions"

        # All critical questions should be required
        for q in critical_questions:
            assert q["is_required"], f"Critical question {q['id']} should be required"


class TestDORAEvidenceRequirements:
    """Test required evidence tracking."""

    def test_all_questions_have_evidence(self, dora_data):
        """Test that all questions specify required evidence."""
        for question in dora_data["questions"]:
            assert "required_evidence" in question
            assert isinstance(question["required_evidence"], list)
            assert len(question["required_evidence"]) > 0, f"Question {question['id']} has no evidence requirements"

    def test_evidence_types(self, dora_data):
        """Test that evidence requirements are categorized."""
        all_evidence = []

        for question in dora_data["questions"]:
            all_evidence.extend(question["required_evidence"])

        # Should have diverse evidence types
        unique_evidence = set(all_evidence)
        assert len(unique_evidence) >= 30, "Should have at least 30 unique evidence types"

        # Check for key evidence categories
        evidence_str = " ".join(all_evidence).lower()

        assert "policy" in evidence_str, "Missing policy evidence"
        assert "procedure" in evidence_str, "Missing procedure evidence"
        assert "certification" in evidence_str or "certificate" in evidence_str, "Missing certification evidence"
        assert "contract" in evidence_str or "agreement" in evidence_str, "Missing contractual evidence"

    def test_certification_evidence(self, dora_data):
        """Test that certification evidence is required where appropriate."""
        # Find questions related to certifications
        cert_questions = [
            q for q in dora_data["questions"]
            if "certification" in q["question_text"].lower() or "iso" in q["question_text"].lower()
        ]

        # These should require certification evidence
        for q in cert_questions:
            evidence_str = " ".join(q["required_evidence"]).lower()
            assert "certification" in evidence_str or "certificate" in evidence_str or "iso" in evidence_str


class TestDORASCFMappings:
    """Test DORA to SCF control mappings."""

    def test_dora_section_exists(self, scf_mappings):
        """Test that dora_ict_tpp section exists in SCF mappings."""
        assert "dora_ict_tpp" in scf_mappings, "Missing dora_ict_tpp section in SCF mappings"

    def test_all_questions_mapped(self, dora_data, scf_mappings):
        """Test that all DORA questions have SCF mappings."""
        dora_mappings = scf_mappings["dora_ict_tpp"]

        for question in dora_data["questions"]:
            q_id = question["id"]

            # Question should be in mappings
            assert q_id in dora_mappings, f"Question {q_id} not found in SCF mappings"

            # Should have at least one SCF control
            assert len(dora_mappings[q_id]) > 0, f"Question {q_id} has no SCF mappings"

    def test_scf_control_format(self, scf_mappings):
        """Test SCF control ID format."""
        dora_mappings = scf_mappings["dora_ict_tpp"]

        for q_id, controls in dora_mappings.items():
            for control in controls:
                # SCF controls are formatted as XXX-NN
                assert "-" in control, f"Invalid SCF control format: {control}"
                parts = control.split("-")
                assert len(parts) == 2, f"Invalid SCF control format: {control}"
                assert parts[0].isupper(), f"SCF control domain should be uppercase: {control}"
                assert parts[1].isdigit(), f"SCF control number should be numeric: {control}"

    def test_tpm_controls_coverage(self, scf_mappings):
        """Test that Third-Party Management (TPM) controls are heavily used."""
        dora_mappings = scf_mappings["dora_ict_tpp"]

        all_controls = []
        for controls in dora_mappings.values():
            all_controls.extend(controls)

        tpm_controls = [c for c in all_controls if c.startswith("TPM-")]

        # TPM controls should be prevalent in DORA mappings
        assert len(tpm_controls) >= 30, "Expected extensive TPM control usage for third-party management"

    def test_key_control_domains(self, scf_mappings):
        """Test that key SCF control domains are represented."""
        dora_mappings = scf_mappings["dora_ict_tpp"]

        all_controls = []
        for controls in dora_mappings.values():
            all_controls.extend(controls)

        control_domains = set(c.split("-")[0] for c in all_controls)

        # Key domains for DORA
        expected_domains = ["TPM", "GOV", "RSK", "BCD", "IRO", "DCH", "CPL", "MON"]

        for domain in expected_domains:
            assert domain in control_domains, f"Missing key control domain: {domain}"


class TestDORACompliance:
    """Test DORA-specific compliance features."""

    def test_article_28_mandatory_requirements(self, dora_data):
        """Test that Article 28 mandatory requirements are all marked required."""
        article_28_questions = [
            q for q in dora_data["questions"]
            if q["regulatory_source"]["article"] == "28"
        ]

        # All Article 28 core questions should be required
        core_questions = [q for q in article_28_questions if q["regulatory_source"]["paragraph"] in ["1", "2", "3", "4"]]

        for q in core_questions:
            assert q["is_required"], f"Article 28 question {q['id']} should be required"

    def test_article_29_mandatory_clauses(self, dora_data):
        """Test that Article 29(1) mandatory clause questions are required."""
        article_29_mandatory = [
            q for q in dora_data["questions"]
            if q["regulatory_source"]["article"] == "29" and q["regulatory_source"]["paragraph"].startswith("1(")
        ]

        # All Article 29(1) mandatory clauses should be required
        for q in article_29_mandatory:
            assert q["is_required"], f"Article 29(1) mandatory clause {q['id']} should be required"

    def test_supervisory_access_requirements(self, dora_data):
        """Test that supervisory access questions are present and critical."""
        # Find supervisory access questions (Article 29(5))
        supervisory_questions = [
            q for q in dora_data["questions"]
            if "supervisory" in q["question_text"].lower() and "authority" in q["question_text"].lower()
        ]

        assert len(supervisory_questions) >= 1, "Missing supervisory authority access questions"

        for q in supervisory_questions:
            assert q["risk_if_inadequate"] in ["critical", "high"], "Supervisory access should be high/critical risk"

    def test_exit_strategy_requirements(self, dora_data):
        """Test exit strategy requirements (Article 28(4) and 29(1)(g))."""
        exit_questions = [
            q for q in dora_data["questions"]
            if "exit" in q["question_text"].lower() or "transition" in q["question_text"].lower()
        ]

        assert len(exit_questions) >= 3, "Should have multiple exit strategy questions"

        # Exit strategy questions should be high criticality
        for q in exit_questions:
            if q["is_required"]:
                assert q["risk_if_inadequate"] in ["critical", "high"], f"Exit question {q['id']} should be high/critical risk"

    def test_subcontracting_requirements(self, dora_data):
        """Test subcontracting requirements (Article 29(1)(e) and Article 30(2)(f))."""
        subcontracting_questions = [
            q for q in dora_data["questions"]
            if "subcontract" in q["question_text"].lower()
        ]

        assert len(subcontracting_questions) >= 2, "Should have multiple subcontracting questions"

        # Check for prior approval requirement
        approval_found = any("approval" in q["question_text"].lower() for q in subcontracting_questions)
        assert approval_found, "Should have question about subcontracting approval"

        # Check for flow-down requirement
        flow_down_found = any("flow-down" in q["question_text"].lower() or "equivalent" in q["description"].lower() for q in subcontracting_questions)
        assert flow_down_found, "Should have question about subcontracting flow-down requirements"

    def test_incident_reporting_timelines(self, dora_data):
        """Test incident reporting timeline requirements (Article 19 and 29(1)(f))."""
        incident_questions = [
            q for q in dora_data["questions"]
            if "incident" in q["question_text"].lower()
        ]

        assert len(incident_questions) >= 3, "Should have multiple incident management questions"

        # Check for timeline-specific questions
        timeline_questions = [
            q for q in incident_questions
            if "timeline" in q["question_text"].lower() or "notification" in q["question_text"].lower()
        ]

        assert len(timeline_questions) >= 1, "Should have questions about incident notification timelines"


class TestDORAIntegration:
    """Test DORA integration with NIS2."""

    def test_nis2_crossreference(self, dora_data):
        """Test that DORA questions reference NIS2 where overlap exists."""
        nis2_references = []

        for question in dora_data["questions"]:
            for mapping in question["regulatory_mappings"]:
                if "NIS2" in mapping:
                    nis2_references.append(question["id"])

        # Should have some NIS2 cross-references
        assert len(nis2_references) >= 5, "Should have NIS2 cross-references for overlapping requirements"

    def test_integration_question_exists(self, dora_data):
        """Test that there's a question about DORA/NIS2 alignment."""
        integration_questions = [
            q for q in dora_data["questions"]
            if "nis2" in q["question_text"].lower() and "dora" in q["question_text"].lower()
        ]

        assert len(integration_questions) >= 1, "Should have question about DORA/NIS2 integration"


class TestDORAQuestionQuality:
    """Test quality and completeness of DORA questions."""

    def test_question_text_length(self, dora_data):
        """Test that question text is substantive."""
        for question in dora_data["questions"]:
            q_text = question["question_text"]
            assert len(q_text) >= 20, f"Question {question['id']} text too short: {q_text}"
            assert len(q_text) <= 500, f"Question {question['id']} text too long"

    def test_description_completeness(self, dora_data):
        """Test that descriptions provide context."""
        for question in dora_data["questions"]:
            desc = question["description"]
            assert len(desc) >= 30, f"Question {question['id']} description too short"

            # Description should reference DORA or provide regulatory context
            assert "DORA" in desc or "Article" in desc or "financial" in desc.lower(), \
                f"Question {question['id']} description lacks regulatory context"

    def test_weight_distribution(self, dora_data):
        """Test that question weights are appropriately distributed."""
        weights = [q["weight"] for q in dora_data["questions"]]

        # Weights should range from 1-10
        assert min(weights) >= 6, "Minimum weight should be at least 6"
        assert max(weights) <= 10, "Maximum weight should be 10"

        # Should have good distribution
        high_weight = len([w for w in weights if w >= 9])
        assert high_weight >= 20, "Should have at least 20 high-weight questions"

    def test_risk_levels_appropriate(self, dora_data):
        """Test that risk levels are appropriately assigned."""
        for question in dora_data["questions"]:
            risk = question["risk_if_inadequate"]
            weight = question["weight"]

            # High weight questions should have high/critical risk
            if weight >= 9:
                assert risk in ["high", "critical"], \
                    f"Question {question['id']} with weight {weight} should have high/critical risk"


def test_dora_questionnaire_loads():
    """Basic test that DORA questionnaire file loads correctly."""
    assert DORA_DATA_PATH.exists(), f"DORA data file not found at {DORA_DATA_PATH}"

    with open(DORA_DATA_PATH) as f:
        data = json.load(f)

    assert "metadata" in data
    assert "questions" in data
    assert len(data["questions"]) > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
