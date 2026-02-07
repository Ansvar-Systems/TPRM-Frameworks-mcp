# Agent 2 Handoff - SCF Control Mapping Task

## Your Mission

Map all 283 CAIQ v4.1 questions to relevant Secure Controls Framework (SCF) controls.

## Input File

**Location**: `/Users/jeffreyvonrotz/Projects/TPRM-Frameworks-mcp/src/tprm_frameworks_mcp/data/caiq_v4_full.json`

**Status**: ✅ Complete, validated, production-ready
**Questions**: 283
**Current SCF Mappings**: 0 (all empty arrays, ready for you to populate)

## Your Task

For each of the 283 questions in `caiq_v4_full.json`, populate the `scf_control_mappings` array with relevant SCF control IDs.

### Example Question Structure

```json
{
  "id": "A&A-01.1",
  "category": "Audit & Assurance",
  "subcategory": "Audit and Assurance Policy and Procedures",
  "question_text": "Are audit and assurance policies, procedures, and standards established, documented, approved, communicated, applied, evaluated, and maintained?",
  "description": "Establish, document, approve, communicate, apply, evaluate and maintain audit and assurance policies and procedures and standards. Review and update the policies and procedures at least annually, or upon significant changes.",
  "ccm_control_id": "A&A-01",
  "scf_control_mappings": [],  // ⬅️ YOUR JOB: Fill this array
  "risk_if_inadequate": "high"
}
```

### Expected Output

```json
{
  "id": "A&A-01.1",
  "scf_control_mappings": ["GOV-03", "CPL-01", "CPL-02"],  // ⬅️ You add these
  // ... other fields unchanged
}
```

## Available Resources

### 1. CCM-to-SCF Mapping Reference

You have access to the existing CCM control mappings. Since each question has a `ccm_control_id`, you can use that to find relevant SCF controls.

### 2. security-controls-mcp Integration

The project integrates with `security-controls-mcp` which has full SCF data. You can query it to:
1. Search for relevant SCF controls based on keywords
2. Get control details
3. Verify control IDs exist

### 3. Existing Mappings

Check `/Users/jeffreyvonrotz/Projects/TPRM-Frameworks-mcp/src/tprm_frameworks_mcp/data/questionnaire-to-scf.json` for examples of existing mappings from other frameworks.

## Approach

### Option 1: Use CCM-to-SCF Mapping (Recommended)

1. Since each question has a `ccm_control_id`, create or use a CCM→SCF mapping table
2. Map all 207 unique CCM controls to SCF controls
3. Apply mappings to all 283 questions based on their CCM control ID

### Option 2: Keyword-Based Mapping

1. Use question text, description, and category to determine relevant SCF domains
2. Query security-controls-mcp for matching controls
3. Add 2-5 most relevant SCF controls per question

### Option 3: Hybrid Approach

1. Start with CCM→SCF mapping for consistency
2. Enhance with keyword-based additions for comprehensive coverage
3. Validate mappings using security-controls-mcp

## Quality Criteria

Your mapping should ensure:

1. ✅ All 283 questions have at least 1 SCF control mapping
2. ✅ SCF control IDs are valid (exist in SCF framework)
3. ✅ Mappings are relevant to the question content
4. ✅ Questions covering similar topics have consistent mappings
5. ✅ High-risk questions map to appropriate high-priority SCF controls

## Validation

Create a validation script that:
1. Checks all questions have SCF mappings
2. Verifies all SCF control IDs exist
3. Shows mapping distribution (avg mappings per question, etc.)
4. Identifies questions with no mappings or too many mappings

## Expected Output Files

1. **Updated JSON**: `caiq_v4_full.json` with all `scf_control_mappings` populated
2. **Mapping Report**: Statistics and validation results
3. **CCM-SCF Mapping Table**: Reusable mapping reference (if you create one)

## Quick Start

```python
import json

# Load CAIQ v4.1 dataset
with open('src/tprm_frameworks_mcp/data/caiq_v4_full.json', 'r') as f:
    data = json.load(f)

# Check current state
questions = data['questions']
print(f"Total questions: {len(questions)}")
print(f"Unique CCM controls: {len(set(q['ccm_control_id'] for q in questions))}")
print(f"Questions with SCF mappings: {sum(1 for q in questions if q['scf_control_mappings'])}")

# Your mapping logic here...

# Save updated dataset
with open('src/tprm_frameworks_mcp/data/caiq_v4_full.json', 'w') as f:
    json.dump(data, f, indent=2, ensure_ascii=False)
```

## Success Metrics

| Metric | Target |
|--------|--------|
| Questions with SCF mappings | 283/283 (100%) |
| Average mappings per question | 2-5 |
| Valid SCF control IDs | 100% |
| Mapping consistency | High (similar questions have similar mappings) |

## Domain Distribution Reference

You'll be mapping across 17 domains:

1. Audit & Assurance (8 questions)
2. Application & Interface Security (13 questions)
3. Business Continuity Management and Operational Resilience (19 questions)
4. Change Control and Configuration Management (12 questions)
5. Cryptography, Encryption & Key Management (23 questions)
6. Data Security and Privacy Lifecycle Management (24 questions)
7. Datacenter Security (28 questions)
8. Governance, Risk and Compliance (10 questions)
9. Human Resources (20 questions)
10. Identity & Access Management (19 questions)
11. Infrastructure Security (15 questions)
12. Interoperability & Portability (8 questions)
13. Logging and Monitoring (19 questions)
14. Security Incident Management, E-Discovery, & Cloud Forensics (16 questions)
15. Supply Chain Management, Transparency, and Accountability (19 questions)
16. Threat & Vulnerability Management (15 questions)
17. Universal Endpoint Management (15 questions)

## Sample CCM Controls to Map

Your first 10 CCM controls to map:
- A&A-01: Audit and Assurance Policy and Procedures
- A&A-02: Independent Audits
- A&A-03: Audit Results Remediation
- A&A-04: Internal Audits
- A&A-05: External Audit Requirements
- A&A-06: Organization Wide Reviews
- AIS-01: Application Security
- AIS-02: Application Security Baseline Requirements
- AIS-03: Application Security Metrics
- AIS-04: Application Security Development Life Cycle Training

---

**Status**: Ready for Agent 2
**Input**: ✅ Complete and validated
**Waiting for**: Your SCF control mappings

Good luck! 🚀
