"""Persistent storage layer for TPRM assessments using SQLite."""

import json
import sqlite3
from contextlib import contextmanager
from datetime import datetime, UTC
from pathlib import Path
from typing import Any, Optional

from .config import config as global_config
from .models import AssessmentResult, Questionnaire


class StorageError(Exception):
    """Base exception for storage errors."""
    pass


class QuestionnaireNotFoundError(StorageError):
    """Raised when a questionnaire is not found."""
    pass


class AssessmentNotFoundError(StorageError):
    """Raised when an assessment is not found."""
    pass


class TPRMStorage:
    """SQLite-based storage for questionnaires and assessments.

    Features:
    - Automatic database creation at ~/.tprm-mcp/tprm.db
    - JSON serialization for complex objects
    - Proper indexes for performance
    - Transaction support
    - Error handling with descriptive messages
    """

    def __init__(self, db_path: str | None = None):
        """
        Initialize storage.

        Args:
            db_path: Path to SQLite database. If None, uses config value or ~/.tprm-mcp/tprm.db
        """
        if db_path is None:
            # Use config value
            db_path = str(global_config.storage.database_path)
            # Ensure parent directory exists
            db_dir = Path(db_path).parent
            db_dir.mkdir(exist_ok=True, parents=True)

        self.db_path = db_path
        self._init_database()

    @contextmanager
    def _get_connection(self):
        """Get a database connection with automatic cleanup."""
        conn = None
        try:
            conn = sqlite3.connect(self.db_path)
            conn.execute("PRAGMA foreign_keys = ON")
            conn.execute("PRAGMA journal_mode = WAL")
            conn.row_factory = sqlite3.Row
            yield conn
        except sqlite3.Error as e:
            if conn:
                conn.rollback()
            raise StorageError(f"Database error: {e}") from e
        finally:
            if conn:
                conn.close()

    def _init_database(self) -> None:
        """Initialize database schema with all required tables and indexes."""
        with self._get_connection() as conn:
            # Questionnaires table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS questionnaires (
                    id TEXT PRIMARY KEY,
                    framework TEXT NOT NULL,
                    version TEXT NOT NULL,
                    scope TEXT,
                    entity_type TEXT,
                    regulations TEXT,
                    total_questions INTEGER NOT NULL,
                    generation_timestamp TEXT NOT NULL,
                    data JSON NOT NULL,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # Assessments table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS assessments (
                    id TEXT PRIMARY KEY,
                    questionnaire_id TEXT NOT NULL,
                    vendor_name TEXT NOT NULL,
                    overall_score REAL NOT NULL,
                    overall_risk_level TEXT NOT NULL,
                    strictness_level TEXT NOT NULL,
                    timestamp TEXT NOT NULL,
                    data JSON NOT NULL,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (questionnaire_id) REFERENCES questionnaires (id)
                )
            """)

            # Vendor history table for tracking assessments over time
            conn.execute("""
                CREATE TABLE IF NOT EXISTS vendor_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    vendor_name TEXT NOT NULL,
                    assessment_id TEXT NOT NULL,
                    assessed_at TEXT NOT NULL,
                    overall_score REAL,
                    risk_level TEXT,
                    framework TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (assessment_id) REFERENCES assessments(id)
                )
            """)

            # Framework versions table for tracking framework updates
            conn.execute("""
                CREATE TABLE IF NOT EXISTS framework_versions (
                    framework TEXT PRIMARY KEY,
                    current_version TEXT NOT NULL,
                    release_date TEXT,
                    last_checked TEXT,
                    is_deprecated INTEGER DEFAULT 0,
                    notes TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # Create indexes for performance
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_vendor_history_name
                ON vendor_history(vendor_name, assessed_at DESC)
            """)

            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_assessments_vendor
                ON assessments(vendor_name, timestamp DESC)
            """)

            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_questionnaires_framework
                ON questionnaires(framework, generation_timestamp DESC)
            """)

            conn.commit()

    def save_questionnaire(self, questionnaire: Questionnaire) -> str:
        """
        Save a questionnaire to storage.

        Args:
            questionnaire: Questionnaire to save

        Returns:
            str: The questionnaire ID

        Raises:
            StorageError: If save fails
        """
        try:
            with self._get_connection() as conn:
                # Serialize questionnaire to JSON
                data = {
                    "id": questionnaire.id,
                    "metadata": {
                        "framework": questionnaire.metadata.framework.value,
                        "version": questionnaire.metadata.version,
                        "total_questions": questionnaire.metadata.total_questions,
                        "categories": questionnaire.metadata.categories,
                        "estimated_completion_time": questionnaire.metadata.estimated_completion_time,
                        "scope": questionnaire.metadata.scope,
                        "entity_type": (
                            questionnaire.metadata.entity_type.value
                            if questionnaire.metadata.entity_type
                            else None
                        ),
                        "applicable_regulations": questionnaire.metadata.applicable_regulations,
                    },
                    "questions": [
                        {
                            "id": q.id,
                            "category": q.category,
                            "subcategory": q.subcategory,
                            "question_text": q.question_text,
                            "description": q.description,
                            "expected_answer_type": q.expected_answer_type,
                            "is_required": q.is_required,
                            "weight": q.weight,
                            "regulatory_mappings": q.regulatory_mappings,
                            "scf_control_mappings": q.scf_control_mappings,
                            "risk_if_inadequate": q.risk_if_inadequate.value,
                            "evaluation_rubric": q.evaluation_rubric,
                        }
                        for q in questionnaire.questions
                    ],
                    "generation_timestamp": questionnaire.generation_timestamp,
                    "custom_parameters": questionnaire.custom_parameters,
                }

                conn.execute(
                    """
                    INSERT OR REPLACE INTO questionnaires
                    (id, framework, version, scope, entity_type, regulations,
                     total_questions, generation_timestamp, data)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        questionnaire.id,
                        questionnaire.metadata.framework.value,
                        questionnaire.metadata.version,
                        questionnaire.metadata.scope,
                        (
                            questionnaire.metadata.entity_type.value
                            if questionnaire.metadata.entity_type
                            else None
                        ),
                        json.dumps(questionnaire.metadata.applicable_regulations),
                        questionnaire.metadata.total_questions,
                        questionnaire.generation_timestamp,
                        json.dumps(data),
                    ),
                )

                conn.commit()
                return questionnaire.id

        except (json.JSONDecodeError, AttributeError) as e:
            raise StorageError(f"Failed to serialize questionnaire: {e}") from e

    def get_questionnaire(self, questionnaire_id: str) -> Questionnaire:
        """
        Retrieve a questionnaire by ID.

        Args:
            questionnaire_id: ID of questionnaire to retrieve

        Returns:
            Questionnaire: The questionnaire object

        Raises:
            QuestionnaireNotFoundError: If questionnaire not found
            StorageError: If retrieval fails
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.execute(
                    "SELECT data FROM questionnaires WHERE id = ?",
                    (questionnaire_id,),
                )

                row = cursor.fetchone()
                if not row:
                    raise QuestionnaireNotFoundError(
                        f"Questionnaire '{questionnaire_id}' not found"
                    )

                # Deserialize from JSON
                data = json.loads(row["data"])

                # Import models here to avoid circular imports
                from .models import (
                    EntityType,
                    Question,
                    QuestionnaireFramework,
                    QuestionnaireMetadata,
                    RiskLevel,
                )

                metadata = QuestionnaireMetadata(
                    framework=QuestionnaireFramework(data["metadata"]["framework"]),
                    version=data["metadata"]["version"],
                    total_questions=data["metadata"]["total_questions"],
                    categories=data["metadata"]["categories"],
                    estimated_completion_time=data["metadata"]["estimated_completion_time"],
                    scope=data["metadata"]["scope"],
                    entity_type=(
                        EntityType(data["metadata"]["entity_type"])
                        if data["metadata"]["entity_type"]
                        else None
                    ),
                    applicable_regulations=data["metadata"]["applicable_regulations"],
                )

                questions = [
                    Question(
                        id=q["id"],
                        category=q["category"],
                        subcategory=q["subcategory"],
                        question_text=q["question_text"],
                        description=q["description"],
                        expected_answer_type=q["expected_answer_type"],
                        is_required=q["is_required"],
                        weight=q["weight"],
                        regulatory_mappings=q["regulatory_mappings"],
                        scf_control_mappings=q["scf_control_mappings"],
                        risk_if_inadequate=RiskLevel(q["risk_if_inadequate"]),
                        evaluation_rubric=q["evaluation_rubric"],
                    )
                    for q in data["questions"]
                ]

                return Questionnaire(
                    id=data["id"],
                    metadata=metadata,
                    questions=questions,
                    generation_timestamp=data["generation_timestamp"],
                    custom_parameters=data["custom_parameters"],
                )

        except json.JSONDecodeError as e:
            raise StorageError(f"Failed to deserialize questionnaire: {e}") from e

    def save_assessment(self, assessment: AssessmentResult) -> str:
        """
        Save an assessment result to storage with automatic vendor history tracking.

        Args:
            assessment: Assessment result to save

        Returns:
            str: The assessment ID

        Raises:
            StorageError: If save fails
        """
        try:
            # Generate assessment ID
            assessment_id = f"assess_{datetime.now(UTC).strftime('%Y%m%d_%H%M%S_%f')}"

            with self._get_connection() as conn:
                # Serialize assessment to JSON
                data = {
                    "questionnaire_id": assessment.questionnaire_id,
                    "vendor_name": assessment.vendor_name,
                    "evaluation_results": [
                        {
                            "question_id": r.question_id,
                            "status": r.status.value,
                            "score": r.score,
                            "risk_level": r.risk_level.value,
                            "findings": r.findings,
                            "recommendations": r.recommendations,
                            "scf_controls_addressed": r.scf_controls_addressed,
                        }
                        for r in assessment.evaluation_results
                    ],
                    "overall_score": assessment.overall_score,
                    "overall_risk_level": assessment.overall_risk_level.value,
                    "critical_findings": assessment.critical_findings,
                    "compliance_gaps": assessment.compliance_gaps,
                    "timestamp": assessment.timestamp,
                    "strictness_level": assessment.strictness_level.value,
                }

                # Save main assessment
                conn.execute(
                    """
                    INSERT INTO assessments
                    (id, questionnaire_id, vendor_name, overall_score, overall_risk_level,
                     strictness_level, timestamp, data)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        assessment_id,
                        assessment.questionnaire_id,
                        assessment.vendor_name,
                        assessment.overall_score,
                        assessment.overall_risk_level.value,
                        assessment.strictness_level.value,
                        assessment.timestamp,
                        json.dumps(data),
                    ),
                )

                # Get framework from questionnaire
                cursor = conn.execute(
                    "SELECT framework FROM questionnaires WHERE id = ?",
                    (assessment.questionnaire_id,)
                )
                framework_row = cursor.fetchone()
                framework = framework_row["framework"] if framework_row else "unknown"

                # Add to vendor history
                conn.execute(
                    """
                    INSERT INTO vendor_history
                    (vendor_name, assessment_id, assessed_at, overall_score, risk_level, framework)
                    VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    (
                        assessment.vendor_name,
                        assessment_id,
                        assessment.timestamp,
                        assessment.overall_score,
                        assessment.overall_risk_level.value,
                        framework,
                    ),
                )

                conn.commit()
                return assessment_id

        except (json.JSONDecodeError, AttributeError) as e:
            raise StorageError(f"Failed to serialize assessment: {e}") from e

    def get_assessment(self, assessment_id: str) -> AssessmentResult:
        """
        Retrieve an assessment by ID.

        Args:
            assessment_id: ID of the assessment to retrieve

        Returns:
            AssessmentResult: The assessment object

        Raises:
            AssessmentNotFoundError: If assessment not found
            StorageError: If retrieval fails
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.execute(
                    "SELECT data FROM assessments WHERE id = ?",
                    (assessment_id,),
                )

                row = cursor.fetchone()
                if not row:
                    raise AssessmentNotFoundError(
                        f"Assessment '{assessment_id}' not found"
                    )

                return self._deserialize_assessment(json.loads(row["data"]))

        except json.JSONDecodeError as e:
            raise StorageError(f"Failed to deserialize assessment: {e}") from e

    def get_vendor_history(self, vendor_name: str, limit: int = 10) -> list[dict[str, Any]]:
        """
        Get assessment history for a vendor.

        Args:
            vendor_name: Name of the vendor
            limit: Maximum number of assessments to return

        Returns:
            list: List of assessment history records with:
                - assessment_id: Assessment ID for details
                - assessed_at: Timestamp
                - overall_score: Score (0-100)
                - risk_level: Risk level
                - framework: Framework used

        Raises:
            StorageError: If retrieval fails
        """
        with self._get_connection() as conn:
            cursor = conn.execute(
                """
                SELECT assessment_id, assessed_at, overall_score, risk_level, framework
                FROM vendor_history
                WHERE vendor_name = ?
                ORDER BY assessed_at DESC
                LIMIT ?
                """,
                (vendor_name, limit),
            )

            return [
                {
                    "assessment_id": row["assessment_id"],
                    "assessed_at": row["assessed_at"],
                    "overall_score": row["overall_score"],
                    "risk_level": row["risk_level"],
                    "framework": row["framework"],
                }
                for row in cursor.fetchall()
            ]

    def compare_assessments(
        self,
        vendor_name: str,
        assessment_id_1: str,
        assessment_id_2: str
    ) -> dict[str, Any]:
        """
        Compare two assessments for the same vendor.

        Args:
            vendor_name: Name of the vendor
            assessment_id_1: First assessment ID
            assessment_id_2: Second assessment ID

        Returns:
            dict: Comparison results with:
                - vendor_name: Vendor name
                - assessment_1: First assessment details
                - assessment_2: Second assessment details
                - score_delta: Score change
                - risk_level_change: Risk level change
                - improvements: List of improved questions
                - regressions: List of regressed questions

        Raises:
            AssessmentNotFoundError: If either assessment not found
            StorageError: If comparison fails
        """
        # Retrieve both assessments
        assessment_1 = self.get_assessment(assessment_id_1)
        assessment_2 = self.get_assessment(assessment_id_2)

        # Verify vendor matches
        if assessment_1.vendor_name != vendor_name or assessment_2.vendor_name != vendor_name:
            raise StorageError(
                f"Assessments do not belong to vendor '{vendor_name}'"
            )

        # Calculate score delta
        score_delta = assessment_2.overall_score - assessment_1.overall_score

        # Determine risk level change
        risk_levels = ["low", "medium", "high", "critical"]
        risk_1_idx = risk_levels.index(assessment_1.overall_risk_level.value)
        risk_2_idx = risk_levels.index(assessment_2.overall_risk_level.value)
        risk_change = "improved" if risk_2_idx < risk_1_idx else (
            "worsened" if risk_2_idx > risk_1_idx else "unchanged"
        )

        # Build question-level comparison
        results_1 = {r.question_id: r for r in assessment_1.evaluation_results}
        results_2 = {r.question_id: r for r in assessment_2.evaluation_results}

        improvements = []
        regressions = []

        for question_id in set(results_1.keys()) & set(results_2.keys()):
            score_1 = results_1[question_id].score
            score_2 = results_2[question_id].score

            if score_2 > score_1:
                improvements.append({
                    "question_id": question_id,
                    "score_change": score_2 - score_1,
                    "old_score": score_1,
                    "new_score": score_2,
                })
            elif score_2 < score_1:
                regressions.append({
                    "question_id": question_id,
                    "score_change": score_2 - score_1,
                    "old_score": score_1,
                    "new_score": score_2,
                })

        return {
            "vendor_name": vendor_name,
            "assessment_1": {
                "id": assessment_id_1,
                "timestamp": assessment_1.timestamp,
                "overall_score": assessment_1.overall_score,
                "risk_level": assessment_1.overall_risk_level.value,
            },
            "assessment_2": {
                "id": assessment_id_2,
                "timestamp": assessment_2.timestamp,
                "overall_score": assessment_2.overall_score,
                "risk_level": assessment_2.overall_risk_level.value,
            },
            "score_delta": score_delta,
            "risk_level_change": risk_change,
            "improvements": improvements,
            "regressions": regressions,
            "total_improvements": len(improvements),
            "total_regressions": len(regressions),
        }

    def update_framework_version(
        self,
        framework: str,
        version: str,
        release_date: Optional[str] = None
    ) -> None:
        """
        Update or insert framework version information.

        Args:
            framework: Framework identifier
            version: Version string
            release_date: Optional release date (ISO format)

        Raises:
            StorageError: If update fails
        """
        with self._get_connection() as conn:
            current_time = datetime.now(UTC).isoformat()

            conn.execute(
                """
                INSERT INTO framework_versions
                (framework, current_version, release_date, last_checked, updated_at)
                VALUES (?, ?, ?, ?, ?)
                ON CONFLICT(framework) DO UPDATE SET
                    current_version = excluded.current_version,
                    release_date = excluded.release_date,
                    last_checked = excluded.last_checked,
                    updated_at = excluded.updated_at
                """,
                (
                    framework,
                    version,
                    release_date,
                    current_time,
                    current_time,
                ),
            )

            conn.commit()

    def get_framework_version(self, framework: str) -> Optional[dict[str, Any]]:
        """
        Get framework version information.

        Args:
            framework: Framework identifier

        Returns:
            dict or None: Framework version info with:
                - framework: Framework identifier
                - current_version: Version string
                - release_date: Release date
                - last_checked: Last check timestamp
                - is_deprecated: Whether deprecated
                - notes: Additional notes

        Raises:
            StorageError: If retrieval fails
        """
        with self._get_connection() as conn:
            cursor = conn.execute(
                "SELECT * FROM framework_versions WHERE framework = ?",
                (framework,)
            )

            row = cursor.fetchone()
            if not row:
                return None

            return {
                "framework": row["framework"],
                "current_version": row["current_version"],
                "release_date": row["release_date"],
                "last_checked": row["last_checked"],
                "is_deprecated": bool(row["is_deprecated"]),
                "notes": row["notes"],
            }

    def mark_framework_deprecated(
        self,
        framework: str,
        notes: Optional[str] = None
    ) -> None:
        """
        Mark a framework as deprecated.

        Args:
            framework: Framework identifier
            notes: Optional deprecation notes

        Raises:
            StorageError: If update fails
        """
        with self._get_connection() as conn:
            conn.execute(
                """
                UPDATE framework_versions
                SET is_deprecated = 1, notes = ?, updated_at = ?
                WHERE framework = ?
                """,
                (notes, datetime.now(UTC).isoformat(), framework)
            )

            conn.commit()

    def get_assessment_details(self, assessment_id: int) -> dict[str, Any] | None:
        """
        Get full assessment details including evaluation results.

        Args:
            assessment_id: Database ID of assessment

        Returns:
            Full assessment data or None if not found
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            cursor.execute(
                "SELECT data FROM assessments WHERE id = ?",
                (assessment_id,),
            )

            row = cursor.fetchone()
            if not row:
                return None

            return json.loads(row[0])

    def _deserialize_assessment(self, data: dict[str, Any]) -> AssessmentResult:
        """Deserialize assessment from JSON."""
        from .models import (
            AnswerStatus,
            EvaluationResult,
            ResponseStrictness,
            RiskLevel,
        )

        evaluation_results = [
            EvaluationResult(
                question_id=r["question_id"],
                status=AnswerStatus(r["status"]),
                score=r["score"],
                risk_level=RiskLevel(r["risk_level"]),
                findings=r["findings"],
                recommendations=r["recommendations"],
                scf_controls_addressed=r["scf_controls_addressed"],
            )
            for r in data["evaluation_results"]
        ]

        return AssessmentResult(
            questionnaire_id=data["questionnaire_id"],
            vendor_name=data["vendor_name"],
            evaluation_results=evaluation_results,
            overall_score=data["overall_score"],
            overall_risk_level=RiskLevel(data["overall_risk_level"]),
            critical_findings=data["critical_findings"],
            compliance_gaps=data["compliance_gaps"],
            timestamp=data["timestamp"],
            strictness_level=ResponseStrictness(data["strictness_level"]),
        )

    def get_all_questionnaires(self, limit: int = 50) -> list[dict[str, Any]]:
        """
        Get all questionnaires (summary view).

        Args:
            limit: Maximum number to return

        Returns:
            list: List of questionnaire summaries

        Raises:
            StorageError: If retrieval fails
        """
        with self._get_connection() as conn:
            cursor = conn.execute(
                """
                SELECT id, framework, version, scope, entity_type, generation_timestamp
                FROM questionnaires
                ORDER BY generation_timestamp DESC
                LIMIT ?
                """,
                (limit,)
            )

            return [
                {
                    "id": row["id"],
                    "framework": row["framework"],
                    "version": row["version"],
                    "scope": row["scope"],
                    "entity_type": row["entity_type"],
                    "generated_at": row["generation_timestamp"],
                }
                for row in cursor.fetchall()
            ]

    def get_all_assessments(self, limit: int = 50) -> list[dict[str, Any]]:
        """
        Get all assessments (summary view).

        Args:
            limit: Maximum number to return

        Returns:
            list: List of assessment summaries

        Raises:
            StorageError: If retrieval fails
        """
        with self._get_connection() as conn:
            cursor = conn.execute(
                """
                SELECT id, vendor_name, overall_score, overall_risk_level, timestamp
                FROM assessments
                ORDER BY timestamp DESC
                LIMIT ?
                """,
                (limit,)
            )

            return [
                {
                    "id": row["id"],
                    "vendor_name": row["vendor_name"],
                    "overall_score": row["overall_score"],
                    "risk_level": row["overall_risk_level"],
                    "assessed_at": row["timestamp"],
                }
                for row in cursor.fetchall()
            ]

    def get_database_stats(self) -> dict[str, Any]:
        """
        Get database statistics.

        Returns:
            dict: Statistics including:
                - total_questionnaires: Total questionnaires
                - total_assessments: Total assessments
                - total_vendors: Unique vendors assessed
                - database_size_bytes: Database file size
                - database_path: Path to database

        Raises:
            StorageError: If stats retrieval fails
        """
        with self._get_connection() as conn:
            # Count questionnaires
            cursor = conn.execute("SELECT COUNT(*) as count FROM questionnaires")
            total_questionnaires = cursor.fetchone()["count"]

            # Count assessments
            cursor = conn.execute("SELECT COUNT(*) as count FROM assessments")
            total_assessments = cursor.fetchone()["count"]

            # Count unique vendors
            cursor = conn.execute("SELECT COUNT(DISTINCT vendor_name) as count FROM vendor_history")
            total_vendors = cursor.fetchone()["count"]

            # Get database size
            db_size = Path(self.db_path).stat().st_size if Path(self.db_path).exists() else 0

            return {
                "total_questionnaires": total_questionnaires,
                "total_assessments": total_assessments,
                "total_vendors": total_vendors,
                "database_size_bytes": db_size,
                "database_path": str(self.db_path),
            }

    def verify_storage(self) -> dict[str, Any]:
        """
        Verify storage is working and return statistics.

        Returns:
            Dictionary with storage status and statistics
        """
        try:
            stats = self.get_database_stats()
            return {
                "status": "healthy",
                **stats
            }
        except Exception as e:
            return {
                "status": "unhealthy",
                "database_path": self.db_path,
                "error": str(e),
            }
