# NIS2 Compliance Guide

## Overview

This guide explains the NIS2 Supply Chain Security Assessment questionnaire, how to use it for vendor assessments, and how it relates to DORA (for organizations subject to both regulations).

## What is NIS2?

**NIS2 (Network and Information Security Directive 2)** is EU Directive 2022/2555, which establishes cybersecurity risk management requirements for essential and important entities across 18 sectors including energy, transport, banking, healthcare, digital infrastructure, and public administration.

### Key Dates
- **Publication**: December 27, 2022
- **Entry into Force**: January 16, 2023
- **Member State Transposition Deadline**: October 17, 2024
- **Application Date**: After transposition by each EU member state

### Scope
NIS2 applies to:
- **Essential entities**: Larger organizations in critical sectors (stricter requirements)
- **Important entities**: Medium-sized organizations in critical sectors
- **18 sectors**: Energy, transport, banking, financial market infrastructure, health, drinking water, waste water, digital infrastructure, ICT service management, public administration, space, postal/courier, waste management, manufacturing, food, digital providers, and research

## NIS2 Articles 20-23 Breakdown

### Article 20: Governance
Management body oversight of cybersecurity risk management

**Requirements**:
- Management body must approve and oversee cybersecurity measures
- Management must receive regular cybersecurity training
- Clear accountability for cybersecurity at board/management level

**Questionnaire Coverage**: Questions NIS2-20.1, NIS2-20.2, NIS2-Compliance-01, NIS2-Compliance-02

### Article 21: Cybersecurity Risk Management Measures
Technical, operational, and organizational measures

**Article 21(1)**: Risk analysis and information system security policies

**Article 21(2) - Specific Measures**:
- **(a)** Incident handling policies and procedures
- **(b)** Business continuity, backup management, disaster recovery, crisis management
- **(c)** Security in acquisition, development, and maintenance (supply chain security)
- **(d)** Network security including segmentation and monitoring
- **(e)** **Multi-factor authentication** and secured communications
- **(f)** Secured emergency communication systems
- **(g)** **Vulnerability handling and disclosure**
- **(h)** Cryptographic controls and encryption
- **(i)** Human resources security and access control
- **(j)** Access control policies and asset management
- **(k)** Security assessments and testing
- **(l)** Cybersecurity training and **basic cyber hygiene**
- **(m)** Cryptographic policies and procedures
- **(n)** **Physical and environmental security**

**Article 21(3)**: Proportionate measures based on state of the art

**Questionnaire Coverage**: Questions NIS2-21.1 through NIS2-Crypto-01 (50+ questions covering all measures)

### Article 22: Supply Chain Security
Managing cybersecurity risks in the supply chain

**Requirements**:
- Assess cybersecurity risks from supplier relationships
- Incorporate security measures into contracts
- Identify all direct ICT suppliers and assess their security
- Monitor suppliers on an ongoing basis

**Questionnaire Coverage**: Questions NIS2-22.1 through NIS2-Supply-05 (10 questions)

### Article 23: Reporting Obligations
Incident notification to authorities

**Reporting Timelines**:
1. **Early Warning**: Within **24 hours** of becoming aware of significant incident
2. **Full Notification**: Within **72 hours** with detailed incident information
3. **Progress Reports**: As requested during ongoing incidents
4. **Final Report**: Within **1 month** with root cause analysis

**Additional Requirements**:
- Report significant cyber threats (even without incidents)
- Notify service recipients when incidents affect them

**Questionnaire Coverage**: Questions NIS2-23.1 through NIS2-23.5 (5 questions)

## Using the NIS2 Questionnaire

### Questionnaire Structure

The NIS2 questionnaire contains **70 questions** organized by:

1. **Governance (Article 20)** - 4 questions
2. **Cybersecurity Risk Management (Article 21)** - 48 questions
3. **Supply Chain Security (Articles 21.2 & 22)** - 13 questions
4. **Incident Handling** - 3 questions
5. **Business Continuity** - 4 questions
6. **Network Security** - 4 questions
7. **Access Control & Authentication** - 5 questions
8. **Cryptography** - 3 questions
9. **Vulnerability Management** - 5 questions
10. **Reporting Obligations (Article 23)** - 5 questions

### Question Format

Each question includes:
- **Question ID**: Maps to specific NIS2 article (e.g., NIS2-21.2.e for MFA requirement)
- **Regulatory Source**: Exact article, paragraph, and requirement
- **Category/Subcategory**: Logical grouping
- **Question Text**: Clear question for the vendor
- **Description**: Context and what assessors should look for
- **Required Evidence**: Documents/artifacts that demonstrate compliance
- **SCF Control Mappings**: Maps to Secure Controls Framework
- **Evaluation Rubric**: Patterns for acceptable/unacceptable answers
- **Risk Level**: Critical/High/Medium/Low if inadequate

### Assessment Workflow

#### Step 1: Determine Applicability
```
Is the vendor:
- An essential or important entity under NIS2?
- A supplier of network and information systems?
- Located in or serving EU markets?

If YES → Use NIS2 questionnaire
If vendor is also subject to DORA → Consider combined assessment
```

#### Step 2: Generate Questionnaire
```python
# Using tprm-frameworks-mcp server
questionnaire_id = generate_questionnaire(
    framework="nis2_supply_chain",
    vendor_name="Acme Cloud Services",
    vendor_context={
        "sector": "digital_infrastructure",
        "entity_type": "essential",  # or "important"
        "services": ["cloud_hosting", "managed_security"]
    }
)
```

#### Step 3: Distribute and Collect Responses
- Send questionnaire to vendor
- Request evidence documents (policies, certifications, test results)
- Set response deadline (recommend 2-4 weeks for comprehensive answers)

#### Step 4: Evaluate Responses
```python
# Evaluate vendor responses
assessment_results = evaluate_response(
    questionnaire_id=questionnaire_id,
    responses=vendor_responses,
    strictness="moderate"  # lenient/moderate/strict
)
```

#### Step 5: Map to SCF Controls
```python
# Get SCF control mappings
control_mappings = map_questionnaire_to_controls(
    questionnaire_id=questionnaire_id
)

# Cross-reference with security-controls-mcp for detailed control requirements
```

#### Step 6: Risk Assessment and Reporting
- Review overall score and individual question scores
- Identify critical/high-risk gaps
- Generate assessment report
- Define remediation requirements for vendor

## Key NIS2-Specific Requirements

### Multi-Factor Authentication (Article 21(2)(e))
**Mandatory** - NIS2 explicitly requires MFA or continuous authentication

**Questions**: NIS2-21.2.e, NIS2-Access-01

**What to Look For**:
- MFA implemented for all users or at minimum privileged users
- MFA enforced, not optional
- Continuous authentication solutions as alternative
- Secured voice, video, text communications

### Vulnerability Disclosure (Article 21(2)(g))
Vulnerability disclosure policy required

**Questions**: NIS2-21.2.g, NIS2-Vuln-01, NIS2-Vuln-02

**What to Look For**:
- Public vulnerability disclosure policy
- Coordinated disclosure process
- Communication channels for researchers
- Timely vulnerability remediation

### Physical Security (Article 21(2)(n))
Physical and environmental security measures

**Questions**: NIS2-21.2.n

**What to Look For**:
- Physical access controls for data centers
- Environmental controls (fire suppression, HVAC, power)
- CCTV and monitoring systems
- Personnel security measures

### Cyber Hygiene (Article 21(2)(l))
Basic cyber hygiene practices for all personnel

**Questions**: NIS2-21.2.l

**What to Look For**:
- Regular security awareness training for all staff
- Practical cybersecurity guidance
- Phishing simulations
- Password hygiene, software updates, secure browsing

### Emergency Communications (Article 21(2)(f))
Secured emergency communication systems operational during crises

**Questions**: NIS2-21.2.f

**What to Look For**:
- Backup communication systems
- Crisis communication plan
- Testing of emergency communications
- Redundancy and resilience

## DORA and NIS2 Combined Assessment

### When to Use Combined Assessment

Use combined assessment when:
1. Vendor is subject to **both** DORA and NIS2 (e.g., financial entity that is also an essential entity)
2. Your organization needs compliance with both regulations
3. Vendor serves both financial sector (DORA) and other critical sectors (NIS2)

### Overlapping Requirements

**Major Overlap Areas**:
1. **Governance**: Management oversight, board accountability
2. **Supply Chain Security**: Vendor risk assessment, contractual requirements, ongoing monitoring
3. **Incident Response**: Detection, response, reporting (different timelines)
4. **Business Continuity**: BCP, DR, backup management, RTO/RPO
5. **Risk Management**: Risk assessment, proportionate controls
6. **Testing**: Security testing, penetration testing, control effectiveness

**Shared SCF Controls**: 87 unique SCF controls cover both DORA and NIS2

### Unique to DORA
- **ICT Concentration Risk** assessment and mitigation
- **Exit Strategies** for all critical ICT third-party services
- **Threat-Led Penetration Testing (TLPT)** for critical entities
- **ICT Third-Party Register** requirement
- **4-hour** initial incident notification (stricter than NIS2)

### Unique to NIS2
- **Mandatory MFA** (explicit requirement)
- **Vulnerability Disclosure** policy
- **Physical Security** requirements
- **Cyber Hygiene** training for all personnel
- **Emergency Communications** systems
- **Cyber Threat Notification** (proactive threat sharing)
- **Service Recipient Notification** of incidents

### Combined Assessment Strategy

**Option 1: Use Both Questionnaires**
- Administer both DORA ICT and NIS2 questionnaires
- Identify overlapping questions and consolidate responses
- Ensure unique requirements from each regulation are covered

**Option 2: Enhanced NIS2 with DORA Addendum**
- Use NIS2 as base questionnaire (broader scope)
- Add DORA-specific questions for:
  - ICT concentration risk
  - Exit strategies
  - TLPT requirements
  - ICT third-party register

**Option 3: Integrated Control Mapping**
- Map both DORA and NIS2 to SCF controls
- Assess vendor against unified SCF control set
- Document compliance with both regulations

**Recommended Approach**: Option 3 provides most efficient assessment with comprehensive coverage

## Reporting Timelines Comparison

| Regulation | Early Warning | Full Notification | Final Report |
|------------|--------------|-------------------|--------------|
| **NIS2** | 24 hours | 72 hours | 1 month |
| **DORA** | 4 hours | 72 hours (intermediate) | 1 month |

**Key Difference**: DORA has **stricter 4-hour initial notification** for major ICT incidents

**Recommendation**: If subject to both, implement processes for **4-hour notification** to satisfy both

## SCF Control Domains for NIS2

### Primary Control Families

1. **Governance (GOV)**: GOV-01, GOV-02, GOV-03, GOV-04, GOV-06, GOV-08
2. **Third-Party Management (TPM)**: TPM-01 through TPM-08
3. **Incident Response (IRO)**: IRO-01, IRO-02, IRO-05, IRO-06, IRO-07, IRO-08, IRO-09, IRO-10
4. **Business Continuity (BCD)**: BCD-01, BCD-02, BCD-03, BCD-05, BCD-06, BCD-07, BCD-08, BCD-09, BCD-11
5. **Access Control (IAC)**: IAC-01 through IAC-12
6. **Network Security (NET)**: NET-01, NET-02, NET-04, NET-06
7. **Cryptography (CRY)**: CRY-01 through CRY-08
8. **Vulnerability Management (TVM)**: TVM-01 through TVM-04
9. **Risk Management (RSK)**: RSK-01, RSK-02, RSK-03, RSK-04, RSK-06, RSK-07
10. **Physical Security (PES)**: PES-01, PES-02, PES-03
11. **Human Resources Security (HRS)**: HRS-01, HRS-02, HRS-07, HRS-08
12. **Monitoring (MON)**: MON-01, MON-02, MON-08
13. **Application Security (APP)**: APP-01, APP-02
14. **Compliance (CPL)**: CPL-01, CPL-02

### Using SCF for Cross-Framework Compliance

The SCF provides a unified control framework that maps to multiple regulations:

```python
# Get NIS2 question's SCF controls
scf_controls = get_scf_controls_for_question("NIS2-22.1")
# Returns: ["TPM-01", "TPM-02", "RSK-03"]

# Map to other frameworks
for control_id in scf_controls:
    control_details = security_controls_mcp.get_control(control_id)
    # Shows how same control maps to ISO 27001, NIST CSF, CIS Controls, etc.
```

## Best Practices

### For Assessors

1. **Start with Risk Assessment**: Focus on critical suppliers first
2. **Request Evidence**: Don't rely only on yes/no answers
3. **Validate Certifications**: Check ISO 27001, SOC 2, or other certifications
4. **Review Incidents**: Ask about past security incidents and lessons learned
5. **Test Procedures**: Ask for evidence of testing (BCP tests, pen tests, etc.)
6. **Verify Timelines**: Ensure incident notification timelines meet NIS2 requirements

### For Vendors

1. **Prepare Evidence Package**: Gather policies, procedures, certifications, test reports
2. **Be Specific**: Provide detailed answers with examples
3. **Show Maturity**: Demonstrate continuous improvement and testing
4. **Document Everything**: Have documented processes for all requirements
5. **Highlight Compliance**: Note ISO 27001, SOC 2, or other relevant certifications
6. **Be Transparent**: Disclose gaps with remediation plans

### For Organizations Subject to Both DORA and NIS2

1. **Unified Governance**: Single board/management oversight for cyber resilience
2. **Integrated Risk Framework**: One ICT risk management framework covering both
3. **Combined TPRM Program**: Single third-party risk management process
4. **Strictest Timelines**: Implement 4-hour incident notification (DORA requirement)
5. **Comprehensive Testing**: Include both DORA TLPT and NIS2 testing requirements
6. **Unified Reporting**: Consolidated compliance dashboard for both regulations

## Resources

### Official NIS2 Resources
- [NIS2 Directive (EU 2022/2555)](https://eur-lex.europa.eu/eli/dir/2022/2555/oj)
- [ENISA NIS2 Guidance](https://www.enisa.europa.eu/)
- National competent authorities (varies by Member State)
- National CSIRTs

### Related Frameworks
- **DORA**: Digital Operational Resilience Act (financial sector)
- **ISO 27001:2022**: Information Security Management
- **ISO 22301**: Business Continuity Management
- **ISO 27035**: Incident Management
- **NIST Cybersecurity Framework**: Risk-based cybersecurity framework
- **SCF**: Secure Controls Framework (meta-framework)

### Tools
- **tprm-frameworks-mcp**: Generate and evaluate NIS2 questionnaires
- **security-controls-mcp**: Get detailed SCF control requirements
- **eu-regulations-mcp**: Query NIS2 articles and requirements (planned)

## Appendix: Question Quick Reference

### Article 20 Questions (Governance)
- **NIS2-20.1**: Management body oversight and approval
- **NIS2-20.2**: Management cybersecurity training
- **NIS2-Compliance-01**: NIS2 compliance program
- **NIS2-Compliance-02**: Authority and CSIRT coordination

### Article 21.2 Questions (Risk Management Measures)
- **NIS2-21.2.a**: Incident handling procedures
- **NIS2-21.2.b**: Business continuity, backup, DR
- **NIS2-21.2.c**: Security in acquisition, development, maintenance
- **NIS2-21.2.d**: Network security and segmentation
- **NIS2-21.2.e**: Multi-factor authentication
- **NIS2-21.2.e.2**: Secured communications
- **NIS2-21.2.f**: Emergency communication systems
- **NIS2-21.2.g**: Vulnerability handling and disclosure
- **NIS2-21.2.h**: Encryption and cryptographic controls
- **NIS2-21.2.i**: Human resources security
- **NIS2-21.2.j**: Access control and asset management
- **NIS2-21.2.k**: Security effectiveness assessments
- **NIS2-21.2.l**: Training and cyber hygiene
- **NIS2-21.2.m**: Cryptographic policies
- **NIS2-21.2.n**: Physical and environmental security

### Article 22 Questions (Supply Chain)
- **NIS2-22.1**: Supply chain risk assessment
- **NIS2-22.2**: Contractual security requirements
- **NIS2-22.3**: ICT supplier identification and assessment
- **NIS2-22.4**: Ongoing supplier monitoring
- **NIS2-22.5**: Subcontractor visibility
- **NIS2-Supply-01** through **NIS2-Supply-05**: Enhanced supply chain questions

### Article 23 Questions (Reporting)
- **NIS2-23.1**: Early warning notification (24 hours)
- **NIS2-23.2**: Full incident notification (72 hours)
- **NIS2-23.3**: Progress and final reports
- **NIS2-23.4**: Cyber threat notification
- **NIS2-23.5**: Service recipient notification

---

**Document Version**: 1.0
**Last Updated**: January 2024
**Regulation**: EU Directive 2022/2555 (NIS2)
**Compliance Deadline**: October 17, 2024
