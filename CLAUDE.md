# TPRM Frameworks MCP - AI Agent Guide

## Project Overview

This is an MCP (Model Context Protocol) server for Third-Party Risk Management (TPRM) workflows in Ansvar AI. It provides tools for generating vendor assessment questionnaires, evaluating responses, and mapping to security controls.

## Architecture

### Core Components

1. **server.py**: Main MCP server with 16 tools
2. **data_loader.py**: Loads questionnaire frameworks from JSON
3. **models.py**: Data classes for questionnaires, questions, assessments
4. **evaluation/rubric.py**: Rule-based evaluation engine

### Data Flow

```
JSON Data → DataLoader → Question Objects → Tools → Evaluation → Results
```

### Key Design Decisions

1. **Structured JSON Output**: Questionnaires are returned as JSON for agent consumption
2. **Rule-Based Evaluation**: Uses regex patterns and keyword matching (not LLM-based)
3. **In-Memory Storage**: Generated questionnaires stored in dict (not persistent)
4. **SCF Integration**: Questions map to SCF controls via security-controls-mcp

## Working with This Codebase

### Adding New Framework Data

1. Create JSON file: `src/tprm_frameworks_mcp/data/<framework_key>.json`
2. Follow the structure in `sig_lite.json` or `caiq_v4.json`
3. Add SCF mappings to `questionnaire-to-scf.json`
4. Framework will auto-load on server start

### Question Data Structure

```json
{
  "id": "unique_id",
  "category": "Category Name",
  "subcategory": "Optional",
  "question_text": "The question?",
  "description": "Additional context",
  "expected_answer_type": "yes_no | text | multiple_choice",
  "is_required": true,
  "weight": 1-10,
  "regulatory_mappings": ["ISO 27001:2022 - 5.2"],
  "scf_control_mappings": ["GOV-01", "GOV-03"],
  "risk_if_inadequate": "critical | high | medium | low",
  "evaluation_rubric": {
    "acceptable": ["yes", "regex patterns"],
    "partially_acceptable": ["partial patterns"],
    "unacceptable": ["no", "negative patterns"],
    "required_keywords": ["keyword1", "keyword2"]
  }
}
```

### Evaluation Rubric System

The rubric evaluator (`evaluation/rubric.py`) uses:

1. **Pattern Matching**: Regex patterns for acceptable/unacceptable answers
2. **Keyword Detection**: Required keywords that must be present
3. **Completeness Scoring**: Based on response length and structure
4. **Strictness Levels**: lenient/moderate/strict adjust scoring

**Important**: Patterns are case-insensitive and use Python regex syntax.

### Testing Changes

```bash
# Quick test
python3 test_server.py

# Test MCP server directly
python3 -m tprm_frameworks_mcp
# (then send MCP protocol messages via stdin)
```

## Integration Points

### With security-controls-mcp

```
1. map_questionnaire_to_controls → get SCF control IDs
2. Use security-controls-mcp.get_control(id) for details
3. Use security-controls-mcp.map_frameworks for cross-framework mapping
```

### With vendor-intel-mcp (future)

```
generate_tprm_report accepts vendor_intel_data object:
{
  "company_profile": {...},
  "certifications": [...],
  "breach_history": [...]
}
```

### With EU-regulations-mcp

DORA and NIS2 questionnaires can be enhanced with:
- Article-level requirements
- Specific technical standards
- Timeline requirements

## Common Tasks

### Adding a New Tool

1. Add Tool definition in `@app.list_tools()` decorator
2. Add handler in `@app.call_tool()` function
3. Update README.md with tool documentation
4. Update server.json capabilities

### Updating Evaluation Logic

**Location**: `src/tprm_frameworks_mcp/evaluation/rubric.py`

- `evaluate_response()`: Main entry point
- `_evaluate_with_rubric()`: Uses question-specific rubric
- `_evaluate_generic()`: Fallback for questions without rubrics
- `_calculate_completeness()`: Scores response quality

### Modifying Risk Scoring

Overall risk calculation in `server.py`, `evaluate_response` tool:

```python
if overall_score >= 80: overall_risk = RiskLevel.LOW
elif overall_score >= 60: overall_risk = RiskLevel.MEDIUM
elif overall_score >= 40: overall_risk = RiskLevel.HIGH
else: overall_risk = RiskLevel.CRITICAL
```

## Known Limitations

1. **Placeholder Data**: Current questionnaires are samples, not full licensed content
2. **In-Memory Storage**: Generated questionnaires lost on restart
3. **No LLM Evaluation**: Uses only rule-based matching
4. **No Persistent Results**: Assessment results not saved
5. **No Multi-Language**: English only

## Future Enhancements

### Priority 1: Production Data
- Obtain licensed SIG content
- Download CAIQ v4 full dataset
- Extract DORA/NIS2 requirements

### Priority 2: Storage
- Add SQLite/PostgreSQL for questionnaires
- Persist evaluation results
- Track assessment history

### Priority 3: Enhanced Evaluation
- Optional LLM-based evaluation
- Evidence document analysis
- Confidence scoring

### Priority 4: Reporting
- PDF report generation
- Executive summary generation
- Trend analysis over time

## Code Patterns to Follow

1. **Enums for Constants**: Use enums (QuestionnaireFramework, RiskLevel, etc.)
2. **Dataclasses for Data**: Use @dataclass for structured data
3. **Type Hints**: Always include type hints
4. **Error Handling**: Return clear error messages, don't raise exceptions in tools
5. **JSON Output**: Structure output for agent consumption

## Testing Strategy

1. **Unit Tests**: Test evaluation rubric with known responses
2. **Integration Tests**: Test full questionnaire → evaluation flow
3. **Validation Tests**: Verify SCF mappings are accurate
4. **Load Tests**: Test with full 800-question SIG questionnaire

## Security Considerations

1. **Sensitive Data**: Vendor responses may contain confidential information
2. **Licensing**: Respect questionnaire framework licenses (SIG requires purchase)
3. **Validation**: Don't trust vendor responses without human review
4. **Rate Limiting**: Consider rate limits for evaluation endpoint

## Documentation Standards

- **Docstrings**: All functions have docstrings describing purpose and parameters
- **Type Hints**: All functions have complete type hints
- **Comments**: Explain "why", not "what"
- **README**: Keep tool documentation in sync with code

## Development Workflow

1. **Branch**: Create feature branch
2. **Implement**: Make changes with tests
3. **Test**: Run `python3 test_server.py`
4. **Document**: Update README.md and this file
5. **Commit**: Clear commit messages
6. **Deploy**: Update server in MCP configuration

## Troubleshooting

### "Framework not found"
- Check JSON file exists in `src/tprm_frameworks_mcp/data/`
- Verify framework key matches QuestionnaireFramework enum

### "Questionnaire not found"
- Questionnaires are in-memory only
- Generate new questionnaire each session
- Consider adding persistent storage

### Evaluation scores seem wrong
- Check rubric patterns in question JSON
- Test patterns with `re.search(pattern, answer, re.IGNORECASE)`
- Adjust strictness level

### Import errors
- Run from project root: `python3 -m tprm_frameworks_mcp`
- Ensure package installed: `pip install -e .`

## Contact & Support

- **Maintainer**: Ansvar Systems
- **Email**: hello@ansvar.eu
- **Issues**: File on GitHub repository

## Git Workflow

- **Never commit directly to `main`.** Always create a feature branch and open a Pull Request.
- Branch protection requires: verified signatures, PR review, and status checks to pass.
- Use conventional commit prefixes: `feat:`, `fix:`, `chore:`, `docs:`, etc.
