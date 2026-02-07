# Data Structure Fix Summary

## Issue Overview

The DORA and NIS2 JSON data files had a critical structural error where `regulatory_mappings` was incorrectly stored as a dictionary object instead of an array of strings. This violated the expected data structure and could cause parsing or processing issues.

## Fixes Applied

### 1. Fixed `regulatory_mappings` Structure

**Before (Incorrect):**
```json
{
  "regulatory_mappings": {
    "regulation": "DORA",
    "article": "28",
    "paragraph": "1",
    "requirement": "ICT third-party risk management framework"
  }
}
```

**After (Correct):**
```json
{
  "regulatory_mappings": [
    "DORA - Article 28",
    "ISO 27001:2022 - A.15"
  ]
}
```

### 2. Added Missing `regulatory_source` Fields

Some questions were missing the `regulatory_source` field entirely. This structured field provides detailed regulatory metadata.

**Added to all questions:**
```json
{
  "regulatory_source": {
    "regulation": "DORA",
    "article": "28",
    "requirement": "ICT third-party risk management framework"
  }
}
```

## Files Modified

### DORA ICT Third-Party Provider Assessment
- **File:** `/src/tprm_frameworks_mcp/data/dora_ict_tpp.json`
- **Total Questions:** 71
- **Fixed regulatory_mappings:** 71/71 questions (100%)
- **Added regulatory_source:** 24/71 questions

**Mapping Rules Applied:**
- Article 28 → `["DORA - Article 28", "ISO 27001:2022 - A.15"]`
- Article 29 → `["DORA - Article 29", "ISO 27001:2022 - A.15"]`
- Article 30 → `["DORA - Article 30", "ISO 27001:2022 - A.15"]`

**Article Distribution:**
- Article 28: 16 questions
- Article 29: 27 questions
- Article 30: 9 questions
- General/Other: 19 questions

### NIS2 Supply Chain Security Assessment
- **File:** `/src/tprm_frameworks_mcp/data/nis2_supply_chain.json`
- **Total Questions:** 73
- **Fixed regulatory_mappings:** 73/73 questions (100%)
- **Added regulatory_source:** 32/73 questions

**Mapping Rules Applied:**
- Article 20 → `["NIS2 - Article 20", "ISO 27001:2022 - 5.1"]`
- Article 21 → `["NIS2 - Article 21", "ISO 27001:2022 - various"]`
- Article 22 → `["NIS2 - Article 22", "ISO 27001:2022 - A.15"]`
- Article 23 → `["NIS2 - Article 23", "ISO 27001:2022 - A.16"]`

**Article Distribution:**
- Article 20: 2 questions (Governance)
- Article 21: 21 questions (Risk Management)
- Article 22: 9 questions (Supply Chain Security)
- Article 23: 9 questions (Incident Reporting)
- General/Other: 32 questions

## Verification Results

### Structure Validation
✓ All 144 questions now have correct structure:
- `regulatory_mappings`: Array of strings ✓
- `regulatory_source`: Dictionary/object ✓
- Both fields present on all questions ✓

### Data Loader Compatibility
✓ TPRMDataLoader successfully loads both questionnaires:
- DORA: 71 questions loaded and validated
- NIS2: 73 questions loaded and validated

### Sample Verification

**DORA Example:**
```json
{
  "id": "DORA-28.1.1",
  "regulatory_mappings": [
    "DORA - Article 28",
    "ISO 27001:2022 - A.15"
  ],
  "regulatory_source": {
    "regulation": "DORA",
    "article": "28",
    "requirement": "ICT third-party risk management framework"
  }
}
```

**NIS2 Example:**
```json
{
  "id": "NIS2-20.1",
  "regulatory_mappings": [
    "NIS2 - Article 20",
    "ISO 27001:2022 - 5.1"
  ],
  "regulatory_source": {
    "regulation": "NIS2",
    "article": "20",
    "requirement": "Governance framework"
  }
}
```

## Data Structure Specification

For future reference, all questions must have:

### regulatory_mappings (Array of Strings)
- **Type:** Array
- **Purpose:** Human-readable regulatory references
- **Format:** `["Regulation - Article X", "ISO Standard - Section Y"]`
- **Required:** Yes

### regulatory_source (Object)
- **Type:** Dictionary/Object
- **Purpose:** Structured regulatory metadata for programmatic processing
- **Required Fields:**
  - `regulation`: String (e.g., "DORA", "NIS2")
  - `article`: String (e.g., "28", "20")
  - `requirement`: String (description of requirement)
- **Optional Fields:**
  - `paragraph`: String (for fine-grained references)
- **Required:** Yes

## Impact

This fix ensures:
1. Consistent data structure across all questionnaires
2. Proper parsing by the TPRMDataLoader
3. Compatibility with MCP server tools
4. Accurate regulatory mapping and reporting
5. Future-proof structure for additional frameworks

## Next Steps

When adding new questionnaires or questions:
1. Always use array of strings for `regulatory_mappings`
2. Always include `regulatory_source` as an object
3. Follow the examples in this document
4. Validate with TPRMDataLoader before committing

---

**Fixed on:** 2026-02-07
**Total Questions Fixed:** 144 (71 DORA + 73 NIS2)
**Validation Status:** ✓ All checks passed
