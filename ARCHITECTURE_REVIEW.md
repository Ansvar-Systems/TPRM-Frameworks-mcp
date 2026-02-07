# TPRM Frameworks MCP - Architecture Review Document

**For:** Ansvar AI Platform Architect Review
**Date:** 2026-02-07
**Purpose:** Define how TPRM-Frameworks MCP integrates into Ansvar AI platform

---

## 1. What This MCP Server Does

### Purpose
Provides **questionnaire data and evaluation logic** for Third-Party Risk Management (TPRM) assessments within Ansvar AI platform.

### Core Capabilities
1. **Questionnaire Library** - Stores and serves TPRM questionnaire frameworks (SIG, CAIQ, DORA, NIS2)
2. **Question Filtering** - Selects relevant questions based on vendor type and regulations
3. **Response Evaluation** - Scores vendor responses using rule-based rubrics
4. **Control Mapping** - Maps questions to SCF security controls (via security-controls-mcp)
5. **Risk Scoring** - Calculates overall vendor risk levels

### What It Does NOT Do
- ❌ Does NOT manage workflows or orchestration (platform handles this)
- ❌ Does NOT store vendor data long-term (platform's database handles this)
- ❌ Does NOT send/receive communications (platform handles this)
- ❌ Does NOT provide UI (platform provides UI)
- ❌ Does NOT handle authentication (platform handles this)

---

## 2. Integration with Ansvar AI Platform

### Architecture Pattern: **MCP as Domain Data Layer**

```
┌─────────────────────────────────────────────────────────┐
│           Ansvar AI Platform (Orchestration)            │
│  ┌──────────────────────────────────────────────────┐  │
│  │  TPRM Workflow Engine                            │  │
│  │  - Vendor onboarding                             │  │
│  │  - Assessment scheduling                         │  │
│  │  - Notification management                       │  │
│  │  - Status tracking                               │  │
│  │  - Report generation                             │  │
│  └────────────┬─────────────────────────────────────┘  │
│               │                                         │
│               │ Calls MCP tools via Agent               │
│               ▼                                         │
│  ┌──────────────────────────────────────────────────┐  │
│  │  AI Agent                                        │  │
│  │  - Interprets user requests                      │  │
│  │  - Orchestrates tool calls                       │  │
│  │  - Formats outputs                               │  │
│  └────────────┬─────────────────────────────────────┘  │
│               │                                         │
└───────────────┼─────────────────────────────────────────┘
                │
                │ MCP Protocol
                ▼
┌───────────────────────────────────────────────────────┐
│         TPRM-Frameworks MCP (Port 8309)               │
│  ┌─────────────────────────────────────────────────┐  │
│  │  Tools (7 tools)                                │  │
│  │  - list_frameworks                              │  │
│  │  - generate_questionnaire                       │  │
│  │  - evaluate_response                            │  │
│  │  - map_questionnaire_to_controls                │  │
│  │  - generate_tprm_report                         │  │
│  │  - get_questionnaire                            │  │
│  │  - search_questions                             │  │
│  └─────────────────────────────────────────────────┘  │
│  ┌─────────────────────────────────────────────────┐  │
│  │  Data Layer                                     │  │
│  │  - Questionnaire frameworks (JSON)              │  │
│  │  - Evaluation rubrics                           │  │
│  │  - SCF control mappings                         │  │
│  └─────────────────────────────────────────────────┘  │
└───────────────────────────────────────────────────────┘
                │
                │ Cross-MCP Integration
                ▼
┌───────────────────────────────────────────────────────┐
│      Related MCP Servers                              │
│  - security-controls-mcp (SCF mappings)               │
│  - EU-regulations-mcp (DORA/NIS2 requirements)        │
│  - vendor-intel-mcp (vendor enrichment)               │
└───────────────────────────────────────────────────────┘
```

---

## 3. Ansvar AI Platform: TPRM Workflow

### Platform-Level Workflow (What Platform Does)

```
┌─ Platform TPRM Workflow ─────────────────────────────────┐
│                                                            │
│  1. INTAKE                                                 │
│     - Client requests vendor assessment                    │
│     - Platform creates assessment record in DB             │
│     - Platform assigns to analyst/agent                    │
│                                                            │
│  2. PLANNING                                               │
│     ┌─ Platform Calls MCP ────────────────────────┐      │
│     │ Agent: "What questionnaire for Salesforce,  │      │
│     │         SaaS provider, DORA compliance?"     │      │
│     │ MCP: list_frameworks()                       │      │
│     │ MCP: generate_questionnaire(caiq_v4, dora)  │      │
│     │ Returns: 85 questions                        │      │
│     └──────────────────────────────────────────────┘      │
│     - Platform generates questionnaire document            │
│     - Platform creates vendor-facing form/portal           │
│                                                            │
│  3. DISTRIBUTION                                           │
│     - Platform sends questionnaire to vendor               │
│       (email, portal link, integration)                    │
│     - Platform tracks status (sent, opened, in-progress)   │
│     - Platform sends reminders                             │
│                                                            │
│  4. COLLECTION                                             │
│     - Vendor submits responses via platform                │
│     - Platform validates completeness                      │
│     - Platform stores responses in DB                      │
│                                                            │
│  5. EVALUATION                                             │
│     ┌─ Platform Calls MCP ────────────────────────┐      │
│     │ Agent: "Evaluate Salesforce responses"      │      │
│     │ MCP: evaluate_response(questionnaire_id,    │      │
│     │                        responses)            │      │
│     │ Returns: score, risk_level, findings        │      │
│     └──────────────────────────────────────────────┘      │
│     - Platform stores evaluation in DB                     │
│     - Platform triggers alerts for critical findings       │
│                                                            │
│  6. REVIEW                                                 │
│     - Analyst reviews AI evaluation                        │
│     - Platform allows manual overrides                     │
│     - Platform tracks approval workflow                    │
│                                                            │
│  7. REPORTING                                              │
│     ┌─ Platform Calls MCP ────────────────────────┐      │
│     │ Agent: "Generate TPRM report"               │      │
│     │ MCP: generate_tprm_report()                 │      │
│     │ MCP: map_questionnaire_to_controls()        │      │
│     │ Returns: findings, control gaps             │      │
│     └──────────────────────────────────────────────┘      │
│     - Platform generates client report (PDF/dashboard)     │
│     - Platform tracks vendor risk score over time          │
│                                                            │
│  8. DECISION & MONITORING                                  │
│     - Client approves/rejects vendor                       │
│     - Platform tracks vendor relationship                  │
│     - Platform schedules re-assessments                    │
│                                                            │
└────────────────────────────────────────────────────────────┘
```

---

## 4. Responsibility Boundaries

### Platform Responsibilities
| Capability | Owner | Notes |
|-----------|-------|-------|
| User authentication | Platform | Platform manages all users |
| Vendor management | Platform | CRM/vendor database |
| Workflow orchestration | Platform | State machine, notifications |
| Data persistence | Platform | PostgreSQL/MongoDB |
| UI/UX | Platform | Web app, dashboards |
| Email/notifications | Platform | SendGrid, etc. |
| Document generation | Platform | PDF generation from MCP data |
| Approval workflows | Platform | Multi-stakeholder reviews |
| Audit logging | Platform | All actions logged |
| Scheduling | Platform | Re-assessment scheduling |
| Integration (external) | Platform | Vendor portals, GRC systems |

### MCP Responsibilities
| Capability | Owner | Notes |
|-----------|-------|-------|
| Questionnaire content | MCP | CAIQ, SIG, DORA, NIS2 |
| Question filtering | MCP | Select relevant questions |
| Evaluation logic | MCP | Rule-based scoring |
| SCF control mapping | MCP | Map questions → controls |
| Risk scoring | MCP | Calculate overall risk |
| Framework versioning | MCP | Track questionnaire versions |
| Regulatory mapping | MCP | Question → regulation mapping |

### Shared Responsibilities
| Capability | Platform Role | MCP Role |
|-----------|---------------|----------|
| Assessment creation | Create DB record, assign ID | Generate question set |
| Response validation | Check completeness | Validate answer formats |
| Risk reporting | Format/present results | Calculate scores/findings |
| Control gap analysis | Display gaps in UI | Map questions to controls |

---

## 5. Data Flow

### 5.1 Assessment Creation

```
User Request → Platform Workflow Engine
                      ↓
              Platform creates assessment_id
                      ↓
              Agent calls MCP: generate_questionnaire({
                framework: "caiq_v4",
                entity_type: "saas_provider",
                regulations: ["dora"]
              })
                      ↓
              MCP returns: {
                questionnaire_id: "Q-123",
                questions: [85 questions with metadata],
                scf_mappings: [...],
                regulatory_mappings: [...]
              }
                      ↓
              Platform stores:
                - assessment_id → questionnaire_id mapping
                - questions in platform DB
                - creates vendor-facing form
                      ↓
              Platform sends questionnaire to vendor
```

### 5.2 Response Evaluation

```
Vendor submits responses → Platform collects in DB
                                      ↓
              Platform triggers evaluation
                                      ↓
              Agent calls MCP: evaluate_response({
                questionnaire_id: "Q-123",
                vendor_name: "Salesforce",
                responses: [{question_id, answer}, ...],
                strictness: "moderate"
              })
                                      ↓
              MCP processes:
                - Match responses to questions
                - Apply evaluation rubrics
                - Calculate scores
                - Identify gaps
                                      ↓
              MCP returns: {
                overall_score: 78,
                risk_level: "medium",
                evaluation_results: [per-question scores],
                critical_findings: [...],
                compliance_gaps: {dora: [gap1, gap2]}
              }
                                      ↓
              Platform stores evaluation in DB
                                      ↓
              Platform presents to analyst for review
```

---

## 6. API Contract (MCP Tools)

### Tool 1: `generate_questionnaire`

**Purpose:** Generate tailored questionnaire based on vendor profile

**Input:**
```json
{
  "framework": "caiq_v4|sig_lite|dora_ict_tpp|nis2_supply_chain",
  "scope": "full|lite|focused",
  "entity_type": "saas_provider|cloud_provider|ict_provider|...",
  "regulations": ["dora", "gdpr", "nis2"],
  "categories": ["Identity & Access", "Data Security"]  // optional, for focused
}
```

**Output:**
```json
{
  "questionnaire_id": "uuid",
  "framework": "caiq_v4",
  "total_questions": 85,
  "questions": [
    {
      "id": "caiq_iam-01",
      "category": "Identity & Access Management",
      "question_text": "Do you implement MFA?",
      "expected_answer_type": "yes_no",
      "weight": 10,
      "regulatory_mappings": ["DORA Article 6", "ISO 27001:2022 - 5.17"],
      "scf_control_mappings": ["IAC-11", "IAC-12"],
      "risk_if_inadequate": "critical"
    }
  ]
}
```

**Platform Usage:**
- Platform calls this during assessment planning
- Platform stores questions in its DB
- Platform generates vendor-facing form from questions
- Platform tracks questionnaire_id for later evaluation

---

### Tool 2: `evaluate_response`

**Purpose:** Score vendor responses and identify risks

**Input:**
```json
{
  "questionnaire_id": "uuid",
  "vendor_name": "Salesforce",
  "responses": [
    {
      "question_id": "caiq_iam-01",
      "answer": "Yes, MFA is required for all users",
      "supporting_documents": ["mfa-policy.pdf"],
      "notes": "Implemented via Okta"
    }
  ],
  "strictness": "lenient|moderate|strict"
}
```

**Output:**
```json
{
  "questionnaire_id": "uuid",
  "vendor_name": "Salesforce",
  "overall_score": 78.5,
  "overall_risk_level": "medium",
  "evaluation_results": [
    {
      "question_id": "caiq_iam-01",
      "status": "acceptable",
      "score": 100,
      "risk_level": "low",
      "findings": ["MFA properly implemented"],
      "recommendations": [],
      "scf_controls_addressed": ["IAC-11", "IAC-12"]
    }
  ],
  "critical_findings": [
    "Encryption key rotation not documented (Q-45)",
    "Incident response plan not tested annually (Q-67)"
  ],
  "compliance_gaps": {
    "dora": ["Article 6.2 - ICT risk documentation", "Article 11.1 - BCP testing"],
    "gdpr": ["Article 32 - Security measures"]
  }
}
```

**Platform Usage:**
- Platform calls after collecting vendor responses
- Platform stores evaluation results in DB
- Platform displays scores/findings in UI
- Platform triggers alerts for critical findings
- Platform uses compliance_gaps for audit reports

---

### Tool 3: `map_questionnaire_to_controls`

**Purpose:** Bridge questionnaire to security control frameworks (SCF)

**Input:**
```json
{
  "framework": "caiq_v4",
  "question_ids": ["caiq_iam-01", "caiq_dsp-01"],  // optional
  "control_framework": "scf"
}
```

**Output:**
```json
{
  "framework": "caiq_v4",
  "mappings": [
    {
      "question_id": "caiq_iam-01",
      "question_text": "Do you implement MFA?",
      "category": "Identity & Access",
      "scf_controls": ["IAC-11", "IAC-12"],
      "weight": 10,
      "regulatory_mappings": ["DORA Article 6"]
    }
  ]
}
```

**Platform Usage:**
- Platform calls to show control coverage
- Platform integrates with security-controls-mcp to get control details
- Platform displays control gaps in dashboard

---

### Tool 4: `generate_tprm_report`

**Purpose:** Aggregate assessment data into report structure

**Input:**
```json
{
  "vendor_name": "Salesforce",
  "questionnaire_results": ["result-id-1"],
  "vendor_intel_data": {},  // from vendor-intel-mcp
  "posture_data": {},       // from security scanning
  "include_recommendations": true
}
```

**Output:**
```json
{
  "vendor_name": "Salesforce",
  "assessment_date": "2026-02-07",
  "overall_risk": "medium",
  "executive_summary": "...",
  "key_findings": [...],
  "recommendations": [...],
  "compliance_status": {...},
  "control_coverage": {...}
}
```

**Platform Usage:**
- Platform calls to generate report data
- Platform formats into PDF/dashboard
- Platform includes additional platform-specific data

---

## 7. Data Storage Strategy

### MCP Server (Ephemeral)
- **Questionnaire templates** - JSON files (static data)
- **Evaluation rubrics** - JSON files (static logic)
- **Generated questionnaires** - In-memory dict (temporary)
- **Assessment results** - In-memory dict (temporary)

**Rationale:** MCP is stateless. Platform owns all persistent data.

### Platform Database (Persistent)
```sql
-- Platform owns all business data
assessments (
  id, client_id, vendor_id, questionnaire_id,
  status, created_at, completed_at
)

questionnaire_instances (
  id, assessment_id, framework, version,
  questions_json, created_at
)

vendor_responses (
  id, assessment_id, question_id,
  answer, documents, submitted_at
)

evaluation_results (
  id, assessment_id, overall_score, risk_level,
  findings_json, evaluated_at
)

vendor_risk_history (
  id, vendor_id, assessment_id,
  score, risk_level, assessed_at
)
```

**Rationale:** Platform manages state, history, relationships.

---

## 8. Cross-MCP Integration

### Integration with security-controls-mcp

```
TPRM-MCP: map_questionnaire_to_controls()
    → Returns: ["IAC-11", "IAC-12", "CRY-01"]
          ↓
Platform Agent calls security-controls-mcp:
    → get_control("IAC-11") → Returns: control details
    → get_control("IAC-12") → Returns: control details
          ↓
Platform displays control gaps in UI
```

### Integration with EU-regulations-mcp

```
TPRM-MCP: DORA questions have regulatory_mappings: ["DORA Article 6.2"]
          ↓
Platform Agent calls EU-regulations-mcp:
    → get_article("dora", "6.2") → Returns: full article text
          ↓
Platform displays regulatory context in assessment UI
```

---

## 9. Deployment Architecture

### Development Environment
```
Local Machine:
  - TPRM-MCP runs on port 8309
  - Platform connects via MCP protocol (stdio/SSE)
  - security-controls-mcp on port 8308
  - EU-regulations-mcp on port [varies]
```

### Production Environment
```
Ansvar AI Cloud:
  ┌─ Platform Services ───────────┐
  │  - Web API (port 443)         │
  │  - Agent Service (internal)   │
  │  - Database (PostgreSQL)      │
  └───────────┬───────────────────┘
              │
  ┌───────────┴───────────────────┐
  │  MCP Server Cluster           │
  │  - TPRM-MCP (8309)            │
  │  - security-controls (8308)   │
  │  - EU-regulations (8xxx)      │
  │  - vendor-intel (8xxx)        │
  └───────────────────────────────┘
```

**Communication:**
- Platform → MCP: MCP protocol over SSE or HTTP
- MCP ↔ MCP: Cross-server tool calls via platform agent
- All connections within VPC, no public exposure

---

## 10. Performance & Scalability

### Expected Load
| Operation | Frequency | Response Time Target |
|-----------|-----------|---------------------|
| generate_questionnaire | 10-50/day | <500ms |
| evaluate_response | 5-20/day | <2s |
| map_to_controls | 5-20/day | <500ms |
| generate_report | 5-20/day | <1s |

### Scaling Strategy
- **Vertical:** Single MCP instance sufficient (CPU-bound operations are fast)
- **Horizontal:** If needed, run multiple MCP instances behind load balancer
- **Caching:** Platform caches generated questionnaires (same config → same output)
- **Database:** MCP is stateless, no database contention

### Data Size
- Questionnaire templates: ~5MB total (all frameworks)
- Generated questionnaire: ~100KB (85 questions)
- Evaluation result: ~50KB
- **Memory footprint:** <100MB per MCP instance

---

## 11. Security Considerations

### Authentication & Authorization
- **MCP Level:** None (platform handles all auth)
- **Platform Level:** Platform authenticates users before allowing MCP calls

### Data Sensitivity
- **Questionnaire templates:** Public (CAIQ, DORA are public)
- **Vendor responses:** CONFIDENTIAL (handled by platform)
- **Evaluation results:** CONFIDENTIAL (handled by platform)

### MCP Security Responsibilities
- ✅ Input validation (prevent injection)
- ✅ Rate limiting (prevent abuse)
- ✅ Error messages (no sensitive data leakage)
- ❌ Authentication (platform's job)
- ❌ Vendor data encryption (platform's job)

---

## 12. Questions for Architect Review

### Integration Questions
1. **MCP Communication:** Does platform use SSE or stdio for MCP protocol?
2. **Agent Architecture:** Does platform have a single agent or multiple specialized agents?
3. **Database Schema:** Does platform have existing TPRM tables, or should we design from scratch?
4. **Document Storage:** Where should generated Excel/PDF files be stored (S3, filesystem)?

### Workflow Questions
5. **Vendor Portal:** Does Ansvar platform have a vendor-facing portal, or do vendors receive email?
6. **Manual Review:** What's the approval workflow after AI evaluation? (analyst review, auto-approve, etc.)
7. **Re-assessments:** How does platform handle periodic re-assessments? (annual, event-triggered)

### Data Questions
8. **Historical Data:** Should MCP track vendor assessment history, or is this 100% platform's responsibility?
9. **Custom Questionnaires:** Should platform be able to create custom questions, or only use MCP templates?
10. **Multi-tenancy:** Does platform need tenant isolation for questionnaire data?

### Technical Questions
11. **Deployment:** Where will MCP servers run? (Kubernetes, VM, serverless)
12. **Monitoring:** What metrics should MCP expose? (Prometheus, CloudWatch, custom)
13. **Updates:** How should framework updates be deployed? (CI/CD, manual, automated)

---

## 13. Success Criteria

### Technical Success
- ✅ MCP server responds to all tool calls in <2s
- ✅ Evaluation accuracy >90% vs. manual scoring
- ✅ Zero data loss (all state in platform DB)
- ✅ Handles 100 concurrent assessments
- ✅ Framework updates deployable in <1 hour

### Business Success
- ✅ Reduces assessment time by 80% (16h → 3h)
- ✅ Consistent, auditable scoring
- ✅ Supports CAIQ, DORA, NIS2 assessments
- ✅ Integrates seamlessly with platform workflow
- ✅ No vendor training required (invisible to vendors)

---

## 14. Next Steps

### For Architect
1. Review architecture and integration points
2. Answer questions in Section 12
3. Provide platform architecture details:
   - Database schema (if exists)
   - Agent architecture
   - MCP communication pattern
   - Deployment environment

### For Implementation
1. Finalize MCP tool contracts based on architect feedback
2. Align data models with platform schema
3. Define deployment strategy
4. Create implementation timeline

### For Testing
1. Set up integration test environment
2. Create test data (vendor responses)
3. Validate with platform workflows
4. Performance testing with realistic load

---

**Document Version:** 1.0
**Prepared For:** Ansvar AI Platform Architect
**Contact:** Claude (via Jeffrey von Rotz)
**Next Action:** Architect review and feedback
