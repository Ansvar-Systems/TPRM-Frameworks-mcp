# TPRM MCP - Workflow-First Redesign

## The Real Problem

**Current Design Issue:**
```
Agent: "Assess Vendor X"
→ generate_questionnaire() → Returns 295-question JSON blob
→ Agent: "...now what? How do I send this to the vendor?"
```

**The JSON dump doesn't help the agent actually DO anything.**

---

## Real Ansvar AI TPRM Workflow

### Scenario: Client needs to assess a cloud provider

```
1. CLIENT REQUEST
   "We need to assess Salesforce for DORA compliance"

2. AGENT PLANNING (needs MCP help)
   - What questionnaire to use?
   - Which questions are relevant?
   - What scope (quick/standard/deep)?

3. QUESTIONNAIRE PREPARATION (needs MCP help)
   - Generate customized question set
   - Export as Excel/PDF for vendor
   - Create tracking ID

4. SEND TO VENDOR (external - NOT MCP)
   - Human emails Excel to vendor
   - OR upload to vendor portal
   - OR client sends via their GRC system

5. WAIT FOR RESPONSES (external - NOT MCP)
   - Vendor fills out Excel
   - Takes 1-4 weeks typically
   - May be partial submissions

6. RECEIVE RESPONSES (needs MCP help)
   - Import vendor's Excel
   - Validate completeness
   - Parse into structured format

7. EVALUATION (needs MCP help)
   - Score responses automatically
   - Identify gaps
   - Calculate risk level

8. REPORTING (needs MCP help)
   - Generate findings report
   - Map to controls
   - Create recommendations

9. CLIENT DELIVERY
   - Agent presents report
   - Client makes decision
```

## What MCP Actually Needs To Provide

### ❌ What We Built (Data-Centric)
- Tool: generate_questionnaire → 295 questions as JSON
- Tool: evaluate_response → expects perfect JSON input
- **Problem:** Doesn't match workflow, too much manual work

### ✅ What We Should Build (Workflow-Centric)

**Stage 1: Assessment Planning**
```
Tool: plan_assessment
Input: {
  vendor_name: "Salesforce",
  vendor_type: "saas_provider",
  assessment_scope: "dora_compliance",
  risk_tier: "high",
  regulations: ["dora", "gdpr"]
}
Output: {
  recommended_framework: "caiq_v4",
  question_count: 85,  // Filtered from 295
  estimated_completion: "4-6 hours",
  assessment_plan: {
    categories: ["Identity", "Data Security", "Incident Response", ...],
    critical_questions: 25,
    standard_questions: 60
  }
}
```

**Stage 2: Questionnaire Preparation**
```
Tool: prepare_questionnaire
Input: {
  assessment_plan_id: "from above",
  export_format: "excel",  // or "pdf", "csv", "json"
  language: "en"
}
Output: {
  questionnaire_id: "Q-2026-001",
  export_file: "/tmp/Salesforce_CAIQ_DORA_2026.xlsx",
  instructions_for_vendor: "Please complete by 2026-03-01",
  questions_included: 85,
  tracking_url: "https://ansvar.eu/assessments/Q-2026-001"
}
```

**Stage 3: Response Import**
```
Tool: import_vendor_responses
Input: {
  questionnaire_id: "Q-2026-001",
  response_file: "Salesforce_responses.xlsx",
  validate: true
}
Output: {
  imported_successfully: true,
  responses_count: 83,
  missing_responses: ["Q-45", "Q-67"],
  validation_errors: [],
  ready_for_evaluation: true
}
```

**Stage 4: Evaluation**
```
Tool: evaluate_vendor_assessment
Input: {
  questionnaire_id: "Q-2026-001",
  strictness: "moderate"
}
Output: {
  overall_score: 78,
  risk_level: "medium",
  category_scores: {
    "Identity & Access": 85,
    "Data Security": 72,
    "Incident Response": 80
  },
  critical_findings: [
    "No MFA on privileged accounts",
    "Encryption key rotation policy missing"
  ],
  compliance_status: {
    "dora": "85% compliant - 3 gaps",
    "gdpr": "92% compliant - 1 gap"
  }
}
```

**Stage 5: Reporting**
```
Tool: generate_assessment_report
Input: {
  questionnaire_id: "Q-2026-001",
  include_recommendations: true,
  format: "pdf"
}
Output: {
  report_file: "Salesforce_TPRM_Report_2026.pdf",
  executive_summary: "...",
  recommendation_count: 8,
  remediation_timeline: "60-90 days"
}
```

---

## Simplified Tool Set (7 → 5 Tools)

### Tool 1: `plan_assessment`
**Purpose:** Help agent decide what questionnaire to use
```json
{
  "tool": "plan_assessment",
  "vendor_name": "Salesforce",
  "vendor_type": "saas_provider",
  "regulations": ["dora", "gdpr"],
  "scope": "standard"
}
```
**Returns:** Assessment plan with recommended questions

### Tool 2: `prepare_questionnaire`
**Purpose:** Generate vendor-ready questionnaire package
```json
{
  "tool": "prepare_questionnaire",
  "plan_id": "from_plan_assessment",
  "format": "excel"
}
```
**Returns:** Excel file ready to send to vendor

### Tool 3: `import_responses`
**Purpose:** Import and validate vendor responses
```json
{
  "tool": "import_responses",
  "questionnaire_id": "Q-2026-001",
  "file": "vendor_responses.xlsx"
}
```
**Returns:** Validation results, ready for evaluation

### Tool 4: `evaluate_assessment`
**Purpose:** Score and analyze responses
```json
{
  "tool": "evaluate_assessment",
  "questionnaire_id": "Q-2026-001"
}
```
**Returns:** Risk score, findings, gaps

### Tool 5: `generate_report`
**Purpose:** Create client-ready report
```json
{
  "tool": "generate_report",
  "questionnaire_id": "Q-2026-001",
  "format": "pdf"
}
```
**Returns:** Formatted report with recommendations

---

## Agent Workflow (Actual Usage)

### Example: Assess Salesforce for DORA

```
USER: "We need to assess Salesforce for DORA compliance"

AGENT THINKS:
1. Call plan_assessment(vendor="Salesforce", regulations=["dora"])
2. Get recommendation: CAIQ v4, 85 questions
3. Call prepare_questionnaire(format="excel")
4. Get Excel file

AGENT TO USER:
"I've prepared a DORA-focused assessment questionnaire for Salesforce
with 85 questions (estimated 4-6 hours to complete).

Download: Salesforce_CAIQ_DORA_2026.xlsx

Please send this to Salesforce and let me know when they respond."

[--- 2 WEEKS LATER ---]

USER: "Salesforce completed the questionnaire"
(Uploads: Salesforce_responses.xlsx)

AGENT THINKS:
1. Call import_responses(file="Salesforce_responses.xlsx")
2. Validation: 83/85 questions answered, 2 missing
3. Call evaluate_assessment()
4. Get results: Score 78, Medium risk, 5 critical findings
5. Call generate_report(format="pdf")

AGENT TO USER:
"Assessment complete. Salesforce scored 78/100 (Medium Risk).

Key Findings:
- ✅ Strong: Data encryption, business continuity
- ⚠️  Concerns: MFA implementation, key rotation
- ❌ Critical: 2 DORA requirements not addressed

Full report: Salesforce_TPRM_Report_2026.pdf

Recommendation: Request remediation plan for critical findings
before approval."
```

---

## What This Solves

### ✅ Agent Can Actually Use It
- Clear workflow steps
- File-based input/output (Excel, PDF)
- No manual JSON formatting
- Trackable assessments

### ✅ Integrates With Real Process
- Export → Human sends to vendor
- Import → Human uploads response
- Evaluate → Automatic scoring
- Report → Client-ready output

### ✅ Handles Partial/Async Workflow
- Create assessment → returns ID
- Import responses later → references ID
- Multiple vendors in parallel → separate IDs

---

## Data Layer (Behind The Scenes)

The comprehensive questionnaire data is still there, but:
- **Hidden from agent** - agent doesn't see 295-question JSON
- **Used by tools** - plan_assessment filters to relevant questions
- **Supports export** - prepare_questionnaire generates Excel
- **Powers evaluation** - evaluate_assessment uses rubrics

---

## File Format Strategy

### Excel (Vendor-Facing)
```
Tab 1: Instructions
- How to complete
- Deadline
- Contact info

Tab 2: Questions
| ID | Category | Question | Response | Evidence |
|----|----------|----------|----------|----------|
| Q1 | IAM | Do you use MFA? | [Dropdown: Yes/No/Partial] | [Text] |
| Q2 | Data | Is data encrypted? | [Dropdown] | [Text] |

Tab 3: Metadata
- Vendor name
- Assessment ID
- Framework version
```

### PDF (Client-Facing Report)
```
Executive Summary
- Overall risk score
- Key findings
- Recommendations

Detailed Analysis
- Category breakdowns
- Compliance gaps
- Evidence review

Appendix
- Full question/response list
- Regulatory mappings
- Control coverage
```

---

## Comparison: Old vs New

### Old Design (Data-Centric)
```
Agent: "Assess vendor"
→ MCP: Here's 295 questions as JSON
Agent: "Uh... how do I send this to the vendor?"
→ Manual work: Format JSON → Create Excel → Email
→ Manual work: Vendor responds → Format to JSON
→ MCP: Evaluate
Agent: "Finally!"
```

### New Design (Workflow-Centric)
```
Agent: "Assess vendor"
→ MCP: "Here's the plan: 85 questions, Excel ready"
Agent: "Great, sending to client"
[Client sends to vendor]
[Vendor responds]
Agent: "Upload vendor response"
→ MCP: "Imported. Evaluating..."
→ MCP: "Score: 78. Report ready."
Agent: "Here's your report"
```

---

## Implementation Priority (Revised)

### Phase 1: Core Workflow (Week 1-2)
- ✅ plan_assessment tool
- ✅ prepare_questionnaire tool (Excel export)
- ✅ Storage for assessment sessions
- ✅ Basic CAIQ data (85 critical questions, not 295)

**Outcome:** Can create and export vendor assessments

### Phase 2: Response Handling (Week 3)
- ✅ import_responses tool (Excel parser)
- ✅ Response validation
- ✅ evaluate_assessment tool

**Outcome:** End-to-end workflow works

### Phase 3: Reporting & Polish (Week 4)
- ✅ generate_report tool (PDF)
- ✅ DORA/NIS2 integration
- ✅ Historical tracking

**Outcome:** Production-ready for client delivery

---

## Critical Question For You

**Which workflows matter most at Ansvar AI?**

1. **Cloud Provider Assessment** (AWS, Azure, Salesforce)
   - Use: CAIQ v4
   - Questions: ~85 (filtered from 295)
   - Frequency: High

2. **Financial Entity Assessment** (DORA)
   - Use: DORA ICT TPP
   - Questions: ~65
   - Frequency: Medium

3. **Generic Vendor Assessment** (SIG)
   - Use: SIG Lite
   - Questions: ~120
   - Frequency: High

**Recommendation:** Start with #1 (Cloud Provider) as MVP
- Most common use case
- CAIQ is free
- 85 questions is manageable
- Clear regulatory mapping

Then add #2 and #3 based on demand.

---

## The "Smaller Run" You Suggested

**YES - This is exactly right!**

Instead of:
- ❌ Load all 295 CAIQ questions
- ❌ Return massive JSON to agent
- ❌ Agent figures out what to send

Do this:
- ✅ Agent: plan_assessment(vendor, scope="dora")
- ✅ MCP: "I recommend 85 questions from CAIQ v4"
- ✅ Agent: prepare_questionnaire()
- ✅ MCP: "Here's Excel with those 85 questions"
- ✅ Agent: "Sending to client..."

**Focused, workflow-oriented, actually useful.**

---

## Next Steps

1. **Validate workflow** with your team
   - Does this match how assessments actually happen?
   - Any steps missing?
   - Any tools that aren't useful?

2. **Prioritize frameworks**
   - Start with CAIQ (cloud providers)?
   - Or SIG (generic vendors)?
   - Or DORA (financial)?

3. **Define "standard assessment"**
   - How many questions is reasonable? (50? 100? 150?)
   - What's the right scope filter?

4. **Rebuild in 2-3 weeks** (much faster than 6 weeks)
   - Focus on workflow tools
   - Excel import/export
   - 85-question CAIQ subset
   - Basic evaluation

**Should I redesign and rebuild with this workflow-first approach?**
