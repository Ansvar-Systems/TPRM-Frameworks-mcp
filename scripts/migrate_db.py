#!/usr/bin/env python3
"""Database migration tool for TPRM Frameworks MCP.

This script manages database schema migrations, allowing you to:
- Check the current schema version
- Apply pending migrations
- Backup database before migration
- Rollback on failure

Usage:
    python scripts/migrate_db.py --check          # Check current version
    python scripts/migrate_db.py --migrate        # Apply migrations
    python scripts/migrate_db.py --rollback       # Rollback last migration
    python scripts/migrate_db.py --force-version <version>  # Set version manually
"""

import argparse
import os
import sqlite3
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Tuple

# Add parent directory to path to import from src
sys.path.insert(0, str(Path(__file__).parent.parent))

# Default database path
DEFAULT_DB_PATH = Path.home() / ".tprm-frameworks" / "tprm.db"


class Migration:
    """Represents a single database migration."""

    def __init__(self, version: int, description: str, up_sql: str, down_sql: str):
        self.version = version
        self.description = description
        self.up_sql = up_sql
        self.down_sql = down_sql


# Define all migrations
MIGRATIONS: List[Migration] = [
    Migration(
        version=1,
        description="Initial schema - questionnaires and assessments",
        up_sql="""
        -- Schema version tracking
        CREATE TABLE IF NOT EXISTS schema_version (
            version INTEGER PRIMARY KEY,
            applied_at TEXT NOT NULL,
            description TEXT NOT NULL
        );

        -- Vendors table
        CREATE TABLE IF NOT EXISTS vendors (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE,
            entity_type TEXT,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            metadata TEXT  -- JSON storage for additional vendor info
        );

        -- Questionnaires table
        CREATE TABLE IF NOT EXISTS questionnaires (
            id TEXT PRIMARY KEY,
            framework TEXT NOT NULL,
            version TEXT NOT NULL,
            scope TEXT,
            entity_type TEXT,
            total_questions INTEGER NOT NULL,
            categories TEXT,  -- JSON array
            applicable_regulations TEXT,  -- JSON array
            generation_timestamp TEXT NOT NULL,
            custom_parameters TEXT,  -- JSON object
            questions_data TEXT NOT NULL  -- Complete questions JSON
        );

        -- Assessments table
        CREATE TABLE IF NOT EXISTS assessments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            vendor_id INTEGER NOT NULL,
            questionnaire_id TEXT NOT NULL,
            vendor_name TEXT NOT NULL,
            overall_score REAL NOT NULL,
            overall_risk_level TEXT NOT NULL,
            strictness_level TEXT NOT NULL,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            evaluation_results TEXT NOT NULL,  -- JSON
            critical_findings TEXT,  -- JSON array
            compliance_gaps TEXT,  -- JSON object
            FOREIGN KEY (vendor_id) REFERENCES vendors(id),
            FOREIGN KEY (questionnaire_id) REFERENCES questionnaires(id)
        );

        -- Assessment responses table (for detailed tracking)
        CREATE TABLE IF NOT EXISTS assessment_responses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            assessment_id INTEGER NOT NULL,
            question_id TEXT NOT NULL,
            answer TEXT,
            status TEXT NOT NULL,
            score REAL NOT NULL,
            risk_level TEXT NOT NULL,
            findings TEXT,  -- JSON array
            recommendations TEXT,  -- JSON array
            scf_controls TEXT,  -- JSON array
            supporting_documents TEXT,  -- JSON array
            notes TEXT,
            created_at TEXT NOT NULL,
            FOREIGN KEY (assessment_id) REFERENCES assessments(id)
        );

        -- Indexes for performance
        CREATE INDEX IF NOT EXISTS idx_assessments_vendor ON assessments(vendor_id);
        CREATE INDEX IF NOT EXISTS idx_assessments_questionnaire ON assessments(questionnaire_id);
        CREATE INDEX IF NOT EXISTS idx_assessments_created ON assessments(created_at);
        CREATE INDEX IF NOT EXISTS idx_responses_assessment ON assessment_responses(assessment_id);
        CREATE INDEX IF NOT EXISTS idx_responses_question ON assessment_responses(question_id);
        CREATE INDEX IF NOT EXISTS idx_vendors_name ON vendors(name);
        """,
        down_sql="""
        DROP INDEX IF EXISTS idx_vendors_name;
        DROP INDEX IF EXISTS idx_responses_question;
        DROP INDEX IF EXISTS idx_responses_assessment;
        DROP INDEX IF EXISTS idx_assessments_created;
        DROP INDEX IF EXISTS idx_assessments_questionnaire;
        DROP INDEX IF EXISTS idx_assessments_vendor;
        DROP TABLE IF EXISTS assessment_responses;
        DROP TABLE IF EXISTS assessments;
        DROP TABLE IF EXISTS questionnaires;
        DROP TABLE IF EXISTS vendors;
        DROP TABLE IF EXISTS schema_version;
        """,
    ),
]


class DatabaseMigrator:
    """Manages database migrations."""

    def __init__(self, db_path: Path):
        self.db_path = db_path
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

    def get_connection(self) -> sqlite3.Connection:
        """Get a database connection."""
        return sqlite3.connect(self.db_path)

    def get_current_version(self) -> int:
        """Get the current schema version."""
        conn = self.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='schema_version'"
            )
            if not cursor.fetchone():
                return 0

            cursor.execute("SELECT MAX(version) FROM schema_version")
            result = cursor.fetchone()
            return result[0] if result[0] is not None else 0
        finally:
            conn.close()

    def get_pending_migrations(self) -> List[Migration]:
        """Get list of pending migrations."""
        current_version = self.get_current_version()
        return [m for m in MIGRATIONS if m.version > current_version]

    def backup_database(self) -> Path:
        """Create a backup of the database."""
        if not self.db_path.exists():
            print("No database to backup.")
            return None

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_dir = self.db_path.parent / "backups"
        backup_dir.mkdir(exist_ok=True)
        backup_path = backup_dir / f"tprm_backup_{timestamp}.db"

        # Copy database file
        import shutil

        shutil.copy2(self.db_path, backup_path)
        print(f"✓ Database backed up to: {backup_path}")
        return backup_path

    def apply_migration(self, migration: Migration) -> bool:
        """Apply a single migration."""
        print(f"Applying migration {migration.version}: {migration.description}")

        conn = self.get_connection()
        try:
            cursor = conn.cursor()

            # Execute migration SQL
            cursor.executescript(migration.up_sql)

            # Record migration
            cursor.execute(
                """
                INSERT INTO schema_version (version, applied_at, description)
                VALUES (?, ?, ?)
                """,
                (migration.version, datetime.now(timezone.utc).isoformat(), migration.description),
            )

            conn.commit()
            print(f"✓ Migration {migration.version} applied successfully")
            return True

        except Exception as e:
            conn.rollback()
            print(f"✗ Migration {migration.version} failed: {e}")
            return False
        finally:
            conn.close()

    def migrate(self, backup: bool = True) -> bool:
        """Apply all pending migrations."""
        pending = self.get_pending_migrations()

        if not pending:
            print("✓ Database is up to date (version {})".format(self.get_current_version()))
            return True

        print(f"Found {len(pending)} pending migration(s)")

        # Backup before migration
        if backup:
            backup_path = self.backup_database()
            if backup_path is None and self.db_path.exists():
                return False

        # Apply migrations
        for migration in pending:
            if not self.apply_migration(migration):
                print("\n⚠️  Migration failed! Database may be in inconsistent state.")
                if backup and backup_path:
                    print(f"You can restore from backup: {backup_path}")
                return False

        current_version = self.get_current_version()
        print(f"\n✓ All migrations applied successfully (version {current_version})")
        return True

    def rollback(self) -> bool:
        """Rollback the last migration."""
        current_version = self.get_current_version()

        if current_version == 0:
            print("No migrations to rollback")
            return False

        # Find the migration to rollback
        migration = next((m for m in MIGRATIONS if m.version == current_version), None)
        if not migration:
            print(f"Migration {current_version} not found in migration list")
            return False

        print(f"Rolling back migration {migration.version}: {migration.description}")

        # Backup before rollback
        backup_path = self.backup_database()

        conn = self.get_connection()
        try:
            cursor = conn.cursor()

            # Execute rollback SQL
            cursor.executescript(migration.down_sql)

            # Remove version record (if table still exists)
            try:
                cursor.execute("DELETE FROM schema_version WHERE version = ?", (migration.version,))
            except sqlite3.OperationalError:
                pass  # Table was dropped

            conn.commit()
            print(f"✓ Migration {migration.version} rolled back successfully")
            return True

        except Exception as e:
            conn.rollback()
            print(f"✗ Rollback failed: {e}")
            if backup_path:
                print(f"You can restore from backup: {backup_path}")
            return False
        finally:
            conn.close()

    def force_version(self, version: int) -> bool:
        """Force set the schema version (use with caution)."""
        print(f"⚠️  Force setting schema version to {version}")

        if version < 0 or version > len(MIGRATIONS):
            print(f"Invalid version: {version}")
            return False

        # Backup first
        self.backup_database()

        conn = self.get_connection()
        try:
            cursor = conn.cursor()

            # Ensure schema_version table exists
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS schema_version (
                    version INTEGER PRIMARY KEY,
                    applied_at TEXT NOT NULL,
                    description TEXT NOT NULL
                )
                """
            )

            # Delete all version records
            cursor.execute("DELETE FROM schema_version")

            # Insert new version
            if version > 0:
                migration = next((m for m in MIGRATIONS if m.version == version), None)
                if not migration:
                    print(f"Migration {version} not found")
                    return False

                cursor.execute(
                    """
                    INSERT INTO schema_version (version, applied_at, description)
                    VALUES (?, ?, ?)
                    """,
                    (version, datetime.now(timezone.utc).isoformat(), migration.description),
                )

            conn.commit()
            print(f"✓ Schema version set to {version}")
            return True

        except Exception as e:
            conn.rollback()
            print(f"✗ Failed to set version: {e}")
            return False
        finally:
            conn.close()

    def get_migration_status(self) -> List[Tuple[int, str, bool]]:
        """Get status of all migrations."""
        current_version = self.get_current_version()
        return [
            (m.version, m.description, m.version <= current_version) for m in MIGRATIONS
        ]


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Database migration tool for TPRM Frameworks MCP")
    parser.add_argument(
        "--db-path",
        type=Path,
        default=os.environ.get("DATABASE_PATH", DEFAULT_DB_PATH),
        help=f"Path to database file (default: {DEFAULT_DB_PATH})",
    )

    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--check", action="store_true", help="Check current schema version")
    group.add_argument("--status", action="store_true", help="Show migration status")
    group.add_argument("--migrate", action="store_true", help="Apply pending migrations")
    group.add_argument("--rollback", action="store_true", help="Rollback last migration")
    group.add_argument("--force-version", type=int, help="Force set schema version (dangerous)")

    parser.add_argument(
        "--no-backup", action="store_true", help="Skip backup before migration (not recommended)"
    )

    args = parser.parse_args()

    migrator = DatabaseMigrator(args.db_path)

    if args.check:
        version = migrator.get_current_version()
        print(f"Current schema version: {version}")
        pending = migrator.get_pending_migrations()
        if pending:
            print(f"Pending migrations: {len(pending)}")
            for m in pending:
                print(f"  - v{m.version}: {m.description}")
        else:
            print("Database is up to date")
        return 0

    elif args.status:
        print("Migration Status:")
        print("-" * 80)
        for version, description, applied in migrator.get_migration_status():
            status = "✓ APPLIED" if applied else "  PENDING"
            print(f"{status}  v{version}: {description}")
        print("-" * 80)
        return 0

    elif args.migrate:
        success = migrator.migrate(backup=not args.no_backup)
        return 0 if success else 1

    elif args.rollback:
        success = migrator.rollback()
        return 0 if success else 1

    elif args.force_version is not None:
        success = migrator.force_version(args.force_version)
        return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
