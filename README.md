# TPRM Frameworks MCP Server

Third-Party Risk Management (TPRM) MCP server for Ansvar AI workflows. Provides questionnaire generation, vendor response evaluation, and compliance mapping for vendor security assessments.

## Features

- **Questionnaire Generation**: Generate tailored vendor assessment questionnaires from industry-standard frameworks
- **Response Evaluation**: Rule-based scoring engine with configurable rubrics
- **Control Mapping**: Bridge questionnaire questions to SCF (Secure Controls Framework) controls
- **Compliance Overlay**: Filter and prioritize questions based on applicable regulations
- **Report Generation**: Aggregate assessment results with vendor intelligence and security posture data
- **Persistence Layer**: SQLite database with historical tracking, vendor history, and trend analysis
- **Database Tools**: Migration, backup/restore, and inspection utilities

## Supported Frameworks

| Framework | Version | Questions | Status | SCF Mappings |
|-----------|---------|-----------|--------|--------------|
| **CAIQ v4.1 Full** | **4.1.0** | **283** | **✅ Production** | **✅ Complete** |
| SIG Full | 2025.1 | ~800 | Placeholder | Partial |
| SIG Lite | 2025.1 | ~180 | Placeholder | ✅ Complete |
| VSA | - | TBD | Placeholder | - |
| DORA ICT TPP | 1.0 | ~85 | Placeholder | Partial |
| NIS2 Supply Chain | 1.0 | ~65 | Placeholder | Partial |

**Production Ready**: CAIQ v4.1 is complete with all 283 questions, enhanced evaluation rubrics, and full SCF control mappings.

**Note**: Other frameworks use sample data for development. Replace with licensed questionnaire content for production use.

## Installation

```bash
# Install from source
cd TPRM-Frameworks-mcp
pip install -e .

# Or with dev dependencies
pip install -e ".[dev]"

# Initialize database (Phase 1+)
python scripts/migrate_db.py --migrate
```

## Usage

### Running the Server

```bash
# Run directly
python -m tprm_frameworks_mcp

# Or use the CLI command
tprm-mcp
```

### MCP Configuration

Add to your MCP settings file:

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

## Available Tools (13 Total)

### Core Assessment Tools
1. **list_frameworks** - List all available questionnaire frameworks
2. **generate_questionnaire** - Generate tailored vendor assessment
3. **evaluate_response** - Score vendor responses with rubric-based evaluation
4. **map_questionnaire_to_controls** - Map questions to SCF controls
5. **generate_tprm_report** - Create comprehensive TPRM report
6. **get_questionnaire** - Retrieve questionnaire by ID
7. **search_questions** - Search questions by keyword

### Persistence & History Tools
8. **get_vendor_history** - Retrieve complete assessment history for a vendor
9. **compare_assessments** - Compare two assessments to show changes over time

### EU Regulations Integration Tools
10. **generate_dora_questionnaire** - Generate DORA ICT third-party questionnaire from EU regulations
11. **generate_nis2_questionnaire** - Generate NIS2 supply chain questionnaire from EU regulations
12. **check_regulatory_compliance** - Check DORA/NIS2 compliance gaps for assessments
13. **get_regulatory_timeline** - Get DORA/NIS2 compliance deadlines and milestones

## CAIQ v4.1 Usage Examples

The complete CSA Consensus Assessment Initiative Questionnaire v4.1 is now available with all 283 questions.

### Generate Full CAIQ Assessment

```python
# Generate complete CAIQ v4.1 questionnaire
{
  "framework": "caiq_v4_full",
  "scope": "full",
  "entity_type": "saas_provider"
}
# Returns: 283 questions across 17 CCM domains
```

### Filter by Domain

```python
# Filter questions by category
from tprm_frameworks_mcp.data_loader import TPRMDataLoader

loader = TPRMDataLoader()
crypto_questions = loader.get_questions(
    "caiq_v4_full",
    category="Cryptography, Encryption & Key Management"
)
# Returns: 23 cryptography questions
```

### Domain Breakdown

- **Cryptography & Encryption**: 23 questions (Weight: 10, Risk: Critical)
- **Data Security & Privacy**: 24 questions (Weight: 8-10)
- **Identity & Access Management**: 19 questions (Weight: 10, Risk: Critical)
- **Datacenter Security**: 28 questions
- **Logging & Monitoring**: 19 questions
- **15 additional CCM domains**: 170 questions

### Enhanced Evaluation Rubrics

CAIQ v4.1 includes domain-specific evaluation patterns:

- **Cryptography**: Detects AES-256, TLS 1.2+, HSM, key rotation
- **Access Control**: Validates MFA, RBAC, least privilege
- **Audit**: Recognizes SOC 2, ISO 27001, independent audits
- **Data Security**: Checks classification, encryption, retention policies

### SCF Control Mappings

All 283 questions map to Secure Controls Framework (SCF) controls for cross-framework compliance analysis.

## EU Regulations Integration

The server now includes dynamic questionnaire generation from DORA and NIS2 regulations, with automatic mapping to regulatory articles.

### Generate DORA Questionnaire

```python
# Generate ICT third-party risk questionnaire from DORA Articles 28-30
{
  "category": "ICT_third_party",
  "scope": "full"
}
# Returns: Dynamic questionnaire with regulatory traceability
```

**DORA Categories**:
- `ICT_third_party` - Articles 28-30 (Third-party risk management)
- `ICT_risk` - Articles 6, 8 (Risk management framework)
- `business_continuity` - Articles 11-13 (BCP/DR)
- `incident_management` - Articles 17, 19-20 (Incident reporting)
- `testing` - Articles 15, 26-27 (Operational resilience testing)

### Generate NIS2 Questionnaire

```python
# Generate supply chain security questionnaire from NIS2 Article 22
{
  "category": "supply_chain",
  "scope": "full"
}
```

**NIS2 Categories**:
- `supply_chain` - Article 22 (Supply chain security)
- `risk_management` - Article 21 (Cybersecurity risk management)
- `governance` - Article 20 (Governance)
- `incident_response` - Article 23 (Reporting obligations)

### Check Regulatory Compliance

```python
# Check DORA compliance after assessment
{
  "assessment_id": 123,
  "regulation": "DORA"
}
# Returns: Coverage 85%, compliance status, gap analysis
```

### Get Regulatory Timeline

```python
# Get DORA/NIS2 deadlines and milestones
{
  "regulation": "DORA"
}
# Returns: Deadline 2025-01-17, days remaining, key milestones
```

**Key Deadlines**:
- **DORA**: 2025-01-17 (Full compliance)
- **NIS2**: 2024-10-17 (Member state transposition)

For detailed integration information, see [EU_REGULATIONS_INTEGRATION.md](EU_REGULATIONS_INTEGRATION.md).

## Database Management

### Migration Tools

```bash
# Check schema version
python scripts/migrate_db.py --check

# Apply pending migrations
python scripts/migrate_db.py --migrate

# View migration status
python scripts/migrate_db.py --status
```

### Backup and Restore

```bash
# Create compressed backup
python scripts/backup_db.py --backup --compress

# List available backups
python scripts/backup_db.py --list

# Restore from backup
python scripts/backup_db.py --restore /path/to/backup.db.gz
```

### Database Inspection

```bash
# Show database statistics
python scripts/inspect_db.py --stats

# List all vendors
python scripts/inspect_db.py --vendors

# View vendor assessment history
python scripts/inspect_db.py --vendor-history "Salesforce"

# List recent assessments
python scripts/inspect_db.py --assessments

# Verify database integrity
python scripts/inspect_db.py --verify
```

See [PHASE_1_PERSISTENCE.md](PHASE_1_PERSISTENCE.md) for complete documentation.

## Data Sources

### Obtaining Questionnaire Content

**Placeholder data is provided.** For production use, obtain licensed content:

- **SIG**: [sharedassessments.org](https://sharedassessments.org) (~$2-5K/year)
- **CAIQ v4**: Free from [CSA](https://cloudsecurityalliance.org)
- **DORA/NIS2**: Derive from EU-regulations MCP server

## Documentation

- **[QUICKSTART.md](QUICKSTART.md)** - 30-minute setup guide
- **[PHASE_1_PERSISTENCE.md](PHASE_1_PERSISTENCE.md)** - Database and persistence layer
- **[DEPLOYMENT.md](DEPLOYMENT.md)** - Production deployment guide
- **[INTEGRATION.md](INTEGRATION.md)** - Cross-MCP integration patterns
- **[TESTING.md](TESTING.md)** - Test suite documentation

## License

Apache-2.0