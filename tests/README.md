# TPRM-Frameworks MCP Integration Tests

Comprehensive integration test suite for validating Phase 0 deployment of the TPRM-Frameworks MCP server.

## Overview

This test suite validates all core functionality of the TPRM-Frameworks MCP server:

- **7 MCP Tools**: All tools are callable and functional
- **Data Loading**: Sample data for CAIQ, SIG, DORA, and NIS2 frameworks
- **Questionnaire Generation**: Full, lite, and focused questionnaires
- **Response Evaluation**: Good, poor, and mixed responses with strictness levels
- **Control Mapping**: Integration with SCF (Secure Controls Framework)
- **Report Generation**: Basic and comprehensive TPRM reports
- **End-to-End Scenarios**: Complete assessment workflows

## Test Structure

```
tests/
├── __init__.py              # Test package initialization
├── conftest.py              # Pytest configuration and fixtures
├── integration_test.py      # Main integration test suite
└── README.md               # This file
```

## Running Tests

### Run All Tests

```bash
# From project root
pytest tests/ -v

# Or with pytest-asyncio
pytest tests/ -v --tb=short
```

### Run Specific Test Classes

```bash
# Test only tool availability
pytest tests/integration_test.py::TestMCPToolAvailability -v

# Test only data loading
pytest tests/integration_test.py::TestDataLoading -v

# Test complete Salesforce scenario
pytest tests/integration_test.py::TestSalesforceDoraScenario -v
```

### Run with Markers

```bash
# Run only scenario tests
pytest tests/ -v -m scenario

# Run only fast tests (exclude slow)
pytest tests/ -v -m "not slow"

# Run integration tests
pytest tests/ -v -m integration
```

### Run with Coverage

```bash
# Install coverage
pip install pytest-cov

# Run with coverage report
pytest tests/ --cov=tprm_frameworks_mcp --cov-report=html --cov-report=term
```

## Test Classes

### 1. TestMCPToolAvailability
Tests that all 7 MCP tools are available and have correct signatures.

- `test_list_tools_count()` - Verify 7 tools exist
- `test_tool_names()` - Verify all expected tool names

### 2. TestDataLoading
Tests that sample data loads correctly from JSON files.

- `test_framework_loading()` - Verify all frameworks load
- `test_sig_lite_questions()` - Verify SIG Lite data
- `test_caiq_questions()` - Verify CAIQ v4 data
- `test_dora_questions()` - Verify DORA ICT TPP data
- `test_nis2_questions()` - Verify NIS2 Supply Chain data

### 3. TestQuestionnaireGeneration
Tests questionnaire generation with various parameters.

- `test_generate_full_questionnaire()` - Full questionnaire
- `test_generate_lite_questionnaire()` - Lite/filtered questionnaire
- `test_generate_with_regulations()` - Regulatory filters

### 4. TestResponseEvaluation
Tests vendor response evaluation with the rubric system.

- `test_evaluate_good_responses()` - High-quality responses
- `test_evaluate_poor_responses()` - Poor/incomplete responses
- `test_evaluate_with_strictness_levels()` - Lenient, moderate, strict

### 5. TestControlMapping
Tests mapping questionnaires to security controls.

- `test_map_questionnaire_to_scf()` - Full framework mapping
- `test_map_specific_questions()` - Specific question mapping

### 6. TestReportGeneration
Tests TPRM report generation.

- `test_generate_basic_report()` - Basic report
- `test_generate_report_with_all_data()` - Comprehensive report with all data sources

### 7. TestUtilityTools
Tests utility functions (list, get, search).

- `test_list_frameworks()` - List all frameworks
- `test_get_questionnaire()` - Retrieve generated questionnaire
- `test_search_questions()` - Search by keyword
- `test_search_questions_all_frameworks()` - Cross-framework search

### 8. TestSalesforceDoraScenario ⭐
**End-to-end integration test** simulating a complete assessment workflow.

**Scenario**: Assess Salesforce (SaaS provider) for DORA compliance

**Steps**:
1. Generate DORA ICT TPP questionnaire for SaaS provider
2. Simulate realistic vendor responses (mix of good/bad/partial answers)
3. Evaluate responses with moderate strictness
4. Map questions to SCF controls
5. Generate comprehensive TPRM report with vendor intelligence and security posture data
6. Verify data consistency end-to-end

**Expected Results**:
- Questionnaire generated successfully
- Responses evaluated with realistic scores (40-80/100)
- Control mappings produced
- Comprehensive report including all data sources

### 9. TestPhase0Validation
Validates Phase 0 deployment readiness.

- `test_all_tools_callable()` - All tools work
- `test_data_integrity()` - Data structure validation
- `test_evaluation_consistency()` - Consistent scoring
- `test_performance_baseline()` - Performance benchmarks

## Fixtures

### `reset_state`
Auto-used fixture that resets server state between tests.

### `sample_vendor_data`
Provides sample vendor profile data for testing.

### `sample_responses`
Provides pre-defined response examples (good, partial, poor, N/A).

### `dora_assessment_context`
Provides DORA assessment context for testing.

## Expected Test Output

```
╔══════════════════════════════════════════════════════════════════════════════╗
║                                                                              ║
║           TPRM-Frameworks MCP Server - Integration Test Suite               ║
║                        Phase 0 Deployment Validation                         ║
║                                                                              ║
╚══════════════════════════════════════════════════════════════════════════════╝

tests/integration_test.py::TestMCPToolAvailability::test_list_tools_count PASSED
tests/integration_test.py::TestMCPToolAvailability::test_tool_names PASSED
tests/integration_test.py::TestDataLoading::test_framework_loading PASSED
tests/integration_test.py::TestDataLoading::test_sig_lite_questions PASSED
tests/integration_test.py::TestDataLoading::test_caiq_questions PASSED
tests/integration_test.py::TestDataLoading::test_dora_questions PASSED
tests/integration_test.py::TestDataLoading::test_nis2_questions PASSED
...
tests/integration_test.py::TestSalesforceDoraScenario::test_complete_salesforce_dora_assessment PASSED

================================================================================
SCENARIO: Assess Salesforce (SaaS Provider) for DORA Compliance
================================================================================

Step 1: Generating DORA ICT TPP questionnaire for SaaS provider...
✓ Generated questionnaire <uuid>
  - Framework: DORA ICT TPP
  - Entity Type: SaaS Provider
  - Total Questions: 85

Step 2: Simulating Salesforce vendor responses...
✓ Simulated 85 vendor responses
  - Mix of excellent, partial, poor, and minimal responses

Step 3: Evaluating Salesforce responses...
✓ Evaluation complete
  - Overall Score: 62.5/100
  - Overall Risk Level: MEDIUM

Step 4: Mapping DORA questions to SCF controls...
✓ Control mapping complete
  - Mapped Questions: 75
  - Target Framework: SCF

Step 5: Generating comprehensive TPRM report...
✓ TPRM Report generated
  - Includes questionnaire assessment
  - Includes vendor intelligence data
  - Includes security posture analysis
  - Includes recommendations

================================================================================
ASSESSMENT SUMMARY
================================================================================
Vendor: Salesforce
Assessment Type: DORA ICT Third-Party Provider
Questions Evaluated: 85
Overall Score: 62.5/100
Risk Level: MEDIUM
Controls Mapped: 75 SCF controls
Certifications: 6 verified
Security Posture: SSL A+, 0 critical vulns
================================================================================

✅ Complete Salesforce DORA assessment scenario passed!

======================== 30 passed in 5.42s ========================
```

## Continuous Integration

### GitHub Actions Example

```yaml
name: Integration Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: ["3.10", "3.11", "3.12"]

    steps:
    - uses: actions/checkout@v3
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: ${{ matrix.python-version }}
    - name: Install dependencies
      run: |
        pip install -e ".[dev]"
    - name: Run integration tests
      run: |
        pytest tests/ -v --cov=tprm_frameworks_mcp --cov-report=xml
    - name: Upload coverage
      uses: codecov/codecov-action@v3
      with:
        files: ./coverage.xml
```

## Troubleshooting

### Import Errors

If you get import errors, ensure you're running from the project root:

```bash
# Install in development mode
pip install -e .

# Or run with PYTHONPATH
PYTHONPATH=./src pytest tests/ -v
```

### Async Test Errors

Ensure `pytest-asyncio` is installed:

```bash
pip install pytest-asyncio
```

### Data File Not Found

Ensure data files exist in `src/tprm_frameworks_mcp/data/`:

```bash
ls -la src/tprm_frameworks_mcp/data/
# Should show: sig_lite.json, caiq_v4.json, dora_ict_tpp.json, nis2_supply_chain.json
```

## Performance Benchmarks

Expected performance for Phase 0:

| Operation | Target Time | Notes |
|-----------|-------------|-------|
| Generate Questionnaire | < 2s | Full questionnaire, 100+ questions |
| Evaluate Response | < 3s | 50 responses |
| Map Controls | < 1s | Full framework mapping |
| Generate Report | < 1s | Basic report |
| Complete Assessment | < 10s | End-to-end scenario |

## Test Coverage Goals

- **Line Coverage**: > 80%
- **Branch Coverage**: > 70%
- **Function Coverage**: > 90%

## Contributing

When adding new features, please:

1. Add corresponding integration tests
2. Update this README
3. Ensure all existing tests pass
4. Add markers for slow tests (`@pytest.mark.slow`)
5. Document expected behavior

## License

Apache 2.0 - See main project LICENSE file
