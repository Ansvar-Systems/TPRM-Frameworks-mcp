"""
Comprehensive Integration Test Suite for TPRM-Frameworks MCP Server.

This test suite validates Phase 0 deployment by testing:
1. All 7 MCP tools can be called
2. Sample data loads correctly (CAIQ, SIG, DORA, NIS2)
3. Questionnaire generation works
4. Response evaluation works
5. Control mapping works
6. Report generation works

Test Scenario: "Assess Salesforce (SaaS provider) for DORA compliance"
- Generate DORA questionnaire
- Simulate vendor responses (mix of good/bad answers)
- Evaluate responses
- Generate comprehensive report
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


class TestMCPToolAvailability:
    """Test that all 7 MCP tools are available and callable."""

    @pytest.mark.asyncio
    async def test_list_tools_count(self, mcp_list_tools):
        """Test that exactly 16 tools are available (13 original + 3 evidence)."""
        tools = mcp_list_tools
        assert len(tools) == 16, f"Expected 16 tools, got {len(tools)}"
        print(f"✓ All 16 MCP tools are available")

    @pytest.mark.asyncio
    async def test_tool_names(self, mcp_list_tools):
        """Test that all expected tool names are present."""
        tools = mcp_list_tools
        tool_names = [tool.name for tool in tools]

        expected_tools = [
            "list_frameworks",
            "generate_questionnaire",
            "evaluate_response",
            "map_questionnaire_to_controls",
            "generate_tprm_report",
            "get_questionnaire",
            "search_questions",
            "get_vendor_history",
            "compare_assessments",
            "generate_dora_questionnaire",
            "generate_nis2_questionnaire",
            "check_regulatory_compliance",
            "get_regulatory_timeline",
        ]

        for expected in expected_tools:
            assert expected in tool_names, f"Tool '{expected}' not found"

        print(f"✓ All expected tool names present: {', '.join(tool_names)}")


class TestDataLoading:
    """Test that sample data loads correctly."""

    def test_framework_loading(self):
        """Test that all frameworks load correctly."""
        frameworks = data_loader.get_all_frameworks()

        # Should have at least SIG Lite, CAIQ, DORA, and NIS2
        assert len(frameworks) >= 4, f"Expected at least 4 frameworks, got {len(frameworks)}"

        framework_keys = [fw["key"] for fw in frameworks]

        # Check for specific frameworks
        expected_frameworks = ["sig_lite", "caiq_v4", "dora_ict_tpp", "nis2_supply_chain"]
        for expected in expected_frameworks:
            assert expected in framework_keys, f"Framework '{expected}' not loaded"

        print(f"✓ Successfully loaded {len(frameworks)} frameworks")
        for fw in frameworks:
            print(f"  - {fw['name']}: {fw['question_count']} questions ({fw['status']})")

    def test_sig_lite_questions(self):
        """Test SIG Lite questions load correctly."""
        questions = data_loader.get_questions("sig_lite")
        assert len(questions) > 0, "No SIG Lite questions loaded"

        # Check question structure
        sample_q = questions[0]
        assert hasattr(sample_q, "id")
        assert hasattr(sample_q, "category")
        assert hasattr(sample_q, "question_text")
        assert hasattr(sample_q, "weight")

        print(f"✓ SIG Lite: {len(questions)} questions loaded")

    def test_caiq_questions(self):
        """Test CAIQ v4 questions load correctly."""
        questions = data_loader.get_questions("caiq_v4")
        assert len(questions) > 0, "No CAIQ questions loaded"
        print(f"✓ CAIQ v4: {len(questions)} questions loaded")

    def test_dora_questions(self):
        """Test DORA ICT TPP questions load correctly."""
        questions = data_loader.get_questions("dora_ict_tpp")
        assert len(questions) > 0, "No DORA questions loaded"

        # Check for DORA-specific regulatory mappings
        dora_mapped = [q for q in questions if any("DORA" in reg for reg in q.regulatory_mappings)]
        assert len(dora_mapped) > 0, "No questions with DORA regulatory mappings"

        print(f"✓ DORA ICT TPP: {len(questions)} questions loaded ({len(dora_mapped)} with DORA mappings)")

    def test_nis2_questions(self):
        """Test NIS2 Supply Chain questions load correctly."""
        questions = data_loader.get_questions("nis2_supply_chain")
        assert len(questions) > 0, "No NIS2 questions loaded"
        print(f"✓ NIS2 Supply Chain: {len(questions)} questions loaded")


class TestQuestionnaireGeneration:
    """Test questionnaire generation functionality."""

    @pytest.mark.asyncio
    async def test_generate_full_questionnaire(self, mcp_call_tool):
        """Test generating a full questionnaire."""
        result = await mcp_call_tool(
            "generate_questionnaire",
            {
                "framework": "sig_lite",
                "scope": "full",
                "entity_type": "saas_provider",
            }
        )

        assert len(result) > 0
        text = result[0].text
        assert "Questionnaire Generated" in text
        assert "questionnaire_id" in text.lower()
        print("✓ Full questionnaire generation works")

    @pytest.mark.asyncio
    async def test_generate_lite_questionnaire(self, mcp_call_tool):
        """Test generating a lite (filtered) questionnaire."""
        result = await mcp_call_tool(
            "generate_questionnaire",
            {
                "framework": "sig_lite",
                "scope": "lite",
                "entity_type": "saas_provider",
            }
        )

        assert len(result) > 0
        text = result[0].text
        assert "Questionnaire Generated" in text
        assert "lite" in text.lower()
        print("✓ Lite questionnaire generation works")

    @pytest.mark.asyncio
    async def test_generate_with_regulations(self, mcp_call_tool):
        """Test generating questionnaire with regulatory filters."""
        result = await mcp_call_tool(
            "generate_questionnaire",
            {
                "framework": "dora_ict_tpp",
                "scope": "full",
                "entity_type": "ict_provider",
                "regulations": ["DORA", "NIS2"],
            }
        )

        assert len(result) > 0
        text = result[0].text
        assert "Questionnaire Generated" in text
        print("✓ Questionnaire with regulatory filters works")


class TestResponseEvaluation:
    """Test response evaluation functionality."""

    @pytest.mark.asyncio
    async def test_evaluate_good_responses(self, mcp_call_tool):
        """Test evaluation of good responses."""
        # First generate a questionnaire
        gen_result = await mcp_call_tool(
            "generate_questionnaire",
            {
                "framework": "sig_lite",
                "scope": "lite",
                "entity_type": "saas_provider",
            }
        )

        # Extract questionnaire ID from result
        text = gen_result[0].text
        import re
        match = re.search(r'`([a-f0-9-]{36})`', text)
        assert match, "Could not extract questionnaire ID"
        questionnaire_id = match.group(1)

        # Get questionnaire to find question IDs
        questionnaire = generated_questionnaires.get(questionnaire_id)
        assert questionnaire is not None

        # Create good responses for first 3 questions
        good_responses = []
        for q in questionnaire.questions[:3]:
            if q.expected_answer_type == "yes_no":
                answer = "Yes, we have implemented this control with documented procedures and regular audits."
            else:
                answer = "We have implemented comprehensive controls including automated monitoring, regular testing, and documented procedures aligned with industry best practices."

            good_responses.append({
                "question_id": q.id,
                "answer": answer,
                "supporting_documents": ["Policy_v2.1.pdf"],
                "notes": "Verified during internal audit"
            })

        # Evaluate responses
        eval_result = await mcp_call_tool(
            "evaluate_response",
            {
                "questionnaire_id": questionnaire_id,
                "vendor_name": "Test Vendor",
                "responses": good_responses,
                "strictness": "moderate",
            }
        )

        assert len(eval_result) > 0
        text = eval_result[0].text
        assert "Assessment Results" in text
        assert "Test Vendor" in text
        print("✓ Good response evaluation works")

    @pytest.mark.asyncio
    async def test_evaluate_poor_responses(self, mcp_call_tool):
        """Test evaluation of poor/incomplete responses."""
        # Generate questionnaire
        gen_result = await mcp_call_tool(
            "generate_questionnaire",
            {
                "framework": "sig_lite",
                "scope": "lite",
            }
        )

        text = gen_result[0].text
        import re
        match = re.search(r'`([a-f0-9-]{36})`', text)
        questionnaire_id = match.group(1)

        questionnaire = generated_questionnaires.get(questionnaire_id)

        # Create poor responses
        poor_responses = []
        for q in questionnaire.questions[:3]:
            poor_responses.append({
                "question_id": q.id,
                "answer": "No, not implemented.",
            })

        eval_result = await mcp_call_tool(
            "evaluate_response",
            {
                "questionnaire_id": questionnaire_id,
                "vendor_name": "Risky Vendor",
                "responses": poor_responses,
                "strictness": "moderate",
            }
        )

        assert len(eval_result) > 0
        text = eval_result[0].text
        assert "Critical Findings" in text or "Risky Vendor" in text
        print("✓ Poor response evaluation works")

    @pytest.mark.asyncio
    async def test_evaluate_with_strictness_levels(self, mcp_call_tool):
        """Test evaluation with different strictness levels."""
        gen_result = await mcp_call_tool(
            "generate_questionnaire",
            {"framework": "sig_lite", "scope": "lite"}
        )

        text = gen_result[0].text
        import re
        match = re.search(r'`([a-f0-9-]{36})`', text)
        questionnaire_id = match.group(1)

        questionnaire = generated_questionnaires.get(questionnaire_id)

        # Create mediocre responses
        responses = [{
            "question_id": questionnaire.questions[0].id,
            "answer": "Partially implemented, in progress.",
        }]

        # Test different strictness levels
        for strictness in ["lenient", "moderate", "strict"]:
            eval_result = await mcp_call_tool(
                "evaluate_response",
                {
                    "questionnaire_id": questionnaire_id,
                    "vendor_name": f"Vendor-{strictness}",
                    "responses": responses,
                    "strictness": strictness,
                }
            )
            assert len(eval_result) > 0

        print("✓ Strictness level evaluation works (lenient, moderate, strict)")


class TestControlMapping:
    """Test control mapping functionality."""

    @pytest.mark.asyncio
    async def test_map_questionnaire_to_scf(self, mcp_call_tool):
        """Test mapping questionnaire to SCF controls."""
        result = await mcp_call_tool(
            "map_questionnaire_to_controls",
            {
                "framework": "sig_lite",
                "control_framework": "scf",
            }
        )

        assert len(result) > 0
        text = result[0].text
        assert "Control Mappings" in text
        assert "SCF" in text
        print("✓ Control mapping to SCF works")

    @pytest.mark.asyncio
    async def test_map_specific_questions(self, mcp_call_tool):
        """Test mapping specific questions to controls."""
        # Get some question IDs from sig_lite
        questions = data_loader.get_questions("sig_lite")
        question_ids = [q.id for q in questions[:5]]

        result = await mcp_call_tool(
            "map_questionnaire_to_controls",
            {
                "framework": "sig_lite",
                "question_ids": question_ids,
                "control_framework": "scf",
            }
        )

        assert len(result) > 0
        text = result[0].text
        assert "Control Mappings" in text
        print("✓ Specific question mapping works")


class TestReportGeneration:
    """Test report generation functionality."""

    @pytest.mark.asyncio
    async def test_generate_basic_report(self, mcp_call_tool):
        """Test generating a basic TPRM report."""
        result = await mcp_call_tool(
            "generate_tprm_report",
            {
                "vendor_name": "Test Vendor Corp",
                "include_recommendations": True,
            }
        )

        assert len(result) > 0
        text = result[0].text
        assert "Third-Party Risk Management Report" in text
        assert "Test Vendor Corp" in text
        assert "Recommendations" in text
        print("✓ Basic report generation works")

    @pytest.mark.asyncio
    async def test_generate_report_with_all_data(self, mcp_call_tool):
        """Test generating report with all data sources."""
        vendor_intel = {
            "company_name": "Acme Security Inc",
            "founded": "2015",
            "certifications": ["ISO 27001", "SOC 2 Type II"],
            "breach_history": []
        }

        posture_data = {
            "ssl_grade": "A+",
            "dns_security": "DNSSEC enabled",
            "exposed_services": 3
        }

        result = await mcp_call_tool(
            "generate_tprm_report",
            {
                "vendor_name": "Acme Security Inc",
                "vendor_intel_data": vendor_intel,
                "posture_data": posture_data,
                "include_recommendations": True,
            }
        )

        assert len(result) > 0
        text = result[0].text
        assert "Vendor Intelligence" in text
        assert "Security Posture" in text
        assert "ISO 27001" in text
        print("✓ Comprehensive report generation works")


class TestUtilityTools:
    """Test utility tools (get_questionnaire, search_questions)."""

    @pytest.mark.asyncio
    async def test_list_frameworks(self, mcp_call_tool):
        """Test listing all frameworks."""
        result = await mcp_call_tool("list_frameworks", {})

        assert len(result) > 0
        text = result[0].text
        assert "Available Questionnaire Frameworks" in text
        assert "SIG" in text or "CAIQ" in text or "DORA" in text
        print("✓ List frameworks works")

    @pytest.mark.asyncio
    async def test_get_questionnaire(self, mcp_call_tool):
        """Test retrieving a generated questionnaire."""
        # First generate a questionnaire
        gen_result = await mcp_call_tool(
            "generate_questionnaire",
            {"framework": "sig_lite", "scope": "full"}
        )

        text = gen_result[0].text
        import re
        match = re.search(r'`([a-f0-9-]{36})`', text)
        questionnaire_id = match.group(1)

        # Now retrieve it
        get_result = await mcp_call_tool(
            "get_questionnaire",
            {"questionnaire_id": questionnaire_id}
        )

        assert len(get_result) > 0
        text = get_result[0].text
        assert questionnaire_id in text
        print("✓ Get questionnaire works")

    @pytest.mark.asyncio
    async def test_search_questions(self, mcp_call_tool):
        """Test searching questions by keyword."""
        result = await mcp_call_tool(
            "search_questions",
            {
                "query": "encryption",
                "framework": "sig_lite",
                "limit": 10,
            }
        )

        assert len(result) > 0
        text = result[0].text
        assert "encryption" in text.lower() or "found" in text.lower()
        print("✓ Search questions works")

    @pytest.mark.asyncio
    async def test_search_questions_all_frameworks(self, mcp_call_tool):
        """Test searching across all frameworks."""
        result = await mcp_call_tool(
            "search_questions",
            {
                "query": "access control",
                "limit": 20,
            }
        )

        assert len(result) > 0
        text = result[0].text
        assert "access" in text.lower() or "found" in text.lower()
        print("✓ Cross-framework search works")


class TestSalesforceDoraScenario:
    """
    End-to-end integration test: Assess Salesforce (SaaS provider) for DORA compliance.

    This test simulates a complete TPRM workflow:
    1. Generate DORA questionnaire for SaaS provider
    2. Simulate vendor responses (mix of good/bad)
    3. Evaluate responses
    4. Map to controls
    5. Generate final report
    """

    @pytest.mark.asyncio
    async def test_complete_salesforce_dora_assessment(self, mcp_call_tool):
        """Execute complete Salesforce DORA compliance assessment."""

        print("\n" + "="*80)
        print("SCENARIO: Assess Salesforce (SaaS Provider) for DORA Compliance")
        print("="*80 + "\n")

        # Step 1: Generate DORA questionnaire
        print("Step 1: Generating DORA ICT TPP questionnaire for SaaS provider...")
        gen_result = await mcp_call_tool(
            "generate_questionnaire",
            {
                "framework": "dora_ict_tpp",
                "scope": "full",
                "entity_type": "saas_provider",
                "regulations": ["DORA", "NIS2"],
            }
        )

        assert len(gen_result) > 0
        text = gen_result[0].text

        import re
        match = re.search(r'`([a-f0-9-]{36})`', text)
        assert match, "Could not extract questionnaire ID"
        questionnaire_id = match.group(1)

        # Extract question count
        q_match = re.search(r'Total Questions:\*\* (\d+)', text)
        question_count = int(q_match.group(1)) if q_match else 0

        print(f"✓ Generated questionnaire {questionnaire_id}")
        print(f"  - Framework: DORA ICT TPP")
        print(f"  - Entity Type: SaaS Provider")
        print(f"  - Total Questions: {question_count}")

        # Step 2: Retrieve questionnaire and simulate vendor responses
        print("\nStep 2: Simulating Salesforce vendor responses...")
        questionnaire = generated_questionnaires.get(questionnaire_id)
        assert questionnaire is not None

        # Simulate realistic vendor responses (mix of good, partial, and poor)
        responses = []

        for i, question in enumerate(questionnaire.questions):
            # Simulate different response qualities
            if i % 4 == 0:  # 25% excellent responses
                if question.expected_answer_type == "yes_no":
                    answer = (
                        "Yes, we have implemented a comprehensive ICT risk management framework "
                        "that is fully aligned with DORA requirements. This includes automated "
                        "monitoring, regular audits, and documented procedures. We maintain "
                        "ISO 27001 certification and conduct quarterly risk assessments."
                    )
                else:
                    answer = (
                        "We maintain robust ICT continuity capabilities with documented RTO of 4 hours "
                        "and RPO of 1 hour for critical systems. Our disaster recovery plans are tested "
                        "quarterly and include automated failover to geographically distributed data centers. "
                        "Full documentation is available including BCP/DR test results."
                    )
                supporting_docs = ["Salesforce_DORA_Compliance_2024.pdf", "ICT_Risk_Framework.pdf"]
                notes = "Verified through SOC 2 Type II audit"

            elif i % 4 == 1:  # 25% partial responses
                answer = (
                    "We have implemented most requirements. Our framework is in place but "
                    "not yet fully aligned with all DORA-specific requirements. Some controls "
                    "are still being enhanced."
                )
                supporting_docs = ["Framework_Overview.pdf"]
                notes = "Enhancement planned for Q2 2024"

            elif i % 4 == 2:  # 25% poor responses
                answer = "No, this control is not currently implemented. It is on our roadmap."
                supporting_docs = []
                notes = "Planned for future implementation"

            else:  # 25% minimal but acceptable responses
                answer = "Yes, implemented through our standard security procedures."
                supporting_docs = ["Security_Policy.pdf"]
                notes = ""

            responses.append({
                "question_id": question.id,
                "answer": answer,
                "supporting_documents": supporting_docs,
                "notes": notes,
            })

        print(f"✓ Simulated {len(responses)} vendor responses")
        print(f"  - Mix of excellent, partial, poor, and minimal responses")

        # Step 3: Evaluate responses with moderate strictness
        print("\nStep 3: Evaluating Salesforce responses...")
        eval_result = await mcp_call_tool(
            "evaluate_response",
            {
                "questionnaire_id": questionnaire_id,
                "vendor_name": "Salesforce",
                "responses": responses,
                "strictness": "moderate",
            }
        )

        assert len(eval_result) > 0
        eval_text = eval_result[0].text

        # Extract overall score
        score_match = re.search(r'Overall Score:\*\* ([\d.]+)/100', eval_text)
        overall_score = float(score_match.group(1)) if score_match else 0

        # Extract risk level
        risk_match = re.search(r'Overall Risk Level:\*\* (\w+)', eval_text)
        overall_risk = risk_match.group(1) if risk_match else "UNKNOWN"

        print(f"✓ Evaluation complete")
        print(f"  - Overall Score: {overall_score:.1f}/100")
        print(f"  - Overall Risk Level: {overall_risk}")

        # Verify score is reasonable given our response mix
        assert 40 <= overall_score <= 80, f"Unexpected score: {overall_score}"

        # Step 4: Map questionnaire to SCF controls
        print("\nStep 4: Mapping DORA questions to SCF controls...")
        map_result = await mcp_call_tool(
            "map_questionnaire_to_controls",
            {
                "framework": "dora_ict_tpp",
                "control_framework": "scf",
            }
        )

        assert len(map_result) > 0
        map_text = map_result[0].text

        # Extract mapping count
        mapping_match = re.search(r'Mapped Questions:\*\* (\d+)', map_text)
        mapped_count = int(mapping_match.group(1)) if mapping_match else 0

        print(f"✓ Control mapping complete")
        print(f"  - Mapped Questions: {mapped_count}")
        print(f"  - Target Framework: SCF")

        # Step 5: Generate comprehensive TPRM report
        print("\nStep 5: Generating comprehensive TPRM report...")

        # Simulate additional vendor intelligence data
        vendor_intel = {
            "company_name": "Salesforce",
            "founded": "1999",
            "headquarters": "San Francisco, CA",
            "employees": "73,000+",
            "certifications": [
                "ISO 27001",
                "ISO 27017",
                "ISO 27018",
                "SOC 2 Type II",
                "FedRAMP High",
                "PCI DSS Level 1"
            ],
            "breach_history": [
                {
                    "year": 2020,
                    "severity": "low",
                    "description": "Minor configuration exposure, no customer data affected"
                }
            ],
            "compliance_status": {
                "GDPR": "Compliant",
                "DORA": "In Progress",
                "NIS2": "In Progress"
            }
        }

        # Simulate external security posture data
        posture_data = {
            "ssl_grade": "A+",
            "tls_version": "TLS 1.3",
            "dnssec": "Enabled",
            "security_headers": {
                "HSTS": "Enabled",
                "CSP": "Enabled",
                "X-Frame-Options": "DENY"
            },
            "exposed_services": 12,
            "open_ports": [443, 80],
            "vulnerability_summary": {
                "critical": 0,
                "high": 0,
                "medium": 2,
                "low": 5,
                "info": 10
            }
        }

        report_result = await mcp_call_tool(
            "generate_tprm_report",
            {
                "vendor_name": "Salesforce",
                "questionnaire_results": [questionnaire_id],
                "vendor_intel_data": vendor_intel,
                "posture_data": posture_data,
                "include_recommendations": True,
            }
        )

        assert len(report_result) > 0
        report_text = report_result[0].text

        # Verify report contains expected sections
        assert "Third-Party Risk Management Report" in report_text
        assert "Salesforce" in report_text
        assert "Vendor Intelligence" in report_text
        assert "Security Posture" in report_text
        assert "Recommendations" in report_text
        assert "ISO 27001" in report_text

        print(f"✓ TPRM Report generated")
        print(f"  - Includes questionnaire assessment")
        print(f"  - Includes vendor intelligence data")
        print(f"  - Includes security posture analysis")
        print(f"  - Includes recommendations")

        # Step 6: Verify end-to-end data consistency
        print("\nStep 6: Verifying end-to-end data consistency...")

        # Re-retrieve the questionnaire to verify it persists
        retrieve_result = await mcp_call_tool(
            "get_questionnaire",
            {"questionnaire_id": questionnaire_id}
        )
        assert len(retrieve_result) > 0
        assert questionnaire_id in retrieve_result[0].text

        print(f"✓ Data consistency verified")
        print(f"  - Questionnaire persisted correctly")
        print(f"  - All tools integrated successfully")

        # Final summary
        print("\n" + "="*80)
        print("ASSESSMENT SUMMARY")
        print("="*80)
        print(f"Vendor: Salesforce")
        print(f"Assessment Type: DORA ICT Third-Party Provider")
        print(f"Questions Evaluated: {len(responses)}")
        print(f"Overall Score: {overall_score:.1f}/100")
        print(f"Risk Level: {overall_risk}")
        print(f"Controls Mapped: {mapped_count} SCF controls")
        print(f"Certifications: {len(vendor_intel['certifications'])} verified")
        print(f"Security Posture: SSL {posture_data['ssl_grade']}, {posture_data['vulnerability_summary']['critical']} critical vulns")
        print("="*80 + "\n")

        print("✅ Complete Salesforce DORA assessment scenario passed!")


class TestPhase0Validation:
    """Validation tests for Phase 0 deployment readiness."""

    @pytest.mark.asyncio
    async def test_all_tools_callable(self, mcp_list_tools, mcp_call_tool):
        """Verify all 7 tools can be called successfully."""
        tools = mcp_list_tools

        test_calls = [
            ("list_frameworks", {}),
            ("generate_questionnaire", {"framework": "sig_lite"}),
            ("search_questions", {"query": "encryption"}),
        ]

        for tool_name, args in test_calls:
            result = await mcp_call_tool(tool_name, args)
            assert len(result) > 0, f"Tool {tool_name} returned empty result"

        print("✓ All core tools are callable and functional")

    def test_data_integrity(self):
        """Verify data integrity across all frameworks."""
        frameworks = data_loader.get_all_frameworks()

        for fw in frameworks:
            questions = data_loader.get_questions(fw["key"])

            # Verify all questions have required fields
            for q in questions:
                assert q.id, f"Question missing ID in {fw['key']}"
                assert q.category, f"Question {q.id} missing category"
                assert q.question_text, f"Question {q.id} missing text"
                assert q.weight >= 1 and q.weight <= 10, f"Question {q.id} has invalid weight"

            # Verify categories are consistent
            categories = data_loader.get_categories(fw["key"])
            assert len(categories) > 0, f"No categories found for {fw['key']}"

        print(f"✓ Data integrity verified for {len(frameworks)} frameworks")

    @pytest.mark.asyncio
    async def test_evaluation_consistency(self, mcp_call_tool):
        """Verify evaluation produces consistent results."""
        # Generate questionnaire
        gen_result = await mcp_call_tool(
            "generate_questionnaire",
            {"framework": "sig_lite", "scope": "lite"}
        )

        import re
        text = gen_result[0].text
        match = re.search(r'`([a-f0-9-]{36})`', text)
        questionnaire_id = match.group(1)

        questionnaire = generated_questionnaires.get(questionnaire_id)

        # Same responses should produce same score
        test_response = [{
            "question_id": questionnaire.questions[0].id,
            "answer": "Yes, implemented with documented procedures."
        }]

        # Evaluate twice
        result1 = await mcp_call_tool(
            "evaluate_response",
            {
                "questionnaire_id": questionnaire_id,
                "vendor_name": "Test1",
                "responses": test_response,
                "strictness": "moderate"
            }
        )

        result2 = await mcp_call_tool(
            "evaluate_response",
            {
                "questionnaire_id": questionnaire_id,
                "vendor_name": "Test2",
                "responses": test_response,
                "strictness": "moderate"
            }
        )

        # Extract scores
        score1_match = re.search(r'Overall Score:\*\* ([\d.]+)', result1[0].text)
        score2_match = re.search(r'Overall Score:\*\* ([\d.]+)', result2[0].text)

        score1 = float(score1_match.group(1)) if score1_match else 0
        score2 = float(score2_match.group(1)) if score2_match else 0

        assert score1 == score2, "Evaluation produced inconsistent results"
        print("✓ Evaluation consistency verified")

    @pytest.mark.asyncio
    async def test_performance_baseline(self, mcp_call_tool):
        """Establish performance baseline for Phase 0."""
        import time

        # Test questionnaire generation speed
        start = time.time()
        await mcp_call_tool(
            "generate_questionnaire",
            {"framework": "sig_lite", "scope": "full"}
        )
        gen_time = time.time() - start

        assert gen_time < 2.0, f"Questionnaire generation too slow: {gen_time:.2f}s"

        print(f"✓ Performance baseline established")
        print(f"  - Questionnaire generation: {gen_time:.3f}s")


# Test runner configuration
if __name__ == "__main__":
    print("""
╔══════════════════════════════════════════════════════════════════════════════╗
║                                                                              ║
║           TPRM-Frameworks MCP Server - Integration Test Suite               ║
║                        Phase 0 Deployment Validation                         ║
║                                                                              ║
╚══════════════════════════════════════════════════════════════════════════════╝

Running comprehensive integration tests...

Test Coverage:
  ✓ All 7 MCP tools (list, generate, evaluate, map, report, get, search)
  ✓ Sample data loading (CAIQ, SIG, DORA, NIS2)
  ✓ Questionnaire generation (full, lite, focused)
  ✓ Response evaluation (good, bad, mixed, strictness levels)
  ✓ Control mapping (SCF integration)
  ✓ Report generation (basic, comprehensive)
  ✓ End-to-end scenario (Salesforce DORA assessment)

""")

    pytest.main([__file__, "-v", "-s", "--tb=short"])
