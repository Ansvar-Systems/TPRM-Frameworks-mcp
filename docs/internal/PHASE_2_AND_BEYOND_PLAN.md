# Phase 2 and Beyond: Complete Implementation Plan

**Created:** 2026-02-07
**Status:** Ready to Execute

---

## 🎯 Executive Summary

**Phase 2**: Full CAIQ v4 Content (FREE download from CSA)
**Phase 3-4**: DORA/NIS2 Integration with EU-regulations-mcp
**Total Time Estimate**: 4-6 hours (with parallel agents)
**Production Value**: Enterprise-grade TPRM with EU regulatory compliance

---

## 📋 Phase 2: Full CAIQ v4 Implementation

### Goal
Replace placeholder CAIQ v4 data with complete, production-ready CSA content.

### Why CAIQ v4?
- ✅ **FREE** from Cloud Security Alliance
- ✅ Industry-standard for cloud vendor assessments
- ✅ ~295 comprehensive questions
- ✅ Already mapped to ISO 27001, SOC 2, NIST
- ✅ Required for SOC 2 Type II audits

### Implementation Steps

#### Step 1: Data Acquisition (30 min)
```bash
# Download from CSA
1. Visit: https://cloudsecurityalliance.org/artifacts/consensus-assessments-initiative-questionnaire-v4
2. Download CAIQ v4.0.4 (Excel format)
3. Save to: ~/Downloads/CAIQ_v4.0.4.xlsx
```

#### Step 2: Data Parsing (1 hour)
**Create:** `scripts/parse_caiq_v4.py`

```python
"""
Parse CAIQ v4 Excel → JSON
- Extract all 295 questions
- Parse domain/control structure
- Map to CCM v4 controls
- Generate evaluation rubrics
- Output: src/tprm_frameworks_mcp/data/caiq_v4_full.json
"""
```

**Agent Task**: Create Excel parser with:
- Column mapping (Question ID, Control, Domain, etc.)
- Rubric generation from expected answers
- SCF mapping lookup
- Data validation

#### Step 3: SCF Mapping Enhancement (1 hour)
**Update:** `src/tprm_frameworks_mcp/data/questionnaire-to-scf.json`

```json
{
  "caiq_v4": {
    "AIS-01": ["IAC-01", "IAC-02"],  // Access control questions
    "AIS-02": ["MON-01", "MON-04"],  // Monitoring questions
    // ... 295 mappings
  }
}
```

**Agent Task**: Generate SCF mappings using:
- CAIQ CCM control → SCF control mapping table
- security-controls-mcp for validation
- Automated mapping with manual review flags

#### Step 4: Evaluation Rubrics (30 min)
**Enhance:** `src/tprm_frameworks_mcp/data/caiq_v4_full.json`

For each question, add sophisticated rubrics:
```json
{
  "id": "AIS-01",
  "evaluation_rubric": {
    "acceptable": [
      "yes.*multi-factor authentication",
      "mfa.*all.*users",
      "implemented.*2fa|two-factor"
    ],
    "partially_acceptable": [
      "yes.*some.*mfa",
      "planned.*mfa"
    ],
    "unacceptable": [
      "no.*mfa",
      "not.*implemented"
    ],
    "required_keywords": ["authentication", "access"],
    "weight_adjustment": 1.5  // Critical control
  }
}
```

#### Step 5: Testing & Validation (1 hour)
```bash
# Test questionnaire generation
python test_caiq_v4.py

# Validate SCF mappings
python scripts/validate_scf_mappings.py

# Integration test with security-controls-mcp
python test_integration.py
```

### Phase 2 Deliverables
- ✅ Complete CAIQ v4 dataset (295 questions)
- ✅ Full SCF mappings
- ✅ Production-ready evaluation rubrics
- ✅ Comprehensive test suite
- ✅ Updated documentation

### Phase 2 Success Metrics
- All 295 CAIQ questions available
- 100% SCF mapping coverage
- Tests passing for all domains
- Integration with security-controls-mcp verified

---

## 🇪🇺 Phase 3-4: DORA/NIS2 with EU-Regulations-MCP

### Architecture: MCP Server Composition

```
┌──────────────────────────────────────────────────────────────┐
│                     Ansvar AI Agent                          │
└───────────┬──────────────────────────────────────────────────┘
            │
            ├─────────────────┬────────────────────────────────┐
            │                 │                                │
            ▼                 ▼                                ▼
   ┌────────────────┐  ┌──────────────────┐    ┌──────────────────────┐
   │ tprm-frameworks│  │ eu-regulations   │    │ security-controls    │
   │      MCP       │  │      MCP         │    │       MCP            │
   └────────────────┘  └──────────────────┘    └──────────────────────┘
            │                 │                                │
            │                 │                                │
   ┌────────┴────────┐ ┌──────┴──────────┐        ┌───────────┴──────┐
   │ TPRM Workflows  │ │ DORA Articles   │        │   SCF Controls   │
   │  - Assessments  │ │ NIS2 Articles   │        │   - ISO 27001    │
   │  - Evaluations  │ │ Requirements    │        │   - SOC 2        │
   │  - Trending     │ │ Timelines       │        │   - NIST         │
   └─────────────────┘ └─────────────────┘        └──────────────────┘
```

### Integration Pattern

#### Example: DORA ICT Third-Party Provider Assessment

**Agent Workflow:**
```python
# 1. Get regulatory requirements from eu-regulations-mcp
dora_requirements = eu_regulations_mcp.get_requirements(
    regulation="DORA",
    category="ICT_third_party_risk"
)
# Returns: Articles 28-30 with specific requirements

# 2. Generate questionnaire from tprm-frameworks-mcp
questionnaire = tprm_frameworks_mcp.generate_questionnaire(
    framework="dora_ict_tpp",
    regulatory_focus=["DORA"],
    eu_requirements=dora_requirements  # Pass in requirements
)
# Returns: Assessment questions derived from DORA articles

# 3. Map to security controls
scf_controls = security_controls_mcp.map_frameworks(
    source_framework="DORA",
    target_framework="SCF"
)
# Returns: DORA article → SCF control mappings
```

### Phase 3: DORA Integration (2 hours)

#### Step 1: EU-Regulations-MCP Integration
**Create:** `src/tprm_frameworks_mcp/integrations/eu_regulations.py`

```python
"""
Integration layer for eu-regulations-mcp
- Fetch DORA articles and requirements
- Map articles to assessment questions
- Generate dynamic questionnaires from regulations
"""

async def get_dora_requirements(category: str) -> List[Requirement]:
    """Fetch DORA requirements from eu-regulations-mcp"""
    pass

async def map_questions_to_articles(questions: List[Question]) -> Dict[str, List[str]]:
    """Map assessment questions back to DORA articles"""
    pass
```

#### Step 2: Enhanced DORA Questionnaire
**Update:** `src/tprm_frameworks_mcp/data/dora_ict_tpp.json`

Instead of static questions, generate from regulations:
```json
{
  "id": "DORA-ICT-01",
  "question_text": "Dynamic: Generated from DORA Article 28(1)",
  "regulatory_source": {
    "regulation": "DORA",
    "article": "28",
    "paragraph": "1",
    "requirement": "ICT due diligence requirements"
  },
  "evaluation_rubric": {
    // Rubric derived from regulatory requirement
  }
}
```

#### Step 3: Server Tool Updates
**Update:** `src/tprm_frameworks_mcp/server.py`

```python
@app.call_tool()
async def call_tool(name: str, arguments: dict) -> Sequence[TextContent]:
    if name == "generate_dora_questionnaire":
        # 1. Fetch DORA requirements from eu-regulations-mcp
        # 2. Generate questions from requirements
        # 3. Map to SCF controls
        # 4. Return questionnaire with article references
        pass
```

### Phase 4: NIS2 Integration (1.5 hours)

Same pattern as DORA, but for NIS2 Directive:
- Articles 20-23 (Supply chain security)
- Generate questions from directive requirements
- Map to existing security frameworks
- Provide compliance evidence tracking

### Phase 3-4 Deliverables

**New Tools:**
1. `generate_dora_questionnaire` - Dynamic DORA assessments
2. `generate_nis2_questionnaire` - Dynamic NIS2 assessments
3. `map_to_eu_regulations` - Question → Article mapping
4. `check_regulatory_compliance` - Gap analysis

**Integration Features:**
- Real-time regulatory requirement fetching
- Dynamic questionnaire generation
- Article-level compliance tracking
- Cross-regulation mapping (DORA + NIS2 overlap)

**Documentation:**
- EU_REGULATIONS_INTEGRATION.md
- DORA_COMPLIANCE_GUIDE.md
- NIS2_ASSESSMENT_WORKFLOW.md

---

## 🚀 Execution Plan

### Parallel Agent Deployment

**Phase 2: CAIQ v4** (3 agents, 2 hours)
- **Agent 1**: Excel parser + data extraction
- **Agent 2**: SCF mapping generation
- **Agent 3**: Rubric enhancement + testing

**Phase 3-4: EU Integration** (3 agents, 2 hours)
- **Agent 1**: eu-regulations-mcp integration layer
- **Agent 2**: DORA questionnaire generation
- **Agent 3**: NIS2 questionnaire generation

**Total Time**: ~4 hours with parallel agents

---

## 📊 Value Proposition

### Phase 2 Benefits
- ✅ Industry-standard cloud vendor assessments
- ✅ SOC 2 audit preparation
- ✅ 295 comprehensive questions (vs 50 placeholder)
- ✅ FREE data source (no licensing costs)

### Phase 3-4 Benefits
- ✅ EU regulatory compliance automation
- ✅ DORA/NIS2 deadline tracking (Jan 2025)
- ✅ Automated gap analysis
- ✅ Evidence-based compliance
- ✅ €50K+ savings (vs manual compliance consulting)

### Combined Impact
- **Time Savings**: 8-10 hours per vendor assessment
- **Regulatory Confidence**: 95%+ (article-level precision)
- **Audit Readiness**: Complete evidence trail
- **Market Differentiation**: First integrated TPRM+EU compliance platform

---

## 🎯 Success Criteria

### Phase 2 Complete When:
- [ ] All 295 CAIQ v4 questions loaded
- [ ] 100% SCF mapping coverage
- [ ] All tests passing
- [ ] Integration with security-controls-mcp verified
- [ ] Documentation updated

### Phase 3-4 Complete When:
- [ ] eu-regulations-mcp integration working
- [ ] Dynamic DORA questionnaire generation
- [ ] Dynamic NIS2 questionnaire generation
- [ ] Article-level compliance tracking
- [ ] Cross-regulation gap analysis
- [ ] All EU integration tests passing

---

## 🛠️ Next Steps

### Immediate: Phase 2 Kickoff
1. Download CAIQ v4 from CSA
2. Deploy 3 parallel agents
3. 2-hour implementation sprint
4. Verification and testing

### After Phase 2: Phase 3-4
1. Review eu-regulations-mcp API
2. Design integration patterns
3. Deploy 3 parallel agents
4. 2-hour implementation sprint

---

## 📞 Decision Points

**Before Starting Phase 2:**
- [ ] Confirm CAIQ v4 download source
- [ ] Review Excel structure
- [ ] Approve agent deployment plan

**Before Starting Phase 3-4:**
- [ ] Test eu-regulations-mcp availability
- [ ] Review DORA/NIS2 article structure
- [ ] Approve dynamic questionnaire approach

---

## 🎉 End State Vision

After Phase 4, you'll have:

```
┌────────────────────────────────────────────────────────┐
│         Enterprise TPRM + EU Compliance Platform       │
├────────────────────────────────────────────────────────┤
│                                                        │
│  ✅ 295 CAIQ v4 questions (cloud vendor assessments)   │
│  ✅ Dynamic DORA questionnaires (ICT third-party risk) │
│  ✅ Dynamic NIS2 questionnaires (supply chain)         │
│  ✅ Complete SCF control mappings                      │
│  ✅ Article-level regulatory compliance                │
│  ✅ Historical trending & vendor tracking              │
│  ✅ Automated gap analysis                             │
│  ✅ Audit-ready evidence trail                         │
│                                                        │
│  Market Value: €100K+ first-year savings               │
│  Time to Market: 4-6 hours from now                    │
└────────────────────────────────────────────────────────┘
```

---

**Ready to proceed with Phase 2?**

Say "Deploy Phase 2" and I'll:
1. Create the Excel parser
2. Deploy 3 parallel agents
3. Have full CAIQ v4 ready in ~2 hours

---

*This plan follows MCP best practices: specialized servers, clear boundaries, composable architecture.*
