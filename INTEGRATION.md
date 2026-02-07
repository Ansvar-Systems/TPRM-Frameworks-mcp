# TPRM Frameworks MCP - Integration Guide

## Overview

This guide explains how to integrate the TPRM Frameworks MCP server with the Ansvar AI platform and other MCP servers.

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Ansvar AI Platform                        │
│                                                              │
│  ┌──────────────────────────────────────────────────────┐   │
│  │              MCP Client / Orchestrator                │   │
│  └──────────────────────────────────────────────────────┘   │
│                           │                                  │
│              ┌────────────┼────────────┐                     │
│              │            │            │                     │
│              ▼            ▼            ▼                     │
│   ┌──────────────┐  ┌──────────┐  ┌──────────────────┐     │
│   │ security-    │  │  TPRM    │  │ eu-regulations-  │     │
│   │ controls-mcp │  │frameworks│  │ mcp              │     │
│   │ (Port 8308)  │  │   -mcp   │  │                  │     │
│   │              │  │(Port 8309│  │                  │     │
│   └──────────────┘  └──────────┘  └──────────────────┘     │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

## Integration Patterns

### 1. Questionnaire Generation with Regulatory Context

**Workflow**: Generate DORA-compliant questionnaire for ICT provider assessment

```javascript
// Step 1: Get DORA ICT TPP requirements from eu-regulations-mcp
const doraRequirements = await use_mcp_tool({
  server_name: "eu-regulations-mcp",
  tool_name: "get_dora_requirements",
  arguments: {
    category: "ict_third_party_risk",
    scope: "critical_tpp"
  }
});

// Step 2: Generate questionnaire with DORA overlay
const questionnaire = await use_mcp_tool({
  server_name: "tprm-frameworks",
  tool_name: "generate_questionnaire",
  arguments: {
    framework: "dora_ict_tpp",
    scope: "full",
    entity_type: "ict_provider",
    regulations: ["dora"]
  }
});

// Result: Questionnaire with questions filtered/prioritized for DORA compliance
```

### 2. Control Gap Analysis

**Workflow**: Map vendor questionnaire responses to control framework gaps

```javascript
// Step 1: Evaluate vendor responses
const evaluation = await use_mcp_tool({
  server_name: "tprm-frameworks",
  tool_name: "evaluate_response",
  arguments: {
    questionnaire_id: "q-12345",
    vendor_name: "CloudVendor Inc",
    responses: vendorResponses,
    strictness: "moderate"
  }
});

// Step 2: Map questionnaire to SCF controls
const controlMappings = await use_mcp_tool({
  server_name: "tprm-frameworks",
  tool_name: "map_questionnaire_to_controls",
  arguments: {
    framework: "sig_lite",
    control_framework: "scf"
  }
});

// Step 3: Get detailed control information for gaps
const criticalGaps = evaluation.evaluation_results
  .filter(r => r.status === "unacceptable" && r.risk_level === "critical")
  .map(r => r.scf_controls_addressed)
  .flat();

const controlDetails = await Promise.all(
  criticalGaps.map(controlId =>
    use_mcp_tool({
      server_name: "security-controls-mcp",
      tool_name: "get_control",
      arguments: {
        control_id: controlId,
        framework: "scf"
      }
    })
  )
);

// Result: Detailed analysis of which specific controls have gaps
```

### 3. Multi-Framework Assessment

**Workflow**: Assess vendor against multiple compliance frameworks

```javascript
// Step 1: Generate SIG Lite questionnaire (broad security)
const sigQuestionnaire = await use_mcp_tool({
  server_name: "tprm-frameworks",
  tool_name: "generate_questionnaire",
  arguments: {
    framework: "sig_lite",
    scope: "lite",
    entity_type: "saas_provider",
    regulations: ["gdpr"]
  }
});

// Step 2: Generate CAIQ v4 questionnaire (cloud-specific)
const caiqQuestionnaire = await use_mcp_tool({
  server_name: "tprm-frameworks",
  tool_name: "generate_questionnaire",
  arguments: {
    framework: "caiq_v4",
    scope: "full",
    entity_type: "cloud_provider"
  }
});

// Step 3: Evaluate both
const sigEvaluation = await use_mcp_tool({
  server_name: "tprm-frameworks",
  tool_name: "evaluate_response",
  arguments: {
    questionnaire_id: sigQuestionnaire.questionnaire_id,
    vendor_name: "CloudVendor Inc",
    responses: sigResponses
  }
});

const caiqEvaluation = await use_mcp_tool({
  server_name: "tprm-frameworks",
  tool_name: "evaluate_response",
  arguments: {
    questionnaire_id: caiqQuestionnaire.questionnaire_id,
    vendor_name: "CloudVendor Inc",
    responses: caiqResponses
  }
});

// Step 4: Generate comprehensive report
const tprmReport = await use_mcp_tool({
  server_name: "tprm-frameworks",
  tool_name: "generate_tprm_report",
  arguments: {
    vendor_name: "CloudVendor Inc",
    questionnaire_results: [
      sigEvaluation.questionnaire_id,
      caiqEvaluation.questionnaire_id
    ],
    include_recommendations: true
  }
});

// Result: Comprehensive multi-framework assessment report
```

### 4. Regulatory Compliance Verification

**Workflow**: Verify NIS2 supply chain security compliance

```javascript
// Step 1: Get NIS2 supply chain requirements
const nis2Requirements = await use_mcp_tool({
  server_name: "eu-regulations-mcp",
  tool_name: "get_nis2_requirements",
  arguments: {
    category: "supply_chain_security"
  }
});

// Step 2: Generate NIS2-focused questionnaire
const questionnaire = await use_mcp_tool({
  server_name: "tprm-frameworks",
  tool_name: "generate_questionnaire",
  arguments: {
    framework: "nis2_supply_chain",
    scope: "full",
    regulations: ["nis2"]
  }
});

// Step 3: Evaluate vendor responses with strict rubric
const evaluation = await use_mcp_tool({
  server_name: "tprm-frameworks",
  tool_name: "evaluate_response",
  arguments: {
    questionnaire_id: questionnaire.questionnaire_id,
    vendor_name: "Supplier XYZ",
    responses: vendorResponses,
    strictness: "strict"  // Strict for regulatory compliance
  }
});

// Step 4: Check for compliance gaps
const complianceGaps = evaluation.compliance_gaps;
const nis2Gaps = complianceGaps["NIS2"] || [];

if (nis2Gaps.length > 0) {
  // Get specific questions with gaps
  const gapQuestions = nis2Gaps.map(questionId =>
    evaluation.evaluation_results.find(r => r.question_id === questionId)
  );

  // Report compliance issues
  console.log(`⚠️ NIS2 Compliance Gaps: ${nis2Gaps.length} questions`);
}

// Result: Detailed NIS2 compliance status with specific gaps identified
```

### 5. Question Search and Custom Questionnaires

**Workflow**: Build custom questionnaire focusing on encryption and data protection

```javascript
// Step 1: Search for encryption-related questions
const encryptionQuestions = await use_mcp_tool({
  server_name: "tprm-frameworks",
  tool_name: "search_questions",
  arguments: {
    query: "encryption",
    limit: 50
  }
});

// Step 2: Search for data protection questions
const dataProtectionQuestions = await use_mcp_tool({
  server_name: "tprm-frameworks",
  tool_name: "search_questions",
  arguments: {
    query: "data protection",
    framework: "caiq_v4",  // Limit to CAIQ
    limit: 30
  }
});

// Step 3: Generate focused questionnaire on specific categories
const customQuestionnaire = await use_mcp_tool({
  server_name: "tprm-frameworks",
  tool_name: "generate_questionnaire",
  arguments: {
    framework: "caiq_v4",
    scope: "focused",
    categories: [
      "Encryption & Key Management",
      "Data Security & Privacy"
    ]
  }
});

// Result: Highly focused questionnaire on specific security domains
```

## Data Flow Patterns

### Pattern 1: Enriched TPRM Report

```
1. Generate Questionnaire (tprm-frameworks)
   ↓
2. Collect Vendor Responses (external)
   ↓
3. Evaluate Responses (tprm-frameworks)
   ↓
4. Get Vendor Intelligence (vendor-intel-mcp)
   ↓
5. Get Security Posture Data (external scanning)
   ↓
6. Map to Controls (security-controls-mcp)
   ↓
7. Generate Final Report (tprm-frameworks)
```

### Pattern 2: Regulatory-First Assessment

```
1. Identify Applicable Regulations (eu-regulations-mcp)
   ↓
2. Extract Required Controls (eu-regulations-mcp)
   ↓
3. Generate Compliant Questionnaire (tprm-frameworks)
   ↓
4. Map to Control Framework (security-controls-mcp)
   ↓
5. Evaluate Vendor (tprm-frameworks)
   ↓
6. Verify Compliance (eu-regulations-mcp + tprm-frameworks)
```

## API Integration Examples

### Python Client

```python
import asyncio
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

async def assess_vendor():
    # Connect to TPRM server
    server_params = StdioServerParameters(
        command="python3",
        args=["-m", "tprm_frameworks_mcp"],
        env={"TPRM_PORT": "8309"}
    )

    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()

            # List frameworks
            result = await session.call_tool(
                "list_frameworks",
                arguments={}
            )
            print(result)

            # Generate questionnaire
            result = await session.call_tool(
                "generate_questionnaire",
                arguments={
                    "framework": "sig_lite",
                    "scope": "lite",
                    "entity_type": "cloud_provider"
                }
            )
            print(f"Generated questionnaire: {result}")

asyncio.run(assess_vendor())
```

### TypeScript/Node.js Client

```typescript
import { Client } from "@modelcontextprotocol/sdk/client/index.js";
import { StdioClientTransport } from "@modelcontextprotocol/sdk/client/stdio.js";

async function assessVendor() {
  const transport = new StdioClientTransport({
    command: "python3",
    args: ["-m", "tprm_frameworks_mcp"],
    env: { TPRM_PORT: "8309" }
  });

  const client = new Client({
    name: "ansvar-ai-client",
    version: "1.0.0"
  }, {
    capabilities: {}
  });

  await client.connect(transport);

  // List frameworks
  const frameworks = await client.callTool({
    name: "list_frameworks",
    arguments: {}
  });
  console.log(frameworks);

  // Generate questionnaire
  const questionnaire = await client.callTool({
    name: "generate_questionnaire",
    arguments: {
      framework: "sig_lite",
      scope: "lite",
      entity_type: "cloud_provider",
      regulations: ["gdpr", "dora"]
    }
  });
  console.log(questionnaire);

  await client.close();
}

assessVendor();
```

## Cross-Server Tool Mapping

### TPRM → Security Controls

| TPRM Tool | Security Controls Tool | Use Case |
|-----------|----------------------|----------|
| `map_questionnaire_to_controls` | `get_control` | Get detailed control descriptions |
| `map_questionnaire_to_controls` | `map_frameworks` | Cross-walk to other control frameworks |
| `evaluate_response` (gaps) | `search_controls` | Find controls to remediate gaps |

### TPRM → EU Regulations

| TPRM Tool | EU Regulations Tool | Use Case |
|-----------|-------------------|----------|
| `generate_questionnaire` | `get_dora_requirements` | Generate DORA-compliant questionnaires |
| `generate_questionnaire` | `get_nis2_requirements` | Generate NIS2-compliant questionnaires |
| `evaluate_response` | `verify_compliance` | Check if responses meet regulatory requirements |

## Error Handling

### Graceful Degradation

```javascript
async function robustAssessment(vendorName, framework) {
  try {
    // Try to generate questionnaire
    const questionnaire = await use_mcp_tool({
      server_name: "tprm-frameworks",
      tool_name: "generate_questionnaire",
      arguments: { framework }
    });

    return questionnaire;

  } catch (error) {
    // If TPRM server unavailable, try fallback
    console.error(`TPRM server error: ${error.message}`);

    // Option 1: Use cached questionnaire
    const cached = await getCachedQuestionnaire(framework);
    if (cached) return cached;

    // Option 2: Use simplified assessment
    return await generateBasicQuestionnaire(framework);
  }
}
```

### Validation

```javascript
function validateTPRMResponse(result) {
  // Validate questionnaire structure
  if (!result.questionnaire_id) {
    throw new Error("Invalid questionnaire: missing ID");
  }

  if (!Array.isArray(result.questions) || result.questions.length === 0) {
    throw new Error("Invalid questionnaire: no questions");
  }

  // Validate question structure
  for (const q of result.questions) {
    if (!q.id || !q.question_text) {
      throw new Error(`Invalid question: ${JSON.stringify(q)}`);
    }
  }

  return true;
}
```

## Performance Optimization

### Caching Questionnaires

```javascript
// Cache generated questionnaires to avoid regeneration
const questionnaireCache = new Map();

async function getCachedQuestionnaire(framework, scope, entityType) {
  const cacheKey = `${framework}-${scope}-${entityType}`;

  if (questionnaireCache.has(cacheKey)) {
    return questionnaireCache.get(cacheKey);
  }

  const questionnaire = await use_mcp_tool({
    server_name: "tprm-frameworks",
    tool_name: "generate_questionnaire",
    arguments: { framework, scope, entity_type: entityType }
  });

  questionnaireCache.set(cacheKey, questionnaire);
  return questionnaire;
}
```

### Parallel Processing

```javascript
// Evaluate multiple vendors in parallel
async function batchAssessment(vendors) {
  const assessments = await Promise.all(
    vendors.map(async vendor => {
      const questionnaire = await getCachedQuestionnaire(
        "sig_lite", "lite", vendor.type
      );

      return use_mcp_tool({
        server_name: "tprm-frameworks",
        tool_name: "evaluate_response",
        arguments: {
          questionnaire_id: questionnaire.questionnaire_id,
          vendor_name: vendor.name,
          responses: vendor.responses
        }
      });
    })
  );

  return assessments;
}
```

## Testing Integration

### Integration Test Example

```python
import pytest
from mcp.client.session import ClientSession

@pytest.mark.asyncio
async def test_tprm_security_controls_integration():
    """Test integration between TPRM and Security Controls servers."""

    # Generate questionnaire
    questionnaire = await tprm_session.call_tool(
        "generate_questionnaire",
        {"framework": "sig_lite", "scope": "lite"}
    )

    # Map to controls
    mappings = await tprm_session.call_tool(
        "map_questionnaire_to_controls",
        {"framework": "sig_lite"}
    )

    # Get control details from security-controls-mcp
    control_id = mappings["mappings"][0]["scf_controls"][0]
    control = await security_controls_session.call_tool(
        "get_control",
        {"control_id": control_id, "framework": "scf"}
    )

    # Verify control exists and has expected structure
    assert control["id"] == control_id
    assert "description" in control
    assert "category" in control
```

## Troubleshooting Integration Issues

### Issue: Server Not Responding

```bash
# Check if server is running
ps aux | grep tprm_frameworks_mcp

# Test server directly
python3 -c "
import asyncio
from tprm_frameworks_mcp.server import health_check

async def test():
    health = await health_check()
    print(health)

asyncio.run(test())
"
```

### Issue: Cross-Server Communication Failing

```javascript
// Verify both servers are accessible
const servers = ["tprm-frameworks", "security-controls-mcp"];

for (const server of servers) {
  try {
    const result = await mcp_client.listTools(server);
    console.log(`✓ ${server}: ${result.length} tools available`);
  } catch (error) {
    console.error(`✗ ${server}: ${error.message}`);
  }
}
```

## Best Practices

1. **Questionnaire Caching**: Cache generated questionnaires to reduce repeated generation
2. **Batch Processing**: Process multiple vendors in parallel when possible
3. **Error Handling**: Always handle server unavailability gracefully
4. **Validation**: Validate all responses from MCP tools before using
5. **Logging**: Log all cross-server calls for debugging and auditing
6. **Timeouts**: Implement timeouts for all MCP tool calls
7. **Rate Limiting**: Respect rate limits when making multiple calls
8. **Version Pinning**: Pin MCP SDK versions for stability

## Support

For integration support:
- Email: hello@ansvar.eu
- Documentation: See DEPLOYMENT.md and README.md
- GitHub Issues: (if applicable)

---

**Last Updated**: 2026-02-07
**Integration Version**: 1.0
**Compatible Servers**: security-controls-mcp (v1.0+), eu-regulations-mcp (v1.0+)
