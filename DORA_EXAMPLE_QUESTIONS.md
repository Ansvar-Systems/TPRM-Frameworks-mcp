# DORA ICT TPP - Example Questions

This document shows examples of completed questions with full regulatory traceability.

## Example 1: Article 28 - Risk Management Framework

```json
{
  "id": "DORA-28.1.1",
  "category": "ICT Third-Party Risk Management",
  "subcategory": "Due Diligence - Risk Management Framework",
  "question_text": "Has your organization established and implemented comprehensive ICT third-party risk management processes in accordance with DORA Article 28(1)?",
  "description": "DORA requires financial entities to manage ICT third-party risk as an integral part of their ICT risk management framework. Verify documented processes for identifying, assessing, and managing ICT third-party risks.",
  "expected_answer_type": "yes_no",
  "is_required": true,
  "weight": 10,
  "regulatory_mappings": [
    "DORA Article 28(1)",
    "NIS2 Article 21",
    "ISO 27001:2022 - 5.19"
  ],
  "scf_control_mappings": [
    "TPM-01",
    "TPM-02",
    "GOV-01",
    "RSK-01"
  ],
  "risk_if_inadequate": "critical",
  "evaluation_rubric": {
    "acceptable": [
      "yes.*documented.*processes",
      "implemented.*dora.*article 28",
      "established.*risk management.*ict.*third-party"
    ],
    "partially_acceptable": [
      "in progress.*implementation",
      "draft.*policy.*exists"
    ],
    "unacceptable": [
      "no.*processes",
      "not.*implemented"
    ],
    "required_keywords": [
      "risk management",
      "ICT",
      "third-party"
    ]
  },
  "regulatory_source": {
    "regulation": "DORA",
    "article": "28",
    "paragraph": "1",
    "requirement": "ICT third-party risk management framework"
  },
  "required_evidence": [
    "ICT third-party risk management policy",
    "Risk management framework documentation",
    "Third-party risk assessment procedures",
    "Board-approved risk management strategy"
  ]
}
```

## Example 2: Article 29 - Contractual Provisions

```json
{
  "id": "DORA-29.1.5",
  "category": "Key Contractual Provisions",
  "subcategory": "Audit Rights - Access and Inspection",
  "question_text": "Do you grant financial entities and their competent authorities full access and audit rights to assess ICT risk management and service delivery?",
  "description": "DORA Article 29(1)(d) mandates comprehensive audit rights for financial entities and their supervisory authorities.",
  "expected_answer_type": "yes_no",
  "is_required": true,
  "weight": 10,
  "regulatory_mappings": [
    "DORA Article 29(1)(d)",
    "DORA Article 29(5)"
  ],
  "scf_control_mappings": [
    "TPM-07",
    "CPL-02",
    "MON-05"
  ],
  "risk_if_inadequate": "critical",
  "evaluation_rubric": {
    "acceptable": [
      "yes.*full.*audit.*rights.*granted",
      "unlimited.*access.*financial.*entities.*authorities"
    ],
    "partially_acceptable": [
      "audit.*rights.*limited.*scope"
    ],
    "unacceptable": [
      "no.*audit.*rights",
      "refuse.*access.*authorities"
    ],
    "required_keywords": [
      "audit rights",
      "access",
      "authorities"
    ]
  },
  "regulatory_source": {
    "regulation": "DORA",
    "article": "29",
    "paragraph": "1",
    "subparagraph": "d",
    "requirement": "Access and audit rights"
  },
  "required_evidence": [
    "Audit rights clauses in contracts",
    "Access procedures for financial entities",
    "Supervisory authority access procedures",
    "Audit cooperation agreements"
  ]
}
```

## Example 3: Article 30 - Register of Information

```json
{
  "id": "DORA-30.2.4",
  "category": "Register of Information",
  "subcategory": "Register Content - Data Processing",
  "question_text": "Does the register specify the nature and location of data being processed, stored, or accessed by ICT third-party providers?",
  "description": "Register must document data types, processing activities, and geographic locations for compliance and risk management.",
  "expected_answer_type": "yes_no",
  "is_required": true,
  "weight": 9,
  "regulatory_mappings": [
    "DORA Article 30(2)(e)",
    "GDPR Article 30"
  ],
  "scf_control_mappings": [
    "DCH-01",
    "PRI-01",
    "TPM-01"
  ],
  "risk_if_inadequate": "high",
  "evaluation_rubric": {
    "acceptable": [
      "yes.*data.*nature.*location.*specified",
      "comprehensive.*processing.*documentation"
    ],
    "partially_acceptable": [
      "data.*types.*documented.*locations.*unclear"
    ],
    "unacceptable": [
      "no.*data.*documentation"
    ],
    "required_keywords": [
      "data",
      "processing",
      "location"
    ]
  },
  "regulatory_source": {
    "regulation": "DORA",
    "article": "30",
    "paragraph": "2",
    "subparagraph": "e",
    "requirement": "Data processing information in register"
  },
  "required_evidence": [
    "Data processing inventory",
    "Data type classification",
    "Processing location documentation",
    "Data flow diagrams"
  ]
}
```

## Example 4: Cybersecurity Controls

```json
{
  "id": "DORA-CYBER-3",
  "category": "Cybersecurity",
  "subcategory": "Access Control - Multi-Factor Authentication",
  "question_text": "Do you enforce multi-factor authentication (MFA) for all privileged access and remote access to systems processing financial entity data?",
  "description": "Strong authentication is essential to prevent unauthorized access to sensitive financial data and systems.",
  "expected_answer_type": "yes_no",
  "is_required": true,
  "weight": 10,
  "regulatory_mappings": [
    "DORA Article 8",
    "ISO 27001:2022 - 5.17",
    "NIS2 Article 21"
  ],
  "scf_control_mappings": [
    "IAC-10",
    "IAC-11",
    "IAC-13"
  ],
  "risk_if_inadequate": "critical",
  "evaluation_rubric": {
    "acceptable": [
      "yes.*mfa.*enforced.*all.*privileged",
      "multi-factor.*authentication.*mandatory"
    ],
    "partially_acceptable": [
      "mfa.*most.*users",
      "some.*exceptions.*mfa"
    ],
    "unacceptable": [
      "no.*mfa",
      "password-only.*authentication"
    ],
    "required_keywords": [
      "MFA",
      "multi-factor",
      "authentication"
    ]
  },
  "regulatory_source": {
    "regulation": "DORA",
    "article": "8",
    "paragraph": "N/A",
    "requirement": "Strong authentication controls"
  },
  "required_evidence": [
    "MFA policy and implementation",
    "Authentication configuration documentation",
    "Access control matrices",
    "MFA compliance reports"
  ]
}
```

## Example 5: Concentration Risk

```json
{
  "id": "DORA-28.5.1",
  "category": "ICT Third-Party Risk Management",
  "subcategory": "Concentration Risk - Single Provider Dependency",
  "question_text": "Have you assessed whether financial entities face concentration risk due to reliance on your services, particularly if you provide critical or important functions?",
  "description": "DORA Article 28(9) requires assessment of concentration risk where multiple financial entities depend on the same ICT third-party service provider.",
  "expected_answer_type": "yes_no",
  "is_required": true,
  "weight": 9,
  "regulatory_mappings": [
    "DORA Article 28(9)",
    "DORA Article 28(2)"
  ],
  "scf_control_mappings": [
    "TPM-03",
    "RSK-06",
    "BCD-01"
  ],
  "risk_if_inadequate": "high",
  "evaluation_rubric": {
    "acceptable": [
      "yes.*concentration.*risk.*assessed",
      "dependency.*analysis.*conducted"
    ],
    "partially_acceptable": [
      "basic.*assessment.*performed"
    ],
    "unacceptable": [
      "no.*concentration.*assessment"
    ],
    "required_keywords": [
      "concentration",
      "dependency",
      "risk"
    ]
  },
  "regulatory_source": {
    "regulation": "DORA",
    "article": "28",
    "paragraph": "9",
    "requirement": "Concentration risk assessment"
  },
  "required_evidence": [
    "Concentration risk analysis report",
    "Customer dependency mapping",
    "Systemic risk assessment",
    "Mitigation strategies for concentration risk"
  ]
}
```

## Key Features Demonstrated

### 1. Regulatory Traceability
Every question includes:
- **regulation**: The regulatory framework (DORA)
- **article**: Specific DORA article number
- **paragraph**: Paragraph within the article
- **subparagraph**: Letter designation where applicable (a, b, c, etc.)
- **requirement**: Clear statement of what's required

### 2. Evidence Requirements
Each question specifies 3-4 concrete evidence items:
- **Policies**: Written governance documents
- **Procedures**: Operational workflows
- **Technical Documentation**: System configurations
- **Reports**: Audit results, assessments, testing
- **Records**: Logs, tracking, compliance documentation

### 3. Multi-Framework Integration
Questions map to multiple frameworks:
- **DORA**: Primary regulatory requirement
- **NIS2**: Cybersecurity Directive alignment
- **ISO 27001**: International security standards
- **GDPR**: Data protection requirements
- **SCF**: Secure Controls Framework for detailed control mapping

### 4. Risk-Based Assessment
- **Risk levels**: Critical, High, Medium, Low
- **Weights**: 1-10 for scoring importance
- **Required/Optional**: Mandatory vs. recommended questions

### 5. Evaluation Rubrics
Automated scoring patterns:
- **Acceptable**: Fully compliant responses
- **Partially Acceptable**: Partial compliance
- **Unacceptable**: Non-compliance
- **Keywords**: Must-have terms for validation

## Coverage Summary

The 71 questions provide comprehensive coverage of:

### DORA Articles 28-30 (Core ICT Third-Party Risk)
- Risk management framework
- Due diligence processes
- Contractual arrangements (all 8 mandatory clauses)
- Exit strategies
- Performance monitoring
- Register of information

### Supporting DORA Articles
- Articles 5-6: Governance
- Articles 8-9: ICT Security
- Articles 11-12: Business Continuity
- Article 17: Logging
- Articles 18-19: Incident Management
- Article 26: Testing (TLPT)
- Articles 31-40: Oversight Framework
- Article 45: Information Sharing

### Additional Topics
- Concentration risk
- Subcontracting and fourth-party risk
- Data localization
- Cybersecurity controls
- Personnel security
- Compliance monitoring

---

**File Location**: `/Users/jeffreyvonrotz/Projects/TPRM-Frameworks-mcp/src/tprm_frameworks_mcp/data/dora_ict_tpp.json`

**Status**: Production-ready for DORA ICT Third-Party Provider assessments
