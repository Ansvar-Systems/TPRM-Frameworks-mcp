#!/usr/bin/env python3
"""Database inspection tool for TPRM Frameworks MCP.

This script provides database inspection and verification functionality:
- Show database statistics (counts, sizes)
- List recent assessments
- Show vendor history
- Verify data integrity
- Display questionnaire details

Usage:
    python scripts/inspect_db.py --stats                    # Show database statistics
    python scripts/inspect_db.py --vendors                  # List all vendors
    python scripts/inspect_db.py --vendor-history <name>    # Show vendor assessment history
    python scripts/inspect_db.py --assessments              # List recent assessments
    python scripts/inspect_db.py --questionnaires           # List questionnaires
    python scripts/inspect_db.py --verify                   # Verify data integrity
    python scripts/inspect_db.py --assessment <id>          # Show assessment details
"""

import argparse
import json
import os
import sqlite3
import sys
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any

# Default database path
DEFAULT_DB_PATH = Path.home() / ".tprm-frameworks" / "tprm.db"


class DatabaseInspector:
    """Inspects and verifies TPRM database."""

    def __init__(self, db_path: Path):
        self.db_path = db_path
        if not self.db_path.exists():
            raise FileNotFoundError(f"Database not found: {self.db_path}")

    def get_connection(self) -> sqlite3.Connection:
        """Get a database connection."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row  # Return rows as dictionaries
        return conn

    def get_stats(self) -> Dict[str, Any]:
        """Get comprehensive database statistics."""
        conn = self.get_connection()
        cursor = conn.cursor()

        stats = {
            "database_path": str(self.db_path),
            "database_size_mb": self.db_path.stat().st_size / (1024 * 1024),
            "created": datetime.fromtimestamp(self.db_path.stat().st_ctime).isoformat(),
            "modified": datetime.fromtimestamp(self.db_path.stat().st_mtime).isoformat(),
        }

        # Get schema version
        try:
            cursor.execute("SELECT MAX(version) FROM schema_version")
            stats["schema_version"] = cursor.fetchone()[0] or 0
        except sqlite3.OperationalError:
            stats["schema_version"] = 0

        # Get table counts
        tables = ["vendors", "questionnaires", "assessments", "assessment_responses"]
        for table in tables:
            try:
                cursor.execute(f"SELECT COUNT(*) FROM {table}")
                stats[f"{table}_count"] = cursor.fetchone()[0]
            except sqlite3.OperationalError:
                stats[f"{table}_count"] = 0

        # Get average assessment score
        try:
            cursor.execute("SELECT AVG(overall_score) FROM assessments")
            avg_score = cursor.fetchone()[0]
            stats["average_assessment_score"] = round(avg_score, 2) if avg_score else 0
        except sqlite3.OperationalError:
            stats["average_assessment_score"] = 0

        # Get date range of assessments
        try:
            cursor.execute("SELECT MIN(created_at), MAX(created_at) FROM assessments")
            min_date, max_date = cursor.fetchone()
            stats["assessments_date_range"] = {
                "first": min_date,
                "last": max_date,
            }
        except sqlite3.OperationalError:
            stats["assessments_date_range"] = {"first": None, "last": None}

        conn.close()
        return stats

    def list_vendors(self, limit: int = None) -> List[Dict[str, Any]]:
        """List all vendors."""
        conn = self.get_connection()
        cursor = conn.cursor()

        query = """
            SELECT
                v.id,
                v.name,
                v.entity_type,
                v.created_at,
                COUNT(a.id) as assessment_count,
                MAX(a.created_at) as last_assessment,
                AVG(a.overall_score) as avg_score
            FROM vendors v
            LEFT JOIN assessments a ON v.id = a.vendor_id
            GROUP BY v.id
            ORDER BY v.name
        """

        if limit:
            query += f" LIMIT {limit}"

        cursor.execute(query)
        vendors = []

        for row in cursor.fetchall():
            vendors.append({
                "id": row["id"],
                "name": row["name"],
                "entity_type": row["entity_type"],
                "created_at": row["created_at"],
                "assessment_count": row["assessment_count"],
                "last_assessment": row["last_assessment"],
                "avg_score": round(row["avg_score"], 2) if row["avg_score"] else None,
            })

        conn.close()
        return vendors

    def get_vendor_history(self, vendor_name: str) -> Dict[str, Any]:
        """Get complete assessment history for a vendor."""
        conn = self.get_connection()
        cursor = conn.cursor()

        # Get vendor info
        cursor.execute("SELECT * FROM vendors WHERE name = ?", (vendor_name,))
        vendor = cursor.fetchone()

        if not vendor:
            conn.close()
            return None

        vendor_data = {
            "id": vendor["id"],
            "name": vendor["name"],
            "entity_type": vendor["entity_type"],
            "created_at": vendor["created_at"],
            "updated_at": vendor["updated_at"],
        }

        # Get assessments
        cursor.execute(
            """
            SELECT
                a.id,
                a.questionnaire_id,
                q.framework,
                q.version,
                a.overall_score,
                a.overall_risk_level,
                a.strictness_level,
                a.created_at,
                a.critical_findings,
                a.compliance_gaps
            FROM assessments a
            JOIN questionnaires q ON a.questionnaire_id = q.id
            WHERE a.vendor_id = ?
            ORDER BY a.created_at DESC
            """,
            (vendor["id"],),
        )

        assessments = []
        for row in cursor.fetchall():
            critical_findings = json.loads(row["critical_findings"]) if row["critical_findings"] else []
            compliance_gaps = json.loads(row["compliance_gaps"]) if row["compliance_gaps"] else {}

            assessments.append({
                "id": row["id"],
                "questionnaire_id": row["questionnaire_id"],
                "framework": row["framework"],
                "framework_version": row["version"],
                "overall_score": row["overall_score"],
                "overall_risk_level": row["overall_risk_level"],
                "strictness_level": row["strictness_level"],
                "created_at": row["created_at"],
                "critical_findings_count": len(critical_findings),
                "compliance_gaps_count": len(compliance_gaps),
            })

        vendor_data["assessments"] = assessments
        vendor_data["assessment_count"] = len(assessments)

        # Calculate trend
        if len(assessments) >= 2:
            scores = [a["overall_score"] for a in reversed(assessments)]
            trend = "improving" if scores[-1] > scores[0] else "declining" if scores[-1] < scores[0] else "stable"
            vendor_data["trend"] = trend
            vendor_data["score_change"] = round(scores[-1] - scores[0], 2)

        conn.close()
        return vendor_data

    def list_assessments(self, limit: int = 20) -> List[Dict[str, Any]]:
        """List recent assessments."""
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT
                a.id,
                a.vendor_name,
                q.framework,
                q.version,
                a.overall_score,
                a.overall_risk_level,
                a.created_at,
                COUNT(ar.id) as response_count
            FROM assessments a
            JOIN questionnaires q ON a.questionnaire_id = q.id
            LEFT JOIN assessment_responses ar ON a.id = ar.assessment_id
            GROUP BY a.id
            ORDER BY a.created_at DESC
            LIMIT ?
            """,
            (limit,),
        )

        assessments = []
        for row in cursor.fetchall():
            assessments.append({
                "id": row["id"],
                "vendor_name": row["vendor_name"],
                "framework": row["framework"],
                "framework_version": row["version"],
                "overall_score": row["overall_score"],
                "overall_risk_level": row["overall_risk_level"],
                "created_at": row["created_at"],
                "response_count": row["response_count"],
            })

        conn.close()
        return assessments

    def get_assessment_details(self, assessment_id: int) -> Dict[str, Any]:
        """Get detailed information about an assessment."""
        conn = self.get_connection()
        cursor = conn.cursor()

        # Get assessment
        cursor.execute(
            """
            SELECT
                a.*,
                q.framework,
                q.version,
                q.total_questions
            FROM assessments a
            JOIN questionnaires q ON a.questionnaire_id = q.id
            WHERE a.id = ?
            """,
            (assessment_id,),
        )

        assessment = cursor.fetchone()
        if not assessment:
            conn.close()
            return None

        result = {
            "id": assessment["id"],
            "vendor_name": assessment["vendor_name"],
            "questionnaire_id": assessment["questionnaire_id"],
            "framework": assessment["framework"],
            "framework_version": assessment["version"],
            "total_questions": assessment["total_questions"],
            "overall_score": assessment["overall_score"],
            "overall_risk_level": assessment["overall_risk_level"],
            "strictness_level": assessment["strictness_level"],
            "created_at": assessment["created_at"],
            "updated_at": assessment["updated_at"],
        }

        # Parse JSON fields
        result["critical_findings"] = json.loads(assessment["critical_findings"]) if assessment["critical_findings"] else []
        result["compliance_gaps"] = json.loads(assessment["compliance_gaps"]) if assessment["compliance_gaps"] else {}

        # Get response summary
        cursor.execute(
            """
            SELECT
                status,
                COUNT(*) as count,
                AVG(score) as avg_score
            FROM assessment_responses
            WHERE assessment_id = ?
            GROUP BY status
            """,
            (assessment_id,),
        )

        response_summary = {}
        for row in cursor.fetchall():
            response_summary[row["status"]] = {
                "count": row["count"],
                "avg_score": round(row["avg_score"], 2) if row["avg_score"] else 0,
            }

        result["response_summary"] = response_summary

        conn.close()
        return result

    def list_questionnaires(self) -> List[Dict[str, Any]]:
        """List all questionnaires."""
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT
                q.id,
                q.framework,
                q.version,
                q.scope,
                q.entity_type,
                q.total_questions,
                q.generation_timestamp,
                COUNT(a.id) as usage_count
            FROM questionnaires q
            LEFT JOIN assessments a ON q.id = a.questionnaire_id
            GROUP BY q.id
            ORDER BY q.generation_timestamp DESC
            """
        )

        questionnaires = []
        for row in cursor.fetchall():
            questionnaires.append({
                "id": row["id"],
                "framework": row["framework"],
                "version": row["version"],
                "scope": row["scope"],
                "entity_type": row["entity_type"],
                "total_questions": row["total_questions"],
                "generation_timestamp": row["generation_timestamp"],
                "usage_count": row["usage_count"],
            })

        conn.close()
        return questionnaires

    def verify_integrity(self) -> Dict[str, Any]:
        """Verify database integrity."""
        conn = self.get_connection()
        cursor = conn.cursor()

        issues = []
        warnings = []
        checks = {
            "sqlite_integrity": False,
            "foreign_keys": False,
            "orphaned_assessments": False,
            "orphaned_responses": False,
            "json_validity": False,
        }

        # Check SQLite integrity
        cursor.execute("PRAGMA integrity_check")
        result = cursor.fetchone()[0]
        checks["sqlite_integrity"] = result == "ok"
        if result != "ok":
            issues.append(f"SQLite integrity check failed: {result}")

        # Check foreign key constraints
        cursor.execute("PRAGMA foreign_key_check")
        fk_violations = cursor.fetchall()
        checks["foreign_keys"] = len(fk_violations) == 0
        if fk_violations:
            issues.append(f"Foreign key violations found: {len(fk_violations)}")

        # Check for orphaned assessments (vendor doesn't exist)
        cursor.execute(
            """
            SELECT COUNT(*)
            FROM assessments a
            LEFT JOIN vendors v ON a.vendor_id = v.id
            WHERE v.id IS NULL
            """
        )
        orphaned_assessments = cursor.fetchone()[0]
        checks["orphaned_assessments"] = orphaned_assessments == 0
        if orphaned_assessments > 0:
            issues.append(f"Found {orphaned_assessments} orphaned assessments")

        # Check for orphaned responses (assessment doesn't exist)
        cursor.execute(
            """
            SELECT COUNT(*)
            FROM assessment_responses ar
            LEFT JOIN assessments a ON ar.assessment_id = a.id
            WHERE a.id IS NULL
            """
        )
        orphaned_responses = cursor.fetchone()[0]
        checks["orphaned_responses"] = orphaned_responses == 0
        if orphaned_responses > 0:
            issues.append(f"Found {orphaned_responses} orphaned responses")

        # Check JSON validity in assessments
        try:
            cursor.execute("SELECT id, critical_findings, compliance_gaps FROM assessments")
            json_errors = 0
            for row in cursor.fetchall():
                try:
                    if row["critical_findings"]:
                        json.loads(row["critical_findings"])
                    if row["compliance_gaps"]:
                        json.loads(row["compliance_gaps"])
                except json.JSONDecodeError:
                    json_errors += 1

            checks["json_validity"] = json_errors == 0
            if json_errors > 0:
                issues.append(f"Found {json_errors} records with invalid JSON")
        except Exception as e:
            checks["json_validity"] = False
            issues.append(f"JSON validation error: {e}")

        # Additional warnings
        stats = self.get_stats()
        if stats["vendors_count"] == 0:
            warnings.append("No vendors in database")
        if stats["assessments_count"] == 0:
            warnings.append("No assessments in database")

        conn.close()

        return {
            "healthy": len(issues) == 0,
            "checks": checks,
            "issues": issues,
            "warnings": warnings,
        }


def print_stats(stats: Dict[str, Any]):
    """Print database statistics."""
    print("\n" + "=" * 80)
    print("DATABASE STATISTICS")
    print("=" * 80)
    print(f"\nPath: {stats['database_path']}")
    print(f"Size: {stats['database_size_mb']:.2f} MB")
    print(f"Schema Version: {stats['schema_version']}")
    print(f"Created: {stats['created']}")
    print(f"Modified: {stats['modified']}")

    print("\nRecord Counts:")
    print(f"  Vendors: {stats['vendors_count']}")
    print(f"  Questionnaires: {stats['questionnaires_count']}")
    print(f"  Assessments: {stats['assessments_count']}")
    print(f"  Assessment Responses: {stats['assessment_responses_count']}")

    if stats['assessments_count'] > 0:
        print(f"\nAssessment Metrics:")
        print(f"  Average Score: {stats['average_assessment_score']}")
        date_range = stats['assessments_date_range']
        if date_range['first'] and date_range['last']:
            print(f"  Date Range: {date_range['first']} to {date_range['last']}")

    print("=" * 80 + "\n")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Database inspection and verification tool")
    parser.add_argument(
        "--db-path",
        type=Path,
        default=os.environ.get("DATABASE_PATH", DEFAULT_DB_PATH),
        help=f"Path to database file (default: {DEFAULT_DB_PATH})",
    )

    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--stats", action="store_true", help="Show database statistics")
    group.add_argument("--vendors", action="store_true", help="List all vendors")
    group.add_argument("--vendor-history", type=str, help="Show vendor assessment history")
    group.add_argument("--assessments", action="store_true", help="List recent assessments")
    group.add_argument("--assessment", type=int, help="Show assessment details")
    group.add_argument("--questionnaires", action="store_true", help="List questionnaires")
    group.add_argument("--verify", action="store_true", help="Verify data integrity")

    parser.add_argument("--limit", type=int, default=20, help="Limit number of results")
    parser.add_argument("--json", action="store_true", help="Output as JSON")

    args = parser.parse_args()

    try:
        inspector = DatabaseInspector(args.db_path)

        if args.stats:
            stats = inspector.get_stats()
            if args.json:
                print(json.dumps(stats, indent=2))
            else:
                print_stats(stats)

        elif args.vendors:
            vendors = inspector.list_vendors(limit=args.limit)
            if args.json:
                print(json.dumps(vendors, indent=2))
            else:
                print(f"\nVendors ({len(vendors)}):")
                print("-" * 80)
                for v in vendors:
                    print(f"\n{v['name']} (ID: {v['id']})")
                    print(f"  Type: {v['entity_type'] or 'N/A'}")
                    print(f"  Assessments: {v['assessment_count']}")
                    if v['avg_score']:
                        print(f"  Average Score: {v['avg_score']}")
                    if v['last_assessment']:
                        print(f"  Last Assessment: {v['last_assessment']}")
                print("-" * 80 + "\n")

        elif args.vendor_history:
            history = inspector.get_vendor_history(args.vendor_history)
            if not history:
                print(f"Vendor '{args.vendor_history}' not found")
                return 1

            if args.json:
                print(json.dumps(history, indent=2))
            else:
                print(f"\nVendor History: {history['name']}")
                print("=" * 80)
                print(f"Entity Type: {history['entity_type'] or 'N/A'}")
                print(f"Created: {history['created_at']}")
                print(f"Total Assessments: {history['assessment_count']}")

                if 'trend' in history:
                    print(f"Trend: {history['trend']} ({history['score_change']:+.2f})")

                print(f"\nAssessment History ({len(history['assessments'])}):")
                print("-" * 80)
                for a in history['assessments']:
                    print(f"\nID: {a['id']} | {a['created_at']}")
                    print(f"  Framework: {a['framework']} v{a['framework_version']}")
                    print(f"  Score: {a['overall_score']:.1f} | Risk: {a['overall_risk_level']}")
                    print(f"  Critical Findings: {a['critical_findings_count']}")
                    print(f"  Compliance Gaps: {a['compliance_gaps_count']}")
                print("=" * 80 + "\n")

        elif args.assessments:
            assessments = inspector.list_assessments(limit=args.limit)
            if args.json:
                print(json.dumps(assessments, indent=2))
            else:
                print(f"\nRecent Assessments ({len(assessments)}):")
                print("-" * 80)
                for a in assessments:
                    print(f"\nID: {a['id']} | {a['vendor_name']}")
                    print(f"  Framework: {a['framework']} v{a['framework_version']}")
                    print(f"  Score: {a['overall_score']:.1f} | Risk: {a['overall_risk_level']}")
                    print(f"  Responses: {a['response_count']}")
                    print(f"  Date: {a['created_at']}")
                print("-" * 80 + "\n")

        elif args.assessment:
            details = inspector.get_assessment_details(args.assessment)
            if not details:
                print(f"Assessment {args.assessment} not found")
                return 1

            if args.json:
                print(json.dumps(details, indent=2))
            else:
                print(f"\nAssessment Details: {details['id']}")
                print("=" * 80)
                print(f"Vendor: {details['vendor_name']}")
                print(f"Framework: {details['framework']} v{details['framework_version']}")
                print(f"Questionnaire ID: {details['questionnaire_id']}")
                print(f"Overall Score: {details['overall_score']:.1f}")
                print(f"Risk Level: {details['overall_risk_level']}")
                print(f"Strictness: {details['strictness_level']}")
                print(f"Created: {details['created_at']}")

                print(f"\nResponse Summary:")
                for status, info in details['response_summary'].items():
                    print(f"  {status}: {info['count']} (avg score: {info['avg_score']})")

                if details['critical_findings']:
                    print(f"\nCritical Findings ({len(details['critical_findings'])}):")
                    for finding in details['critical_findings'][:5]:
                        print(f"  - {finding}")

                if details['compliance_gaps']:
                    print(f"\nCompliance Gaps:")
                    for reg, gaps in details['compliance_gaps'].items():
                        print(f"  {reg}: {len(gaps)} gaps")

                print("=" * 80 + "\n")

        elif args.questionnaires:
            questionnaires = inspector.list_questionnaires()
            if args.json:
                print(json.dumps(questionnaires, indent=2))
            else:
                print(f"\nQuestionnaires ({len(questionnaires)}):")
                print("-" * 80)
                for q in questionnaires:
                    print(f"\nID: {q['id'][:8]}...")
                    print(f"  Framework: {q['framework']} v{q['version']}")
                    print(f"  Scope: {q['scope'] or 'N/A'} | Type: {q['entity_type'] or 'N/A'}")
                    print(f"  Questions: {q['total_questions']}")
                    print(f"  Used in {q['usage_count']} assessment(s)")
                    print(f"  Generated: {q['generation_timestamp']}")
                print("-" * 80 + "\n")

        elif args.verify:
            result = inspector.verify_integrity()
            if args.json:
                print(json.dumps(result, indent=2))
            else:
                print("\nDatabase Integrity Verification")
                print("=" * 80)

                print("\nChecks:")
                for check, passed in result['checks'].items():
                    status = "✓ PASS" if passed else "✗ FAIL"
                    print(f"  {status}: {check}")

                if result['issues']:
                    print(f"\nIssues Found ({len(result['issues'])}):")
                    for issue in result['issues']:
                        print(f"  ✗ {issue}")

                if result['warnings']:
                    print(f"\nWarnings ({len(result['warnings'])}):")
                    for warning in result['warnings']:
                        print(f"  ⚠ {warning}")

                print("\nOverall Status:", "✓ HEALTHY" if result['healthy'] else "✗ ISSUES FOUND")
                print("=" * 80 + "\n")

        return 0

    except FileNotFoundError as e:
        print(f"✗ Error: {e}", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"✗ Unexpected error: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
