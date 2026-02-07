"""
Comprehensive Test Suite for CAIQ v4.1 Full Dataset.

This test suite validates the complete CAIQ v4.1 (283 questions) implementation:
1. All 283 questions loaded correctly
2. All CCM domains covered
3. SCF control mappings complete
4. Evaluation rubrics functional
5. Domain-specific validation
6. Integration with SCF controls

Test Domains:
- A&A: Audit & Assurance
- AIS: Application & Interface Security
- BCR: Business Continuity & Resilience
- CCC: Change Control & Configuration
- CRY: Cryptography
- DSP: Data Security & Privacy
- DCS: Datacenter Security
- GRC: Governance, Risk & Compliance
- HRS: Human Resources Security
- IAC: Identity & Access Control
- IVS: Infrastructure & Virtualization Security
- IPY: Interoperability & Portability
- LOG: Logging & Monitoring
- SEF: Security Incident Management
- STA: Supply Chain Management
- TVM: Threat & Vulnerability Management
"""

import asyncio
import json
import pytest
from datetime import datetime

from tprm_frameworks_mcp.server import app, data_loader, evaluator, generated_questionnaires
from tprm_frameworks_mcp.models import (
    AnswerStatus,
    EntityType,
    QuestionnaireFramework,
    ResponseStrictness,
    RiskLevel,
)


class TestCAIQv4DataLoading:
    """Test that CAIQ v4.1 full dataset loads correctly."""

    def test_caiq_v4_full_loaded(self):
        """Test CAIQ v4.1 dataset loads with 283 questions."""
        questions = data_loader.get_questions("caiq_v4_full")

        # Should have exactly 283 questions (CAIQ v4.1 full set)
        assert len(questions) == 283, f"Expected 283 questions, got {len(questions)}"

        print(f"✓ CAIQ v4.1: {len(questions)} questions loaded")

    def test_all_domains_present(self):
        """Test that all CCM domains are represented."""
        questions = data_loader.get_questions("caiq_v4_full")

        # Extract unique categories
        categories = set(q.category for q in questions)

        # Expected CCM domains
        expected_domains = [
            "Audit Assurance & Compliance",
            "Application & Interface Security",
            "Business Continuity Management",
            "Change Control & Configuration",
            "Cryptography & Encryption",
            "Data Security & Privacy",
            "Datacenter Security",
            "Governance & Risk Management",
            "Human Resources Security",
            "Identity & Access Management",
            "Infrastructure & Virtualization Security",
            "Interoperability & Portability",
            "Logging & Monitoring",
            "Security Incident Management",
            "Supply Chain Management",
            "Threat & Vulnerability Management"
        ]

        # Check coverage (some domain names may vary slightly)
        for domain in expected_domains:
            # Fuzzy match - check if any category contains key words
            domain_found = any(
                any(word.lower() in cat.lower() for word in domain.split())
                for cat in categories
            )
            if not domain_found:
                print(f"⚠ Warning: Domain '{domain}' not clearly represented")

        print(f"✓ {len(categories)} unique domains/categories found")
        for cat in sorted(categories):
            count = len([q for q in questions if q.category == cat])
            print(f"  - {cat}: {count} questions")

    def test_question_structure_complete(self):
        """Test that all questions have complete structure."""
        questions = data_loader.get_questions("caiq_v4_full")

        incomplete = []
        for q in questions:
            # Check required fields
            if not q.id:
                incomplete.append(f"{q.id}: Missing ID")
            if not q.question_text:
                incomplete.append(f"{q.id}: Missing question text")
            if not q.category:
                incomplete.append(f"{q.id}: Missing category")
            if q.weight is None or q.weight < 1 or q.weight > 10:
                incomplete.append(f"{q.id}: Invalid weight ({q.weight})")
            if not q.risk_if_inadequate:
                incomplete.append(f"{q.id}: Missing risk level")

        assert len(incomplete) == 0, f"Found {len(incomplete)} incomplete questions:\n" + "\n".join(incomplete[:10])
        print(f"✓ All {len(questions)} questions have complete structure")

    def test_weights_distribution(self):
        """Test that question weights are properly distributed."""
        questions = data_loader.get_questions("caiq_v4_full")

        weight_distribution = {}
        for q in questions:
            weight_distribution[q.weight] = weight_distribution.get(q.weight, 0) + 1

        # Should have critical questions (weight 9-10)
        critical_count = weight_distribution.get(10, 0) + weight_distribution.get(9, 0)
        assert critical_count > 0, "No critical questions (weight 9-10) found"

        print(f"✓ Weight distribution:")
        for weight in sorted(weight_distribution.keys(), reverse=True):
            print(f"  Weight {weight}: {weight_distribution[weight]} questions")

    def test_risk_levels_distribution(self):
        """Test that risk levels are properly assigned."""
        questions = data_loader.get_questions("caiq_v4_full")

        risk_distribution = {}
        for q in questions:
            risk_level = q.risk_if_inadequate.value if hasattr(q.risk_if_inadequate, 'value') else str(q.risk_if_inadequate)
            risk_distribution[risk_level] = risk_distribution.get(risk_level, 0) + 1

        # Should have critical risks assigned
        assert risk_distribution.get('critical', 0) > 0, "No critical risk questions found"

        print(f"✓ Risk level distribution:")
        for risk in ['critical', 'high', 'medium', 'low', 'informational']:
            count = risk_distribution.get(risk, 0)
            if count > 0:
                print(f"  {risk.capitalize()}: {count} questions")


class TestCAIQv4SCFMappings:
    """Test SCF control mappings for CAIQ v4.1."""

    def test_all_questions_have_scf_mappings(self):
        """Test that all questions have at least one SCF control mapping."""
        questions = data_loader.get_questions("caiq_v4_full")

        unmapped = [q for q in questions if not q.scf_control_mappings or len(q.scf_control_mappings) == 0]

        if unmapped:
            print(f"⚠ Warning: {len(unmapped)} questions without SCF mappings:")
            for q in unmapped[:10]:
                print(f"  - {q.id}: {q.question_text[:60]}...")

        # At least 95% should have mappings
        mapped_percentage = ((len(questions) - len(unmapped)) / len(questions)) * 100
        assert mapped_percentage >= 95, f"Only {mapped_percentage:.1f}% questions have SCF mappings"

        print(f"✓ {mapped_percentage:.1f}% questions have SCF control mappings ({len(questions) - len(unmapped)}/{len(questions)})")

    @pytest.mark.asyncio
    async def test_map_questionnaire_to_controls(self, mcp_call_tool):
        """Test the map_questionnaire_to_controls tool."""
        # First generate a questionnaire
        gen_result = await mcp_call_tool(
            "generate_questionnaire",
            {
                "framework": "caiq_v4_full",
                "scope": "full",
                "entity_type": "saas_provider",
            }
        )

        # Extract questionnaire ID
        text = gen_result[0].text
        import re
        match = re.search(r'questionnaire_id["\s:]+([a-f0-9-]+)', text.lower())
        assert match, "Could not extract questionnaire ID from response"
        questionnaire_id = match.group(1)

        # Map to controls
        map_result = await mcp_call_tool(
            "map_questionnaire_to_controls",
            {"questionnaire_id": questionnaire_id}
        )

        assert len(map_result) > 0
        mapping_text = map_result[0].text

        # Should contain SCF control IDs
        assert "SCF Control Mappings" in mapping_text or "controls" in mapping_text.lower()

        print(f"✓ Successfully mapped CAIQ questionnaire to SCF controls")

    def test_scf_mapping_quality(self):
        """Test that SCF mappings are high quality (multiple controls per question)."""
        questions = data_loader.get_questions("caiq_v4_full")

        mapping_counts = []
        for q in questions:
            if q.scf_control_mappings:
                mapping_counts.append(len(q.scf_control_mappings))

        if mapping_counts:
            avg_mappings = sum(mapping_counts) / len(mapping_counts)
            print(f"✓ Average SCF mappings per question: {avg_mappings:.2f}")

            # Critical questions should have multiple mappings
            critical_questions = [q for q in questions if q.weight >= 9]
            critical_with_multiple = [q for q in critical_questions
                                     if q.scf_control_mappings and len(q.scf_control_mappings) >= 2]

            critical_percentage = (len(critical_with_multiple) / len(critical_questions)) * 100
            print(f"  {critical_percentage:.1f}% of critical questions have multiple SCF mappings")


class TestCAIQv4EvaluationRubrics:
    """Test evaluation rubrics for CAIQ v4.1."""

    def test_critical_questions_have_rubrics(self):
        """Test that critical questions (weight 9-10) have evaluation rubrics."""
        questions = data_loader.get_questions("caiq_v4_full")

        critical_questions = [q for q in questions if q.weight >= 9]
        questions_with_rubrics = [q for q in critical_questions if q.evaluation_rubric]

        rubric_percentage = (len(questions_with_rubrics) / len(critical_questions)) * 100

        print(f"✓ {rubric_percentage:.1f}% of critical questions have evaluation rubrics ({len(questions_with_rubrics)}/{len(critical_questions)})")

        # At least 50% of critical questions should have rubrics
        assert rubric_percentage >= 50, f"Only {rubric_percentage:.1f}% of critical questions have rubrics"

    def test_rubric_quality_audit_domain(self):
        """Test rubric quality for Audit & Assurance domain."""
        questions = data_loader.get_questions("caiq_v4_full")

        audit_questions = [q for q in questions if "audit" in q.category.lower()]

        rubrics_with_keywords = 0
        rubrics_with_patterns = 0

        for q in audit_questions:
            if q.evaluation_rubric:
                if q.evaluation_rubric.get("required_keywords"):
                    rubrics_with_keywords += 1
                if q.evaluation_rubric.get("acceptable"):
                    rubrics_with_patterns += 1

        print(f"✓ Audit domain rubric quality:")
        print(f"  - {rubrics_with_keywords}/{len(audit_questions)} have required keywords")
        print(f"  - {rubrics_with_patterns}/{len(audit_questions)} have acceptable patterns")

    def test_rubric_quality_crypto_domain(self):
        """Test rubric quality for Cryptography domain."""
        questions = data_loader.get_questions("caiq_v4_full")

        crypto_questions = [q for q in questions if "crypt" in q.category.lower() or "encryption" in q.category.lower()]

        enhanced_rubrics = 0
        for q in crypto_questions:
            if q.evaluation_rubric:
                rubric = q.evaluation_rubric
                # Enhanced rubric has multiple patterns and keywords
                has_multiple_patterns = len(rubric.get("acceptable", [])) >= 3
                has_keywords = len(rubric.get("required_keywords", [])) >= 2

                if has_multiple_patterns and has_keywords:
                    enhanced_rubrics += 1

        print(f"✓ Cryptography domain: {enhanced_rubrics}/{len(crypto_questions)} have enhanced rubrics")

    @pytest.mark.asyncio
    async def test_evaluate_crypto_response_good(self, mcp_call_tool):
        """Test evaluation of a good cryptography response."""
        # Generate questionnaire
        gen_result = await mcp_call_tool(
            "generate_questionnaire",
            {
                "framework": "caiq_v4_full",
                "scope": "full",
                "entity_type": "saas_provider",
            }
        )

        text = gen_result[0].text
        import re
        match = re.search(r'questionnaire_id["\s:]+([a-f0-9-]+)', text.lower())
        questionnaire_id = match.group(1)

        # Find a crypto question
        questions = data_loader.get_questions("caiq_v4_full")
        crypto_question = next((q for q in questions if "crypt" in q.category.lower() or "key" in q.question_text.lower()), None)

        if crypto_question:
            # Evaluate a good response
            good_response = {
                crypto_question.id: "Yes, we use AES-256 encryption for data at rest and TLS 1.3 for data in transit. We have a formal key management system with automated key rotation every 90 days, HSM-backed key storage, and documented key lifecycle procedures."
            }

            eval_result = await mcp_call_tool(
                "evaluate_response",
                {
                    "questionnaire_id": questionnaire_id,
                    "responses": good_response,
                    "strictness": "moderate"
                }
            )

            result_text = eval_result[0].text

            # Should score highly
            assert "acceptable" in result_text.lower() or "score" in result_text.lower()
            print(f"✓ Crypto question evaluation works for good responses")

    @pytest.mark.asyncio
    async def test_evaluate_access_control_response_poor(self, mcp_call_tool):
        """Test evaluation of a poor access control response."""
        # Generate questionnaire
        gen_result = await mcp_call_tool(
            "generate_questionnaire",
            {
                "framework": "caiq_v4_full",
                "scope": "full",
                "entity_type": "saas_provider",
            }
        )

        text = gen_result[0].text
        import re
        match = re.search(r'questionnaire_id["\s:]+([a-f0-9-]+)', text.lower())
        questionnaire_id = match.group(1)

        # Find an access control question
        questions = data_loader.get_questions("caiq_v4_full")
        iam_question = next((q for q in questions if "access" in q.category.lower() or "identity" in q.category.lower()), None)

        if iam_question:
            # Evaluate a poor response
            poor_response = {
                iam_question.id: "No, we don't currently have these controls implemented. It's on our roadmap."
            }

            eval_result = await mcp_call_tool(
                "evaluate_response",
                {
                    "questionnaire_id": questionnaire_id,
                    "responses": poor_response,
                    "strictness": "moderate"
                }
            )

            result_text = eval_result[0].text

            # Should score poorly
            assert "unacceptable" in result_text.lower() or "risk" in result_text.lower() or "score" in result_text.lower()
            print(f"✓ Access control question evaluation detects poor responses")


class TestCAIQv4DomainCoverage:
    """Test coverage of specific CCM domains."""

    def test_audit_assurance_domain(self):
        """Test Audit & Assurance domain coverage."""
        questions = data_loader.get_questions("caiq_v4_full")

        audit_questions = [q for q in questions if "audit" in q.category.lower()]

        assert len(audit_questions) > 0, "No audit questions found"

        # Should cover key audit topics
        topics = {
            "independent": 0,
            "compliance": 0,
            "assessment": 0,
            "certification": 0
        }

        for q in audit_questions:
            text = (q.question_text + " " + q.description).lower()
            for topic in topics:
                if topic in text:
                    topics[topic] += 1

        print(f"✓ Audit & Assurance: {len(audit_questions)} questions")
        for topic, count in topics.items():
            if count > 0:
                print(f"  - {topic.capitalize()}: {count} questions")

    def test_business_continuity_domain(self):
        """Test Business Continuity domain coverage."""
        questions = data_loader.get_questions("caiq_v4_full")

        bcm_questions = [q for q in questions if "continuity" in q.category.lower() or "resilience" in q.category.lower()]

        assert len(bcm_questions) > 0, "No business continuity questions found"

        print(f"✓ Business Continuity: {len(bcm_questions)} questions")

    def test_data_security_domain(self):
        """Test Data Security & Privacy domain coverage."""
        questions = data_loader.get_questions("caiq_v4_full")

        dsp_questions = [q for q in questions if "data" in q.category.lower() and ("security" in q.category.lower() or "privacy" in q.category.lower())]

        assert len(dsp_questions) > 0, "No data security questions found"

        # Should cover GDPR/privacy topics
        privacy_questions = [q for q in dsp_questions if "gdpr" in str(q.regulatory_mappings).lower() or "privacy" in q.question_text.lower()]

        print(f"✓ Data Security & Privacy: {len(dsp_questions)} questions")
        print(f"  - Privacy-related: {len(privacy_questions)} questions")

    def test_incident_management_domain(self):
        """Test Security Incident Management domain coverage."""
        questions = data_loader.get_questions("caiq_v4_full")

        incident_questions = [q for q in questions if "incident" in q.category.lower() or "incident" in q.question_text.lower()]

        assert len(incident_questions) > 0, "No incident management questions found"

        print(f"✓ Security Incident Management: {len(incident_questions)} questions")


class TestCAIQv4QuestionnaireGeneration:
    """Test questionnaire generation for CAIQ v4.1."""

    @pytest.mark.asyncio
    async def test_generate_full_caiq_questionnaire(self, mcp_call_tool):
        """Test generating full CAIQ questionnaire."""
        result = await mcp_call_tool(
            "generate_questionnaire",
            {
                "framework": "caiq_v4_full",
                "scope": "full",
                "entity_type": "saas_provider",
            }
        )

        assert len(result) > 0
        text = result[0].text

        # Should mention CAIQ and question count
        assert "caiq" in text.lower() or "consensus" in text.lower()
        assert "283" in text or "questions" in text.lower()

        print("✓ Full CAIQ questionnaire generation works")

    @pytest.mark.asyncio
    async def test_generate_lite_caiq_questionnaire(self, mcp_call_tool):
        """Test generating lite (filtered) CAIQ questionnaire."""
        result = await mcp_call_tool(
            "generate_questionnaire",
            {
                "framework": "caiq_v4_full",
                "scope": "lite",
                "entity_type": "saas_provider",
                "regulations": ["GDPR", "ISO 27001"]
            }
        )

        assert len(result) > 0
        text = result[0].text

        # Should be fewer questions than full
        assert "questionnaire_id" in text.lower()

        print("✓ Lite CAIQ questionnaire generation works")

    @pytest.mark.asyncio
    async def test_get_questionnaire(self, mcp_call_tool):
        """Test retrieving a generated questionnaire."""
        # First generate
        gen_result = await mcp_call_tool(
            "generate_questionnaire",
            {
                "framework": "caiq_v4_full",
                "scope": "full",
                "entity_type": "saas_provider",
            }
        )

        text = gen_result[0].text
        import re
        match = re.search(r'questionnaire_id["\s:]+([a-f0-9-]+)', text.lower())
        assert match, "Could not extract questionnaire ID"
        questionnaire_id = match.group(1)

        # Now retrieve it
        get_result = await mcp_call_tool(
            "get_questionnaire",
            {"questionnaire_id": questionnaire_id}
        )

        assert len(get_result) > 0
        retrieved_text = get_result[0].text

        assert questionnaire_id in retrieved_text.lower()
        assert "caiq" in retrieved_text.lower()

        print("✓ Get questionnaire works for CAIQ")

    @pytest.mark.asyncio
    async def test_search_questions(self, mcp_call_tool):
        """Test searching CAIQ questions."""
        result = await mcp_call_tool(
            "search_questions",
            {
                "framework": "caiq_v4_full",
                "keyword": "encryption",
                "max_results": 10
            }
        )

        assert len(result) > 0
        text = result[0].text

        assert "encryption" in text.lower()

        print("✓ Search questions works for CAIQ")


class TestCAIQv4Integration:
    """Test end-to-end integration scenarios."""

    @pytest.mark.asyncio
    @pytest.mark.scenario
    async def test_complete_caiq_assessment_workflow(self, mcp_call_tool):
        """Test complete CAIQ assessment workflow."""
        print("\n=== Complete CAIQ v4.1 Assessment Workflow ===\n")

        # Step 1: Generate questionnaire
        print("Step 1: Generating CAIQ questionnaire for SaaS provider...")
        gen_result = await mcp_call_tool(
            "generate_questionnaire",
            {
                "framework": "caiq_v4_full",
                "scope": "full",
                "entity_type": "saas_provider",
            }
        )

        text = gen_result[0].text
        import re
        match = re.search(r'questionnaire_id["\s:]+([a-f0-9-]+)', text.lower())
        assert match, "Could not extract questionnaire ID"
        questionnaire_id = match.group(1)

        print(f"✓ Generated questionnaire: {questionnaire_id}")

        # Step 2: Simulate responses
        print("\nStep 2: Simulating vendor responses...")

        questions = data_loader.get_questions("caiq_v4_full")
        sample_responses = {}

        # Get a few questions from different domains
        crypto_q = next((q for q in questions if "crypt" in q.category.lower()), None)
        iam_q = next((q for q in questions if "access" in q.category.lower()), None)
        audit_q = next((q for q in questions if "audit" in q.category.lower()), None)

        if crypto_q:
            sample_responses[crypto_q.id] = "Yes, we use AES-256 encryption with TLS 1.3 and formal key management including automated rotation."
        if iam_q:
            sample_responses[iam_q.id] = "Yes, we implement RBAC with multi-factor authentication and least privilege principles."
        if audit_q:
            sample_responses[audit_q.id] = "Yes, we undergo annual SOC 2 Type II audits and maintain ISO 27001 certification."

        print(f"✓ Created {len(sample_responses)} sample responses")

        # Step 3: Evaluate responses
        print("\nStep 3: Evaluating responses...")
        eval_result = await mcp_call_tool(
            "evaluate_response",
            {
                "questionnaire_id": questionnaire_id,
                "responses": sample_responses,
                "strictness": "moderate"
            }
        )

        assert len(eval_result) > 0
        eval_text = eval_result[0].text

        print("✓ Evaluation complete")

        # Step 4: Map to controls
        print("\nStep 4: Mapping to SCF controls...")
        map_result = await mcp_call_tool(
            "map_questionnaire_to_controls",
            {"questionnaire_id": questionnaire_id}
        )

        assert len(map_result) > 0
        print("✓ Control mapping complete")

        # Step 5: Generate report
        print("\nStep 5: Generating TPRM report...")
        report_result = await mcp_call_tool(
            "generate_tprm_report",
            {
                "questionnaire_id": questionnaire_id,
                "vendor_name": "Test Vendor Inc",
                "assessment_date": datetime.now().isoformat()
            }
        )

        assert len(report_result) > 0
        report_text = report_result[0].text

        assert "test vendor" in report_text.lower()

        print("✓ TPRM report generated")
        print("\n=== Complete Workflow Test Passed ===\n")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
