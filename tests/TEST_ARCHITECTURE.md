# Integration Test Architecture

## Test Suite Overview

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                 TPRM-Frameworks MCP Integration Test Suite                 │
│                         Phase 0 Deployment Validation                       │
└─────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────┐
│  Test Classes: 9                                                            │
│  Test Methods: 30+                                                          │
│  Coverage Target: > 80%                                                     │
│  Frameworks: SIG Lite, CAIQ v4, DORA ICT TPP, NIS2 Supply Chain            │
└─────────────────────────────────────────────────────────────────────────────┘
```

## Test Class Hierarchy

```
integration_test.py
│
├── TestMCPToolAvailability (2 tests)
│   ├── test_list_tools_count()
│   └── test_tool_names()
│
├── TestDataLoading (5 tests)
│   ├── test_framework_loading()
│   ├── test_sig_lite_questions()
│   ├── test_caiq_questions()
│   ├── test_dora_questions()
│   └── test_nis2_questions()
│
├── TestQuestionnaireGeneration (3 tests)
│   ├── test_generate_full_questionnaire()
│   ├── test_generate_lite_questionnaire()
│   └── test_generate_with_regulations()
│
├── TestResponseEvaluation (3 tests)
│   ├── test_evaluate_good_responses()
│   ├── test_evaluate_poor_responses()
│   └── test_evaluate_with_strictness_levels()
│
├── TestControlMapping (2 tests)
│   ├── test_map_questionnaire_to_scf()
│   └── test_map_specific_questions()
│
├── TestReportGeneration (2 tests)
│   ├── test_generate_basic_report()
│   └── test_generate_report_with_all_data()
│
├── TestUtilityTools (4 tests)
│   ├── test_list_frameworks()
│   ├── test_get_questionnaire()
│   ├── test_search_questions()
│   └── test_search_questions_all_frameworks()
│
├── TestSalesforceDoraScenario (1 comprehensive test) ⭐
│   └── test_complete_salesforce_dora_assessment()
│       ├── Step 1: Generate DORA questionnaire
│       ├── Step 2: Simulate vendor responses
│       ├── Step 3: Evaluate responses
│       ├── Step 4: Map to SCF controls
│       ├── Step 5: Generate TPRM report
│       └── Step 6: Validate consistency
│
└── TestPhase0Validation (4 tests)
    ├── test_all_tools_callable()
    ├── test_data_integrity()
    ├── test_evaluation_consistency()
    └── test_performance_baseline()
```

## Test Coverage Map

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                            MCP Server Components                            │
└─────────────────────────────────────────────────────────────────────────────┘

server.py (7 tools)
├── list_frameworks           ✓ Tested by: TestUtilityTools
├── generate_questionnaire    ✓ Tested by: TestQuestionnaireGeneration
├── evaluate_response         ✓ Tested by: TestResponseEvaluation
├── map_questionnaire_to_controls ✓ Tested by: TestControlMapping
├── generate_tprm_report      ✓ Tested by: TestReportGeneration
├── get_questionnaire         ✓ Tested by: TestUtilityTools
└── search_questions          ✓ Tested by: TestUtilityTools

data_loader.py
├── get_all_frameworks()      ✓ Tested by: TestDataLoading
├── get_questions()           ✓ Tested by: TestDataLoading
├── get_control_mappings()    ✓ Tested by: TestControlMapping
├── get_categories()          ✓ Tested by: TestQuestionnaireGeneration
└── search_questions()        ✓ Tested by: TestUtilityTools

evaluation/rubric.py
├── evaluate_response()       ✓ Tested by: TestResponseEvaluation
├── _evaluate_with_rubric()   ✓ Tested by: TestSalesforceDoraScenario
├── _evaluate_generic()       ✓ Tested by: TestResponseEvaluation
└── _calculate_completeness() ✓ Tested by: TestResponseEvaluation

models.py
├── All data classes          ✓ Tested by: All tests
└── All enums                 ✓ Tested by: All tests

data/
├── sig_lite.json             ✓ Tested by: TestDataLoading
├── caiq_v4.json              ✓ Tested by: TestDataLoading
├── dora_ict_tpp.json         ✓ Tested by: TestDataLoading, TestSalesforceDoraScenario
├── nis2_supply_chain.json    ✓ Tested by: TestDataLoading
└── questionnaire-to-scf.json ✓ Tested by: TestControlMapping
```

## End-to-End Scenario Flow

```
┌─────────────────────────────────────────────────────────────────────────────┐
│       TestSalesforceDoraScenario: Complete Assessment Workflow              │
└─────────────────────────────────────────────────────────────────────────────┘

Input: Salesforce (SaaS Provider) + DORA Compliance Requirements

┌─────────────────────────────────────────────────────────────────────────────┐
│ STEP 1: Generate Questionnaire                                              │
├─────────────────────────────────────────────────────────────────────────────┤
│ Tool: generate_questionnaire                                                │
│ Input:                                                                       │
│   - framework: "dora_ict_tpp"                                               │
│   - scope: "full"                                                           │
│   - entity_type: "saas_provider"                                            │
│   - regulations: ["DORA", "NIS2"]                                           │
│ Output:                                                                      │
│   - questionnaire_id: <uuid>                                                │
│   - total_questions: 85                                                     │
│   - categories: 7 (ICT Risk, Business Continuity, etc.)                     │
└─────────────────────────────────────────────────────────────────────────────┘
                                    ↓
┌─────────────────────────────────────────────────────────────────────────────┐
│ STEP 2: Simulate Vendor Responses                                           │
├─────────────────────────────────────────────────────────────────────────────┤
│ Response Quality Distribution:                                              │
│   - 25% Excellent (comprehensive with docs)                                 │
│   - 25% Partial (some gaps)                                                 │
│   - 25% Poor (not implemented)                                              │
│   - 25% Minimal (basic compliance)                                          │
│ Total: 85 responses                                                         │
└─────────────────────────────────────────────────────────────────────────────┘
                                    ↓
┌─────────────────────────────────────────────────────────────────────────────┐
│ STEP 3: Evaluate Responses                                                  │
├─────────────────────────────────────────────────────────────────────────────┤
│ Tool: evaluate_response                                                     │
│ Input:                                                                       │
│   - questionnaire_id: <from step 1>                                         │
│   - vendor_name: "Salesforce"                                               │
│   - responses: <85 responses from step 2>                                   │
│   - strictness: "moderate"                                                  │
│ Output:                                                                      │
│   - overall_score: 40-80/100 (expected range)                               │
│   - overall_risk_level: MEDIUM (expected)                                   │
│   - critical_findings: <list of gaps>                                       │
│   - compliance_gaps: {regulation: [question_ids]}                           │
└─────────────────────────────────────────────────────────────────────────────┘
                                    ↓
┌─────────────────────────────────────────────────────────────────────────────┐
│ STEP 4: Map to Controls                                                     │
├─────────────────────────────────────────────────────────────────────────────┤
│ Tool: map_questionnaire_to_controls                                         │
│ Input:                                                                       │
│   - framework: "dora_ict_tpp"                                               │
│   - control_framework: "scf"                                                │
│ Output:                                                                      │
│   - mapped_questions: 75+ (expected)                                        │
│   - scf_controls: RSK-01, RSK-02, BCD-01, IRO-01, etc.                      │
│   - categories: ICT Risk Management, Business Continuity, etc.              │
└─────────────────────────────────────────────────────────────────────────────┘
                                    ↓
┌─────────────────────────────────────────────────────────────────────────────┐
│ STEP 5: Generate TPRM Report                                                │
├─────────────────────────────────────────────────────────────────────────────┤
│ Tool: generate_tprm_report                                                  │
│ Input:                                                                       │
│   - vendor_name: "Salesforce"                                               │
│   - questionnaire_results: [<uuid from step 1>]                             │
│   - vendor_intel_data: {certifications, breach_history, etc.}               │
│   - posture_data: {ssl_grade, vulnerabilities, etc.}                        │
│   - include_recommendations: true                                           │
│ Output:                                                                      │
│   - Comprehensive TPRM report including:                                    │
│     • Executive Summary                                                     │
│     • Questionnaire Assessment Results                                      │
│     • Vendor Intelligence (6 certifications)                                │
│     • Security Posture (SSL A+, 0 critical vulns)                           │
│     • Risk Assessment                                                       │
│     • Recommendations                                                       │
└─────────────────────────────────────────────────────────────────────────────┘
                                    ↓
┌─────────────────────────────────────────────────────────────────────────────┐
│ STEP 6: Validate Consistency                                                │
├─────────────────────────────────────────────────────────────────────────────┤
│ Tool: get_questionnaire                                                     │
│ Validates:                                                                   │
│   - Questionnaire persisted correctly                                       │
│   - Data retrievable by ID                                                  │
│   - All tools integrated successfully                                       │
└─────────────────────────────────────────────────────────────────────────────┘
                                    ↓
                           ✅ ASSESSMENT COMPLETE
```

## Test Data Flow

```
┌──────────────┐
│  JSON Data   │
│    Files     │
└──────┬───────┘
       │
       ├─── sig_lite.json
       ├─── caiq_v4.json
       ├─── dora_ict_tpp.json
       ├─── nis2_supply_chain.json
       └─── questionnaire-to-scf.json
       │
       ↓
┌──────────────┐
│ TPRMDataLoader│
│  (data_loader)│
└──────┬───────┘
       │
       ├─── get_all_frameworks()
       ├─── get_questions()
       ├─── get_control_mappings()
       └─── search_questions()
       │
       ↓
┌──────────────┐
│ MCP Server   │
│    Tools     │
└──────┬───────┘
       │
       ├─── generate_questionnaire
       ├─── evaluate_response
       ├─── map_questionnaire_to_controls
       ├─── generate_tprm_report
       ├─── get_questionnaire
       └─── search_questions
       │
       ↓
┌──────────────┐
│ Integration  │
│    Tests     │
└──────────────┘
```

## Test Fixtures

```
conftest.py
│
├── reset_state
│   └── Resets server state between tests
│       ├── Clears generated_questionnaires
│       └── Restores original state
│
├── sample_vendor_data
│   └── Provides test vendor profile
│       ├── name, type, employees
│       ├── certifications
│       └── regions
│
├── sample_responses
│   └── Provides pre-defined response examples
│       ├── good: High-quality responses
│       ├── partial: Incomplete responses
│       ├── poor: Inadequate responses
│       └── na: Not applicable responses
│
└── dora_assessment_context
    └── Provides DORA assessment context
        ├── framework, entity_type
        ├── regulations
        └── vendor_profile
```

## Performance Targets

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                          Performance Benchmarks                             │
├─────────────────────────┬────────────┬─────────────┬────────────────────────┤
│ Operation               │ Target     │ Expected    │ Test                   │
├─────────────────────────┼────────────┼─────────────┼────────────────────────┤
│ Generate Questionnaire  │ < 2s       │ ~0.5s       │ test_performance_      │
│                         │            │             │   baseline()           │
├─────────────────────────┼────────────┼─────────────┼────────────────────────┤
│ Evaluate 50 Responses   │ < 3s       │ ~1.2s       │ test_evaluate_         │
│                         │            │             │   good_responses()     │
├─────────────────────────┼────────────┼─────────────┼────────────────────────┤
│ Map Controls            │ < 1s       │ ~0.3s       │ test_map_              │
│                         │            │             │   questionnaire_to_scf()│
├─────────────────────────┼────────────┼─────────────┼────────────────────────┤
│ Generate Report         │ < 1s       │ ~0.2s       │ test_generate_         │
│                         │            │             │   basic_report()       │
├─────────────────────────┼────────────┼─────────────┼────────────────────────┤
│ Complete Assessment     │ < 10s      │ ~5s         │ test_complete_         │
│ (End-to-End)            │            │             │   salesforce_dora_     │
│                         │            │             │   assessment()         │
└─────────────────────────┴────────────┴─────────────┴────────────────────────┘
```

## Coverage Analysis

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           Coverage Breakdown                                │
├──────────────────────────┬──────────────────────────────────────────────────┤
│ Component                │ Test Coverage                                    │
├──────────────────────────┼──────────────────────────────────────────────────┤
│ server.py                │ All 7 tools: 100%                                │
│   - list_frameworks      │ ✓ 2 tests                                        │
│   - generate_questionnaire│ ✓ 4 tests                                       │
│   - evaluate_response    │ ✓ 4 tests                                        │
│   - map_to_controls      │ ✓ 2 tests                                        │
│   - generate_report      │ ✓ 2 tests                                        │
│   - get_questionnaire    │ ✓ 2 tests                                        │
│   - search_questions     │ ✓ 2 tests                                        │
├──────────────────────────┼──────────────────────────────────────────────────┤
│ data_loader.py           │ Core functions: 100%                             │
│   - Framework loading    │ ✓ 5 tests                                        │
│   - Question retrieval   │ ✓ 8 tests                                        │
│   - Control mapping      │ ✓ 2 tests                                        │
│   - Search               │ ✓ 2 tests                                        │
├──────────────────────────┼──────────────────────────────────────────────────┤
│ evaluation/rubric.py     │ Evaluation logic: 90%+                           │
│   - Generic evaluation   │ ✓ 3 tests                                        │
│   - Rubric evaluation    │ ✓ 2 tests                                        │
│   - Strictness levels    │ ✓ 1 test                                         │
│   - Completeness calc    │ ✓ Tested indirectly                              │
├──────────────────────────┼──────────────────────────────────────────────────┤
│ models.py                │ Data models: 100%                                │
│   - All dataclasses      │ ✓ Used in all tests                              │
│   - All enums            │ ✓ Used in all tests                              │
├──────────────────────────┼──────────────────────────────────────────────────┤
│ data/*.json              │ Sample data: 100%                                │
│   - 4 questionnaires     │ ✓ 5 tests                                        │
│   - Control mappings     │ ✓ 2 tests                                        │
└──────────────────────────┴──────────────────────────────────────────────────┘

Expected Overall Coverage: > 80% (line), > 70% (branch), > 90% (function)
```

## CI/CD Pipeline

```
GitHub Actions Workflow
│
├── Test Matrix
│   ├── Python 3.10
│   ├── Python 3.11
│   └── Python 3.12
│
├── Jobs
│   │
│   ├── test (Matrix)
│   │   ├── Install dependencies
│   │   ├── Verify data files
│   │   ├── Run fast tests
│   │   ├── Run full tests with coverage
│   │   ├── Upload test results
│   │   └── Upload coverage (Python 3.11 only)
│   │
│   ├── test-summary
│   │   ├── Download all test results
│   │   └── Publish combined results
│   │
│   └── phase0-validation
│       ├── Run Phase 0 validation tests
│       ├── Run Salesforce DORA scenario
│       ├── Verify all 7 tools operational
│       └── Create deployment badge
│
└── Triggers
    ├── Push to main/develop
    ├── Pull requests
    └── Manual workflow dispatch
```

## Test Execution Order

```
Recommended execution order for efficient testing:

1. TestMCPToolAvailability       (< 1s)   - Quick sanity check
2. TestDataLoading               (< 1s)   - Verify data integrity
3. TestUtilityTools              (< 2s)   - Test basic operations
4. TestQuestionnaireGeneration   (< 2s)   - Test questionnaire creation
5. TestResponseEvaluation        (< 3s)   - Test evaluation engine
6. TestControlMapping            (< 2s)   - Test control mapping
7. TestReportGeneration          (< 2s)   - Test report generation
8. TestPhase0Validation          (< 3s)   - Deployment checks
9. TestSalesforceDoraScenario    (< 5s)   - Complete end-to-end test

Total estimated time: ~20 seconds for all tests
```

## Validation Checklist

```
Phase 0 Deployment Validation
├── [ ] All 7 MCP tools callable
├── [ ] 4 framework data files loaded
├── [ ] Questionnaire generation (full, lite, focused)
├── [ ] Response evaluation (all strictness levels)
├── [ ] Control mapping (SCF integration)
├── [ ] Report generation (basic + comprehensive)
├── [ ] End-to-end scenario passes
├── [ ] Data integrity validated
├── [ ] Performance benchmarks met
├── [ ] All 30+ tests passing
└── [ ] Coverage > 80%

When all boxes checked → Phase 0 Validated ✅
```

## Architecture Summary

The integration test suite provides comprehensive validation of the TPRM-Frameworks MCP server through:

1. **Unit-level testing** of individual tools and components
2. **Integration testing** of tool combinations and data flow
3. **End-to-end testing** via the Salesforce DORA scenario
4. **Performance testing** via baseline benchmarks
5. **Data integrity testing** via validation checks
6. **CI/CD integration** via GitHub Actions workflow

This ensures Phase 0 deployment is production-ready and all functionality works as expected.
