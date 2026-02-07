"""
Complete CAIQ v4.1 Assessment Workflow Example

This example demonstrates a complete end-to-end vendor assessment using
the CSA Consensus Assessments Initiative Questionnaire (CAIQ) v4.1.

Workflow:
1. Generate CAIQ v4.1 questionnaire (283 questions)
2. Submit vendor responses
3. Evaluate with enhanced rubrics
4. Map to SCF controls
5. Generate compliance report

Use Case: Assessing a SaaS provider for cloud security compliance
"""

import asyncio
import json
from datetime import datetime


async def complete_caiq_assessment():
    """Run a complete CAIQ v4.1 assessment workflow."""

    # Import MCP server tools (in real usage, these would be called via MCP protocol)
    from tprm_frameworks_mcp.data_loader import TPRMDataLoader
    from tprm_frameworks_mcp.evaluation.rubric import EvaluationRubric
    from tprm_frameworks_mcp.storage import TPRMStorage
    from tprm_frameworks_mcp.models import (
        Questionnaire,
        QuestionnaireMetadata,
        QuestionnaireFramework,
        QuestionResponse,
        ResponseStrictness,
        RiskLevel,
        AnswerStatus,
        EvaluationResult,
        AssessmentResult,
    )
    import uuid

    print("=" * 80)
    print("CAIQ v4.1 Cloud Security Assessment Workflow")
    print("=" * 80)

    # Initialize components
    loader = TPRMDataLoader()
    evaluator = EvaluationRubric()
    storage = TPRMStorage()

    # Vendor information
    vendor_name = "CloudTech Solutions Inc"
    vendor_type = "saas_provider"

    # =========================================================================
    # Step 1: Generate CAIQ v4.1 Questionnaire
    # =========================================================================
    print("\n[Step 1] Generating CAIQ v4.1 Questionnaire...")
    print("-" * 80)

    # Load all CAIQ v4.1 questions
    all_questions = loader.get_questions("caiq_v4_full")
    print(f"✓ Loaded {len(all_questions)} CAIQ v4.1 questions")

    # For this example, let's focus on critical domains
    critical_domains = [
        "Cryptography, Encryption & Key Management",
        "Identity & Access Management",
        "Data Security and Privacy Lifecycle Management",
        "Security Incident Management, E-Discovery, & Cloud Forensics",
    ]

    # Filter questions to critical domains
    focused_questions = [q for q in all_questions if q.category in critical_domains]
    print(f"✓ Focusing on {len(focused_questions)} questions in critical domains:")
    for domain in critical_domains:
        count = len([q for q in focused_questions if q.category == domain])
        print(f"  - {domain}: {count} questions")

    # Create questionnaire metadata
    metadata = QuestionnaireMetadata(
        framework=QuestionnaireFramework.CAIQ_V4_FULL,
        version="4.1.0",
        total_questions=len(focused_questions),
        categories=critical_domains,
        estimated_completion_time="90 minutes",
        scope="focused",
        applicable_regulations=["ISO 27001:2022", "SOC 2", "GDPR"],
    )

    # Create questionnaire
    questionnaire_id = str(uuid.uuid4())
    questionnaire = Questionnaire(
        id=questionnaire_id,
        metadata=metadata,
        questions=focused_questions,
        generation_timestamp=datetime.utcnow().isoformat(),
        custom_parameters={
            "vendor_type": vendor_type,
            "assessment_purpose": "cloud_security_due_diligence",
        },
    )

    # Save questionnaire
    storage.save_questionnaire(questionnaire)
    print(f"✓ Generated questionnaire ID: {questionnaire_id}")

    # =========================================================================
    # Step 2: Simulate Vendor Responses
    # =========================================================================
    print("\n[Step 2] Simulating Vendor Responses...")
    print("-" * 80)

    # In a real scenario, these would come from the vendor's CAIQ submission
    # Here we'll simulate various quality responses

    responses = []

    # Excellent response example (Cryptography domain)
    crypto_question = next(
        (
            q
            for q in focused_questions
            if "encryption" in q.question_text.lower() and "data at rest" in q.question_text.lower()
        ),
        None,
    )
    if crypto_question:
        responses.append(
            QuestionResponse(
                question_id=crypto_question.id,
                answer="Yes. We implement AES-256-GCM encryption for all data at rest using AWS KMS with "
                "customer-managed keys (CMK). Our encryption architecture includes: 1) Envelope encryption "
                "with automatic key rotation every 90 days, 2) HSM-backed key storage with FIPS 140-2 Level 3 "
                "certification, 3) Documented key lifecycle management procedures, 4) Separation of duties for "
                "key administration. All encryption practices are validated annually through SOC 2 Type II audits.",
                supporting_documents=[
                    "encryption-architecture-diagram.pdf",
                    "soc2-type2-report-2025.pdf",
                ],
                notes="Latest SOC 2 audit confirmed no findings in cryptographic controls",
            )
        )

    # Good response example (IAM domain)
    iam_question = next(
        (q for q in focused_questions if "multi-factor" in q.question_text.lower()),
        None,
    )
    if iam_question:
        responses.append(
            QuestionResponse(
                question_id=iam_question.id,
                answer="Yes. MFA is mandatory for all users with the following implementation: "
                "TOTP-based authentication (Google Authenticator, Authy), hardware security keys "
                "(YubiKey) for privileged accounts, and biometric authentication for mobile access. "
                "MFA enforcement is technically controlled and cannot be bypassed.",
                supporting_documents=["iam-policy-2025.pdf"],
            )
        )

    # Partial response example (Data Security domain)
    data_question = next(
        (q for q in focused_questions if "data classification" in q.question_text.lower()),
        None,
    )
    if data_question:
        responses.append(
            QuestionResponse(
                question_id=data_question.id,
                answer="We have a data classification scheme with three levels: Public, Internal, and "
                "Confidential. Classification is currently manual and documented in our security policy.",
                notes="Automated classification tooling planned for Q3 2026",
            )
        )

    # Poor response example (Incident Management domain)
    incident_question = next(
        (q for q in focused_questions if "incident response" in q.question_text.lower()),
        None,
    )
    if incident_question:
        responses.append(
            QuestionResponse(
                question_id=incident_question.id,
                answer="We have basic incident response procedures but they are not formally documented. "
                "Incidents are handled on a case-by-case basis by the engineering team.",
            )
        )

    # Add some more typical responses
    for q in focused_questions[:20]:
        if not any(r.question_id == q.id for r in responses):
            responses.append(
                QuestionResponse(
                    question_id=q.id,
                    answer="Yes, we have implemented controls to address this requirement with "
                    "regular monitoring and annual reviews.",
                )
            )

    print(f"✓ Created {len(responses)} vendor responses")
    print(f"  - Excellent responses: 1")
    print(f"  - Good responses: 1")
    print(f"  - Partial responses: 1")
    print(f"  - Poor responses: 1")
    print(f"  - Standard responses: {len(responses) - 4}")

    # =========================================================================
    # Step 3: Evaluate Responses with Enhanced Rubrics
    # =========================================================================
    print("\n[Step 3] Evaluating Vendor Responses...")
    print("-" * 80)

    evaluation_results = []
    response_map = {r.question_id: r for r in responses}

    for question in focused_questions:
        response = response_map.get(question.id)

        if not response:
            # Unanswered question
            eval_result = EvaluationResult(
                question_id=question.id,
                status=AnswerStatus.UNANSWERED,
                score=0.0,
                risk_level=question.risk_if_inadequate,
                findings=["Question not answered by vendor"],
                recommendations=[
                    "Request vendor to complete this critical security question"
                ],
                scf_controls_addressed=[],
            )
        else:
            # Evaluate with rubric
            status, score, findings, risk = evaluator.evaluate_response(
                question, response, ResponseStrictness.MODERATE
            )

            recommendations = []
            if status == AnswerStatus.UNACCEPTABLE:
                recommendations.append(
                    f"CRITICAL: {question.category} controls are inadequate and must be improved"
                )
            elif status == AnswerStatus.PARTIALLY_ACCEPTABLE:
                recommendations.append(
                    f"Enhance {question.category} controls to meet industry standards"
                )

            if question.scf_control_mappings:
                recommendations.append(
                    f"Review SCF controls: {', '.join(question.scf_control_mappings[:3])}"
                )

            eval_result = EvaluationResult(
                question_id=question.id,
                status=status,
                score=score,
                risk_level=risk,
                findings=findings,
                recommendations=recommendations,
                scf_controls_addressed=question.scf_control_mappings,
            )

        evaluation_results.append(eval_result)

    # Calculate overall score
    scored_results = [r for r in evaluation_results if r.status != AnswerStatus.NOT_APPLICABLE]
    overall_score = sum(r.score for r in scored_results) / len(scored_results) if scored_results else 0

    # Determine risk level
    if overall_score >= 80:
        overall_risk = RiskLevel.LOW
    elif overall_score >= 60:
        overall_risk = RiskLevel.MEDIUM
    elif overall_score >= 40:
        overall_risk = RiskLevel.HIGH
    else:
        overall_risk = RiskLevel.CRITICAL

    # Find critical findings
    critical_findings = [
        f"{r.question_id}: {', '.join(r.findings)}"
        for r in evaluation_results
        if r.risk_level == RiskLevel.CRITICAL and r.status == AnswerStatus.UNACCEPTABLE
    ]

    print(f"✓ Evaluation complete")
    print(f"  Overall Score: {overall_score:.1f}/100")
    print(f"  Risk Level: {overall_risk.value.upper()}")
    print(f"  Critical Findings: {len(critical_findings)}")

    # Status breakdown
    status_counts = {}
    for r in evaluation_results:
        status_counts[r.status] = status_counts.get(r.status, 0) + 1

    print(f"\n  Response Status Breakdown:")
    for status, count in sorted(status_counts.items(), key=lambda x: x[1], reverse=True):
        pct = (count / len(evaluation_results)) * 100
        print(f"    - {status.value}: {count} ({pct:.1f}%)")

    # =========================================================================
    # Step 4: Map to SCF Controls
    # =========================================================================
    print("\n[Step 4] Mapping to SCF Controls...")
    print("-" * 80)

    scf_mappings = {}
    for question in focused_questions:
        for scf_control in question.scf_control_mappings:
            if scf_control not in scf_mappings:
                scf_mappings[scf_control] = []
            scf_mappings[scf_control].append(question.id)

    print(f"✓ Mapped to {len(scf_mappings)} unique SCF controls")

    # Show top controls
    print(f"\n  Top SCF Controls (by question coverage):")
    sorted_controls = sorted(scf_mappings.items(), key=lambda x: len(x[1]), reverse=True)
    for control_id, questions in sorted_controls[:10]:
        print(f"    - {control_id}: {len(questions)} questions")

    # =========================================================================
    # Step 5: Generate Compliance Report
    # =========================================================================
    print("\n[Step 5] Generating Compliance Report...")
    print("-" * 80)

    # Create assessment result
    assessment = AssessmentResult(
        questionnaire_id=questionnaire_id,
        vendor_name=vendor_name,
        evaluation_results=evaluation_results,
        overall_score=overall_score,
        overall_risk_level=overall_risk,
        critical_findings=critical_findings,
        compliance_gaps={},
        timestamp=datetime.utcnow().isoformat(),
        strictness_level=ResponseStrictness.MODERATE,
    )

    # Save assessment
    assessment_id = storage.save_assessment(assessment)
    print(f"✓ Assessment saved: {assessment_id}")

    # Generate report
    report = f"""
{'=' * 80}
THIRD-PARTY RISK MANAGEMENT ASSESSMENT REPORT
{'=' * 80}

Vendor: {vendor_name}
Assessment Date: {datetime.utcnow().strftime('%Y-%m-%d')}
Assessment ID: {assessment_id}
Framework: CSA CAIQ v4.1.0
Assessor: Ansvar AI TPRM System

{'=' * 80}
EXECUTIVE SUMMARY
{'=' * 80}

Overall Security Score: {overall_score:.1f}/100
Overall Risk Level: {overall_risk.value.upper()}

Assessment Scope:
- Total Questions Evaluated: {len(evaluation_results)}
- Critical Security Domains: {len(critical_domains)}
- SCF Control Coverage: {len(scf_mappings)} controls

Response Quality:
"""

    for status, count in sorted(status_counts.items(), key=lambda x: x[1], reverse=True):
        pct = (count / len(evaluation_results)) * 100
        report += f"  - {status.value.replace('_', ' ').title()}: {count} ({pct:.1f}%)\n"

    report += f"""
{'=' * 80}
CRITICAL FINDINGS
{'=' * 80}

"""

    if critical_findings:
        for i, finding in enumerate(critical_findings[:10], 1):
            report += f"{i}. {finding}\n"
        if len(critical_findings) > 10:
            report += f"\n... and {len(critical_findings) - 10} more critical findings\n"
    else:
        report += "No critical findings identified.\n"

    report += f"""
{'=' * 80}
SCF CONTROL COVERAGE
{'=' * 80}

This assessment covers {len(scf_mappings)} SCF (Secure Controls Framework) controls:

Top 10 Controls by Coverage:
"""

    for i, (control_id, questions) in enumerate(sorted_controls[:10], 1):
        report += f"  {i}. {control_id}: {len(questions)} questions\n"

    report += f"""
{'=' * 80}
RECOMMENDATIONS
{'=' * 80}

Based on this assessment, we recommend:

1. Address all critical findings immediately (Risk: {overall_risk.value.upper()})
2. Enhance incident response capabilities with formal documentation
3. Implement automated data classification tooling
4. Request evidence documentation for all partially acceptable responses
5. Schedule quarterly re-assessment to track improvement

{'=' * 80}
NEXT STEPS
{'=' * 80}

1. Review this report with vendor and request remediation plan
2. Map gaps to your security-controls-mcp for control coverage analysis
3. Use compare_assessments tool for quarterly progress tracking
4. Integrate with vendor-intel-mcp for external security posture validation

Assessment completed: {datetime.utcnow().isoformat()}
{'=' * 80}
"""

    print(report)

    # Save report to file
    report_file = f"caiq_assessment_{vendor_name.replace(' ', '_')}_{datetime.utcnow().strftime('%Y%m%d')}.txt"
    with open(report_file, "w") as f:
        f.write(report)

    print(f"\n✓ Report saved to: {report_file}")

    # =========================================================================
    # Summary
    # =========================================================================
    print("\n" + "=" * 80)
    print("WORKFLOW COMPLETE")
    print("=" * 80)
    print(f"Questionnaire ID: {questionnaire_id}")
    print(f"Assessment ID: {assessment_id}")
    print(f"Overall Score: {overall_score:.1f}/100")
    print(f"Risk Level: {overall_risk.value.upper()}")
    print(f"Report: {report_file}")
    print("=" * 80 + "\n")

    return {
        "questionnaire_id": questionnaire_id,
        "assessment_id": assessment_id,
        "overall_score": overall_score,
        "risk_level": overall_risk.value,
        "critical_findings_count": len(critical_findings),
        "report_file": report_file,
    }


if __name__ == "__main__":
    result = asyncio.run(complete_caiq_assessment())
    print(f"\nWorkflow result: {json.dumps(result, indent=2)}")
