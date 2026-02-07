"""
Cloud Provider Security Assessment - Real-World Example

This example demonstrates assessing major cloud providers (AWS, Azure, GCP)
using CAIQ v4.1 with domain-specific focus areas.

Focus Areas:
- Cryptography & Key Management
- Identity & Access Management
- Data Security & Privacy
- Infrastructure Security
- Compliance & Certifications

Use Case: Enterprise selecting cloud infrastructure for regulated workloads
"""

import asyncio
import json
from datetime import datetime


async def assess_cloud_provider(provider_name: str, provider_type: str = "aws"):
    """
    Assess a cloud provider using CAIQ v4.1.

    Args:
        provider_name: Name of the cloud provider (e.g., "Amazon Web Services")
        provider_type: Type code ("aws", "azure", "gcp")
    """

    from tprm_frameworks_mcp.data_loader import TPRMDataLoader
    from tprm_frameworks_mcp.evaluation.rubric import EvaluationRubric
    from tprm_frameworks_mcp.storage import TPRMStorage
    from tprm_frameworks_mcp.models import (
        QuestionResponse,
        ResponseStrictness,
    )

    print(f"\n{'=' * 80}")
    print(f"Cloud Provider Security Assessment: {provider_name}")
    print(f"{'=' * 80}\n")

    loader = TPRMDataLoader()
    evaluator = EvaluationRubric()
    storage = TPRMStorage()

    # Load CAIQ v4.1 questions
    all_questions = loader.get_questions("caiq_v4_full")

    # Define cloud provider assessment priorities
    priority_domains = [
        "Cryptography, Encryption & Key Management",
        "Identity & Access Management",
        "Data Security and Privacy Lifecycle Management",
        "Infrastructure Security",
        "Datacenter Security",
    ]

    # Filter to priority domains
    questions = [q for q in all_questions if q.category in priority_domains]

    print(f"Assessment Scope: {len(questions)} questions across {len(priority_domains)} domains\n")

    # =========================================================================
    # Simulated Responses Based on Cloud Provider Type
    # =========================================================================

    responses = []

    # AWS-specific strong responses
    if provider_type == "aws":
        # Cryptography
        crypto_qs = [q for q in questions if "cryptography" in q.category.lower()]
        for q in crypto_qs[:5]:
            responses.append(
                QuestionResponse(
                    question_id=q.id,
                    answer="Yes. AWS provides comprehensive encryption services including AWS KMS (FIPS 140-2 Level 2 validated), "
                    "CloudHSM (FIPS 140-2 Level 3), and AWS Certificate Manager. All services support encryption at rest and "
                    "in transit. Customer-managed keys (CMK) with automatic rotation, envelope encryption, and integration with "
                    "AWS CloudTrail for audit logging. Third-party attestations: SOC 1/2/3, PCI DSS, ISO 27001:2022.",
                    supporting_documents=["aws-compliance-programs.pdf", "aws-kms-whitepaper.pdf"],
                )
            )

        # IAM
        iam_qs = [q for q in questions if "identity" in q.category.lower() or "access" in q.category.lower()]
        for q in iam_qs[:5]:
            responses.append(
                QuestionResponse(
                    question_id=q.id,
                    answer="Yes. AWS IAM provides fine-grained access control with: 1) IAM policies with least privilege, "
                    "2) MFA enforcement capabilities, 3) IAM roles for service-to-service auth, 4) AWS Organizations for "
                    "multi-account management, 5) IAM Access Analyzer for policy validation, 6) AWS SSO for centralized "
                    "access management. All IAM actions are logged in CloudTrail.",
                    supporting_documents=["aws-iam-best-practices.pdf"],
                )
            )

        # Data Security
        data_qs = [q for q in questions if "data" in q.category.lower()]
        for q in data_qs[:5]:
            responses.append(
                QuestionResponse(
                    question_id=q.id,
                    answer="Yes. AWS provides comprehensive data protection: S3 Object Lock for immutability, "
                    "S3 Versioning, Macie for sensitive data discovery, GuardDuty for threat detection, "
                    "VPC endpoints for private connectivity, and AWS Backup for centralized backup management. "
                    "Data residency controls available in all regions.",
                    supporting_documents=["aws-data-protection.pdf"],
                )
            )

    elif provider_type == "azure":
        # Azure-specific strong responses
        crypto_qs = [q for q in questions if "cryptography" in q.category.lower()]
        for q in crypto_qs[:5]:
            responses.append(
                QuestionResponse(
                    question_id=q.id,
                    answer="Yes. Azure provides Azure Key Vault (FIPS 140-2 Level 2 validated HSM), "
                    "Azure Dedicated HSM (Level 3), and automated key rotation. Supports bring-your-own-key (BYOK) "
                    "and hold-your-own-key (HYOK) scenarios. Integration with Azure Policy for encryption enforcement. "
                    "Certifications: ISO 27001, SOC 2, FedRAMP High.",
                    supporting_documents=["azure-security-baseline.pdf"],
                )
            )

        # IAM
        iam_qs = [q for q in questions if "identity" in q.category.lower() or "access" in q.category.lower()]
        for q in iam_qs[:5]:
            responses.append(
                QuestionResponse(
                    question_id=q.id,
                    answer="Yes. Azure Active Directory (Entra ID) provides: 1) Conditional Access policies, "
                    "2) Passwordless authentication, 3) Privileged Identity Management (PIM), 4) Identity Protection "
                    "for risk-based policies, 5) Azure RBAC for resource-level access control. MFA enforced for all "
                    "privileged accounts. Integration with on-premises AD via Azure AD Connect.",
                    supporting_documents=["azure-identity-security.pdf"],
                )
            )

    elif provider_type == "gcp":
        # GCP-specific strong responses
        crypto_qs = [q for q in questions if "cryptography" in q.category.lower()]
        for q in crypto_qs[:5]:
            responses.append(
                QuestionResponse(
                    question_id=q.id,
                    answer="Yes. Google Cloud provides Cloud KMS (FIPS 140-2 Level 1 and Level 3), "
                    "Cloud HSM, and external key manager (EKM) integration. Default encryption at rest "
                    "for all services with Google-managed keys, customer-managed keys, or external keys. "
                    "Automatic key rotation and centralized key management. Compliance: ISO 27001, SOC 2/3, PCI DSS.",
                    supporting_documents=["gcp-encryption-whitepaper.pdf"],
                )
            )

        # IAM
        iam_qs = [q for q in questions if "identity" in q.category.lower() or "access" in q.category.lower()]
        for q in iam_qs[:5]:
            responses.append(
                QuestionResponse(
                    question_id=q.id,
                    answer="Yes. Google Cloud IAM provides: 1) Resource hierarchy for organization-wide policies, "
                    "2) IAM Recommender for least privilege, 3) VPC Service Controls for data exfiltration protection, "
                    "4) Context-aware access with BeyondCorp Enterprise, 5) Workload Identity for service accounts. "
                    "Cloud Audit Logs for all IAM changes.",
                    supporting_documents=["gcp-iam-overview.pdf"],
                )
            )

    # Fill remaining questions with standard cloud provider responses
    for q in questions:
        if not any(r.question_id == q.id for r in responses):
            responses.append(
                QuestionResponse(
                    question_id=q.id,
                    answer="Yes. This requirement is addressed through our cloud provider's comprehensive security "
                    "controls, documented in our shared responsibility model, and validated through third-party "
                    "audits (SOC 2 Type II, ISO 27001:2022). Control evidence available upon request.",
                )
            )

    print(f"Generated {len(responses)} vendor responses\n")

    # =========================================================================
    # Evaluate Responses
    # =========================================================================

    print("Evaluating responses...\n")

    from tprm_frameworks_mcp.models import (
        EvaluationResult,
        AnswerStatus,
        AssessmentResult,
        Questionnaire,
        QuestionnaireMetadata,
        QuestionnaireFramework,
        RiskLevel,
    )
    import uuid

    evaluation_results = []
    response_map = {r.question_id: r for r in responses}

    for question in questions:
        response = response_map.get(question.id)

        if response:
            status, score, findings, risk = evaluator.evaluate_response(
                question, response, ResponseStrictness.STRICT  # Use strict for cloud providers
            )

            eval_result = EvaluationResult(
                question_id=question.id,
                status=status,
                score=score,
                risk_level=risk,
                findings=findings,
                recommendations=[],
                scf_controls_addressed=question.scf_control_mappings,
            )
        else:
            eval_result = EvaluationResult(
                question_id=question.id,
                status=AnswerStatus.UNANSWERED,
                score=0.0,
                risk_level=question.risk_if_inadequate,
                findings=["Not answered"],
                recommendations=[],
                scf_controls_addressed=[],
            )

        evaluation_results.append(eval_result)

    # Calculate scores by domain
    domain_scores = {}
    for q in questions:
        eval_result = next((r for r in evaluation_results if r.question_id == q.id), None)
        if eval_result and eval_result.status != AnswerStatus.NOT_APPLICABLE:
            if q.category not in domain_scores:
                domain_scores[q.category] = []
            domain_scores[q.category].append(eval_result.score)

    print("Domain-Level Scores:")
    print("-" * 80)
    for domain in sorted(domain_scores.keys()):
        scores = domain_scores[domain]
        avg_score = sum(scores) / len(scores)
        print(f"{domain:60s} {avg_score:5.1f}/100")

    # Overall score
    all_scores = [s for scores in domain_scores.values() for s in scores]
    overall_score = sum(all_scores) / len(all_scores) if all_scores else 0

    if overall_score >= 80:
        overall_risk = RiskLevel.LOW
    elif overall_score >= 60:
        overall_risk = RiskLevel.MEDIUM
    elif overall_score >= 40:
        overall_risk = RiskLevel.HIGH
    else:
        overall_risk = RiskLevel.CRITICAL

    print("-" * 80)
    print(f"{'OVERALL SCORE':60s} {overall_score:5.1f}/100")
    print(f"{'RISK LEVEL':60s} {overall_risk.value.upper()}")
    print("-" * 80)

    # =========================================================================
    # SOC 2 Compliance Analysis
    # =========================================================================

    print("\n\nSOC 2 Trust Service Criteria Compliance:")
    print("-" * 80)

    # Map CAIQ domains to SOC 2 criteria
    soc2_mapping = {
        "Security (CC)": [
            "Cryptography, Encryption & Key Management",
            "Identity & Access Management",
            "Infrastructure Security",
        ],
        "Availability (A)": ["Business Continuity Management and Operational Resilience"],
        "Confidentiality (C)": [
            "Data Security and Privacy Lifecycle Management",
            "Cryptography, Encryption & Key Management",
        ],
        "Processing Integrity (PI)": ["Change Control and Configuration Management"],
        "Privacy (P)": ["Data Security and Privacy Lifecycle Management"],
    }

    soc2_scores = {}
    for criteria, domains in soc2_mapping.items():
        relevant_scores = []
        for domain in domains:
            if domain in domain_scores:
                relevant_scores.extend(domain_scores[domain])

        if relevant_scores:
            soc2_scores[criteria] = sum(relevant_scores) / len(relevant_scores)
            status = "✓ PASS" if soc2_scores[criteria] >= 70 else "✗ FAIL"
            print(f"{criteria:40s} {soc2_scores[criteria]:5.1f}/100  {status}")

    print("-" * 80)

    # =========================================================================
    # Save Assessment
    # =========================================================================

    metadata = QuestionnaireMetadata(
        framework=QuestionnaireFramework.CAIQ_V4_FULL,
        version="4.1.0",
        total_questions=len(questions),
        categories=priority_domains,
        estimated_completion_time="120 minutes",
    )

    questionnaire_id = str(uuid.uuid4())
    questionnaire = Questionnaire(
        id=questionnaire_id,
        metadata=metadata,
        questions=questions,
        generation_timestamp=datetime.utcnow().isoformat(),
    )

    storage.save_questionnaire(questionnaire)

    assessment = AssessmentResult(
        questionnaire_id=questionnaire_id,
        vendor_name=provider_name,
        evaluation_results=evaluation_results,
        overall_score=overall_score,
        overall_risk_level=overall_risk,
        critical_findings=[],
        compliance_gaps={},
        timestamp=datetime.utcnow().isoformat(),
        strictness_level=ResponseStrictness.STRICT,
    )

    assessment_id = storage.save_assessment(assessment)

    print(f"\nAssessment saved: {assessment_id}")

    return {
        "provider": provider_name,
        "assessment_id": assessment_id,
        "overall_score": overall_score,
        "risk_level": overall_risk.value,
        "domain_scores": {k: sum(v) / len(v) for k, v in domain_scores.items()},
        "soc2_scores": soc2_scores,
    }


async def compare_cloud_providers():
    """Compare multiple cloud providers side-by-side."""

    print("\n" + "=" * 80)
    print("CLOUD PROVIDER SECURITY COMPARISON")
    print("=" * 80)

    providers = [
        ("Amazon Web Services (AWS)", "aws"),
        ("Microsoft Azure", "azure"),
        ("Google Cloud Platform (GCP)", "gcp"),
    ]

    results = []
    for provider_name, provider_type in providers:
        result = await assess_cloud_provider(provider_name, provider_type)
        results.append(result)

    # Comparison table
    print("\n\n" + "=" * 80)
    print("COMPARISON SUMMARY")
    print("=" * 80)

    print(f"\n{'Provider':25s} {'Overall Score':15s} {'Risk Level':15s} {'SOC 2 Security':15s}")
    print("-" * 80)

    for result in results:
        soc2_security = result["soc2_scores"].get("Security (CC)", 0)
        print(
            f"{result['provider']:25s} "
            f"{result['overall_score']:15.1f} "
            f"{result['risk_level']:15s} "
            f"{soc2_security:15.1f}"
        )

    print("-" * 80)

    # Recommendation
    best_provider = max(results, key=lambda x: x["overall_score"])
    print(f"\nRecommendation: {best_provider['provider']} (Score: {best_provider['overall_score']:.1f}/100)")

    print("\nNote: Scores are based on simulated responses for demonstration purposes.")
    print("In production, use actual vendor CAIQ responses and supporting documentation.\n")


if __name__ == "__main__":
    # Run individual assessment
    # asyncio.run(assess_cloud_provider("Amazon Web Services", "aws"))

    # Run comparison
    asyncio.run(compare_cloud_providers())
