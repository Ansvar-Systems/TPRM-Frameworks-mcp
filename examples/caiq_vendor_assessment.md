# CAIQ v4.1 Vendor Assessment Guide

Complete guide for conducting vendor security assessments using the CSA Consensus Assessments Initiative Questionnaire (CAIQ) v4.1 through the TPRM Frameworks MCP.

## Table of Contents

1. [Overview](#overview)
2. [Pre-Assessment Preparation](#pre-assessment-preparation)
3. [Step-by-Step Workflow](#step-by-step-workflow)
4. [Question Examples & Guidance](#question-examples--guidance)
5. [Response Evaluation](#response-evaluation)
6. [Scoring Interpretation](#scoring-interpretation)
7. [SCF Control Mapping](#scf-control-mapping)
8. [Report Generation](#report-generation)

---

## Overview

### What is CAIQ v4.1?

The Consensus Assessments Initiative Questionnaire (CAIQ) is a comprehensive security questionnaire developed by the Cloud Security Alliance (CSA). Version 4.1 contains **283 questions** across **17 security domains** aligned with the Cloud Controls Matrix (CCM) v4.0.10.

### When to Use CAIQ

- **Cloud service provider assessments** (SaaS, PaaS, IaaS)
- **Third-party vendor security reviews**
- **Compliance validation** (ISO 27001, SOC 2, PCI DSS)
- **Due diligence** for M&A or strategic partnerships
- **Ongoing vendor monitoring** (annual re-assessments)

### TPRM MCP Integration

The TPRM Frameworks MCP provides:
- ✅ 283 CAIQ v4.1 questions with enhanced evaluation rubrics
- ✅ 566+ mappings to SCF (Secure Controls Framework) controls
- ✅ Automated response evaluation and scoring
- ✅ Persistent storage for historical tracking
- ✅ Cross-framework comparison capabilities

---

## Pre-Assessment Preparation

### 1. Define Assessment Scope

Determine which CAIQ scope to use:

| Scope | Questions | Use Case | Duration |
|-------|-----------|----------|----------|
| **Full** | 283 | Comprehensive cloud provider assessment | 4-6 hours |
| **Lite** | 80-100 | Focused on critical controls (weight ≥8) | 1-2 hours |
| **Focused** | Variable | Specific domains (e.g., crypto, IAM, data) | 30-90 min |

### 2. Select Priority Domains

**Critical Domains for Most Assessments:**
- Cryptography, Encryption & Key Management (23 questions)
- Identity & Access Management (19 questions)
- Data Security & Privacy Lifecycle Management (24 questions)
- Security Incident Management (16 questions)

**Additional Domains by Vendor Type:**

| Vendor Type | Additional Priority Domains |
|-------------|----------------------------|
| SaaS Provider | Application Security, Logging & Monitoring |
| Cloud Provider | Datacenter Security, Infrastructure Security |
| Data Processor | Data Security & Privacy, Audit & Assurance |
| Financial | GRC, BCM & Operational Resilience |

### 3. Gather Vendor Information

Before starting, collect:
- ✅ Vendor legal name and primary contact
- ✅ Service/product description
- ✅ Current certifications (SOC 2, ISO 27001, etc.)
- ✅ Existing security documentation
- ✅ Previous assessment results (if available)

---

## Step-by-Step Workflow

### Step 1: Generate Questionnaire

**Using MCP Tool:**
```json
{
  "tool": "generate_questionnaire",
  "arguments": {
    "framework": "caiq_v4_full",
    "scope": "full",
    "entity_type": "saas_provider",
    "regulations": ["ISO 27001:2022", "SOC 2", "GDPR"]
  }
}
```

**Example Output:**
```
Questionnaire Generated

ID: e7d8f4a2-3b1c-4e5f-9a7b-2d3e4f5a6b7c
Framework: CSA CAIQ v4.1.0
Scope: full
Total Questions: 283
Entity Type: saas_provider
```

### Step 2: Distribute to Vendor

Provide vendor with:
1. **Questionnaire ID** for reference
2. **Response deadline** (typically 2-4 weeks)
3. **Submission instructions**
4. **Evidence requirements** (documents, certifications, policies)

**Response Guidelines for Vendors:**
- Answer each question comprehensively
- Provide specific details (not just "Yes" or "No")
- Include evidence references
- Note any N/A questions with justification
- Flag questions requiring clarification

### Step 3: Collect Vendor Responses

**MCP Integration:**
Submit responses through the `evaluate_response` tool:

```json
{
  "tool": "evaluate_response",
  "arguments": {
    "questionnaire_id": "e7d8f4a2-3b1c-4e5f-9a7b-2d3e4f5a6b7c",
    "vendor_name": "CloudTech Solutions Inc",
    "responses": [
      {
        "question_id": "CRY-01.1",
        "answer": "Yes. We use AES-256-GCM encryption...",
        "supporting_documents": ["encryption-policy.pdf"],
        "notes": "Validated in SOC 2 audit"
      }
    ],
    "strictness": "moderate"
  }
}
```

### Step 4: Review Evaluation Results

The system automatically evaluates responses using enhanced rubrics:

**Score Ranges:**
- **90-100**: Excellent - Industry-leading controls
- **80-89**: Good - Meets security standards
- **70-79**: Acceptable - Minor improvements needed
- **60-69**: Partial - Significant gaps present
- **<60**: Inadequate - Critical controls missing

### Step 5: Map to Security Controls

Use the `map_questionnaire_to_controls` tool to see SCF coverage:

```json
{
  "tool": "map_questionnaire_to_controls",
  "arguments": {
    "framework": "caiq_v4_full",
    "control_framework": "scf"
  }
}
```

This shows which SCF controls are addressed by vendor responses.

### Step 6: Generate Final Report

```json
{
  "tool": "generate_tprm_report",
  "arguments": {
    "vendor_name": "CloudTech Solutions Inc",
    "questionnaire_results": ["<assessment_id>"],
    "include_recommendations": true
  }
}
```

---

## Question Examples & Guidance

### Domain: Cryptography & Key Management

**Question CRY-01.1:**
> Does your organization use encryption to protect customer data at rest?

**What to Look For:**
- ✅ Encryption algorithm (AES-256, AES-256-GCM)
- ✅ Key management system (AWS KMS, Azure Key Vault, etc.)
- ✅ Key rotation frequency (90 days standard)
- ✅ HSM usage for key storage
- ✅ Separation of duties for key administration

**Good Response Example:**
```
Yes. All customer data at rest is encrypted using AES-256-GCM encryption.
Encryption keys are managed via AWS KMS with customer-managed keys (CMK).
Key rotation occurs automatically every 90 days. Master keys are stored in
FIPS 140-2 Level 3 validated HSMs. Our key management procedures are
documented in our Cryptographic Controls Policy (v3.2, 2025-01-15) and
validated annually through SOC 2 Type II audits. Access to key administration
functions requires dual approval and is restricted to the Security Operations
team with all actions logged in CloudTrail.
```

**Poor Response Example:**
```
Yes, we encrypt data.
```

**Scoring:**
- Good Response: 95-100 (comprehensive, specific, evidenced)
- Poor Response: 30-40 (lacks detail, no evidence)

---

### Domain: Identity & Access Management

**Question IAM-02.2:**
> Do you enforce multi-factor authentication (MFA) for all user accounts?

**What to Look For:**
- ✅ MFA enforcement scope (all users vs. privileged only)
- ✅ MFA methods (TOTP, hardware tokens, biometric)
- ✅ Technical vs. policy-based enforcement
- ✅ Exceptions process
- ✅ MFA for administrative/privileged access

**Good Response Example:**
```
Yes. MFA is mandatory for all user accounts with the following implementation:
- Standard users: TOTP-based authentication (Google Authenticator, Authy)
- Privileged accounts: Hardware security keys (YubiKey 5 Series) required
- Mobile access: Biometric authentication (Face ID/Touch ID) with device attestation
- MFA enforcement is technically controlled via our identity provider (Okta) and
  cannot be disabled by users or local administrators
- Zero exceptions policy - any user requiring MFA bypass must be approved by CISO
  and is limited to 24 hours with compensating controls
- 99.8% MFA adoption rate across 1,250 employee accounts
- MFA configuration validated quarterly in access reviews
```

**Partial Response Example:**
```
Yes. We have an MFA policy that requires all employees to use MFA.
It's documented in our Security Awareness training.
```

**Scoring:**
- Good Response: 95-100 (comprehensive technical controls)
- Partial Response: 60-70 (policy exists but enforcement unclear)

---

### Domain: Data Security & Privacy

**Question DSP-03.1:**
> Do you have a data classification scheme and is it enforced?

**What to Look For:**
- ✅ Classification levels (Public, Internal, Confidential, Restricted)
- ✅ Classification criteria
- ✅ Automated vs. manual classification
- ✅ Enforcement mechanisms (DLP, access controls)
- ✅ Handling procedures per classification

**Good Response Example:**
```
Yes. We maintain a four-tier data classification scheme:
1. Public: No confidentiality impact
2. Internal: Limited to employees and contractors
3. Confidential: Business-critical, requires authorization
4. Restricted: Highly sensitive (PII, PHI, payment data)

Classification Process:
- Automated: Microsoft Purview scans all documents/emails, applies labels based on
  content patterns (SSN, credit card, etc.)
- Manual: Data owners classify datasets at creation
- Default: All data defaults to "Internal" unless explicitly downgraded

Enforcement:
- DLP policies block Restricted data from email/cloud sharing
- Access controls tied to classification (Confidential requires MFA + justification)
- Encryption mandatory for Confidential/Restricted (AES-256)
- Audit logging for all Restricted data access

Coverage: 98.5% of stored data classified, validated monthly via automated reporting.
```

**Inadequate Response Example:**
```
We are currently developing a data classification policy.
Expected completion Q3 2026.
```

**Scoring:**
- Good Response: 90-100 (implemented, automated, enforced)
- Inadequate Response: 20-30 (not yet implemented)

---

## Response Evaluation

### Evaluation Rubric Components

Each question is evaluated using:

1. **Pattern Matching**: Keywords and phrases indicating strong controls
2. **Completeness**: Level of detail and specificity
3. **Evidence**: References to policies, audits, certifications
4. **Risk Alignment**: Response quality vs. question criticality

### Strictness Levels

| Level | Description | Use Case |
|-------|-------------|----------|
| **Lenient** | Accepts partial answers | Initial vendor screening |
| **Moderate** | Standard evaluation | Most assessments |
| **Strict** | Requires comprehensive answers | Critical vendors, regulated industries |

### Status Values

- **Acceptable**: Response fully addresses requirements
- **Partially Acceptable**: Response addresses some requirements, gaps exist
- **Unacceptable**: Response does not meet requirements
- **Not Applicable**: Question not relevant to vendor's service
- **Unanswered**: No response provided

---

## Scoring Interpretation

### Overall Score Ranges

| Score | Risk Level | Interpretation | Action |
|-------|------------|----------------|--------|
| **90-100** | Low | Excellent security posture | Approve with standard monitoring |
| **80-89** | Low | Good security posture | Approve with periodic re-assessment |
| **70-79** | Medium | Acceptable with gaps | Approve with remediation plan |
| **60-69** | Medium | Significant gaps | Conditional approval, quarterly review |
| **40-59** | High | Major control deficiencies | Request immediate improvements |
| **<40** | Critical | Inadequate security controls | Do not approve, seek alternatives |

### Domain-Level Analysis

Review scores by domain to identify specific weaknesses:

**Example:**
```
Cryptography & Encryption:           92/100 (Excellent)
Identity & Access Management:        88/100 (Good)
Data Security & Privacy:             75/100 (Acceptable)
Incident Management:                 58/100 (Gaps)
Business Continuity:                 45/100 (Deficient) ⚠️
```

**Interpretation**: Strong crypto/IAM controls, but BC/DR capabilities need significant improvement before approval.

### Critical Findings

Always address findings marked as **CRITICAL** risk:
- Missing MFA enforcement
- No encryption for sensitive data
- Lack of incident response plan
- No security awareness training
- Insufficient access controls
- Missing audit logging

---

## SCF Control Mapping

### Understanding SCF Mappings

Each CAIQ question maps to 2 SCF (Secure Controls Framework) controls on average:

**Example Mapping:**
```
CAIQ Question: CRY-01.1 (Data at rest encryption)
SCF Controls:
  - CRY-01: Encryption At Rest
  - CRY-02: Encryption Key Management
```

### Using SCF Mappings

1. **Gap Analysis**: Identify which SCF controls are not adequately addressed
2. **Cross-Framework**: Map to ISO 27001, NIST, PCI DSS via SCF
3. **Remediation**: Provide specific control recommendations to vendor
4. **Coverage**: Track what percentage of required controls are satisfied

### Integration with security-controls-mcp

```json
{
  "tool": "security-controls-mcp.get_control",
  "arguments": {
    "control_id": "CRY-01"
  }
}
```

Returns detailed control description, implementation guidance, and cross-framework mappings.

---

## Report Generation

### Report Structure

1. **Executive Summary**
   - Overall score and risk level
   - Key findings (top 5 strengths, top 5 gaps)
   - Go/no-go recommendation

2. **Assessment Details**
   - Questionnaire metadata
   - Response statistics
   - Domain-level scores

3. **Critical Findings**
   - High/critical risk items requiring immediate attention
   - Compliance gaps by regulation

4. **SCF Control Coverage**
   - Controls addressed vs. not addressed
   - Control coverage percentage

5. **Recommendations**
   - Prioritized remediation actions
   - Timeline for re-assessment
   - Continuous monitoring requirements

### Sample Report Excerpt

```
EXECUTIVE SUMMARY

Vendor: CloudTech Solutions Inc
Assessment Date: 2026-02-07
Overall Score: 78/100
Risk Level: MEDIUM

This vendor demonstrates good security controls in cryptography and access
management but requires improvements in incident response and business
continuity capabilities before full approval.

RECOMMENDATION: Conditional approval pending:
1. Implementation of formal incident response plan (60 days)
2. Business continuity testing with documented results (90 days)
3. Re-assessment in 6 months to validate improvements

CRITICAL FINDINGS:
1. No documented incident response plan (SEF-01)
2. Business continuity tests not performed in past 12 months (BCR-02)
3. MFA enforcement gaps for privileged accounts (IAM-02)
```

---

## Best Practices

### For Assessors

1. **Start with lite scope** for initial vendor screening
2. **Use focused scope** for specific compliance requirements
3. **Set strict evaluation** for high-risk/critical vendors
4. **Request evidence** for all "acceptable" responses
5. **Schedule follow-up** for partially acceptable responses
6. **Track historical trends** using vendor history tool
7. **Map to your controls** via security-controls-mcp integration

### For Vendors

1. **Provide comprehensive answers** with specific details
2. **Reference policies and procedures** by name and version
3. **Include audit evidence** (SOC 2, ISO 27001 certificates)
4. **Explain N/A** responses with clear justification
5. **Ask for clarification** on ambiguous questions
6. **Update annually** or after significant infrastructure changes
7. **Treat as opportunity** to demonstrate security maturity

---

## Common Pitfalls

### Inadequate Responses

❌ **Too Brief:** "Yes, we have this control."
✅ **Better:** "Yes, we implement [specific technology/process] with [frequency] validation via [audit/tool]."

❌ **No Evidence:** "We follow industry best practices."
✅ **Better:** "We implement NIST CSF controls validated in our 2025 SOC 2 Type II audit (attached)."

❌ **Future State:** "We plan to implement this control next quarter."
✅ **Better:** "Not currently implemented. Planned for Q3 2026 with [specific vendor/solution]."

### Scoring Disputes

If vendor disputes scoring:
1. Review response against evaluation rubric
2. Request additional evidence/clarification
3. Adjust strictness level if appropriate
4. Document rationale for final score
5. Provide specific improvement recommendations

---

## Appendix: Complete Domain List

| Domain Code | Domain Name | Questions |
|-------------|-------------|-----------|
| A&A | Audit & Assurance | 8 |
| AIS | Application & Interface Security | 13 |
| BCR | Business Continuity Management | 19 |
| CCC | Change Control & Configuration | 12 |
| CRY | Cryptography & Encryption | 23 |
| DSP | Data Security & Privacy | 24 |
| DCS | Datacenter Security | 28 |
| GRC | Governance, Risk & Compliance | 10 |
| HRS | Human Resources | 20 |
| IAM | Identity & Access Management | 19 |
| INF | Infrastructure Security | 15 |
| IPY | Interoperability & Portability | 8 |
| LOG | Logging & Monitoring | 19 |
| SEF | Security Incident Management | 16 |
| STA | Supply Chain Management | 19 |
| TVM | Threat & Vulnerability Management | 15 |
| UEM | Universal Endpoint Management | 15 |

**Total:** 283 questions across 17 domains

---

## Quick Reference Commands

### Generate Full Assessment
```json
{"tool": "generate_questionnaire", "arguments": {"framework": "caiq_v4_full", "scope": "full"}}
```

### Generate Lite Assessment
```json
{"tool": "generate_questionnaire", "arguments": {"framework": "caiq_v4_full", "scope": "lite"}}
```

### Search Questions
```json
{"tool": "search_questions", "arguments": {"query": "encryption", "framework": "caiq_v4_full"}}
```

### Get Vendor History
```json
{"tool": "get_vendor_history", "arguments": {"vendor_name": "CloudTech Solutions Inc"}}
```

### Compare Assessments
```json
{"tool": "compare_assessments", "arguments": {"vendor_name": "CloudTech Solutions Inc"}}
```

---

**For support or questions about CAIQ v4.1 assessments:**
- Documentation: `/docs/` directory
- Issues: File on GitHub
- Contact: hello@ansvar.eu
