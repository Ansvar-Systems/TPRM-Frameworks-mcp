# Integration Tests - Quick Start

## Installation

```bash
# Install with dev dependencies
pip install -e ".[dev]"
```

## Run Tests

### Basic Commands

```bash
# All tests (recommended first run)
pytest tests/ -v

# Fast tests only (skip slow tests)
pytest tests/ -v -m "not slow"

# Only the Salesforce DORA scenario
pytest tests/integration_test.py::TestSalesforceDoraScenario -v -s
```

### Using the Test Runner Script

```bash
# Make executable (one time)
chmod +x run_integration_tests.sh

# Run all tests
./run_integration_tests.sh

# Run fast tests only
./run_integration_tests.sh fast

# Run scenario tests only
./run_integration_tests.sh scenario

# Run with coverage report
./run_integration_tests.sh coverage
```

## Expected Results

### Success Indicators

```
✅ 30 passed in ~5 seconds
✅ Coverage > 80%
✅ Salesforce DORA scenario completes
✅ Overall Score: 40-80/100 (realistic mix)
✅ All 7 tools callable
```

### Key Tests

| Test | What It Validates |
|------|-------------------|
| `TestMCPToolAvailability` | All 7 tools exist and callable |
| `TestDataLoading` | CAIQ, SIG, DORA, NIS2 data loads |
| `TestSalesforceDoraScenario` | **Complete end-to-end workflow** |
| `TestPhase0Validation` | Deployment readiness |

## Test Output Example

```
SCENARIO: Assess Salesforce (SaaS Provider) for DORA Compliance
================================================================================

Step 1: Generating DORA ICT TPP questionnaire for SaaS provider...
✓ Generated questionnaire <uuid>
  - Framework: DORA ICT TPP
  - Entity Type: SaaS Provider
  - Total Questions: 85

Step 2: Simulating Salesforce vendor responses...
✓ Simulated 85 vendor responses

Step 3: Evaluating Salesforce responses...
✓ Evaluation complete
  - Overall Score: 62.5/100
  - Overall Risk Level: MEDIUM

Step 4: Mapping DORA questions to SCF controls...
✓ Control mapping complete
  - Mapped Questions: 75

Step 5: Generating comprehensive TPRM report...
✓ TPRM Report generated

ASSESSMENT SUMMARY
================================================================================
Vendor: Salesforce
Questions Evaluated: 85
Overall Score: 62.5/100
Risk Level: MEDIUM
Controls Mapped: 75 SCF controls
✅ Complete Salesforce DORA assessment scenario passed!
```

## Troubleshooting

### Issue: Module not found

```bash
# Solution
pip install -e .
```

### Issue: pytest not found

```bash
# Solution
pip install pytest pytest-asyncio
```

### Issue: Data files not found

```bash
# Verify files exist
ls -la src/tprm_frameworks_mcp/data/

# Should have: sig_lite.json, caiq_v4.json, dora_ict_tpp.json, nis2_supply_chain.json
```

## Specific Test Examples

```bash
# Test all 7 tools are available
pytest tests/integration_test.py::TestMCPToolAvailability -v

# Test data loading
pytest tests/integration_test.py::TestDataLoading -v

# Test questionnaire generation
pytest tests/integration_test.py::TestQuestionnaireGeneration -v

# Test response evaluation
pytest tests/integration_test.py::TestResponseEvaluation -v

# Test complete Salesforce scenario (most important!)
pytest tests/integration_test.py::TestSalesforceDoraScenario::test_complete_salesforce_dora_assessment -v -s
```

## Coverage Report

```bash
# Generate HTML coverage report
pytest tests/ --cov=tprm_frameworks_mcp --cov-report=html

# Open in browser
open htmlcov/index.html  # macOS
xdg-open htmlcov/index.html  # Linux
```

## CI/CD

Tests run automatically on:
- Push to `main` or `develop`
- Pull requests
- Manual trigger via GitHub Actions

Check workflow: `.github/workflows/integration-tests.yml`

## Phase 0 Deployment Checklist

Run these commands to validate Phase 0:

```bash
# 1. Verify all tools callable
pytest tests/integration_test.py::TestMCPToolAvailability -v

# 2. Verify data loads
pytest tests/integration_test.py::TestDataLoading -v

# 3. Run Salesforce scenario
pytest tests/integration_test.py::TestSalesforceDoraScenario -v -s

# 4. Run validation tests
pytest tests/integration_test.py::TestPhase0Validation -v

# 5. Full test suite
pytest tests/ -v

# 6. Coverage check
pytest tests/ --cov=tprm_frameworks_mcp --cov-report=term-missing
```

If all pass → **Phase 0 Validated ✅**

## More Information

- Detailed docs: `tests/README.md`
- Testing guide: `TESTING.md`
- Test code: `tests/integration_test.py`

## Quick Reference

| Command | Purpose |
|---------|---------|
| `pytest tests/ -v` | Run all tests |
| `pytest -m "not slow"` | Fast tests only |
| `pytest -m scenario` | Scenario tests only |
| `pytest --collect-only` | List all tests |
| `pytest tests/ --cov` | Run with coverage |
| `pytest -k salesforce` | Run Salesforce tests |
| `pytest -x` | Stop on first failure |
| `pytest -s` | Show print output |
| `pytest --tb=short` | Short traceback |
