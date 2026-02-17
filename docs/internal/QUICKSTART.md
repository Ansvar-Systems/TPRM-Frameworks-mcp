# TPRM Frameworks MCP - Quickstart Guide

**Get your TPRM assessment workflow running in 30 minutes**

Version: 0.1.0
Last Updated: 2026-02-07
Target Platform: Ansvar AI

---

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Installation](#installation)
3. [MCP Configuration](#mcp-configuration)
4. [Running the Server](#running-the-server)
5. [Testing the Integration](#testing-the-integration)
6. [Integration with Ansvar AI Workflow](#integration-with-ansvar-ai-workflow)
7. [Cross-MCP Integration](#cross-mcp-integration)
8. [Troubleshooting](#troubleshooting)
9. [Next Steps](#next-steps)

---

## Prerequisites

### System Requirements

- **Python**: 3.10 or higher (3.11, 3.12 recommended)
- **Operating System**: macOS, Linux, or Windows with WSL
- **Memory**: 512MB minimum
- **Disk Space**: 100MB

### Check Your Python Version

```bash
python3 --version
# Should show: Python 3.10.x or higher
```

### Required Dependencies

All dependencies are automatically installed during setup:
- `mcp>=0.9.0` - Model Context Protocol library

### Optional (for development)

```bash
# Development tools
pip install -e ".[dev]"
```

This includes:
- pytest (testing)
- pytest-asyncio (async testing)
- black (code formatting)
- ruff (linting)
- pre-commit (git hooks)

---

## Installation

### Step 1: Clone/Navigate to Repository

```bash
cd /Users/jeffreyvonrotz/Projects/TPRM-Frameworks-mcp
```

### Step 2: Install in Editable Mode

```bash
pip install -e .
```

This command:
- Installs the package in "editable" mode (changes reflect immediately)
- Installs all required dependencies
- Creates the `tprm-mcp` command-line tool
- Sets up package data (JSON questionnaire files)

### Step 3: Verify Installation

```bash
# Check that the command is available
which tprm-mcp

# Test the server (Ctrl+C to exit)
python -m tprm_frameworks_mcp
```

You should see the server start up without errors. Press `Ctrl+C` to stop.

### Step 4: Run Test Suite

```bash
# Run basic functionality test
python test_server.py
```

Expected output:
```
🧪 Testing TPRM Frameworks MCP Server

1. Testing Data Loader...
   ✓ Loaded 6 frameworks
   - Shared Assessments SIG Lite: 180 questions (placeholder)
   - CAIQ v4: 295 questions (placeholder)
   ...

✅ All tests passed!
```

---

## MCP Configuration

### For Claude Desktop

Add to your `claude_desktop_config.json`:

**Location**:
- macOS: `~/Library/Application Support/Claude/claude_desktop_config.json`
- Windows: `%APPDATA%\Claude\claude_desktop_config.json`

**Configuration**:

```json
{
  "mcpServers": {
    "tprm-frameworks": {
      "command": "python",
      "args": ["-m", "tprm_frameworks_mcp"],
      "env": {}
    }
  }
}
```

### For Ansvar AI Platform

Add to your MCP registry configuration:

```json
{
  "mcpServers": {
    "tprm-frameworks": {
      "command": "python",
      "args": ["-m", "tprm_frameworks_mcp"],
      "env": {},
      "metadata": {
        "name": "TPRM Frameworks MCP",
        "version": "0.1.0",
        "description": "Vendor risk assessment questionnaire generation and evaluation",
        "capabilities": [
          "questionnaire_generation",
          "response_evaluation",
          "control_mapping",
          "regulatory_compliance"
        ],
        "integrations": {
          "security-controls-mcp": "SCF control mappings",
          "vendor-intel-mcp": "Vendor intelligence enrichment",
          "eu-regulations-mcp": "DORA/NIS2 requirements"
        }
      }
    }
  }
}
```

### Alternative: Use Absolute Path

If the `python -m` approach doesn't work, use an absolute path:

```json
{
  "mcpServers": {
    "tprm-frameworks": {
      "command": "/usr/bin/python3",
      "args": [
        "/Users/jeffreyvonrotz/Projects/TPRM-Frameworks-mcp/src/tprm_frameworks_mcp/__main__.py"
      ],
      "env": {}
    }
  }
}
```

Find your Python path with:
```bash
which python3
```

---

## Running the Server

### Direct Execution (for testing)

```bash
# Method 1: Python module
python -m tprm_frameworks_mcp

# Method 2: Command-line tool
tprm-mcp

# Method 3: Direct script
python /Users/jeffreyvonrotz/Projects/TPRM-Frameworks-mcp/src/tprm_frameworks_mcp/__main__.py
```

### Via MCP Client (Production)

The server runs automatically when accessed through MCP clients (Claude Desktop, Ansvar AI agents).

**Restart Claude Desktop** after updating configuration to load the new server.

### Verify Server is Running

In Claude Desktop or your MCP client:

```
User: "What TPRM frameworks are available?"
```

Expected response should list available frameworks (SIG, CAIQ, DORA, NIS2, etc.)

---

## Testing the Integration

### Test 1: List Available Frameworks

**Tool Call**:
```json
{
  "tool": "list_frameworks",
  "arguments": {}
}
```

**Expected Output**:
```
**TPRM Frameworks MCP Server v0.1.0**

**Available Questionnaire Frameworks: 6**

### Shared Assessments SIG Lite
- **Key:** `sig_lite`
- **Version:** 2025.1
- **Questions:** 180
- **Status:** placeholder
  ⚠️ *Placeholder data - replace with licensed questionnaire content*

### CAIQ v4
- **Key:** `caiq_v4`
- **Version:** 4.0.4
- **Questions:** 295
- **Status:** placeholder
...
```

### Test 2: Generate a Cloud Provider Questionnaire

**Tool Call**:
```json
{
  "tool": "generate_questionnaire",
  "arguments": {
    "framework": "caiq_v4",
    "scope": "lite",
    "entity_type": "cloud_provider",
    "regulations": ["gdpr", "dora"]
  }
}
```

**Expected Output**:
```json
{
  "questionnaire_id": "550e8400-e29b-41d4-a716-446655440000",
  "framework": "caiq_v4",
  "scope": "lite",
  "entity_type": "cloud_provider",
  "total_questions": 85,
  "categories": [
    "Identity & Access Management",
    "Data Security & Privacy",
    "Infrastructure & Virtualization Security",
    ...
  ],
  "questions": [
    {
      "id": "caiq_iam_01",
      "category": "Identity & Access Management",
      "question_text": "Do you support multi-factor authentication for user access?",
      "weight": 10,
      "is_required": true,
      "risk_if_inadequate": "high"
    }
    ...
  ]
}
```

### Test 3: Evaluate Vendor Responses

**Tool Call**:
```json
{
  "tool": "evaluate_response",
  "arguments": {
    "questionnaire_id": "550e8400-e29b-41d4-a716-446655440000",
    "vendor_name": "Acme Cloud Services",
    "strictness": "moderate",
    "responses": [
      {
        "question_id": "caiq_iam_01",
        "answer": "Yes, we require MFA for all user accounts using TOTP authenticators.",
        "supporting_documents": ["MFA_Policy_v2.pdf"],
        "notes": "MFA enforced via Okta"
      },
      {
        "question_id": "caiq_data_01",
        "answer": "Data is encrypted at rest using AES-256.",
        "supporting_documents": ["Encryption_Spec.pdf"]
      }
    ]
  }
}
```

**Expected Output**:
```
**Vendor Assessment Results: Acme Cloud Services**

**Overall Score:** 78.5/100
**Overall Risk Level:** MEDIUM
**Questionnaire:** 550e8400-e29b-41d4-a716-446655440000
**Strictness:** moderate

**Response Summary:**
- acceptable: 65
- partially_acceptable: 15
- unacceptable: 3
- unanswered: 2

**⚠️ Critical Findings (3):**
- caiq_bcm_01: Business continuity plan missing RTO/RPO definitions
- caiq_sec_05: No evidence of annual security testing
- caiq_irp_02: Incident response plan not tested in last 12 months
...
```

### Test 4: Map to Security Controls

**Tool Call**:
```json
{
  "tool": "map_questionnaire_to_controls",
  "arguments": {
    "framework": "caiq_v4",
    "control_framework": "scf"
  }
}
```

**Expected Output**:
```
**Questionnaire to SCF Control Mappings**

**Framework:** caiq_v4
**Control Framework:** scf
**Mapped Questions:** 295

### Identity & Access Management
- **caiq_iam_01**: IAM-02, IAM-03, IAM-11
- **caiq_iam_02**: IAM-01, IAM-05
...

**Integration Tip:**
Use the security-controls-mcp server to:
- Get detailed control descriptions: `get_control(control_id)`
- Map to other frameworks: `map_frameworks(source='scf', target='iso_27001_2022')`
```

### Test 5: Search for Specific Topics

**Tool Call**:
```json
{
  "tool": "search_questions",
  "arguments": {
    "query": "encryption",
    "framework": "caiq_v4",
    "limit": 5
  }
}
```

**Expected Output**:
```
**Found 12 question(s) matching 'encryption'**

### caiq_dsp_01 (Data Security & Privacy)
**Q:** Do you encrypt data at rest?
**SCF Controls:** CRY-01, CRY-02
**Weight:** 10/10

### caiq_dsp_02 (Data Security & Privacy)
**Q:** Do you encrypt data in transit?
**SCF Controls:** CRY-03, CRY-04
**Weight:** 10/10
...
```

---

## Integration with Ansvar AI Workflow

### Typical TPRM Assessment Workflow

#### Phase 1: Assessment Planning

**Agent receives request**:
```
User: "We need to assess Salesforce for DORA compliance"
```

**Agent calls**:
```json
{
  "tool": "generate_questionnaire",
  "arguments": {
    "framework": "caiq_v4",
    "scope": "focused",
    "entity_type": "saas_provider",
    "regulations": ["dora", "gdpr"],
    "categories": [
      "Identity & Access Management",
      "Data Security & Privacy",
      "Business Continuity",
      "Incident Response",
      "Security Operations"
    ]
  }
}
```

**Agent responds**:
```
I've prepared a DORA-focused assessment for Salesforce with 85 questions
covering critical security areas. The questionnaire emphasizes:

- Identity & Access Management (18 questions)
- Data Security & Privacy (22 questions)
- Business Continuity & Resilience (15 questions)
- Incident Response (12 questions)
- Security Operations (18 questions)

Questionnaire ID: abc-123-def
Estimated completion time: 6-8 hours

Would you like me to export this as an Excel file for sending to Salesforce?
```

#### Phase 2: Response Collection

**Human process** (outside MCP):
1. Export questionnaire to Excel/PDF
2. Send to vendor contact
3. Vendor completes questionnaire (1-4 weeks typically)
4. Receive completed questionnaire

#### Phase 3: Evaluation

**User uploads completed questionnaire**:
```
User: "Salesforce completed the assessment. Here are their responses."
[Uploads: salesforce_responses.json]
```

**Agent calls**:
```json
{
  "tool": "evaluate_response",
  "arguments": {
    "questionnaire_id": "abc-123-def",
    "vendor_name": "Salesforce",
    "strictness": "moderate",
    "responses": [/* parsed from upload */]
  }
}
```

**Agent analyzes and responds**:
```
Assessment complete for Salesforce.

**Overall Risk Score:** 82/100 (Low-Medium Risk)

**Key Findings:**
✅ Strong Areas:
- Identity & Access Management: 95/100 (MFA, SSO, privileged access controls)
- Data Encryption: 90/100 (AES-256 at rest, TLS 1.3 in transit)
- Business Continuity: 88/100 (Documented BCP with tested failover)

⚠️ Areas for Improvement:
- Incident Response Testing: 65/100 (No tabletop exercise in last 12 months)
- Third-Party Security: 70/100 (Subprocessor assessments incomplete)

❌ Critical Gaps (2):
1. Missing documented RTO/RPO for critical services (DORA Article 11 requirement)
2. ICT incident reporting timeline exceeds DORA 4-hour requirement

**Compliance Status:**
- DORA: 85% compliant (3 gaps require remediation)
- GDPR: 92% compliant (1 gap - subprocessor documentation)

**Recommendation:** Request remediation plan for critical gaps before approval.
```

#### Phase 4: Control Mapping

**Agent enriches with control mappings**:
```json
{
  "tool": "map_questionnaire_to_controls",
  "arguments": {
    "framework": "caiq_v4",
    "question_ids": ["caiq_bcm_01", "caiq_irp_02"]
  }
}
```

**Then queries security-controls-mcp** (cross-MCP integration):
```json
{
  "tool": "get_control",
  "server": "security-controls-mcp",
  "arguments": {
    "control_id": "BCD-01"
  }
}
```

**Agent provides detailed remediation guidance**:
```
Gap: Missing RTO/RPO documentation

**Mapped Controls:**
- SCF BCD-01: Business Continuity Management
- SCF BCD-02: Business Impact Analysis
- ISO 27001:2022 A.17.1.2: Implementing information security continuity

**Remediation Steps:**
1. Conduct Business Impact Analysis (BIA) for all critical services
2. Define Recovery Time Objectives (RTO) and Recovery Point Objectives (RPO)
3. Document in Business Continuity Plan
4. Test recovery procedures quarterly
5. Provide evidence of BCP testing to assessor

**Regulatory Requirement:**
DORA Article 11(1) requires documented RTOs and RPOs for all critical ICT services.
```

#### Phase 5: Report Generation

**Agent calls**:
```json
{
  "tool": "generate_tprm_report",
  "arguments": {
    "vendor_name": "Salesforce",
    "questionnaire_results": ["assessment-abc-123"],
    "vendor_intel_data": {/* from vendor-intel-mcp */},
    "posture_data": {/* from security scanning */},
    "include_recommendations": true
  }
}
```

**Final deliverable**: Comprehensive TPRM report ready for client review.

---

## Cross-MCP Integration

### Integration with security-controls-mcp

**Purpose**: Enrich questionnaire questions with detailed control descriptions and cross-framework mappings.

**Example Flow**:

1. **Generate questionnaire** (tprm-frameworks-mcp):
```json
{
  "tool": "generate_questionnaire",
  "arguments": {"framework": "caiq_v4", "scope": "lite"}
}
```

2. **Map to controls** (tprm-frameworks-mcp):
```json
{
  "tool": "map_questionnaire_to_controls",
  "arguments": {"framework": "caiq_v4"}
}
```
Returns: `["IAM-02", "CRY-01", "BCD-01", ...]`

3. **Get control details** (security-controls-mcp):
```json
{
  "tool": "get_control",
  "server": "security-controls-mcp",
  "arguments": {"control_id": "IAM-02"}
}
```
Returns: Full control description, implementation guidance, metrics

4. **Map to client's framework** (security-controls-mcp):
```json
{
  "tool": "map_frameworks",
  "server": "security-controls-mcp",
  "arguments": {
    "source": "scf",
    "target": "iso_27001_2022",
    "control_id": "IAM-02"
  }
}
```
Returns: ISO 27001:2022 equivalent controls

**Result**: Questionnaire questions now enriched with:
- Detailed control descriptions
- Implementation guidance
- Metrics and evidence requirements
- Mappings to client's preferred framework (ISO, NIST, etc.)

### Integration with eu-regulations-mcp

**Purpose**: Source DORA/NIS2 regulatory requirements for questionnaire generation.

**Example Flow**:

1. **Get DORA requirements** (eu-regulations-mcp):
```json
{
  "tool": "get_regulation_articles",
  "server": "eu-regulations-mcp",
  "arguments": {
    "regulation": "dora",
    "chapter": "ICT Risk Management"
  }
}
```
Returns: DORA Articles 6-15 with full text

2. **Generate DORA questionnaire** (tprm-frameworks-mcp):
```json
{
  "tool": "generate_questionnaire",
  "arguments": {
    "framework": "dora_ict_tpp",
    "regulations": ["dora"]
  }
}
```
Questions automatically include regulatory references

3. **Enrich questions with article context** (eu-regulations-mcp):
```json
{
  "tool": "get_article",
  "server": "eu-regulations-mcp",
  "arguments": {
    "regulation": "dora",
    "article": "Article 6"
  }
}
```
Returns: Full article text to add as context to questions

**Result**: DORA questionnaires with:
- Direct traceability to regulation articles
- Full regulatory context for each question
- Compliance gap analysis against specific requirements

### Integration with vendor-intel-mcp

**Purpose**: Enrich TPRM reports with vendor intelligence data.

**Example Flow**:

1. **Get vendor profile** (vendor-intel-mcp):
```json
{
  "tool": "get_company_profile",
  "server": "vendor-intel-mcp",
  "arguments": {"company_name": "Salesforce"}
}
```
Returns: Company size, certifications, breach history

2. **Get security posture** (vendor-intel-mcp):
```json
{
  "tool": "get_security_ratings",
  "server": "vendor-intel-mcp",
  "arguments": {"company_name": "Salesforce"}
}
```
Returns: External security ratings, CVEs, exposed services

3. **Generate comprehensive report** (tprm-frameworks-mcp):
```json
{
  "tool": "generate_tprm_report",
  "arguments": {
    "vendor_name": "Salesforce",
    "questionnaire_results": ["assessment-123"],
    "vendor_intel_data": {/* from above */},
    "posture_data": {/* from above */}
  }
}
```

**Result**: Comprehensive TPRM report combining:
- Questionnaire assessment results (internal)
- Vendor intelligence data (external)
- Security posture findings (external scanning)
- Compliance status (regulatory)
- Control mappings (SCF/ISO/NIST)

---

## Troubleshooting

### Server Won't Start

**Symptom**:
```bash
$ python -m tprm_frameworks_mcp
ModuleNotFoundError: No module named 'tprm_frameworks_mcp'
```

**Solution**:
```bash
# Reinstall in editable mode
cd /Users/jeffreyvonrotz/Projects/TPRM-Frameworks-mcp
pip install -e .

# Verify installation
pip show tprm-frameworks-mcp
```

### MCP Client Can't Find Server

**Symptom**: Claude Desktop or Ansvar AI doesn't show the tprm-frameworks server.

**Solutions**:

1. **Check configuration file location**:
```bash
# macOS
cat ~/Library/Application\ Support/Claude/claude_desktop_config.json

# Verify server is listed under mcpServers
```

2. **Restart the MCP client** (Claude Desktop, etc.)

3. **Check Python path**:
```bash
which python3
# Use this exact path in configuration
```

4. **Test server manually**:
```bash
python -m tprm_frameworks_mcp
# Should start without errors
```

### Questions Not Loading

**Symptom**:
```
list_frameworks returns 0 frameworks
```

**Solution**:
```bash
# Check data files exist
ls /Users/jeffreyvonrotz/Projects/TPRM-Frameworks-mcp/src/tprm_frameworks_mcp/data/

# Should show:
# sig_lite.json
# caiq_v4.json
# dora_ict_tpp.json
# nis2_supply_chain.json
# questionnaire-to-scf.json

# If missing, check package installation
pip install -e . --force-reinstall
```

### Evaluation Returns Low Scores

**Symptom**: All vendor responses score poorly even with good answers.

**Solution**: This is expected with placeholder rubrics. The current rubrics are basic examples.

**To improve**:
1. Review `evaluation_rubric` in data files
2. Add more comprehensive acceptable answer patterns
3. Tune `weight` values per question importance
4. Adjust `strictness` parameter (try "lenient" vs "strict")

Example enhancement:
```json
{
  "evaluation_rubric": {
    "acceptable": [
      "yes",
      "implemented",
      "we have.*mfa",
      "multi-factor.*authentication.*required",
      "totp|authenticator|yubikey|fido2"
    ],
    "partially_acceptable": [
      "partial",
      "in progress",
      "planned.*2026",
      "mfa.*optional"
    ],
    "unacceptable": [
      "no",
      "not implemented",
      "no plans",
      "password only"
    ],
    "required_keywords": ["multi-factor", "authentication"]
  }
}
```

### Cross-MCP Integration Failing

**Symptom**: Can't call security-controls-mcp or eu-regulations-mcp from tprm-frameworks-mcp.

**Solution**: Cross-MCP calls must be orchestrated by the AI agent, not directly by the server.

**Correct Pattern**:
```
Agent receives request
  ↓
Agent calls tprm-frameworks-mcp.map_questionnaire_to_controls
  ↓
Agent receives SCF control IDs
  ↓
Agent calls security-controls-mcp.get_control (separate call)
  ↓
Agent combines results in response
```

**Incorrect Pattern**:
```
tprm-frameworks-mcp tries to call security-controls-mcp directly ❌
```

MCP servers cannot call each other directly. The AI agent orchestrates all cross-server integration.

### Memory Issues with Large Questionnaires

**Symptom**: Server slows down or crashes with 295-question CAIQ.

**Solution**:
1. Use `scope: "lite"` to filter to high-priority questions
2. Use `categories` parameter to focus on specific areas
3. Increase system memory allocation
4. Consider implementing pagination for large result sets

**Example**:
```json
{
  "tool": "generate_questionnaire",
  "arguments": {
    "framework": "caiq_v4",
    "scope": "lite",  // Filters to weight >= 8
    "categories": ["Identity & Access Management", "Data Security"]
  }
}
```

This reduces from 295 questions to ~50-60 focused questions.

---

## Next Steps

### Phase 1: Replace Placeholder Data (Week 1-2)

**Current Status**: All frameworks contain placeholder/sample data.

**Action Items**:

1. **CAIQ v4 (FREE)**:
   - Download from: https://cloudsecurityalliance.org/artifacts/csa-caiq-v4-0/
   - Parse Excel to JSON format
   - Replace `/src/tprm_frameworks_mcp/data/caiq_v4.json`
   - Enhance evaluation rubrics

2. **DORA ICT TPP**:
   - Query eu-regulations-mcp for DORA articles
   - Transform requirements to questions
   - Map to SCF controls
   - Replace `/src/tprm_frameworks_mcp/data/dora_ict_tpp.json`

3. **NIS2 Supply Chain**:
   - Query eu-regulations-mcp for NIS2 Article 21
   - Transform requirements to questions
   - Replace `/src/tprm_frameworks_mcp/data/nis2_supply_chain.json`

4. **SIG Lite** (LICENSED - $2-5K/year):
   - Obtain license from: https://sharedassessments.org
   - Download latest SIG Lite
   - Parse to JSON format
   - Replace `/src/tprm_frameworks_mcp/data/sig_lite.json`

**Documentation**: See `OPTION_2_IMPLEMENTATION_PLAN.md` for detailed import scripts.

### Phase 2: Add Persistence Layer (Week 3)

**Goal**: Store generated questionnaires and assessment results in database.

**Current Status**: In-memory storage (data lost when server restarts).

**Action Items**:

1. Implement SQLite storage (`src/tprm_frameworks_mcp/storage.py`)
2. Add database initialization on server startup
3. Implement questionnaire persistence
4. Implement assessment persistence
5. Add vendor history tracking
6. Add new tools:
   - `get_vendor_history`
   - `compare_assessments`
   - `check_framework_versions`

**Benefits**:
- Persistent questionnaires across sessions
- Historical tracking of vendor assessments
- Trend analysis (vendor improvement over time)
- Audit trail for compliance

### Phase 3: Excel Import/Export (Week 4)

**Goal**: Generate Excel questionnaires for vendors and import completed responses.

**Current Status**: JSON-only input/output.

**Action Items**:

1. Implement Excel export tool:
   - Tab 1: Instructions
   - Tab 2: Questions with dropdown responses
   - Tab 3: Metadata

2. Implement Excel import tool:
   - Parse vendor responses
   - Validate completeness
   - Convert to JSON format

3. Add new tools:
   - `export_questionnaire_excel`
   - `import_responses_excel`

**Benefits**:
- Vendors can complete questionnaires in familiar Excel format
- No manual JSON formatting required
- Built-in validation and data quality checks

### Phase 4: Enhanced Evaluation Rubrics (Week 5)

**Goal**: Improve evaluation accuracy from ~60% to >90%.

**Current Status**: Basic rubrics with keyword matching.

**Action Items**:

1. Review top 50 critical questions per framework
2. Enhance rubrics with:
   - More comprehensive acceptable answer patterns
   - Context-aware scoring
   - Industry-specific terminology
   - Evidence requirements

3. Implement rubric testing:
   - 100 good response examples
   - 100 poor response examples
   - Measure accuracy against human scoring

4. Add rubric versioning and A/B testing

**Benefits**:
- More accurate assessment scores
- Reduced manual review time
- Better gap identification
- Higher confidence in risk ratings

### Phase 5: Regulatory Integration (Week 6)

**Goal**: Full integration with eu-regulations-mcp for DORA/NIS2.

**Action Items**:

1. Implement regulatory requirement extraction
2. Auto-generate questions from regulation articles
3. Add regulatory traceability (question → article → requirement)
4. Implement compliance gap reporting
5. Add regulatory update monitoring

**Benefits**:
- Always current with regulatory changes
- Full audit trail (question → regulation)
- Automated compliance gap analysis
- RTS (Regulatory Technical Standards) integration

### Phase 6: Production Hardening (Week 7-8)

**Goal**: Production-ready deployment.

**Action Items**:

1. **Testing**:
   - Comprehensive test suite (>80% coverage)
   - Performance testing (large questionnaires)
   - Load testing (concurrent assessments)
   - Integration testing (cross-MCP)

2. **Documentation**:
   - API reference
   - Integration guides
   - Operations runbook
   - Troubleshooting guide

3. **Monitoring**:
   - Error logging
   - Performance metrics
   - Usage analytics
   - Framework version tracking

4. **Security**:
   - Input validation
   - Rate limiting
   - Data encryption (at rest)
   - Audit logging

**Benefits**:
- Production-grade reliability
- Operational visibility
- Security compliance
- Maintainability

---

## Additional Resources

### Documentation

- **README.md**: Project overview and features
- **CLAUDE.md**: AI agent integration guide
- **ARCHITECTURE_REVIEW.md**: Technical architecture details
- **WORKFLOW_FIRST_REDESIGN.md**: Workflow-centric design philosophy
- **OPTION_2_IMPLEMENTATION_PLAN.md**: Detailed phase-by-phase implementation plan
- **PRODUCTION_READINESS_ASSESSMENT.md**: Production readiness checklist

### Data Sources

- **CAIQ v4**: https://cloudsecurityalliance.org/artifacts/csa-caiq-v4-0/ (FREE)
- **SIG**: https://sharedassessments.org (LICENSED)
- **DORA**: Regulation (EU) 2022/2554 (PUBLIC)
- **NIS2**: Directive (EU) 2022/2555 (PUBLIC)

### Related MCP Servers

- **security-controls-mcp**: SCF control framework and cross-framework mappings
- **vendor-intel-mcp**: Vendor intelligence and security ratings
- **eu-regulations-mcp**: EU regulatory requirements (DORA, NIS2, GDPR, etc.)

### Support

- **Issues**: https://github.com/Ansvar-Systems/tprm-frameworks-mcp/issues
- **Email**: hello@ansvar.eu

---

## Quick Reference Card

### Essential Commands

```bash
# Install
pip install -e .

# Test
python test_server.py

# Run server
python -m tprm_frameworks_mcp

# Configuration location
~/Library/Application Support/Claude/claude_desktop_config.json
```

### Essential Tools

| Tool | Purpose | Key Parameters |
|------|---------|----------------|
| `list_frameworks` | Show available frameworks | None |
| `generate_questionnaire` | Create assessment | `framework`, `scope`, `entity_type`, `regulations` |
| `evaluate_response` | Score vendor responses | `questionnaire_id`, `vendor_name`, `responses`, `strictness` |
| `map_questionnaire_to_controls` | Map to SCF controls | `framework`, `question_ids` |
| `search_questions` | Find questions by keyword | `query`, `framework`, `limit` |
| `generate_tprm_report` | Create comprehensive report | `vendor_name`, `questionnaire_results` |

### Common Workflows

**Quick Assessment (Cloud Provider)**:
```
1. generate_questionnaire(framework="caiq_v4", scope="lite", entity_type="cloud_provider")
2. [Vendor completes questionnaire]
3. evaluate_response(questionnaire_id, vendor_name, responses, strictness="moderate")
4. map_questionnaire_to_controls(framework="caiq_v4")
5. generate_tprm_report(vendor_name, questionnaire_results)
```

**DORA Compliance Assessment**:
```
1. generate_questionnaire(framework="dora_ict_tpp", regulations=["dora"])
2. [Vendor completes questionnaire]
3. evaluate_response(questionnaire_id, vendor_name, responses, strictness="strict")
4. [Check eu-regulations-mcp for article details]
5. generate_tprm_report(vendor_name, include_recommendations=true)
```

---

## Success Checklist

Use this checklist to verify your integration is working:

- [ ] Server starts without errors (`python -m tprm_frameworks_mcp`)
- [ ] Test suite passes (`python test_server.py`)
- [ ] MCP configuration added to Claude Desktop / Ansvar AI
- [ ] `list_frameworks` returns 6 frameworks
- [ ] Can generate questionnaire with custom parameters
- [ ] Can evaluate vendor responses and get risk score
- [ ] Can map questions to SCF controls
- [ ] Can search questions by keyword
- [ ] Cross-MCP integration working (security-controls-mcp)
- [ ] Cross-MCP integration working (eu-regulations-mcp)

Once all items are checked, you're ready for production use!

---

**Version**: 0.1.0
**Last Updated**: 2026-02-07
**Maintained by**: Ansvar Systems
**License**: Apache-2.0
