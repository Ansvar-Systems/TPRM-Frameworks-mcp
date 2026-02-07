# Option 2: CAIQ + Regulatory Focus - Implementation Plan

**Timeline:** 4-6 weeks
**Outcome:** Production-ready TPRM for cloud providers + regulated entities (DORA/NIS2)

---

## Phase 1: Persistence Layer (Week 1)

### Tasks

**Day 1-2: Database Schema & Implementation**
```python
# Add src/tprm_frameworks_mcp/storage.py

import sqlite3
from pathlib import Path
from typing import Any
import json
from datetime import datetime

class TPRMStorage:
    """SQLite storage for questionnaires and assessments."""

    def __init__(self, db_path: str = None):
        if db_path is None:
            db_path = Path.home() / ".tprm-mcp" / "tprm.db"
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _init_db(self):
        """Initialize database schema."""
        conn = sqlite3.connect(self.db_path)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS questionnaires (
                id TEXT PRIMARY KEY,
                framework TEXT NOT NULL,
                version TEXT,
                scope TEXT,
                entity_type TEXT,
                regulations TEXT,  -- JSON array
                generated_at TEXT NOT NULL,
                questions TEXT NOT NULL,  -- JSON
                metadata TEXT  -- JSON
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS assessments (
                id TEXT PRIMARY KEY,
                questionnaire_id TEXT NOT NULL,
                vendor_name TEXT NOT NULL,
                overall_score REAL,
                risk_level TEXT,
                strictness TEXT,
                assessed_at TEXT NOT NULL,
                results TEXT NOT NULL,  -- JSON
                critical_findings TEXT,  -- JSON
                compliance_gaps TEXT,  -- JSON
                FOREIGN KEY (questionnaire_id) REFERENCES questionnaires(id)
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS vendor_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                vendor_name TEXT NOT NULL,
                assessment_id TEXT NOT NULL,
                assessed_at TEXT NOT NULL,
                overall_score REAL,
                risk_level TEXT,
                framework TEXT,
                FOREIGN KEY (assessment_id) REFERENCES assessments(id)
            )
        """)
        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_vendor_history_name
            ON vendor_history(vendor_name, assessed_at DESC)
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS framework_versions (
                framework TEXT PRIMARY KEY,
                current_version TEXT NOT NULL,
                release_date TEXT,
                last_checked TEXT,
                is_deprecated INTEGER DEFAULT 0,
                notes TEXT
            )
        """)
        conn.commit()
        conn.close()

    def save_questionnaire(self, questionnaire: "Questionnaire"):
        """Save generated questionnaire."""
        conn = sqlite3.connect(self.db_path)
        conn.execute("""
            INSERT OR REPLACE INTO questionnaires
            (id, framework, version, scope, entity_type, regulations,
             generated_at, questions, metadata)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            questionnaire.id,
            questionnaire.metadata.framework.value,
            questionnaire.metadata.version,
            questionnaire.custom_parameters.get("scope"),
            questionnaire.custom_parameters.get("entity_type"),
            json.dumps(questionnaire.metadata.applicable_regulations),
            questionnaire.generation_timestamp,
            json.dumps([q.__dict__ for q in questionnaire.questions]),
            json.dumps(questionnaire.custom_parameters)
        ))
        conn.commit()
        conn.close()

    def save_assessment(self, assessment: "AssessmentResult"):
        """Save assessment results."""
        conn = sqlite3.connect(self.db_path)

        # Save main assessment
        assessment_id = f"assess_{datetime.utcnow().isoformat()}"
        conn.execute("""
            INSERT INTO assessments
            (id, questionnaire_id, vendor_name, overall_score, risk_level,
             strictness, assessed_at, results, critical_findings, compliance_gaps)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            assessment_id,
            assessment.questionnaire_id,
            assessment.vendor_name,
            assessment.overall_score,
            assessment.overall_risk_level.value,
            assessment.strictness_level.value,
            assessment.timestamp,
            json.dumps([r.__dict__ for r in assessment.evaluation_results]),
            json.dumps(assessment.critical_findings),
            json.dumps(assessment.compliance_gaps)
        ))

        # Add to vendor history
        conn.execute("""
            INSERT INTO vendor_history
            (vendor_name, assessment_id, assessed_at, overall_score, risk_level, framework)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            assessment.vendor_name,
            assessment_id,
            assessment.timestamp,
            assessment.overall_score,
            assessment.overall_risk_level.value,
            "unknown"  # TODO: Get from questionnaire
        ))

        conn.commit()
        conn.close()
        return assessment_id

    def get_vendor_history(self, vendor_name: str, limit: int = 10):
        """Get assessment history for a vendor."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.execute("""
            SELECT assessed_at, overall_score, risk_level, framework
            FROM vendor_history
            WHERE vendor_name = ?
            ORDER BY assessed_at DESC
            LIMIT ?
        """, (vendor_name, limit))
        results = cursor.fetchall()
        conn.close()
        return results
```

**Day 3: Integration with Server**
- Modify `server.py` to use storage instead of in-memory dict
- Add storage initialization on startup
- Update tool handlers to save/retrieve from DB

**Day 4: Add New Tools**
```python
# Add to server.py tools:

Tool(
    name="get_vendor_history",
    description="Get assessment history for a vendor to track improvement over time",
    inputSchema={
        "type": "object",
        "properties": {
            "vendor_name": {"type": "string"},
            "limit": {"type": "integer", "default": 10}
        },
        "required": ["vendor_name"]
    }
)

Tool(
    name="compare_assessments",
    description="Compare two assessments for the same vendor to show risk trend",
    inputSchema={
        "type": "object",
        "properties": {
            "vendor_name": {"type": "string"},
            "assessment_id_1": {"type": "string"},
            "assessment_id_2": {"type": "string"}
        },
        "required": ["vendor_name"]
    }
)
```

**Deliverable:** Persistent storage with historical tracking ✅

---

## Phase 2: CAIQ v4 Full Data (Week 2)

### Day 1: Download & Parse CAIQ v4

**Source:** https://cloudsecurityalliance.org/artifacts/csa-caiq-v4-0/

```python
# Create scripts/import_caiq_v4.py

import pandas as pd
import json
from pathlib import Path

def parse_caiq_excel(excel_path: str):
    """Parse official CAIQ v4 Excel to our JSON format."""

    df = pd.read_excel(excel_path, sheet_name='CAIQ v4.0')

    # CAIQ structure:
    # Column A: Domain
    # Column B: Control ID
    # Column C: Control Specification
    # Column D: Question (what we need)

    questions = []
    current_category = None

    for idx, row in df.iterrows():
        if pd.notna(row['Domain']):
            current_category = row['Domain']

        if pd.notna(row['Question']):
            question = {
                "id": f"caiq_{row['Control ID'].lower().replace(' ', '_')}",
                "category": current_category,
                "subcategory": None,  # TODO: Parse from domain
                "question_text": row['Question'],
                "description": row.get('Control Specification', ''),
                "expected_answer_type": "text",  # Most CAIQ are text
                "is_required": True,  # All CAIQ are important
                "weight": calculate_weight(row['Control ID']),
                "regulatory_mappings": extract_regulatory_mappings(row),
                "scf_control_mappings": [],  # TODO: Map manually
                "risk_if_inadequate": "high",  # Default for CAIQ
                "evaluation_rubric": generate_default_rubric(row)
            }
            questions.append(question)

    return questions

def calculate_weight(control_id: str) -> int:
    """Assign weight based on control importance."""
    # Critical controls (identity, encryption, incident)
    if any(x in control_id for x in ['IAM', 'EKM', 'SIM', 'BCM']):
        return 10
    # High priority
    elif any(x in control_id for x in ['DSP', 'GRC', 'TVM']):
        return 9
    # Standard
    else:
        return 8

def generate_default_rubric(row) -> dict:
    """Generate basic rubric from control specification."""
    spec = row.get('Control Specification', '').lower()

    # Extract key terms
    positive_terms = []
    if 'documented' in spec:
        positive_terms.append('documented')
    if 'implemented' in spec:
        positive_terms.append('implemented')
    if 'annually' in spec or 'regular' in spec:
        positive_terms.append('regularly|annually')

    return {
        "acceptable": ["yes"] + positive_terms,
        "partially_acceptable": ["partial", "in progress", "planned"],
        "unacceptable": ["no", "not implemented"],
        "required_keywords": []
    }
```

**Days 2-3: Manual Rubric Enhancement**
- Review top 50 most critical CAIQ questions
- Create detailed evaluation rubrics
- Add SCF control mappings
- Validate with test responses

**Days 4-5: Testing & Validation**
- Create test dataset (20 good responses, 20 bad responses)
- Run evaluation engine
- Validate accuracy >90% agreement with manual scoring
- Adjust rubrics as needed

**Deliverable:** Complete CAIQ v4 with 295 questions ✅

---

## Phase 3: DORA/NIS2 Integration (Week 3-4)

### Week 3: Extract DORA Requirements

**Approach:** Query EU-regulations-mcp for DORA content, transform to questions

```python
# Create scripts/extract_dora_questions.py

from typing import List, Dict

# Map DORA articles to assessment questions
DORA_ARTICLE_MAPPING = {
    "Article 6": {
        "title": "ICT Risk Management Framework",
        "questions": [
            {
                "id": "dora_art6_1",
                "question": "Do you have an ICT risk management framework covering identification, protection, detection, response, recovery, and learning?",
                "regulatory_ref": "DORA Article 6(1)",
                "scf_controls": ["RSK-01", "RSK-02", "GOV-01"],
                "weight": 10,
                "risk": "critical"
            },
            {
                "id": "dora_art6_2",
                "question": "Is your ICT risk management framework documented, approved by management, and subject to internal audit?",
                "regulatory_ref": "DORA Article 6(2)",
                "scf_controls": ["GOV-01", "GOV-03", "CPL-01"],
                "weight": 9,
                "risk": "high"
            }
        ]
    },
    "Article 11": {
        "title": "Business Continuity",
        "questions": [
            {
                "id": "dora_art11_1",
                "question": "Do you have ICT business continuity policies and plans with defined RTOs and RPOs?",
                "regulatory_ref": "DORA Article 11(1)",
                "scf_controls": ["BCD-01", "BCD-02", "BCD-06"],
                "weight": 10,
                "risk": "critical"
            }
        ]
    },
    "Article 19": {
        "title": "ICT-Related Incident Reporting",
        "questions": [
            {
                "id": "dora_art19_1",
                "question": "Do you have processes to detect, report, and escalate ICT incidents within DORA timelines (4h initial, 72h intermediate)?",
                "regulatory_ref": "DORA Article 19",
                "scf_controls": ["IRO-01", "IRO-02", "IRO-08"],
                "weight": 10,
                "risk": "critical"
            }
        ]
    }
    # Continue for all relevant articles...
}

def generate_dora_questionnaire():
    """Generate complete DORA ICT TPP questionnaire."""
    questions = []

    for article_num, article_data in DORA_ARTICLE_MAPPING.items():
        category = article_data["title"]

        for q_data in article_data["questions"]:
            question = {
                "id": q_data["id"],
                "category": category,
                "subcategory": article_num,
                "question_text": q_data["question"],
                "description": f"Requirement from {q_data['regulatory_ref']}",
                "expected_answer_type": "text",
                "is_required": True,
                "weight": q_data["weight"],
                "regulatory_mappings": [q_data["regulatory_ref"]],
                "scf_control_mappings": q_data["scf_controls"],
                "risk_if_inadequate": q_data["risk"],
                "evaluation_rubric": generate_dora_rubric(q_data)
            }
            questions.append(question)

    return {
        "metadata": {
            "name": "DORA ICT Third-Party Provider Assessment",
            "version": "1.0",
            "total_questions": len(questions),
            "status": "production",
            "categories": list(set(q["category"] for q in questions)),
            "estimated_completion_time": "6-8 hours"
        },
        "questions": questions
    }
```

**Integration with EU-regulations-mcp:**
```python
# Add tool: enrich_with_dora_articles
# Calls EU-regulations-mcp to get full article text for context

async def enrich_question_with_regulation(question_id: str, regulation_ref: str):
    """
    Query EU-regulations-mcp for full article text.
    Add as context to question description.
    """
    # Call EU-regulations-mcp
    article_text = await call_eu_regs_mcp("get_article", {
        "regulation": "dora",
        "article": regulation_ref
    })

    # Enhance question description
    return {
        **question,
        "regulatory_context": article_text,
        "official_source": "Regulation (EU) 2022/2554"
    }
```

**Week 4: Extract NIS2 Requirements**

Similar approach for NIS2 supply chain requirements:

```python
NIS2_ARTICLE_MAPPING = {
    "Article 21": {
        "title": "Cybersecurity Risk Management",
        "requirements": [
            "Supply chain security",
            "Security in network and information systems",
            "Incident handling",
            "Business continuity",
            "Supply chain security",
            "Security in acquisition, development, maintenance"
        ]
    }
}
```

**Deliverable:**
- DORA questionnaire: ~85 questions covering all ICT risk requirements ✅
- NIS2 questionnaire: ~65 questions covering supply chain & cybersecurity ✅
- Full regulatory traceability (question → article → requirement) ✅

---

## Phase 4: Version Tracking & Updates (Week 5)

### Task 1: Add Framework Version Management

```python
# Add to storage.py

class FrameworkVersionManager:
    """Manage framework versions and check for updates."""

    def __init__(self, storage: TPRMStorage):
        self.storage = storage
        self.update_sources = {
            "caiq_v4": {
                "url": "https://cloudsecurityalliance.org/artifacts/csa-caiq-v4-0/",
                "check_method": "web_scrape",
                "current_indicator": "v4.0"
            },
            "sig_lite": {
                "url": "https://sharedassessments.org/sig/",
                "check_method": "requires_auth",
                "current_indicator": "2025"
            },
            "dora": {
                "url": "eu_regulations_mcp",
                "check_method": "mcp_query",
                "current_indicator": "RTS_2024"
            }
        }

    def check_for_updates(self, framework: str) -> dict:
        """Check if framework has updates available."""
        current = self.get_current_version(framework)
        source = self.update_sources.get(framework)

        if source["check_method"] == "web_scrape":
            latest = self._check_web_version(source["url"])
        elif source["check_method"] == "mcp_query":
            latest = self._check_mcp_version(source["url"], framework)
        else:
            latest = None

        return {
            "framework": framework,
            "current_version": current,
            "latest_version": latest,
            "update_available": latest and latest != current,
            "last_checked": datetime.utcnow().isoformat()
        }

    def mark_deprecated(self, framework: str, version: str, reason: str):
        """Mark a framework version as deprecated."""
        # Add warning to questionnaire generation
        pass
```

### Task 2: Add Update Checking Tool

```python
# Add to server.py

Tool(
    name="check_framework_versions",
    description="Check if questionnaire frameworks have updates available",
    inputSchema={
        "type": "object",
        "properties": {
            "framework": {
                "type": "string",
                "description": "Optional: specific framework to check, or all if not provided"
            }
        }
    }
)
```

### Task 3: Create Update Workflow Documentation

```markdown
# Framework Update Process

## Monthly Update Check (1st of month)

1. Run version checker:
   ```bash
   python -m tprm_frameworks_mcp.tools.check_updates
   ```

2. Review output for available updates

3. For each update:
   - Download new version
   - Run import script
   - Compare changes (diff report)
   - Review impact on existing rubrics
   - Update SCF mappings if needed
   - Run test suite
   - Deploy to production

## Emergency Update (critical CVE or regulation change)

1. Immediate notification
2. Expedited review process
3. Deploy within 24-48 hours
```

**Deliverable:** Version tracking and update checking system ✅

---

## Phase 5: Testing & Documentation (Week 6)

### Task 1: Comprehensive Testing

```python
# tests/test_production_readiness.py

def test_full_caiq_assessment():
    """Test complete CAIQ assessment workflow."""
    # Generate questionnaire
    questionnaire = generate_questionnaire(
        framework="caiq_v4",
        scope="full",
        entity_type="cloud_provider"
    )
    assert len(questionnaire.questions) == 295

    # Simulate vendor responses
    responses = generate_test_responses(questionnaire)

    # Evaluate
    assessment = evaluate_response(
        questionnaire_id=questionnaire.id,
        vendor_name="Test Cloud Provider",
        responses=responses,
        strictness="moderate"
    )

    # Verify results
    assert assessment.overall_score is not None
    assert assessment.overall_risk_level in [RiskLevel.LOW, RiskLevel.MEDIUM, RiskLevel.HIGH, RiskLevel.CRITICAL]
    assert len(assessment.evaluation_results) == 295

def test_dora_regulatory_overlay():
    """Test DORA questionnaire with regulatory traceability."""
    questionnaire = generate_questionnaire(
        framework="dora_ict_tpp",
        regulations=["dora"]
    )

    # Verify all questions have regulatory mappings
    for q in questionnaire.questions:
        assert len(q.regulatory_mappings) > 0
        assert any("DORA" in mapping for mapping in q.regulatory_mappings)

def test_vendor_history_tracking():
    """Test historical assessment tracking."""
    vendor = "Acme Corp"

    # First assessment
    assessment_1 = run_assessment(vendor, score=65)

    # Second assessment (after remediation)
    assessment_2 = run_assessment(vendor, score=82)

    # Verify history
    history = get_vendor_history(vendor)
    assert len(history) == 2
    assert history[0].score > history[1].score  # Improvement over time
```

### Task 2: Documentation Updates

**README.md** - Update with:
- Production status: "Production Ready for CAIQ v4, DORA, NIS2"
- Data completeness: "CAIQ: 295/295 ✅, DORA: 85/85 ✅, NIS2: 65/65 ✅"
- New tools: vendor_history, compare_assessments, check_framework_versions

**CLAUDE.md** - Add:
- Storage layer documentation
- Version management guide
- Regulatory integration patterns
- Update procedures

### Task 3: Operations Runbook

```markdown
# TPRM MCP Operations Runbook

## Daily Operations
- Monitor error logs (if any failures)
- Check database size (backup if >1GB)

## Weekly Operations
- Review assessment quality (spot-check 5 random assessments)
- Check for framework updates
- Backup database

## Monthly Operations
- Run full test suite
- Review evaluation accuracy
- Update documentation
- Check for new regulatory changes

## Quarterly Operations
- Full data validation
- Rubric recalibration
- Performance optimization
- Security audit

## Emergency Procedures

### Framework Becomes Outdated
1. Check for official update
2. Download new version
3. Run import and validation
4. Deploy within 48 hours
5. Notify users

### Database Corruption
1. Stop server
2. Restore from backup
3. Verify data integrity
4. Restart server
5. Post-mortem analysis
```

**Deliverable:** Fully tested, documented, production-ready system ✅

---

## Success Criteria

### Technical Metrics
- [x] CAIQ v4: 295 questions with validated rubrics
- [x] DORA: 85 questions with regulatory traceability
- [x] NIS2: 65 questions with regulatory traceability
- [x] Database persistence with <100ms query time
- [x] Historical tracking for vendor trends
- [x] Version tracking with update checking
- [x] Test coverage >80%
- [x] Documentation complete

### Business Metrics
- [x] Can assess cloud providers (CAIQ)
- [x] Can assess financial entities (DORA)
- [x] Can assess critical infrastructure (NIS2)
- [x] Can track vendor improvement over time
- [x] Can generate compliance reports
- [x] Can map to security controls (SCF)
- [x] System stays current with frameworks

---

## Risks & Mitigation

| Risk | Impact | Mitigation |
|------|--------|----------|
| CAIQ Excel format changes | High | Validate structure before import |
| DORA RTS not final | Medium | Mark as "draft", update when final |
| Evaluation accuracy <90% | High | Manual calibration of rubrics |
| Database performance issues | Medium | Add indexes, monitor query times |
| Framework updates missed | Medium | Automated weekly checks |

---

## Budget & Resources

### Costs
- **CAIQ v4**: Free ✅
- **Database**: SQLite (free) ✅
- **DORA/NIS2**: EU regulations (public) ✅
- **Total**: $0

### Time Investment
- **Week 1**: 40 hours (persistence)
- **Week 2**: 40 hours (CAIQ integration)
- **Week 3**: 40 hours (DORA)
- **Week 4**: 40 hours (NIS2)
- **Week 5**: 40 hours (version management)
- **Week 6**: 40 hours (testing & docs)
- **Total**: 240 hours (6 weeks full-time or 12 weeks half-time)

### Ongoing Maintenance
- **Monthly**: 8 hours (monitoring & updates)
- **Quarterly**: 16 hours (full review)
- **Annual**: 40 hours (major updates)
- **Total**: ~150 hours/year

---

## Next Steps

1. **Get approval** for 6-week timeline
2. **Set up development environment**
3. **Start with Phase 1** (persistence layer)
4. **Weekly check-ins** on progress
5. **Deploy to production** after Phase 6

Ready to start when you are! 🚀
