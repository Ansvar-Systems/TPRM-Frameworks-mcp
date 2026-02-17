# Before/After Comparison: Regulatory Mappings Fix

## The Problem

The `regulatory_mappings` field in DORA and NIS2 JSON files was incorrectly structured as a dictionary/object when it should have been an array of strings. This caused:

1. Type mismatch issues in data processing
2. Inconsistency with other questionnaire frameworks
3. Potential parsing errors
4. Difficulty in generating reports and mappings

## Before (Incorrect Structure)

### Example Question - BEFORE

```json
{
  "id": "DORA-28.1.1",
  "category": "ICT Third-Party Risk Management",
  "question_text": "Has your organization established ICT third-party risk management processes?",
  "weight": 10,
  
  "regulatory_mappings": {
    "regulation": "DORA",
    "article": "28",
    "paragraph": "1",
    "requirement": "ICT third-party risk management framework"
  },
  
  "scf_control_mappings": ["TPM-01", "GOV-01"],
  "risk_if_inadequate": "critical"
}
```

**Issues:**
- `regulatory_mappings` is an object (wrong!)
- Cannot easily display or iterate as strings
- Inconsistent with other frameworks
- Missing human-readable references
- Some questions missing `regulatory_source` entirely

## After (Correct Structure)

### Example Question - AFTER

```json
{
  "id": "DORA-28.1.1",
  "category": "ICT Third-Party Risk Management",
  "question_text": "Has your organization established ICT third-party risk management processes?",
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
  
  "scf_control_mappings": ["TPM-01", "GOV-01"],
  "risk_if_inadequate": "critical"
}
```

**Benefits:**
- `regulatory_mappings` is an array of strings (correct!)
- Easy to display and iterate
- Human-readable format
- Includes ISO 27001 cross-references
- `regulatory_source` provides structured metadata for filtering
- Both fields present on all questions

## Changes Made

### 1. Converted regulatory_mappings to Arrays

**DORA:**
```python
# Before
"regulatory_mappings": {
  "regulation": "DORA",
  "article": "28",
  ...
}

# After
"regulatory_mappings": [
  "DORA - Article 28",
  "ISO 27001:2022 - A.15"
]
```

**NIS2:**
```python
# Before
"regulatory_mappings": {
  "regulation": "NIS2",
  "article": "21",
  ...
}

# After
"regulatory_mappings": [
  "NIS2 - Article 21",
  "ISO 27001:2022 - various"
]
```

### 2. Added regulatory_source Field

For questions missing the `regulatory_source` field, we added it:

```json
"regulatory_source": {
  "regulation": "DORA",
  "article": "28",
  "requirement": "ICT third-party risk management framework"
}
```

## Field Purposes

### regulatory_mappings (Array of Strings)
**Purpose:** Human-readable references for display in reports and UI

**Use Cases:**
- Displaying regulation references in questionnaires
- Generating compliance reports
- Cross-referencing with other frameworks (ISO 27001, NIST, etc.)
- Export to PDF/Excel reports

**Example Display:**
```
Regulatory References:
- DORA - Article 28
- ISO 27001:2022 - A.15
```

### regulatory_source (Object)
**Purpose:** Structured metadata for programmatic filtering and processing

**Use Cases:**
- Filtering questions by regulation
- Grouping by article
- Building article-level reports
- API queries (e.g., "get all Article 28 questions")
- Validation and compliance checking

**Example Query:**
```python
# Get all Article 28 questions
questions = [q for q in questions if q.regulatory_source['article'] == '28']
```

## Validation Results

### DORA ICT Third-Party Provider
- **Total Questions:** 71
- **Fixed regulatory_mappings:** 71/71 (100%)
- **Added regulatory_source:** 24/71 (34%)
- **Status:** ✓ All checks passed

### NIS2 Supply Chain Security
- **Total Questions:** 73
- **Fixed regulatory_mappings:** 73/73 (100%)
- **Added regulatory_source:** 32/73 (44%)
- **Status:** ✓ All checks passed

## Impact on Code

### Data Loader Compatibility
The `TPRMDataLoader` class successfully loads both questionnaires:

```python
from tprm_frameworks_mcp.data_loader import TPRMDataLoader

loader = TPRMDataLoader()

# Load DORA questions
dora_questions = loader.get_questions('dora_ict_tpp')
# Returns 71 Question objects with correct structure

# Load NIS2 questions
nis2_questions = loader.get_questions('nis2_supply_chain')
# Returns 73 Question objects with correct structure
```

### Question Object Structure
Each Question object now has:

```python
question.regulatory_mappings  # List[str]
# ["DORA - Article 28", "ISO 27001:2022 - A.15"]

question.regulatory_source    # dict (via Question model)
# Accessed through question attributes in the dataclass
```

## Documentation Created

Three new reference documents were created:

1. **DATA_STRUCTURE_FIX_SUMMARY.md**
   - Detailed summary of all changes
   - Statistics and validation results
   - Impact assessment

2. **REGULATORY_FIELDS_REFERENCE.md**
   - Complete field specification
   - Examples for all frameworks
   - Validation guidelines
   - Common mistakes to avoid

3. **DATA_FIX_VERIFICATION.txt**
   - Automated verification report
   - All validation checks
   - Article distribution
   - Final status confirmation

## Files Modified

1. `/src/tprm_frameworks_mcp/data/dora_ict_tpp.json` (71 questions)
2. `/src/tprm_frameworks_mcp/data/nis2_supply_chain.json` (73 questions)

## Backwards Compatibility

This change is **not backwards compatible** with code that expects `regulatory_mappings` to be an object. However:

- The `TPRMDataLoader` handles the new structure correctly
- The `Question` dataclass expects the correct structure
- All MCP server tools work with the fixed data

If you have custom code that accesses `regulatory_mappings`, update it:

```python
# OLD (no longer works)
regulation = question.regulatory_mappings['regulation']

# NEW (correct)
primary_mapping = question.regulatory_mappings[0]  # "DORA - Article 28"
regulation = question.regulatory_source['regulation']  # "DORA"
```

## Testing Performed

1. JSON structure validation (types, presence of fields)
2. Data loader compatibility test
3. Question object instantiation test
4. Regulatory reference cross-check
5. ISO 27001 mapping validation

**Result:** All tests passed ✓

## Next Steps

When adding new questionnaires:

1. Use array of strings for `regulatory_mappings`
2. Include `regulatory_source` as an object
3. Follow examples in `REGULATORY_FIELDS_REFERENCE.md`
4. Validate with `TPRMDataLoader` before committing
5. Run structure validation script

---

**Fix Date:** 2026-02-07  
**Questions Fixed:** 144 (71 DORA + 73 NIS2)  
**Status:** Complete ✓  
**Validation:** All checks passed ✓
