# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2026-02-17

### Added
- Full CAIQ v4.1 questionnaire (283 questions, 17 CCM domains)
- 16 MCP tools for TPRM workflows
- Streamable HTTP transport with /health endpoint
- SQLite persistence with vendor history tracking
- DORA/NIS2 dynamic questionnaire generation from EU regulations
- Evidence document storage and validation
- Assessment comparison and trend analysis
- Golden contract tests (fixtures/golden-tests.json)
- Data drift detection (fixtures/golden-hashes.json)
- sources.yml for complete data provenance
- 6-layer security scanning (CodeQL, Semgrep, Trivy, Gitleaks, pip-audit, OSSF Scorecard)
- CHANGELOG.md

### Changed
- Upgraded from stdio-only to dual-channel transport (stdio + Streamable HTTP)
- Improved tool descriptions for LLM agent readability
- Hardened input validation on all tools
- Synced server.json and manifest.json with actual tool definitions
- Moved internal docs from root to docs/internal/

### Fixed
- server.json only listed 7 of 16 tools
- manifest.json had empty tools array

## [0.1.0] - 2025-01-01

### Added
- Initial release with SIG Lite, CAIQ v4 sample, DORA, NIS2 frameworks
- 7 core tools (list, generate, evaluate, map, report, get, search)
- Rule-based evaluation engine
- SCF control mapping
