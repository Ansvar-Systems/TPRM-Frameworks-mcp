# Regulatory Fields Reference Guide

## Quick Reference

Every question in TPRM questionnaires MUST have both of these fields:

1. **regulatory_mappings** - Array of human-readable strings
2. **regulatory_source** - Structured object with metadata

## Field Specifications

### regulatory_mappings (REQUIRED)

**Type:** Array of Strings
**Purpose:** Human-readable regulatory references for display and reporting

**Format:**
```json
"regulatory_mappings": [
  "Regulation Name - Article X",
  "Standard Name - Section Y",
  "Framework Name - Control Z"
]
```

**Examples:**

DORA:
```json
"regulatory_mappings": [
  "DORA - Article 28",
  "ISO 27001:2022 - A.15"
]
```

NIS2:
```json
"regulatory_mappings": [
  "NIS2 - Article 21",
  "ISO 27001:2022 - various"
]
```

SIG Lite:
```json
"regulatory_mappings": [
  "CSA SIG Lite v1.0",
  "ISO 27001:2022 - 5.2"
]
```

CAIQ v4:
```json
"regulatory_mappings": [
  "CSA CAIQ v4.0",
  "ISO 27001:2022 - A.15"
]
```

---

### regulatory_source (REQUIRED)

**Type:** Object/Dictionary
**Purpose:** Structured metadata for programmatic processing and filtering

**Required Fields:**
- `regulation` (string): Short name of regulation/framework
- `article` (string): Article/section number
- `requirement` (string): Brief description of the requirement

**Optional Fields:**
- `paragraph` (string): Sub-section or paragraph number
- `subparagraph` (string): Fine-grained reference

**Format:**
```json
"regulatory_source": {
  "regulation": "REGULATION_NAME",
  "article": "ARTICLE_NUMBER",
  "requirement": "Description of requirement",
  "paragraph": "OPTIONAL_PARAGRAPH"
}
```

**Examples:**

DORA Article 28:
```json
"regulatory_source": {
  "regulation": "DORA",
  "article": "28",
  "requirement": "ICT third-party risk management framework"
}
```

DORA Article 29 (with paragraph):
```json
"regulatory_source": {
  "regulation": "DORA",
  "article": "29",
  "paragraph": "3",
  "requirement": "Audit rights and access to premises"
}
```

NIS2 Article 20:
```json
"regulatory_source": {
  "regulation": "NIS2",
  "article": "20",
  "requirement": "Governance framework"
}
```

NIS2 Article 21:
```json
"regulatory_source": {
  "regulation": "NIS2",
  "article": "21",
  "requirement": "Cybersecurity risk management measures"
}
```

Non-regulatory (SIG, CAIQ):
```json
"regulatory_source": {
  "regulation": "CSA_SIG",
  "article": "Security & Privacy",
  "requirement": "Data Protection & Privacy"
}
```

---

## Complete Question Example

```json
{
  "id": "DORA-28.1.1",
  "category": "ICT Third-Party Risk Management",
  "subcategory": "Due Diligence - Risk Management Framework",
  "question_text": "Has your organization established and implemented comprehensive ICT third-party risk management processes?",
  "description": "DORA requires financial entities to manage ICT third-party risk as an integral part of their ICT risk management framework.",
  "expected_answer_type": "yes_no",
  "is_required": true,
  "weight": 10,

  "regulatory_mappings": [
    "DORA - Article 28",
    "ISO 27001:2022 - A.15"
  ],

  "regulatory_source": {
    "regulation": "DORA",
    "article": "28",
    "paragraph": "1",
    "requirement": "ICT third-party risk management framework"
  },

  "scf_control_mappings": [
    "TPM-01",
    "TPM-02",
    "GOV-01"
  ],
  "risk_if_inadequate": "critical"
}
```

---

## Validation Rules

### regulatory_mappings
- MUST be an array (not an object)
- MUST contain at least one string
- All items MUST be strings
- Should include primary regulation/framework reference
- Should include relevant standards (ISO 27001, NIST, etc.)

### regulatory_source
- MUST be an object (not an array)
- MUST contain `regulation` field
- MUST contain `article` field
- MUST contain `requirement` field
- MAY contain `paragraph` field
- MAY contain `subparagraph` field

---

## Common Mistakes to Avoid

### ❌ WRONG: regulatory_mappings as object
```json
"regulatory_mappings": {
  "regulation": "DORA",
  "article": "28"
}
```

### ✓ CORRECT: regulatory_mappings as array
```json
"regulatory_mappings": [
  "DORA - Article 28",
  "ISO 27001:2022 - A.15"
]
```

---

### ❌ WRONG: Missing regulatory_source
```json
{
  "id": "DORA-28.1.1",
  "regulatory_mappings": ["DORA - Article 28"]
  // Missing regulatory_source field!
}
```

### ✓ CORRECT: Both fields present
```json
{
  "id": "DORA-28.1.1",
  "regulatory_mappings": ["DORA - Article 28", "ISO 27001:2022 - A.15"],
  "regulatory_source": {
    "regulation": "DORA",
    "article": "28",
    "requirement": "ICT third-party risk management framework"
  }
}
```

---

## Mapping Guidelines by Regulation

### DORA (Digital Operational Resilience Act)

**Articles to use:**
- Article 28: ICT third-party risk management
- Article 29: Key contractual provisions
- Article 30: Register of information

**ISO 27001 mappings:**
- Article 28 → ISO 27001:2022 - A.15 (Supplier relationships)
- Article 29 → ISO 27001:2022 - A.15 (Supplier relationships)
- Article 30 → ISO 27001:2022 - A.15 (Supplier relationships)

---

### NIS2 (Network and Information Security Directive)

**Articles to use:**
- Article 20: Governance
- Article 21: Cybersecurity risk management
- Article 22: Supply chain security
- Article 23: Incident reporting

**ISO 27001 mappings:**
- Article 20 → ISO 27001:2022 - 5.1 (Policies)
- Article 21 → ISO 27001:2022 - various (risk management)
- Article 22 → ISO 27001:2022 - A.15 (Supplier relationships)
- Article 23 → ISO 27001:2022 - A.16 (Incident management)

---

### SIG (Standardized Information Gathering)

**Format:**
```json
"regulatory_mappings": ["CSA SIG Lite v1.0", "ISO 27001:2022 - relevant section"],
"regulatory_source": {
  "regulation": "CSA_SIG",
  "article": "Category Name",
  "requirement": "Specific requirement description"
}
```

---

### CAIQ (Consensus Assessments Initiative Questionnaire)

**Format:**
```json
"regulatory_mappings": ["CSA CAIQ v4.0", "ISO 27001:2022 - relevant section"],
"regulatory_source": {
  "regulation": "CSA_CAIQ",
  "article": "Domain Name",
  "requirement": "Specific control description"
}
```

---

## Validation Commands

**Check structure:**
```bash
python3 -c "
import json
with open('src/tprm_frameworks_mcp/data/YOUR_FILE.json', 'r') as f:
    data = json.load(f)
    for q in data['questions']:
        assert isinstance(q['regulatory_mappings'], list), f\"{q['id']}: not a list\"
        assert isinstance(q['regulatory_source'], dict), f\"{q['id']}: not a dict\"
print('✓ All checks passed')
"
```

**Load with DataLoader:**
```bash
python3 -c "
import sys
sys.path.insert(0, 'src')
from tprm_frameworks_mcp.data_loader import TPRMDataLoader
loader = TPRMDataLoader()
questions = loader.get_questions('YOUR_FRAMEWORK_KEY')
print(f'✓ Loaded {len(questions)} questions')
"
```

---

## Summary

**Two fields, two purposes:**

1. **regulatory_mappings (array)** → For humans (display, reports)
2. **regulatory_source (object)** → For machines (filtering, processing)

Both are required. Both must be present on every question.

---

**Last Updated:** 2026-02-07
**Status:** Production Standard
