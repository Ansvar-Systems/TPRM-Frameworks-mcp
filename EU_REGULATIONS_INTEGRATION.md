# EU Regulations Integration

This document describes the integration between `tprm-frameworks-mcp` and `eu-regulations-mcp` for dynamic DORA/NIS2 questionnaire generation.

## Overview

The EU Regulations integration layer enables dynamic generation of TPRM questionnaires directly from regulatory articles, ensuring questionnaires stay aligned with the latest regulatory requirements.

### Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    TPRM Frameworks MCP                          │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │         EU Regulations Integration Layer                  │  │
│  │  • EURegulationsClient                                    │  │
│  │  • get_dora_requirements()                                │  │
│  │  • get_nis2_requirements()                                │  │
│  │  • generate_questions_from_articles()                     │  │
│  └──────────────────────────────────────────────────────────┘  │
│                             │                                   │
│                             ▼                                   │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │         MCP Tools (13 total)                              │  │
│  │  • generate_dora_questionnaire                            │  │
│  │  • generate_nis2_questionnaire                            │  │
│  │  • check_regulatory_compliance                            │  │
│  │  • get_regulatory_timeline                                │  │
│  └──────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
                             │
                             ▼
         ┌───────────────────────────────────┐
         │   eu-regulations-mcp (optional)   │
         │   • DORA Articles                 │
         │   • NIS2 Articles                 │
         │   • Regulatory Timelines          │
         └───────────────────────────────────┘
                             │
                             ▼ (fallback)
         ┌───────────────────────────────────┐
         │   Local Mapping Data              │
         │   eu-regulations-mapping.json     │
         └───────────────────────────────────┘
```

## Integration Components

### 1. EURegulationsClient

Location: `src/tprm_frameworks_mcp/integrations/eu_regulations.py`

The client handles communication with the `eu-regulations-mcp` server and provides graceful fallback to local data.

**Features:**
- Async API for fetching regulatory articles
- Automatic fallback to local JSON data if server unavailable
- Caching for improved performance
- Support for both DORA and NIS2 regulations

**Configuration:**
```python
# Environment variable (optional)
export EU_REGULATIONS_MCP_URL="http://localhost:8310"

# Or initialize directly
from tprm_frameworks_mcp.integrations import EURegulationsClient
client = EURegulationsClient(server_url="http://localhost:8310")
```

### 2. Regulatory Mapping Data

Location: `src/tprm_frameworks_mcp/data/eu-regulations-mapping.json`

This file provides the local fallback data when `eu-regulations-mcp` is not available.

**Structure:**
```json
{
  "dora": {
    "article_28": {
      "title": "ICT third-party risk management",
      "category": "ICT Third-Party Risk",
      "question_templates": [...],
      "scf_controls": ["TPM-01", "TPM-02"],
      "required_evidence": [...]
    }
  },
  "nis2": {
    "article_22": {
      "title": "Supply chain security",
      "category": "Supply Chain",
      "question_templates": [...],
      "scf_controls": ["TPM-01", "TPM-02"],
      "required_evidence": [...]
    }
  },
  "deadlines": {
    "dora": "2025-01-17",
    "nis2": "2024-10-17"
  }
}
```

### 3. Core Functions

#### `get_dora_requirements(category)`

Fetch DORA regulatory requirements by category.

**Categories:**
- `ICT_third_party` - Articles 28-30 (Third-party risk management)
- `ICT_risk` - Articles 6, 8 (ICT risk management framework)
- `business_continuity` - Articles 11-13 (BCP/DR)
- `incident_management` - Articles 17, 19-20 (Incident reporting)
- `testing` - Articles 15, 26-27 (Operational resilience testing)

**Example:**
```python
requirements = await get_dora_requirements("ICT_third_party")
# Returns: List[RegulatoryRequirement]
```

#### `get_nis2_requirements(category)`

Fetch NIS2 regulatory requirements by category.

**Categories:**
- `supply_chain` - Article 22 (Supply chain security)
- `risk_management` - Article 21 (Cybersecurity risk management)
- `governance` - Article 20 (Governance)
- `incident_response` - Article 23 (Reporting obligations)

**Example:**
```python
requirements = await get_nis2_requirements("supply_chain")
# Returns: List[RegulatoryRequirement]
```

#### `generate_questions_from_articles(requirements, framework_prefix)`

Convert regulatory requirements into questionnaire questions.

**Example:**
```python
requirements = await get_dora_requirements("ICT_third_party")
questions = await generate_questions_from_articles(requirements, "dora")
# Returns: List[Dict] - ready to convert to Question objects
```

#### `map_questions_to_articles(questions)`

Create reverse mapping from questions to articles.

**Example:**
```python
article_map = await map_questions_to_articles(questions)
# Returns: {"DORA - Article 28": ["dora_28_1", "dora_28_2"], ...}
```

## MCP Tools

### 1. generate_dora_questionnaire

Generate DORA ICT third-party questionnaire dynamically from regulations.

**Input Schema:**
```json
{
  "category": "ICT_third_party",  // Optional
  "scope": "full"                  // Optional: "full" or "focused"
}
```

**Usage Example:**
```python
# Via MCP client
result = await mcp_client.call_tool(
    "generate_dora_questionnaire",
    {"category": "ICT_third_party", "scope": "full"}
)
```

**Output:**
- Questionnaire ID
- Total questions generated
- Regulatory coverage (which articles are covered)
- Complete question set with SCF mappings
- Source tracking (eu-regulations-mcp or local)

### 2. generate_nis2_questionnaire

Generate NIS2 supply chain questionnaire dynamically from regulations.

**Input Schema:**
```json
{
  "category": "supply_chain",  // Optional
  "scope": "full"              // Optional: "full" or "focused"
}
```

**Usage Example:**
```python
result = await mcp_client.call_tool(
    "generate_nis2_questionnaire",
    {"category": "supply_chain", "scope": "full"}
)
```

**Output:**
- Questionnaire ID
- Total questions generated
- Regulatory coverage
- Complete question set with SCF mappings

### 3. check_regulatory_compliance

Check DORA/NIS2 compliance gaps based on assessment results.

**Input Schema:**
```json
{
  "assessment_id": 123,
  "regulation": "DORA"  // "DORA" or "NIS2"
}
```

**Usage Example:**
```python
result = await mcp_client.call_tool(
    "check_regulatory_compliance",
    {"assessment_id": 123, "regulation": "DORA"}
)
```

**Output:**
- Compliance status (compliant/partial/non_compliant)
- Coverage percentage
- Total questions assessed
- Detailed gap analysis
- Findings per gap

### 4. get_regulatory_timeline

Get DORA/NIS2 compliance deadlines and milestones.

**Input Schema:**
```json
{
  "regulation": "DORA"  // "DORA" or "NIS2"
}
```

**Usage Example:**
```python
result = await mcp_client.call_tool(
    "get_regulatory_timeline",
    {"regulation": "DORA"}
)
```

**Output:**
- Final deadline
- Days until deadline
- Overdue status
- Key milestones with dates

## Workflow Examples

### End-to-End DORA Assessment

```python
# 1. Generate DORA questionnaire from regulations
questionnaire = await generate_dora_questionnaire(
    category="ICT_third_party",
    scope="full"
)
# → Returns questionnaire_id

# 2. Vendor completes questionnaire (external process)

# 3. Evaluate vendor responses
assessment = await evaluate_response(
    questionnaire_id=questionnaire_id,
    vendor_name="Critical ICT Provider",
    responses=[...],
    strictness="strict"
)
# → Returns assessment_id

# 4. Check DORA compliance
compliance = await check_regulatory_compliance(
    assessment_id=assessment_id,
    regulation="DORA"
)
# → Returns compliance status and gaps

# 5. Get timeline for remediation
timeline = await get_regulatory_timeline(regulation="DORA")
# → Returns deadlines and milestones
```

### NIS2 Supply Chain Assessment

```python
# 1. Generate NIS2 questionnaire
questionnaire = await generate_nis2_questionnaire(
    category="supply_chain",
    scope="full"
)

# 2. Evaluate supplier
assessment = await evaluate_response(
    questionnaire_id=questionnaire_id,
    vendor_name="Critical Supplier",
    responses=[...]
)

# 3. Check NIS2 compliance
compliance = await check_regulatory_compliance(
    assessment_id=assessment_id,
    regulation="NIS2"
)

# 4. Map to SCF controls
control_mapping = await map_questionnaire_to_controls(
    framework="nis2_supply_chain"
)
```

## Article → Question Mapping Strategy

### DORA Example: Article 28

**Regulatory Text:**
> "Financial entities shall manage ICT third-party risk as an integral component of ICT risk within their ICT risk management framework."

**Generated Questions:**
1. "Do you have a documented third-party risk management process for ICT services?"
2. "Are all ICT third-party service providers subject to due diligence before engagement?"
3. "Do you maintain a register of all ICT third-party service providers?"
4. "Are third-party contracts reviewed for DORA compliance?"

**SCF Mappings:**
- TPM-01: Third-Party Management
- TPM-02: Third-Party Requirements
- TPM-03: Third-Party Contracts
- GOV-01: Governance Program

### NIS2 Example: Article 22

**Regulatory Text:**
> "Essential and important entities shall take appropriate measures to address cybersecurity risks arising from the supply chain."

**Generated Questions:**
1. "Do you assess and manage cybersecurity risks in your supply chain?"
2. "Are security requirements included in supplier contracts?"
3. "Do you evaluate the overall quality of products and cybersecurity practices of suppliers?"
4. "Are critical suppliers subject to enhanced due diligence?"

**SCF Mappings:**
- TPM-01: Third-Party Management
- TPM-02: Third-Party Requirements
- TPM-06: Third-Party Risk Assessment
- TPM-09: Supply Chain Risk Management

## Error Handling and Fallbacks

### Scenario 1: eu-regulations-mcp Server Unavailable

**Behavior:** Automatically falls back to local mapping data

```python
client = EURegulationsClient()
# Checks if server is available
if not await client.is_server_available():
    # Uses local data from eu-regulations-mapping.json
    articles = client._fetch_from_local("dora", "ICT_third_party")
```

### Scenario 2: Missing Mapping Data

**Behavior:** Returns empty list with warning

```python
requirements = await get_dora_requirements("unknown_category")
# Returns: []
# Tool response: "No DORA requirements found for category 'unknown_category'"
```

### Scenario 3: Assessment Not Found

**Behavior:** Returns error message

```python
compliance = await check_regulatory_compliance(
    assessment_id=999,
    regulation="DORA"
)
# Returns: "Assessment ID 999 not found."
```

## Integration with Other MCP Servers

### security-controls-mcp

All generated questions include SCF control mappings. Use `security-controls-mcp` to:

```python
# Get control details
control = await security_controls_mcp.get_control("TPM-01")

# Map to other frameworks
mapping = await security_controls_mcp.map_frameworks(
    source="scf",
    target="iso_27001_2022",
    control_ids=["TPM-01", "TPM-02"]
)
```

### vendor-intel-mcp (Future)

Combine regulatory compliance with vendor intelligence:

```python
# Get vendor intelligence
intel = await vendor_intel_mcp.get_vendor_profile("Critical ICT Provider")

# Generate report combining both
report = await generate_tprm_report(
    vendor_name="Critical ICT Provider",
    questionnaire_results=[assessment_id],
    vendor_intel_data=intel
)
```

## Configuration

### Environment Variables

```bash
# Optional: URL to eu-regulations-mcp server
export EU_REGULATIONS_MCP_URL="http://localhost:8310"

# Database location (optional, defaults to ~/.tprm-mcp/tprm.db)
export TPRM_DB_PATH="/custom/path/tprm.db"
```

### MCP Server Configuration

Add to `~/.config/mcp/server.json`:

```json
{
  "mcpServers": {
    "tprm-frameworks-mcp": {
      "command": "python",
      "args": ["-m", "tprm_frameworks_mcp"],
      "env": {
        "EU_REGULATIONS_MCP_URL": "http://localhost:8310"
      }
    },
    "eu-regulations-mcp": {
      "command": "python",
      "args": ["-m", "eu_regulations_mcp"]
    }
  }
}
```

## Testing

### Unit Tests

```bash
# Test EU regulations integration
python -m pytest tests/test_eu_regulations.py

# Test DORA questionnaire generation
python -m pytest tests/test_dora_generation.py -v

# Test NIS2 questionnaire generation
python -m pytest tests/test_nis2_generation.py -v
```

### Integration Tests

```bash
# Test full workflow
python test_integration.py --test eu-regulations

# Test with mock eu-regulations-mcp server
python test_integration.py --mock-eu-regs
```

### Manual Testing

```bash
# Start server
python -m tprm_frameworks_mcp

# In another terminal, test tools
python test_server.py generate_dora_questionnaire
python test_server.py generate_nis2_questionnaire
python test_server.py get_regulatory_timeline
```

## Performance Considerations

### Caching

- Regulatory mapping data is cached in memory after first load
- Questionnaires are stored in SQLite for persistence
- Article mappings are computed on-demand but can be cached

### Optimization Tips

1. **Batch Article Fetches:** Fetch all articles for a category at once
2. **Reuse Questionnaires:** Store generated questionnaires for reuse
3. **Limit Scope:** Use "focused" scope for specific assessments
4. **Cache Control Mappings:** Map questionnaires to controls once, reuse results

## Roadmap

### Phase 1 (Complete)
- ✅ EU regulations integration layer
- ✅ Local mapping data
- ✅ 4 new MCP tools
- ✅ Documentation

### Phase 2 (Future)
- [ ] Connect to live eu-regulations-mcp server
- [ ] Support for regulatory updates
- [ ] Automatic questionnaire versioning
- [ ] Regulatory change tracking

### Phase 3 (Future)
- [ ] Multi-language support (EN, DE, FR)
- [ ] Regulatory interpretation guidance
- [ ] Evidence collection workflows
- [ ] Compliance reporting automation

## Troubleshooting

### Issue: "No requirements found"

**Cause:** Invalid category or missing mapping data

**Solution:**
```python
# Check available categories
client = EURegulationsClient()
mapping = client._load_mapping_data()
print(mapping["category_mapping"]["dora"])
```

### Issue: "eu-regulations-mcp connection failed"

**Cause:** Server not running or incorrect URL

**Solution:**
```bash
# Check if server is running
curl http://localhost:8310/health

# Or fall back to local data (automatic)
# Client will use eu-regulations-mapping.json
```

### Issue: "Question generation failed"

**Cause:** Invalid requirement format

**Solution:**
```python
# Validate requirements
for req in requirements:
    assert req.regulation in ["DORA", "NIS2"]
    assert req.article
    assert req.requirement_text or req.question_templates
```

## Support

For issues and questions:
- **GitHub Issues:** File issues on the repository
- **Email:** hello@ansvar.eu
- **Documentation:** See CLAUDE.md for AI agent guidance

## License

Copyright © 2024 Ansvar Systems. All rights reserved.
